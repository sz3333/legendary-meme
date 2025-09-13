# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/

# meta developer: Femboy4k.t.me
from telethon import events
from .. import loader, utils
from telethon.tl.types import Message
import random
import logging
import asyncio
import sqlite3
import os
import aiohttp
from telethon.errors import ChannelPrivateError, ChannelInvalidError, PeerIdInvalidError, RPCError

logger = logging.getLogger(__name__)
DB_PATH = "furry_cache.db"

@loader.tds
class FurryCacheMod(loader.Module):
    """Няшный NSFW Furry мод с кэшем, шифрованием и лапками 🐾 + арты e621"""

    strings = {
        "name": "Furry NSFW (Gay++)",
        "fetching": "Мяу~ тяну из хранилища арт 🐾",
        "fetching_remote": "Мурр~ загружаю сообщения с канала… потерпи котейку~",
        "no_media": "Ничего не нашёл, даже хвостик не видно :(",
        "error": "Упс... что-то поломалось 🧨",
        "cleared": "Кеш очищен! Чисто как в ванной после тебя 🛁",
        "info": "📦 В кеше: <b>{}</b> медиа\n🔁 Запросов: <b>{}</b>",
        "channel_error": "Все каналы недоступны 😿 Попробуй добавить свой канал командой .furrset <канал>",
        "channel_set": "✅ Канал установлен: <b>{}</b>",
        "no_cache": "Кеш пуст! Сначала загрузи медиа командой .furrload"
    }

    def __init__(self):
        self._init_db()
        self.running = False
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channels",
                ["@FurryFemboysPlace", "fur_pub_sas", "gexfor20"],
                "Список каналов для загрузки (через запятую или список)",
                validator=loader.validators.Union(
                    loader.validators.Series(loader.validators.String()),
                    loader.validators.String()
                )
            ),
            loader.ConfigValue(
                "max_messages",
                2000,
                "Максимум сообщений для загрузки",
                validator=loader.validators.Integer(minimum=100, maximum=10000)
            )
        )

    # ================== e621 ==================
    async def e6cmd(self, message):
        """Ищет арты на e621: .e6 тег;тег;тег количество"""
        args = utils.get_args_raw(message).split()
        if len(args) < 2:
            await utils.answer(message, "❌ Используй: `.e6 femboy;catboy 5`")
            return

        tags = args[0].split(";")
        try:
            count = int(args[1])
        except ValueError:
            await utils.answer(message, "❌ Количество должно быть числом")
            return

        self.running = True
        await utils.answer(message, f"🧦 Отправляю {count} артов с тегами: {', '.join(tags)}")
        asyncio.create_task(self._send_e6(message, tags, count))

    async def _send_e6(self, message, tags, count):
        headers = {"User-Agent": "HikkaBot/1.0 by Lidik"}
        sent = 0
        tag_query = "+".join(tags)

        async with aiohttp.ClientSession() as session:
            while self.running and sent < count:
                url = f"https://e621.net/posts.json?tags={tag_query}+order:random&limit=1"
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            await asyncio.sleep(10)
                            continue

                        data = await resp.json()
                        posts = data.get("posts", [])

                        for post in posts:
                            file_url = post.get("file", {}).get("url")
                            if not file_url:
                                continue
                            try:
                                await message.client.send_file(
                                    message.chat_id,
                                    file_url,
                                    caption=f"🎨 Теги: {', '.join(tags)}"
                                )
                                sent += 1
                            except Exception:
                                continue
                            await asyncio.sleep(random.randint(5, 10))
                except Exception:
                    await asyncio.sleep(5)

        await message.respond("✅ Отправка завершена.")

    async def stop_e6cmd(self, message):
        """Остановить e621 загрузку"""
        self.running = False
        await utils.answer(message, "🛑 e621 остановлен.")

    # ================== FurryCache ==================
    def _init_db(self):
        self._conn = sqlite3.connect(DB_PATH)
        cursor = self._conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message_id INTEGER,
            UNIQUE(chat_id, message_id)
        )""")
        try:
            cursor.execute("SELECT channel_name FROM media LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE media ADD COLUMN channel_name TEXT DEFAULT 'unknown'")
        cursor.execute("""CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            chat_id INTEGER,
            accessible INTEGER DEFAULT 1
        )""")
        self._conn.commit()

    def _increment_stat(self, key):
        cursor = self._conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0)", (key,))
        cursor.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
        self._conn.commit()

    def _get_stat(self, key):
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM stats WHERE key = ?", (key,))
        res = cursor.fetchone()
        return res[0] if res else 0

    def _get_channels(self):
        channels = self.config["channels"]
        if isinstance(channels, str):
            channels = [c.strip() for c in channels.split(",")]
        fallback_channels = ["gexfor20","@gexfor20","furryart","@furryart","furry_nsfw","@furry_nsfw"]
        return list(dict.fromkeys(channels + fallback_channels))

    async def _test_channel_access(self, channel_name):
        try:
            channel = await self.client.get_entity(channel_name)
            messages = await self.client.get_messages(channel, limit=1)
            return channel, True
        except Exception as e:
            logger.warning(f"Канал {channel_name} недоступен: {e}")
            return None, False

    async def _find_accessible_channels(self):
        channels = self._get_channels()
        accessible = []
        for channel_name in channels:
            channel, is_accessible = await self._test_channel_access(channel_name)
            if is_accessible:
                accessible.append((channel_name, channel))
                logger.info(f"✅ Канал доступен: {channel_name}")
            await asyncio.sleep(0.5)
        return accessible

    async def _load_from_channel(self, channel_name, channel, max_messages):
        media_loaded = 0
        offset_id = 0
        limit = 100
        try:
            while media_loaded < max_messages:
                messages = await self.client.get_messages(channel, limit=min(limit, max_messages - media_loaded), offset_id=offset_id)
                if not messages:
                    break
                cursor = self._conn.cursor()
                for msg in messages:
                    if msg.media:
                        try:
                            cursor.execute("INSERT OR IGNORE INTO media (chat_id, message_id, channel_name) VALUES (?, ?, ?)",
                                           (msg.chat_id, msg.id, channel_name))
                            media_loaded += 1
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении медиа: {e}")
                self._conn.commit()
                if messages:
                    offset_id = messages[-1].id
                await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Ошибка при загрузке из {channel_name}: {e}")
        return media_loaded

    async def furrloadcmd(self, message: Message):
        await utils.answer(message, "🔍 Ищу доступные каналы...")
        accessible_channels = await self._find_accessible_channels()
        if not accessible_channels:
            await utils.answer(message, self.strings("channel_error"))
            return
        await utils.answer(message, f"📥 Загружаю из {len(accessible_channels)} каналов...")
        total_loaded = 0
        max_per_channel = self.config["max_messages"] // len(accessible_channels)
        for channel_name, channel in accessible_channels:
            loaded = await self._load_from_channel(channel_name, channel, max_per_channel)
            total_loaded += loaded
        await utils.answer(message, f"✅ Загружено {total_loaded} медиа файлов!")

    async def furrcmd(self, message: Message):
        try:
            await utils.answer(message, self.strings("fetching"))
            cursor = self._conn.cursor()
            try:
                cursor.execute("SELECT chat_id, message_id, channel_name FROM media ORDER BY RANDOM() LIMIT 1")
                row = cursor.fetchone()
                if row:
                    chat_id, msg_id, channel_name = row
                else:
                    await utils.answer(message, self.strings("no_cache"))
                    return
            except sqlite3.Operational