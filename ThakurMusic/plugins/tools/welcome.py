import os
import asyncio
from unidecode import unidecode
from PIL import ImageDraw, Image, ImageFont, ImageChops
from pyrogram import *
from pyrogram.types import *
from logging import getLogger
from ThakurMusic import LOGGER
from pyrogram.types import Message, ChatJoinRequest
from ThakurMusic.misc import SUDOERS
from ThakurMusic import app
from ThakurMusic.helper.Weldb import *
from config import LOGGER_ID, SUPPORT_CHAT, SUPPORT_CHANNEL, START_IMG_URL

LOGGER = getLogger(__name__)


class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None


def circle(pfp, size=(450, 450)):
    pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp


def welcomepic(pic, user, chat, id, uname):
    background = Image.open("ThakurMusic/assets/WELL2.PNG")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((605, 605))
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype("ThakurMusic/assets/font.ttf", size=75)
    font2 = ImageFont.truetype("ThakurMusic/assets/font.ttf", size=90)

    draw.text((150, 450), f"ID : {id}", fill="black", font=font)
    draw.text((150, 550), f"USERNAME : {uname}", fill="black", font=font)

    pfp_position = (1077, 183)
    background.paste(pfp, pfp_position, pfp)
    background.save(f"downloads/welcome#{id}.png")

    return f"downloads/welcome#{id}.png"


@app.on_message(filters.command("wel") & ~filters.private)
async def auto_state(_, message):
    usage = "**❖ ᴜsᴀɢᴇ ➥** /wel [enable|disable]"

    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(
        message.chat.id,
        message.from_user.id
    )

    if user.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        A = await wlcm.find_one({"chat_id": chat_id})
        state = message.text.split(None, 1)[1].strip().lower()

        if state == "enable":
            if A:
                return await message.reply_text(
                    "✦ Special Welcome Already Enabled"
                )

            await add_wlcm(chat_id)

            await message.reply_text(
                f"✦ Enabled Special Welcome in {message.chat.title}"
            )

        elif state == "disable":
            if not A:
                return await message.reply_text(
                    "✦ Special Welcome Already Disabled"
                )

            await rm_wlcm(chat_id)

            await message.reply_text(
                f"✦ Disabled Special Welcome in {message.chat.title}"
            )

        else:
            await message.reply_text(usage)

    else:
        await message.reply("✦ Only Admins Can Use This Command")


@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    chat_id = member.chat.id

    A = await wlcm.find_one({"chat_id": chat_id})

    # Normal welcome OFF by default
    if not A:
        return

    if (
        not member.new_chat_member
        or member.new_chat_member.status in {
            "banned",
            "left",
            "restricted",
        }
        or member.old_chat_member
    ):
        return

    user = (
        member.new_chat_member.user
        if member.new_chat_member
        else member.from_user
    )

    try:
        pic = await app.download_media(
            user.photo.big_file_id,
            file_name=f"pp{user.id}.png",
        )
    except AttributeError:
        pic = "ThakurMusic/assets/upic.png"

    if temp.MELCOW.get(
        f"welcome-{member.chat.id}"
    ) is not None:
        try:
            await temp.MELCOW[
                f"welcome-{member.chat.id}"
            ].delete()
        except Exception as e:
            LOGGER.error(e)

    try:
        welcomeimg = welcomepic(
            pic,
            user.first_name,
            member.chat.title,
            user.id,
            user.username,
        )

        msg = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
ㅤㅤ◦•●◉✿ ᴡᴇʟᴄᴏᴍᴇ ✿◉●•◦
▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

● ɴᴀᴍᴇ ➥  {user.mention}
● ᴜsᴇʀɴᴀᴍᴇ ➥  @{user.username}
● ᴜsᴇʀ ɪᴅ ➥  {user.id}

▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
""",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✙ ᴋɪᴅɴᴀᴘ ᴍᴇ ✙",
                            url="https://t.me/Subbbumusicbot?startgroup=new",
                        ),
                    ]
                ]
            ),
        )

        temp.MELCOW[
            f"welcome-{member.chat.id}"
        ] = msg

        await asyncio.sleep(300)
        await msg.delete()

    except Exception as e:
        LOGGER.error(e)

    try:
        os.remove(
            f"downloads/welcome#{user.id}.png"
        )
        os.remove(
            f"downloads/pp{user.id}.png"
        )
    except Exception:
        pass


# ============================================================
#                    JOIN REQUEST HANDLER
# ============================================================
@app.on_chat_join_request()
async def join_request_dm(client, request: ChatJoinRequest):
    user = request.from_user
    chat = request.chat

    # Apni JPG/PNG image ka direct link yahan lagao
    JOIN_REQUEST_IMAGE = "https://i.ibb.co/n8MBzzfz/photo-AQAD-A9r-Gx-ETm-FV9.jpg"

    # Bot must be admin + Add/Invite Users permission
    try:
        bot_member = await client.get_chat_member(chat.id, "me")

        if bot_member.status not in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ):
            return

        privileges = bot_member.privileges

        if not privileges or not privileges.can_invite_users:
            return

    except Exception as e:
        LOGGER.error(f"JOIN REQUEST PERMISSION ERROR: {e}")
        return

    # Bot username
    try:
        bot_username = client.me.username
        bot_name = client.me.first_name
    except Exception:
        return

    if not bot_username:
        return

    # Clickable bot mention
    bot_mention = (
        f'<a href="https://t.me/{bot_username}">{bot_name}</a>'
    )

    # Buttons
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{bot_username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 sᴜᴘᴘᴏʀᴛ",
                    url=SUPPORT_CHAT,
                ),
                InlineKeyboardButton(
                    "📢 ᴜᴘᴅᴀᴛᴇs",
                    url=SUPPORT_CHANNEL,
                ),
            ],
        ]
    )

    # Message
    text = f"""
<b>👋 ʜᴇʏ {user.mention}!</b>

<b>💮 ᴛʜᴀɴᴋs ғᴏʀ ʀᴇǫᴜᴇsᴛɪɴɢ ᴛᴏ ᴊᴏɪɴ - {chat.title} !! 🎶</b>

<b>🎵 ɪ'ᴍ {bot_mention} - ᴀ ʜɪɢʜ ǫᴜᴀʟɪᴛʏ ᴍᴜsɪᴄ
sᴛʀᴇᴀᴍɪɴɢ ʙᴏᴛ ғᴏʀ ᴛᴇʟᴇɢʀᴀᴍ
ɢʀᴏᴜᴘs & ᴄʜᴀɴɴᴇʟs 🚀</b>

<b>ᴊᴜsᴛ sᴇɴᴅ /start ᴛᴏ sᴇᴇ ʙᴏᴛ ᴍᴇɴᴜ ᴀɴᴅ
ᴄᴏᴍᴍᴀɴᴅs 📋</b>
"""

    # Send image + message
    try:
        await client.send_photo(
            chat_id=user.id,
            photo=JOIN_REQUEST_IMAGE,
            caption=text,
            reply_markup=buttons,
        )

    except Exception as e:
        LOGGER.info(
            f"Join Request Photo DM failed for {user.id}: {e}"
        )

        # Fallback if image URL fails
        try:
            await client.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=buttons,
            )
        except Exception as e2:
            LOGGER.info(
                f"Join Request DM failed for {user.id}: {e2}"
            )
    
