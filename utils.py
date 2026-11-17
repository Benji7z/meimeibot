import asyncio
import subprocess as sp
import time

import yt_dlp

from config import EXEMPT_ROLE


def isBlocked(author):
    return any(role.name == EXEMPT_ROLE for role in author.roles)


async def get_video_title(url):
    options = {
        "quiet": True
    }

    def extract():
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            return info["title"]

    return await asyncio.to_thread(extract)


def temperature_monitor():
    while True:
        try:
            result = sp.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode()

            temp = float(result.split("=")[1].split("'")[0])
            print(f"Temperature: {temp}°C")

            if temp >= 65:
                sp.run(["sudo", "systemctl", "poweroff"])
                break

        except Exception as e:
            print(f"Temperature monitor error: {e}")

        time.sleep(30)
