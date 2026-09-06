import asyncio
import time
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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from ThakurMusic import app
from ThakurMusic.utils.stream.autoplay import is_autoplay, enable_autoplay, disable_autoplay
from ThakurMusic.utils.stream.autoclear import auto_clean
from ThakurMusic.utils.decorators.admins import ActualAdminCB
from config import BANNED_USERS

@app.on_message(
    filters.command(["autoplay", "ap"])
    & filters.group
    & ~BANNED_USERS
)
async def autoplay_command(client, message: Message):
    chat_id = message.chat.id
    status = await is_autoplay(chat_id)

    current_status = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"

    text = (
        f"💮 <b>ᴀᴜᴛᴏᴘʟᴀʏ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</b>\n\n"
        f"ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {current_status}\n\n"
        f"ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛʀᴏʟ ᴀᴜᴛᴏᴘʟᴀʏ."
    )

    buttons = [
        [
            InlineKeyboardButton("ᴇɴᴀʙʟᴇ", callback_data="set_autoplay|enable"),
            InlineKeyboardButton("ᴅɪsᴀʙʟᴇ", callback_data="set_autoplay|disable")
        ],
        [
            InlineKeyboardButton("ᴄʟᴏsᴇ ⌫", callback_data="close")
        ]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ─────────────────────────────────────────────────────────────
# More Settings panel from the playback controls.
# The panel automatically returns to the playback controls after 5s.
# ─────────────────────────────────────────────────────────────
from ThakurMusic.utils.inline.play import stream_markup_timer, MORE_SETTINGS_UNTIL
from ThakurMusic.utils.formatters import seconds_to_min
from ThakurMusic.misc import db

# Autoplay controls use a Shruti-style admin alert while preserving the
# existing authorization rules (admins, sudoers and authorized users).
def _AutoplayAdminCB(mystic):
    async def wrapper(client, callback_query):
        from pyrogram.enums import ChatType
        from ThakurMusic.misc import SUDOERS
        from ThakurMusic.utils.database import (
            get_authuser_names, get_lang, is_maintenance, is_nonadmin_chat
        )
        from ThakurMusic.utils.formatters import int_to_alpha
        from strings import get_string

        try:
            if await is_maintenance() is False and callback_query.from_user.id not in SUDOERS:
                return await callback_query.answer(
                    f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ.", show_alert=True
                )
        except Exception:
            pass

        try:
            language = await get_lang(callback_query.message.chat.id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")

        if callback_query.message.chat.type == ChatType.PRIVATE:
            return await mystic(client, callback_query, _)

        if callback_query.from_user.id in SUDOERS:
            return await mystic(client, callback_query, _)

        try:
            if await is_nonadmin_chat(callback_query.message.chat.id):
                return await mystic(client, callback_query, _)

            member = await app.get_chat_member(
                callback_query.message.chat.id, callback_query.from_user.id
            )
            privileges = getattr(member, "privileges", None)
            is_admin = bool(privileges and privileges.can_manage_video_chats)

            if not is_admin:
                token = await int_to_alpha(callback_query.from_user.id)
                authorized = await get_authuser_names(callback_query.from_user.id)
                if token not in authorized:
                    return await callback_query.answer(
                        "⚠️ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀs ᴄᴀɴ ᴅᴏ ᴛʜᴇsᴇ ᴀᴄᴛɪᴏɴs.",
                        show_alert=True,
                    )
        except Exception:
            return await callback_query.answer(
                "⚠️ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀs ᴄᴀɴ ᴅᴏ ᴛʜᴇsᴇ ᴀᴄᴛɪᴏɴs.",
                show_alert=True,
            )

        return await mystic(client, callback_query, _)

    return wrapper


async def _restore_playback_markup(callback_query, chat_id):
    """Restore the live playback controls after the settings timeout."""
    try:
        await asyncio.sleep(3)

        playing = db.get(chat_id)
        if not playing or not playing[0].get("mystic"):
            return

        # Only restore if the same message is still being displayed.
        mystic = playing[0]["mystic"]
        if mystic.id != callback_query.message.id:
            return

        language = callback_query.from_user.language_code or "en"
        try:
            from strings import get_string
            _ = get_string(language if language in ("en", "hi") else "en")
        except Exception:
            _ = None

        played = playing[0].get("played", 0)
        dur = playing[0].get("dur") or playing[0].get("seconds", 0)
        if _ is not None and dur:
            markup = stream_markup_timer(_, chat_id, seconds_to_min(played), playing[0].get("dur", seconds_to_min(dur)))
        else:
            from ThakurMusic.utils.inline.play import stream_markup
            markup = stream_markup(_, chat_id) if _ is not None else []

        if markup:
            await mystic.edit_reply_markup(reply_markup=InlineKeyboardMarkup(markup))
    except Exception:
        # The message may have been deleted/edited in the meantime.
        pass


@app.on_callback_query(filters.regex(r"^more_settings\|") & ~BANNED_USERS)
async def more_settings_callback(client, callback_query: CallbackQuery):
    try:
        chat_id = int(callback_query.data.split("|", 1)[1])
    except (ValueError, IndexError):
        return await callback_query.answer("❌ Invalid settings request.", show_alert=True)

    if callback_query.message.chat.id != chat_id:
        return await callback_query.answer("❌ Invalid chat.", show_alert=True)

    status = await is_autoplay(chat_id)
    status_text = "ᴀᴜᴛᴏᴘʟᴀʏ : ᴏɴ ✅" if status else "ᴀᴜᴛᴏᴘʟᴀʏ : ᴏғғ ❌"

    text = (
        f"⚙️ <b>ᴍᴏʀᴇ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"🔁 <b>{status_text}</b>\n\n"
        f"ᴛʜɪs ᴘᴀɴᴇʟ ᴡɪʟʟ ʀᴇᴛᴜʀɴ ᴛᴏ ᴘʟᴀʏʙᴀᴄᴋ ɪɴ <b>3 sᴇᴄᴏɴᴅs</b>."
    )

    buttons = [
        [
            InlineKeyboardButton(
                text="🔁 ᴛᴏɢɢʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ",
                callback_data="set_autoplay|toggle|settings",
            )
        ],
        [
            InlineKeyboardButton(
                text="⏭️ ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘ",
                callback_data=f"autoplay_skip|{chat_id}",
            )
        ],
    ]

    await callback_query.answer()
    try:
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        return

    # Run the timeout in the background so Telegram callback handling is immediate.
    MORE_SETTINGS_UNTIL[chat_id] = time.monotonic() + 3
    asyncio.create_task(_restore_playback_markup(callback_query, chat_id))


@app.on_callback_query(filters.regex(r"^set_autoplay\|") & ~BANNED_USERS)
@_AutoplayAdminCB
async def autoplay_callback(client, callback_query: CallbackQuery, _):
    chat_id = callback_query.message.chat.id
    data_parts = callback_query.data.split("|")
    data = data_parts[1] if len(data_parts) > 1 else ""
    is_from_settings = len(data_parts) > 2 and data_parts[2] == "settings"

    current_status = await is_autoplay(chat_id)

    if data == "toggle":
        if current_status:
            await disable_autoplay(chat_id)
            new_status_text = "ᴀᴜᴛᴏᴘʟᴀʏ : ᴏғғ ❌"
            await callback_query.answer("❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ", show_alert=False)
        else:
            await enable_autoplay(chat_id)
            new_status_text = "ᴀᴜᴛᴏᴘʟᴀʏ : ᴏɴ ✅"
            await callback_query.answer("✅ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ", show_alert=False)

        if is_from_settings:
            buttons = [
                [
                    InlineKeyboardButton(
                        text="🔁 ᴛᴏɢɢʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ",
                        callback_data="set_autoplay|toggle|settings",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⏭️ ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘ",
                        callback_data=f"autoplay_skip|{chat_id}",
                    )
                ],
            ]
            text = (
                f"⚙️ <b>ᴍᴏʀᴇ sᴇᴛᴛɪɴɢs</b>\n\n"
                f"🔁 <b>{new_status_text}</b>\n\n"
                f"ᴛʜɪs ᴘᴀɴᴇʟ ᴡɪʟʟ ʀᴇᴛᴜʀɴ ᴛᴏ ᴘʟᴀʏʙᴀᴄᴋ ɪɴ <b>3 sᴇᴄᴏɴᴅs</b>."
            )
            try:
                await callback_query.message.edit_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except Exception:
                pass
        return

    # Keep the original /autoplay enable/disable behaviour intact.
    if data == "enable":
        if current_status:
            return await callback_query.answer("⚠️ ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴀʟʀᴇᴀᴅʏ ᴇɴᴀʙʟᴇᴅ.!", show_alert=True)
        await enable_autoplay(chat_id)
        new_status_text = "ᴇɴᴀʙʟᴇᴅ ✅"
        await callback_query.answer("✅ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.!", show_alert=False)
    else:
        if not current_status:
            return await callback_query.answer("⚠️ ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ.!", show_alert=True)
        await disable_autoplay(chat_id)
        new_status_text = "ᴅɪsᴀʙʟᴇᴅ ❌"
        await callback_query.answer("❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.!", show_alert=False)

    text = (
        f"💮 <b>ᴀᴜᴛᴏᴘʟᴀʏ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</b>\n\n"
        f"ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {new_status_text}\n\n"
        f"ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴᴛʀᴏʟ ᴀᴜᴛᴏᴘʟᴀʏ."
    )
    buttons = [
        [
            InlineKeyboardButton("ᴇɴᴀʙʟᴇ", callback_data=f"set_autoplay|enable|settings" if is_from_settings else "set_autoplay|enable"),
            InlineKeyboardButton("ᴅɪsᴀʙʟᴇ", callback_data=f"set_autoplay|disable|settings" if is_from_settings else "set_autoplay|disable")
        ]
    ]
    if is_from_settings:
        buttons.append([InlineKeyboardButton("ᴄʟᴏsᴇ ⌫", callback_data="close")])
    else:
        buttons.append([InlineKeyboardButton("ᴄʟᴏsᴇ ⌫", callback_data="close")])
    try:
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^autoplay_skip\|") & ~BANNED_USERS)
@_AutoplayAdminCB
async def autoplay_skip_callback(client, callback_query: CallbackQuery, _):
    """Run AutoPlay Skip directly from More Settings."""
    try:
        chat_id = int(callback_query.data.split("|", 1)[1])
    except (ValueError, IndexError):
        return await callback_query.answer("❌ Invalid request.", show_alert=True)

    if callback_query.message.chat.id != chat_id:
        return await callback_query.answer("❌ Invalid chat.", show_alert=True)

    check = db.get(chat_id)
    if not check:
        return await callback_query.answer("🔁 ɴᴏ sᴏɴɢ ᴘʟᴀʏɪɴɢ!", show_alert=True)

    if not await is_autoplay(chat_id):
        return await callback_query.answer(
            "❌ ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴏғғ.!\n\nᴇɴᴀʙʟᴇ it ғɪʀsᴛ ᴠɪᴀ /autoplay",
            show_alert=True,
        )

    # Keep the existing /askip behaviour by dispatching a normal command
    # message to the same command handler's core logic.
    await callback_query.answer("⏭️ ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘᴘɪɴɢ...", show_alert=False)
    await _perform_autoplay_skip(client, callback_query.message, _, chat_id)


async def _perform_autoplay_skip(cli, message: Message, _, chat_id: int):
    """Shared AutoPlay Skip implementation for command and callback."""
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

    await mystic.edit_text("🔁 <b>ᴀᴜᴛᴏᴘʟᴀʏ sᴋɪᴘ</b> | ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...")
    try:
        file_path, direct = await YouTube.download(related_vidid, mystic, videoid=True, video=False)
    except Exception as e:
        await mystic.edit_text(f"❌ <b>ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ:</b> {str(e)}")
        return

    if not file_path:
        return await mystic.edit_text("❌ <b>ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ.!</b>")

    db[chat_id] = []
    await put_queue(
        chat_id, original_chat_id, file_path if direct else f"vid_{related_vidid}",
        title, duration_min, "🔁 AutoPlay", related_vidid, 0, "audio"
    )

    autoplay_stream = MediaStream(file_path, audio_parameters=AudioQuality.STUDIO)
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
    except Exception:
        pass

    thumb_status = await is_thumb_enabled(chat_id)
    caption = _["stream_1"].format(
        f"https://t.me/{app.username}?start=info_{related_vidid}",
        title[:23], duration_min, "🔁 AutoPlay",
    )
    if thumb_status:
        img = await gen_thumb(related_vidid)
        run = await message.reply_photo(photo=img, has_spoiler=False, caption=caption, reply_markup=InlineKeyboardMarkup(button))
    else:
        run = await message.reply_text(text=caption, reply_markup=InlineKeyboardMarkup(button))

    db[chat_id][0]["mystic"] = run
    db[chat_id][0]["markup"] = "stream"
    add_to_history(chat_id, related_vidid)
    try:
        await autoplay_logs(chat_id, original_chat_id, title, duration_min, related_vidid)
    except Exception:
        pass
