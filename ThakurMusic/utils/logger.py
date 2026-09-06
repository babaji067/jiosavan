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

from pyrogram.enums import ParseMode
from ThakurMusic import app
from ThakurMusic.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""<blockquote>
<b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{message.chat.id}</code>
<b>ᴄʜᴀᴛ ɴᴀᴍᴇ :</b> {message.chat.title}
<b>ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.chat.username}

<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>ɴᴀᴍᴇ :</b> {message.from_user.mention}
<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}

<b>ǫᴜᴇʀʏ :</b> {message.text.split(None, 1)[1]}
<b>sᴛʀᴇᴀᴍᴛʏᴘᴇ :</b> {streamtype}</blockquote>"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return

async def autoplay_logs(chat_id, original_chat_id, title, duration_min, vidid):
    if await is_on_off(2):
        try:
            chat = await app.get_chat(original_chat_id)
            c_name = chat.title
            c_username = f"@{chat.username}" if chat.username else "Private Chat"
        except:
            c_name = "Unknown"
            c_username = "Unknown"

        logger_text = f"""<blockquote>
<b>{app.mention} ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>

<b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{original_chat_id}</code>
<b>ᴄʜᴀᴛ ɴᴀᴍᴇ :</b> {c_name}
<b>ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ :</b> {c_username}

<b>ᴛɪᴛʟᴇ :</b> {title}
<b>ᴅᴜʀᴀᴛɪᴏɴ :</b> {duration_min} ᴍɪɴs
<b>ᴠɪᴅᴇᴏ ɪᴅ :</b> <code>{vidid}</code>

<b>sᴛʀᴇᴀᴍᴛʏᴘᴇ :</b> ᴀᴜᴛᴏᴘʟᴀʏ</blockquote>"""
        if original_chat_id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return