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
from pyrogram.types import Message
from ThakurMusic import YouTube, app
from ThakurMusic.core.call import ThakurMusic
from ThakurMusic.misc import db
from ThakurMusic.utils import AdminRightsCheck, seconds_to_min
from ThakurMusic.utils.decorators.admins import ActualAdminCB
from ThakurMusic.utils.database import get_lang
from ThakurMusic.utils.inline.play import stream_markup_timer
from strings import get_string
from ThakurMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(
    filters.command(["seek", "cseek", "seekback", "cseekback"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def seek_comm(cli, message: Message, _, chat_id):
    if len(message.command) == 1:
        return await message.reply_text(_["admin_20"])
    query = message.text.split(None, 1)[1].strip()
    if not query.isnumeric():
        return await message.reply_text(_["admin_21"])
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_22"])
    file_path = playing[0]["file"]
    duration_played = int(playing[0]["played"])
    duration_to_skip = int(query)
    duration = playing[0]["dur"]
    if message.command[0][-2] == "c":
        if (duration_played - duration_to_skip) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played - duration_to_skip + 1
    else:
        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played + duration_to_skip + 1
    mystic = await message.reply_text(_["admin_24"])
    if "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0:
            return await message.reply_text(_["admin_22"])
    check = (playing[0]).get("speed_path")
    if check:
        file_path = check
    if "index_" in file_path:
        file_path = playing[0]["vidid"]
    try:
        await ThakurMusic.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except:
        return await mystic.edit_text(_["admin_26"], reply_markup=close_markup(_))
    if message.command[0][-2] == "c":
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip
    await mystic.edit_text(
        text=_["admin_25"].format(seconds_to_min(to_seek), message.from_user.mention),
        reply_markup=close_markup(_),
    )

@app.on_callback_query(filters.regex(r"^SEEK (?:-15|\+15)\|") & ~BANNED_USERS)
@ActualAdminCB
async def seek_15_callback(client, CallbackQuery, _):
    """Seek the current track backward/forward by exactly 15 seconds."""
    try:
        action, chat = CallbackQuery.data.split("|", 1)
        chat_id = int(chat)
        if CallbackQuery.message.chat.id != chat_id:
            return await CallbackQuery.answer("❌ Invalid chat.", show_alert=True)
    except (ValueError, AttributeError):
        return await CallbackQuery.answer("❌ Invalid seek request.", show_alert=True)

    playing = db.get(chat_id)
    if not playing:
        return await CallbackQuery.answer("❌ ɴᴏ sᴏɴɢ ɪs ᴘʟᴀʏɪɴɢ.", show_alert=True)

    current = playing[0]
    duration_seconds = int(current.get("seconds", 0) or 0)
    played = int(current.get("played", 0) or 0)
    if duration_seconds <= 0:
        return await CallbackQuery.answer("❌ ᴛʀᴀᴄᴋ ᴅᴜʀᴀᴛɪᴏɴ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ.", show_alert=True)

    amount = 15 if action == "SEEK +15" else -15
    target = played + amount

    # Keep the stream away from the first/last few seconds where seeking can fail.
    if target <= 0:
        return await CallbackQuery.answer("⏪ ʀᴇᴀᴄʜᴇᴅ ᴛʜᴇ sᴛᴀʀᴛ.", show_alert=True)
    if target >= duration_seconds - 10:
        return await CallbackQuery.answer("⏩ ʀᴇᴀᴄʜᴇᴅ ᴛʜᴇ ᴇɴᴅ.", show_alert=True)

    file_path = current.get("file")
    if not file_path:
        return await CallbackQuery.answer("❌ ᴍᴇᴅɪᴀ ɴᴏᴛ ғᴏᴜɴᴅ.", show_alert=True)

    if "vid_" in str(file_path):
        try:
            n, file_path = await YouTube.video(current["vidid"], True)
        except Exception:
            n = 0
        if n == 0:
            return await CallbackQuery.answer("❌ ᴜɴᴀʙʟᴇ ᴛᴏ ʟᴏᴀᴅ ᴛʀᴀᴄᴋ.", show_alert=True)

    speed_path = current.get("speed_path")
    if speed_path:
        file_path = speed_path
    if "index_" in str(file_path):
        file_path = current["vidid"]

    try:
        await ThakurMusic.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(target),
            current["dur"],
            current["streamtype"],
        )
    except Exception:
        return await CallbackQuery.answer("❌ sᴇᴇᴋ ғᴀɪʟᴇᴅ. ᴛʀʏ ᴀɢᴀɪɴ.", show_alert=True)

    current["played"] = target
    await CallbackQuery.answer("⏪ 15s" if amount < 0 else "⏩ 15s")

    # Refresh the timer/progress controls immediately after seeking.
    try:
        buttons = stream_markup_timer(
            _, chat_id, seconds_to_min(target), current["dur"]
        )
        await CallbackQuery.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        pass

