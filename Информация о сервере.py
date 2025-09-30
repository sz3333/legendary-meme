# meta developer: @Femboy4k

import contextlib
import os
import platform
import sys
import time
from datetime import timedelta
import psutil
from telethon.tl.types import Message
from .. import loader, utils
#кто прочитал тот гейчик

def bytes_to_megabytes(b: int) -> float:
    return round(b / 1024 / 1024, 1)

def bytes_to_gb(b: int) -> float:
    return round(b / 1024 / 1024 / 1024, 2)

def seconds_to_readable(seconds: int) -> str:
    return str(timedelta(seconds=seconds))

@loader.tds
class serverInfoMod(loader.Module):
    """Модуль для мониторинга параметров системы и сервера"""

    strings = {"name": "Детальный мониторинг сервера"}

    @loader.command()
    async def infoserv(self, message: Message):
        """Выводит мониторинг всех системных параметров сервера"""
        await utils.answer(message, "Собираю информацию о сервере...")

    strings = {
        "name": "Информация о сервере",
        "loading": "⚙️ Жди, я загружаю информацию",
        "servinfo": (
            "⚙️ Информация о сервере:\n\n"
            "📝 ЦПУ: {cpu_cores} ядра @ {cpu_freq} ГГц, нагрузка: {cpu_load}%\n"
            "👌 Память: {ram_used} / {ram_total} МБ ({ram_percent}%)\n"
            "💾 Диск: {disk_used} / {disk_total} ГБ ({disk_percent}%)\n"
            "🖥 Ядро: {kernel}\n"
            "💻 Архитектура: {arch}\n"
            "⚠ Операционная система: {os}\n"
            "❄ Температура: {temperature}\n"
            "💻 Скорость вентилятора: {fan_speed}\n"
            "🚄 Пинг: {ping} мс\n"
            "🕘 Время работы: {uptime}\n"
            "👨‍💻 Версия Python: {python}\n"
            "📺 Процессы: {processes}\n"
            "🌕 Пользователи: {users}"
        ),
    }

    @loader.command()
    async def serverinfo(self, message: Message):
        """Показывает детальную информацию о сервере"""
        await utils.answer(message, self.strings("loading"))

        info = {
            "cpu_cores": "n/a",
            "cpu_freq": "n/a",
            "cpu_load": "n/a",
            "ram_used": "n/a",
            "ram_total": "n/a",
            "ram_percent": "n/a",
            "disk_used": "n/a",
            "disk_total": "n/a",
            "disk_percent": "n/a",
            "kernel": "n/a",
            "arch": "n/a",
            "os": "n/a",
            "temperature": "n/a",
            "fan_speed": "n/a",
            "ping": "n/a",
            "uptime": "n/a",
            "python": "n/a",
            "processes": "n/a",
            "users": "n/a",
        }

        # Информация о процессоре
        with contextlib.suppress(Exception):
            info["cpu_cores"] = psutil.cpu_count(logical=True)

        with contextlib.suppress(Exception):
            cpu_freq = psutil.cpu_freq().current / 1000  # Перевод в ГГц
            info["cpu_freq"] = round(cpu_freq, 2)

        with contextlib.suppress(Exception):
            info["cpu_load"] = psutil.cpu_percent()

        # Информация о памяти
        with contextlib.suppress(Exception):
            ram = psutil.virtual_memory()
            info["ram_used"] = bytes_to_megabytes(ram.used)
            info["ram_total"] = bytes_to_megabytes(ram.total)
            info["ram_percent"] = ram.percent

        # Информация о диске
        with contextlib.suppress(Exception):
            disk = psutil.disk_usage("/")
            info["disk_used"] = bytes_to_gb(disk.used)
            info["disk_total"] = bytes_to_gb(disk.total)
            info["disk_percent"] = disk.percent

        # Информация о ядре и ОС
        with contextlib.suppress(Exception):
            info["kernel"] = platform.release()

        with contextlib.suppress(Exception):
            info["arch"] = platform.architecture()[0]

        with contextlib.suppress(Exception):
            system = os.popen("cat /etc/*release").read()
            b = system.find('PRETTY_NAME="') + 13
            info["os"] = system[b : system.find('"', b)]

        # Температура и скорость вентилятора
        with contextlib.suppress(Exception):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                info["temperature"] = f"{temps['coretemp'][0].current}°C"
            else:
                info["temperature"] = "Не поддерживается"

        with contextlib.suppress(Exception):
            fans = psutil.sensors_fans()
            if fans:
                fan_speeds = [f.current for f in fans.get(next(iter(fans)), []) if f.current]
                info["fan_speed"] = f"{fan_speeds[0]} RPM" if fan_speeds else "Не поддерживается"

        # Пинг
        with contextlib.suppress(Exception):
            start = time.time()
            os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
            info["ping"] = round((time.time() - start) * 1000, 2)

        # Время работы
        with contextlib.suppress(Exception):
            uptime_seconds = time.time() - psutil.boot_time()
            info["uptime"] = seconds_to_readable(int(uptime_seconds))

        # Версия Python
        with contextlib.suppress(Exception):
            info["python"] = (
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            )

        # Процессы
        with contextlib.suppress(Exception):
            info["processes"] = len(psutil.pids())

        # Пользователи
        with contextlib.suppress(Exception):
            users = psutil.users()
            info["users"] = ", ".join({user.name for user in users})

        await utils.answer(message, self.strings("servinfo").format(**info))