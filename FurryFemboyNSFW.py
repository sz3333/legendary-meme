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

    # Остальной код твоего FurryCache (furrloadcmd, furrcmd, furrsetcmd, furrinfocmd, furrclearcmd)
    # можно вставить сюда без изменений, чтобы всё в одном модуле