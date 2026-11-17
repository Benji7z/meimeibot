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