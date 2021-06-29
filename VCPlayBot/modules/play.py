import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Voice
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from VCPlayBot.config import ARQ_API_KEY
from VCPlayBot.config import BOT_NAME as bn
from VCPlayBot.config import DURATION_LIMIT
from VCPlayBot.config import UPDATES_CHANNEL as updateschannel
from VCPlayBot.config import que
from VCPlayBot.function.admins import admins as a
from VCPlayBot.helpers.admins import get_administrators
from VCPlayBot.helpers.channelmusic import get_chat_id
from VCPlayBot.helpers.errors import DurationLimitError
from VCPlayBot.helpers.decorators import errors
from VCPlayBot.helpers.decorators import authorized_users_only
from VCPlayBot.helpers.filters import command, other_filters
from VCPlayBot.helpers.gets import get_file_name
from VCPlayBot.services.callsmusic import callsmusic, queues
from VCPlayBot.services.callsmusic.callsmusic import client as USER
from VCPlayBot.services.converter.converter import convert
from VCPlayBot.services.downloaders import youtube

aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)
DISABLED_GROUPS = []
useer ="NaN"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("تۆ ڕێگەت پێنەدراوە!", show_alert=True)
            return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((205, 550), f"Title: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"زیادکرا لەلایەن: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return    
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("Player is idle")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**ئیستا پەخشکرا** in {}".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- داواکراوەلەلایەن " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**ڕیز**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- {name}"
            msg += f"\n- داواکراوە لەلایەن {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = "ڕێکبەندەکانی **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "سەوت : {}%\n".format(vol)
            stats += "گۆرانیەکان لە ڕیزدا : `{}`\n".format(len(que))
            stats += "گۆرانی پەخشکراو : **{}**\n".format(queue[0][0])
            stats += "داواکراوەکان : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "دەرچۆن"),
                InlineKeyboardButton("⏸", "راگرتن"),
                InlineKeyboardButton("▶️", "پەخشکردنەوە"),
                InlineKeyboardButton("⏭", "تێپەڕاندن"),
            ],
            [
                InlineKeyboardButton("لیستی پەخشکراوەکان 📖", "playlist"),
            ],
            [InlineKeyboardButton("❌ داخستن", "cls")],
        ]
    )
    return mar


@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("هیچ حاڵەتێکی VC نیە کە لەم چاتەدا کاربکات")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    if message.chat.id in DISABLED_GROUPS:
        await message.reply("لێدەرێکی مووزیک ناچالاک کراوە")
        return    
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))

        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("هیچ حاڵەتێکی VC نیە کە لەم چاتەدا کاربکات")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "من تەنها دەیناسیتەوە `/musicplayer یان`  /musicplayer"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`پرۆسەکردن...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("ژەنیاری مووزیک پێشتر چالاک کراوە لەم چاتەدا")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Enabled For Users In The Chat {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`پرۆسەکردن...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("لەم گرووپە پەخشکردن پێشتر چاڵاکراوە")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Deactivated For Users In The Chat {message.chat.id}"
        )
    else:
        await message.reply_text(
            "من تەنیا `/musicplayer on` لەگەڵ  یان /musicplayer `off` ئەتوانم بناسمەوە"
        )    
        

@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Player is idle")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**ئیستا پەخشکراوە** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- داواکراوە " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**ڕێز**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- لەلایەن {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("چاتە نەبەستراوەتەوە!", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("پەخشکردن وەستا!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("چاتە نەبەستراوەتەوە!", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("پەخشکردن دەستی پێکردەوە!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("لێدەر بێکار")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**ئیستا پەخشکرا** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- داواکراوە لەلایەن " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**ڕێز**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- داواکراوە لەلایەن {usr}\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("چات نەبەستراوە تەوە یان هەر ئێستا پەخشکردن", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("پەخشکردن دەستی پێکردەوە!")
    elif type_ == "puse":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("چات نەبەستراوە تەوە یان ڕاگیراوە", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("پەخشکردن ڕاگیرا!")
    elif type_ == "cls":
        await cb.answer("داخرا ")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("لاپەڕەی ڕێکخستن کراوە")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "دەرچۆن"),
                    InlineKeyboardButton("⏸", "راگرتن"),
                    InlineKeyboardButton("▶️", "پەخشکردن"),
                    InlineKeyboardButton("⏭", "تێپەڕاندن"),
                ],
                [
                    InlineKeyboardButton("لیستی پەخشکراوەکان 📖", "playlist"),
                ],
                [InlineKeyboardButton("❌ داخستن", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.pytgcalls.active_calls:
            await cb.answer("چاتە نەبەستراوەتەوە!", show_alert=True)
        else:
            callsmusic.queues.task_done(chet_id)

            if callsmusic.queues.is_empty(chet_id):
                callsmusic.pytgcalls.leave_group_call(chet_id)

                await cb.message.edit("- چات نەبەستراوە تەوە یان هەر ئێستا پەخشکردن..\n-  بەجێهێشتنی VC!")
            else:
                callsmusic.pytgcalls.change_stream(
                    chet_id, callsmusic.queues.get(chet_id)["file"]
                )
                await cb.answer("Skipped")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- تراکە تێپەڕەندرا\n- پەخشی ئیستا **{qeue[0][0]}**"
                )

    else:
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass

            callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit("بە سەرکەوتوویی چاتەکەی جێهێشت!")
        else:
            await cb.answer("چات نەبەستراوەتەوە!", show_alert=True)


@Client.on_message(command("play") & other_filters)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return    
    lel = await message.reply("🔄 **پرۆسە**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>لەبیرت بێت بۆ زیادکردنی یارمەتیدەر بۆ کەناڵەکەت</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>یەکەم جار وەک بەڕێوەبەری گرووپی یور زیادم بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "من بۆ ژەنینی موزیک لە ڤی سی بەشداریم لەم گرووپە کرد"
                    )
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە چاتەکەتەوە</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ گروپەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                                                " بە دەستی یاریدەدەرێک زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ بدە</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot لەم چاتەدا نیە، داوا لە سەرپەرشتیار بکە بۆ یەکەم جار فەرمانی ناردن/play یان زیادکردنی {user.first_name} بە دەستی لێرە داوای @teamkurdishchat بە بەستەری گرووپەکەت</i>"
        )
        return
    text_links=None
    await lel.edit("🔎 **ئەدۆزێتەوە**")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ ڕێگە بە ڤیدیۆکان درێژتر لە {DURATION_LIMIT} خولەک(ەکان) نادات!"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 لیستی پەخشکردن", callback_data="playlist"),
                    InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
                ],
                [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🎵 **پڕۆسە**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "گۆرانی نەدۆزرایەوە گۆرانییەکی تر تاقی بکەوە یان بە دروستی بینوسە."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 لیستی پەخشکراو", callback_data="playlist"),
                    InlineKeyboardButton("رێبەندەکان ⏯ ", callback_data="menu"),
                ],
                [
                    InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                    InlineKeyboardButton(text="داگرتن 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("🎵 **پرۆسە**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        
        try:
          results = YoutubeSearch(query, max_results=5).to_dict()
        except:
          await lel.edit("شتێکم بدە بۆ یاریکردن")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "**گۆرانیە هەڵبژێرە کە ئەتەوێ ئەزیزم**\n\n"
            j = 0
            useer=user_name
            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣",]

            while j < 5:
                toxxt += f"{emojilist[j]} [Title - {results[j]['title']}](https://youtube.com{results[j]['url_suffix']})\n"
                toxxt += f" ╚ **Duration** - {results[j]['duration']}\n"
                toxxt += f" ╚ **Views** - {results[j]['views']}\n"
                toxxt += f" ╚ **Channel** - {results[j]['channel']}\n\n"

                j += 1            
            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}'),
                    ],
                    [InlineKeyboardButton(text="❌", callback_data="cls")],
                ]
            )       
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            # WHY PEOPLE ALWAYS LOVE PORN ?? (A point to think)
            return
            # Returning to pornhub
        except:
            await lel.edit("هیچ ئەنجامێک نیە بۆ هەڵبژاردن دەستپێکردنی پەخشی ڕاستەوخۆ..")
                        
            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                    "گۆرانی نەدۆزرایەوە گۆرانییەکی تر تاقی بکەوە یان بە دروستی بینوسە."
                )
                print(str(e))
                return
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("📖 لیستی پەخشکراو", callback_data="playlist"),
                        InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
                    ],
                    [
                        InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                        InlineKeyboardButton(text="داگرتن 📥", url=f"{dlurl}"),
                    ],
                    [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
                ]
            )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"#⃣ گۆرانیەی داوات کردوە چوە ڕێزی {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("پەیوەندی گرووپ گرێنەدراوە یان ناتوانم پەیوەندی پێوە ی ببم")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="▶️ * ژەنین * لێرەدا گۆرانی داواکراوە لەلایەن { } لە ڕێگەی مۆسیقای یوتۆبۆت . 😜".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command("ytplay") & filters.group & ~filters.edited)
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔄 **پڕۆسەکە**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>لەبیرت بێت بۆ زیادکردنی یارمەتیدەر بۆ کەناڵەکەت</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>سەرەتا وەک بەڕێوەبەر زیادم بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "من بۆ ژەنینی موزیک لە ڤی سی بەشداریم لەم گرووپە کرد"
                    )
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە چاتەکەتەوە</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ گروپەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                                                "\n\n بە دەستی یاریدەدەرێک زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ دەوەستەوە لێرە داوای @teamkurdishchat بە لینکی گرووپەکەت</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot لەم چاتەدا نیە، داوا لە سەرپەرشتیار بکە بۆ یەکەم جار فەرمانی ناردن/play  بنێرە یان {user.first_name} بە دەستی لێرە داوا بکە @teamkurdishchat بەستەری گرووپەکەت</i>"
        )
        return
    await lel.edit("🔎 **ئەدۆزێتەوە**")
    user_id = message.from_user.id
    user_name = message.from_user.first_name
     

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    await lel.edit("🎵 **پرۆسەکە**")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.edit(
            "گۆرانی نەدۆزرایەوە گۆرانییەکی تر تاقی بکەوە یان بە دروستی بینوسە."
        )
        print(str(e))
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەخشکردن", callback_data="playlist"),
                InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                InlineKeyboardButton(text="داگرتن 📥", url=f"{dlurl}"),
            ],
            [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
        ]
    )
    requested_by = message.from_user.first_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"#⃣ گۆرانی داواکراوت **لە شوێنی {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("پەیوەندی گرووپ گرێنەدراوە یان ناتوانم پەیوەندی پێوە ی ببم")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="▶️ **ژەنین ** لێرەدا گۆرانی داواکراوە لەلایەن { } لە ڕێگەی مۆسیقای یوتۆبۆت 😜".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()
    
@Client.on_message(filters.command("dplay") & filters.group & ~filters.edited)
async def deezer(client: Client, message_: Message):
    if message_.chat.id in DISABLED_GROUPS:
        return
    global que
    lel = await message_.reply("🔄 **پرۆسەکە**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "Music Hama"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>لەبیرت بێت بۆ زیادکردنی یارمەتیدەر بۆ کەناڵەکەت</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>سەرەتا من وەک بەڕێوەبەر زیادی گرووپت بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "من بۆ ژەنینی موزیک لە ڤی سی بەشداریم لەم گرووپە کرد"
                    )
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە چاتەکەتەوە</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ گروپەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                                                "\n\n یان بە دەستی یاریدەدەرێک زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ بدە لێرە داوا @teamkurdishchat بە لینکی گروپەکەت</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot لەم چاتەدا نیە، داوا لە سەرپەرشتیار بکە بۆ یەکەم جار فەرمانی ناردن/play بنێرە یان {user.first_name} بە دەستی لێرە داوا بکە @teamkurdishchat بەستەری گرووپەکەت</i>"
        )
        return
    requested_by = message_.from_user.first_name

    text = message_.text.split(" ", 1)
    queryy = text[1]
    query = queryy
    res = lel
    await res.edit(f"گەران 👀👀👀 بۆ `{queryy}` لە deezer")
    try:
        songs = await arq.deezer(query,1)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        duration = songs.result[0].duration
        thumbnail = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"

    except:
        await res.edit("هیچ شتێکت نەدۆزیەوە، پێویستە لەسەر ئینگلیزیەکەت کار بکەی!")
        return
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"مووزیک درێژترە لە {DURATION_LIMIT}خولەک ڕێگە پێدراو نیە بۆ پەخشکردن")
            return
    except:
        pass    
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەخشکراوەکان", callback_data="playlist"),
                InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
            ],
            [InlineKeyboardButton(text="بینینی لە Deezer 🎬", url=f"{url}")],
            [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(url))
    await res.edit("دروست کردنی وێنە بچووکەکان")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        await res.edit("زیادکرا بۆ ڕێزەکە")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"✯{bn}✯= #️⃣ ڕێز بەندی لە  {position}")
    else:
        await res.edit_text(f"✯{bn}✯=▶️ پەخشکرا.....")

        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("پەیوەندی گرووپ نەبەستراوە بە من ناتوانم پەیوەندی پێوە ی ببم")
            return

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"پەخشکراوە [{title}]({url}) لە Deezer",
    )
    os.remove("final.png")


@Client.on_message(filters.command("splay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    if message_.chat.id in DISABLED_GROUPS:
        return    
    lel = await message_.reply("🔄 **پرۆسە**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "music_hamabot"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>لەبیرت بێت بۆ زیادکردنی یارمەتیدەر بۆ کەناڵەکەت</b>",
                    )
                    pass
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>یەکەم جار وەک بەڕێوەبەری گرووپ زیادم بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "من بۆ ژەنینی موزیک لە ڤی سی بەشداریم لەم گرووپە کرد"
                    )
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە چاتەکەتەوە</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ گروپەکەت بەهۆی داواکاریە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                                                "/n/n بە دەستی یی @music_hamabot زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ بدە لێرە داوای @teamkurdishchat بە لینکی گرووپەکەت</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> یارمەتیدەر Userbot لەم چاتەدا نیە، پرسیار لە سەرپەرشتیار بکە بۆ یەکەم جار فەرمانی ناردن/play یان زیادکردنی یارمەتیدەر داواکاری دەستی لێرە @teamkurdishchat بە لینکی گرووپەکەت</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"گەڕان 👀👀👀 بۆ `{query}` لەسەر جیۆ ساڤن")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("هیچ شتێک نەدۆزرایەوە!، پێویستە لەسەر ئینگلیزیەکەت کار بکەی.")
        print(str(e))
        return
    try:    
        duuration= round(sduration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"مووزیک درێژترە لە {DURATION_LIMIT} ڕێگە پێدراو نین بۆ پەخشکردن")
            return
    except:
        pass    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەخشکراوەکان", callback_data="playlist"),
                InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(
                    text="نوێ کردنەوەی بۆت", url=f"https://t.me/{updateschannel}"
                )
            ],
            [InlineKeyboardButton(text="❌ داختن", callback_data="cls")],
        ]
    )
    file_path = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"✯{bn}✯=#️⃣ ڕیزکردن لە شوێنی {position}",
        )

    else:
        await res.edit_text(f"{bn}=▶️ پەخشکراوو.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("پەیوەندی گرووپ نەبەستراوە بە من ناتوانم پەیوەندی پێوە ی ببم")
            return
    await res.edit("دروست کردنی وێنە بچووکەکان.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"پەخشکراو {sname} له ڕێگای جیوساڤان",
    )
    os.remove("final.png")


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que

    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    #useer_id = cb.message.reply_to_message.from_user.id
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("گۆرانی نەدۆزراوە")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("تۆ ئەو کەسە نیی کە داوای گۆرانیت کردووە!", show_alert=True)
        return
    await cb.message.edit("ڕاوەسته... دەستپێکردنی لێدەر")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    
    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:40]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://youtube.com{resultss}"
    
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"Music longer than {DURATION_LIMIT}min are not allowed to play")
            return
    except:
        pass
    try:
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەخشکراوەکان", callback_data="playlist"),
                InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="menu"),
            ],
            [
                InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                InlineKeyboardButton(text="داگرتن 📥", url=f"{dlurl}"),
            ],
            [InlineKeyboardButton(text="❌ داخستن", callback_data="cls")],
        ]
    )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))  
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption=f"#⃣  گۆرانی داواکراو لەلایەن {r_by.mention} **ڕێز**  {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)

        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            reply_markup=keyboard,
            caption=f"▶️ **پەخشکرا** لێرەدا گۆرانیەکە داواکرا لەلایەن {r_by.mention} لە ڕێگەی مۆسیقای یوتۆب 😜",
        )
        
        os.remove("final.png")

# Have u read all. If read RESPECT :-)
