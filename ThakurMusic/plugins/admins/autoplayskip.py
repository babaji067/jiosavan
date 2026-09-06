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

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message
from pytgcalls.types import MediaStream, AudioQuality

from ThakurMusic import YouTube, app
from ThakurMusic.core.call import ThakurMusic
from ThakurMusic.misc import db
from ThakurMusic.utils.database import (
    add_active_chat, 
    get_lang, 
    group_assistant, 
    is_thumb_enabled
)
from ThakurMusic.utils.decorators import AdminRightsCheck
from ThakurMusic.utils.inline.play import stream_markup
from ThakurMusic.utils.stream.autoclear import auto_clean
from ThakurMusic.utils.stream.autoplay import add_to_history, get_related_video, is_autoplay
from ThakurMusic.utils.stream.queue import put_queue
from ThakurMusic.utils.thumbnails import get_thumb as gen_thumb
from ThakurMusic.utils.logger import autoplay_logs
from config import BANNED_USERS
from strings import get_string


@app.on_message(
    filters.command(["askip", "apskip", "autoplayskip"], prefixes=["", "/", "!", "%", ",", ".", "@", "#"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def autoplay_skip_command(cli, message: Message, _, chat_id):
    check = db.get(chat_id)
    if not check:
        return await message.reply_text("🔁 <b>ɴᴏ sᴏɴɢ ᴘʟᴀʏɪɴɢ!</b>")

    if not await is_autoplay(chat_id):
        return await message.reply_text(
            "❌ <b>ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴏғғ.!</b>\n\nᴇɴᴀʙʟᴇ it ғɪʀsᴛ ᴠɪᴀ /autoplay"
        )

    popped = None
    try:
        popped = check.pop(0)
        if popped:
            await auto_clean(popped)
    except Exception as e:
        return await message.reply_text(f"❌ <b>ᴇʀʀᴏʀ:</b> {str(e)}")

    if not popped:
        return await message.reply_text("❌ <b>ɴᴏ ᴘʀᴇᴠɪᴏᴜs sᴏɴɢ ғᴏᴜɴᴅ.!</b>")

    last_vidid = popped.get("vidid")
    if not last_vidid or last_vidid in ["telegram", "soundcloud"]:
        return await message.reply_text("❌ <b>ᴄᴀɴɴᴏᴛ ᴀᴜᴛᴏᴘʟᴀʏ ᴛʜɪs ᴛʏᴘᴇ ᴏғ ᴛʀᴀᴄᴋ.!</b>")

    add_to_history(chat_id, last_vidid)

    mystic = await message.reply_text("🔁 <b>ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘ</b> | ғᴇᴛᴄʜɪɴɢ ɴᴇxᴛ sᴏɴɢ...")

    related_vidid, details = await get_related_video(chat_id, last_vidid)

    if not related_vidid or not details:
        await mystic.delete()
        return await message.reply_text("❌ <b>ɴᴏ ʀᴇʟᴀᴛᴇᴅ ᴠɪᴅᴇᴏ ғᴏᴜɴᴅ.!</b>")

    original_chat_id = popped.get("chat_id", chat_id)
    title = (details["title"]).title()
    duration_min = details["duration_min"]
    thumbnail = details["thumb"]

    await mystic.edit_text("🔁 <b>ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘ</b> | ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...")

    try:
        file_path, direct = await YouTube.download(related_vidid, mystic, videoid=True, video=False)
    except Exception as e:
        await mystic.edit_text(f"❌ <b>ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ:</b> {str(e)}")
        return

    if not file_path:
        await mystic.edit_text("❌ <b>ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ.!</b>")
        return

    db[chat_id] = []
    await put_queue(
        chat_id,
        original_chat_id,
        file_path if direct else f"vid_{related_vidid}",
        title,
        duration_min,
        "🔁 AutoPlay",
        related_vidid,
        0,
        "audio",
    )

    autoplay_stream = MediaStream(
        file_path,
        audio_parameters=AudioQuality.STUDIO,
    )

    try:
        assistant = await group_assistant(ThakurMusic, chat_id)
        await assistant.play(chat_id, autoplay_stream)
    except Exception as e:
        await mystic.edit_text(f"❌ <b>ғᴀɪʟᴇᴅ ᴛᴏ ᴘʟᴀʏ:</b> {str(e)}")
        await ThakurMusic.stop_stream(chat_id)
        return

    await add_active_chat(chat_id)

    button = stream_markup(_, chat_id)
    try:
        await mystic.delete()
    except:
        pass

    thumb_status = await is_thumb_enabled(chat_id)
    caption = _["stream_1"].format(
        f"https://t.me/{app.username}?start=info_{related_vidid}",
        title[:23],
        duration_min,
        "🔁 AutoPlay",
    )

    if thumb_status:
        img = await gen_thumb(related_vidid)
        run = await message.reply_photo(
            photo=img,
            has_spoiler=True,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(button),
        )
    else:
        run = await message.reply_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(button),
        )

    db[chat_id][0]["mystic"] = run
    db[chat_id][0]["markup"] = "stream"
    add_to_history(chat_id, related_vidid)

    try:
        await autoplay_logs(chat_id, original_chat_id, title, duration_min, related_vidid)
    except:
        pass