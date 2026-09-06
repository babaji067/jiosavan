# -----------------------------------------------
# 🔸 ThakurMusic Project
# 🔹 Developed & Maintained by: ThakurMusic Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# -----------------------------------------------

import re
import aiohttp
from ThakurMusic.platforms.Youtube import YouTubeAPI
from ThakurMusic.utils.database import disable_autoplay_db, enable_autoplay_db, is_autoplay_enabled

YouTube = YouTubeAPI()

MAX_AUTOPLAY_DURATION = 10 * 60
MAX_HISTORY = 20

SKIP_TITLE_KEYWORDS = [
    "best of",
    "top songs",
    "top hits",
    "all songs",
    "greatest hits",
    "full album",
    "full playlist",
    "jukebox",
    "nonstop",
    "non stop",
    "mashup",
    "megamix",
    "mega mix",
    "back to back",
    "hits collection",
    "all time hits",
    "superhits",
    "super hits",
    "evergreen hits",
    "audio jukebox",
    "video jukebox",
    "collection",
    "playlist",
    "album",
    "mixtape",
    "compilation",
    "class ",
]

autoplay_history = {}


def is_skip_title(title: str) -> bool:
    title_lower = title.lower()
    for keyword in SKIP_TITLE_KEYWORDS:
        if keyword in title_lower:
            return True
    return False


def add_to_history(chat_id: int, vidid: str):
    if chat_id not in autoplay_history:
        autoplay_history[chat_id] = []
    history = autoplay_history[chat_id]
    if vidid not in history:
        history.append(vidid)
    if len(history) > MAX_HISTORY:
        history.pop(0)


def is_in_history(chat_id: int, vidid: str) -> bool:
    return vidid in autoplay_history.get(chat_id, [])


def clear_history(chat_id: int):
    autoplay_history[chat_id] = []


async def get_related_video(chat_id: int, vidid: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://www.youtube.com/watch?v={vidid}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return None, None
                html = await response.text()
                pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
                matches = re.findall(pattern, html)
                seen = set()
                unique = []
                for m in matches:
                    if m != vidid and m not in seen:
                        seen.add(m)
                        unique.append(m)

                for candidate_id in unique[:20]:
                    try:
                        if is_in_history(chat_id, candidate_id):
                            continue

                        details, _ = await YouTube.track(candidate_id, True)
                        title = details.get("title", "")
                        duration_str = details.get("duration_min", "")

                        if is_skip_title(title):
                            continue

                        if not duration_str:
                            continue

                        parts = duration_str.split(":")
                        if len(parts) == 2:
                            duration_sec = int(parts[0]) * 60 + int(parts[1])
                        elif len(parts) == 3:
                            duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        else:
                            continue

                        if duration_sec <= MAX_AUTOPLAY_DURATION:
                            result = {
                                "title": title,
                                "thumb": details.get("thumb", f"https://i.ytimg.com/vi/{candidate_id}/hqdefault.jpg"),
                                "duration_min": duration_str,
                            }
                            return candidate_id, result

                    except Exception:
                        continue

                return None, None
    except Exception:
        return None, None


async def enable_autoplay(chat_id: int):
    await enable_autoplay_db(chat_id)
    clear_history(chat_id)


async def disable_autoplay(chat_id: int):
    await disable_autoplay_db(chat_id)
    clear_history(chat_id)


async def is_autoplay(chat_id: int) -> bool:
    return await is_autoplay_enabled(chat_id)
