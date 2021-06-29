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
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import Voice
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch
from VCPlayBot.modules.play import generate_cover
from VCPlayBot.modules.play import arq
from VCPlayBot.modules.play import cb_admin_check
from VCPlayBot.modules.play import transcode
from VCPlayBot.modules.play import convert_seconds
from VCPlayBot.modules.play import time_to_seconds
from VCPlayBot.modules.play import changeImageSize
from VCPlayBot.config import BOT_NAME as bn
from VCPlayBot.config import DURATION_LIMIT
from VCPlayBot.config import UPDATES_CHANNEL as updateschannel
from VCPlayBot.config import que
from VCPlayBot.function.admins import admins as a
from VCPlayBot.helpers.errors import DurationLimitError
from VCPlayBot.helpers.decorators import errors
from VCPlayBot.helpers.admins import get_administrators
from VCPlayBot.helpers.channelmusic import get_chat_id
from VCPlayBot.helpers.decorators import authorized_users_only
from VCPlayBot.helpers.filters import command, other_filters
from VCPlayBot.helpers.gets import get_file_name
from VCPlayBot.services.callsmusic import callsmusic, queues
from VCPlayBot.services.callsmusic.callsmusic import client as USER
from VCPlayBot.services.converter.converter import convert
from VCPlayBot.services.downloaders import youtube

chat_id = None



@Client.on_message(filters.command(["channelplaylist","cplaylist"]) & filters.group & ~filters.edited)
async def playlist(client, message):
    try:
      lel = await client.get_chat(message.chat.id)
      lol = lel.linked_chat.id
    except:
      message.reply("ئایا ئەم پشیلەیە تەنانەت بەستراوەتەوە?")
      return
    global que
    queue = que.get(lol)
    if not queue:
        await message.reply_text("لێدەر بێکار")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**پەخشی ئیستا** in {}".format(lel.linked_chat.title)
    msg += "\n- " + now_playing
    msg += "\n- داواکراوە لەلایەن  " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**ڕێز**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- {name}"
            msg += f"\n- داواکراوە {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = "ڕێکبەندەکانی **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "قەبارە : {}%\n".format(vol)
            stats += "ڕێزی گۆرانیە : `{}`\n".format(len(que))
            stats += "پەخشی ئیستا : **{}**\n".format(queue[0][0])
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
                InlineKeyboardButton("⏹", "cleave"),
                InlineKeyboardButton("⏸", "cpuse"),
                InlineKeyboardButton("▶️", "cresume"),
                InlineKeyboardButton("⏭", "cskip"),
            ],
            [
                InlineKeyboardButton("لیستی پەخشکردن 📖", "cplaylist"),
            ],
            [InlineKeyboardButton("❌ داخستن", "ccls")],
        ]
    )
    return mar


@Client.on_message(filters.command(["channelcurrent","ccurrent"]) & filters.group & ~filters.edited)
async def ee(client, message):
    try:
      lel = await client.get_chat(message.chat.id)
      lol = lel.linked_chat.id
      conv = lel.linked_chat
    except:
      await message.reply("چات تەنانەت بەستراوە")
      return
    queue = que.get(lol)
    stats = updated_stats(conv, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("هیچ حاڵەتێکی VC نیە کە لەم چاتەدا کاربکات")


@Client.on_message(filters.command(["channelplayer","cplayer"]) & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    playing = None
    try:
      lel = await client.get_chat(message.chat.id)
      lol = lel.linked_chat.id
      conv = lel.linked_chat
    except:
      await message.reply("چات تەنانەت بەستراوە")
      return
    queue = que.get(lol)
    stats = updated_stats(conv, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))

        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("هیچ حاڵەتێکی VC نیە کە لەم چاتەدا کاربکات")


@Client.on_callback_query(filters.regex(pattern=r"^(cplaylist)$"))
async def p_cb(b, cb):
    global que
    try:
      lel = await client.get_chat(cb.message.chat.id)
      lol = lel.linked_chat.id
      conv = lel.linked_chat
    except:
      return    
    que.get(lol)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(lol)
        if not queue:
            await cb.message.edit("لێدەر بێکار")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**پەخشی ئیستا** in {}".format(conv.title)
        msg += "\n- " + now_playing
        msg += "\n- لەلایەن " + by
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
    filters.regex(pattern=r"^(cplay|cpause|cskip|cleave|cpuse|cresume|cmenu|ccls)$")
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
      try:
        lel = await b.get_chat(cb.message.chat.id)
        lol = lel.linked_chat.id
        conv = lel.linked_chat
        chet_id = lol
      except:
        return
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat
    

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "cpause":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("چات نەبەستراوە تەوە !", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("گۆرانی ڕاگیرا!")
            await cb.message.edit(
                updated_stats(conv, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "cplay":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("چات نەبەستراوە تەوە !", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("گۆرانی لێداوە!")
            await cb.message.edit(
                updated_stats(conv, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "cplaylist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("پەخشکراو")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**ئیستا پەخشکراوە** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- لەلایەن " + by
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

    elif type_ == "cresume":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "playing"
        ):
            await cb.answer("چات نەبەستراوە تەوە یان پێشتر لێنەدراوە", show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chet_id)
            await cb.answer("گۆرانی پەخشکراوە!")
    elif type_ == "cpuse":
        if (chet_id not in callsmusic.pytgcalls.active_calls) or (
            callsmusic.pytgcalls.active_calls[chet_id] == "paused"
        ):
            await cb.answer("چات نەبەستراوە تەوە یان پێشتر راگیراوە", show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chet_id)

            await cb.answer("گۆرانی ڕاگیرا!")
    elif type_ == "ccls":
        await cb.answer("ڕێبەندەکان داخرا")
        await cb.message.delete()

    elif type_ == "cmenu":
        stats = updated_stats(conv, qeue)
        await cb.answer("ڕێبەندەکان کاوە")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "cleave"),
                    InlineKeyboardButton("⏸", "cpuse"),
                    InlineKeyboardButton("▶️", "cresume"),
                    InlineKeyboardButton("⏭", "cskip"),
                ],
                [
                    InlineKeyboardButton("لیستی پەخشکراوەکان 📖", "cplaylist"),
                ],
                [InlineKeyboardButton("❌ داخستن", "ccls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "cskip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.pytgcalls.active_calls:
            await cb.answer("نەبەستراوەتەوە بەچات!", show_alert=True)
        else:
            callsmusic.queues.task_done(chet_id)

            if callsmusic.queues.is_empty(chet_id):
                callsmusic.pytgcalls.leave_group_call(chet_id)

                await cb.message.edit("- زیاتر نیە لەلیستی پەخشکردن..\n- ڕۆشت لە VC!")
            else:
                callsmusic.pytgcalls.change_stream(
                    chet_id, callsmusic.queues.get(chet_id)["file"]
                )
                await cb.answer("تێپەڕێنرا")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- تڕاک تێپەڕاندا\n- پەخشی ئیستا **{qeue[0][0]}**"
                )

    else:
        if chet_id in callsmusic.pytgcalls.active_calls:
            try:
                callsmusic.queues.clear(chet_id)
            except QueueEmpty:
                pass

            callsmusic.pytgcalls.leave_group_call(chet_id)
            await cb.message.edit("چاتی بەجێهێشت!")
        else:
            await cb.answer("چات نەبەستراوەتەوە!", show_alert=True)


@Client.on_message(filters.command(["channelplay","cplay"])  & filters.group & ~filters.edited)
@authorized_users_only
async def play(_, message: Message):
    global que
    lel = await message.reply("🔄 **پڕۆسەکە**")

    try:
      conchat = await _.get_chat(message.chat.id)
      conv = conchat.linked_chat
      conid = conchat.linked_chat.id
      chid = conid
    except:
      await message.reply("لینکی چاتی بەتسراوەتەوە")
      return
    try:
      administrators = await get_administrators(conv)
    except:
      await message.reply("من بەڕێوەبەری کەناڵم")
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
                        "<b>وەک بەڕێوەبەری کەناڵی یور زیادم بکە  first</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە کەناڵەکەت</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ کەناڵەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                       " یان بە دەستی یاریدەدەرێک زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ بدە</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot لەم چاتەدا نیە، پرسیار بکە لە بەڕێوەبەری کەناڵ بۆ ناردنی/play فەرمان بۆ یەکەم جار یان زیادکردن {user.first_name} </i>"
        )
        return
    message.from_user.id
    text_links = None
    message.from_user.first_name
    await lel.edit("🔎 **گەران**")
    message.from_user.id
    user_id = message.from_user.id
    message.from_user.first_name
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
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
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ ڤیدیۆکە زۆر دڕێژە {DURATION_LIMIT} خوڵەکە(s) زیاتر ناتوانێ پەخشبکەم!"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 یستی پەحشکردن", callback_data="cplaylist"),
                    InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="cmenu"),
                ],
                [InlineKeyboardButton(text="❌ داخستن", callback_data="ccls")],
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
        await lel.edit("🎵 **پڕۆسەکە**")
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
        dlurl = url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 لیستی پەخشکردن", callback_data="cplaylist"),
                    InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="cmenu"),
                ],
                [
                    InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                    InlineKeyboardButton(text="دەبەزاندن 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="❌ داخستن", callback_data="ccls")],
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
        await lel.edit("🎵 **پڕۆسەکە**")
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

        dlurl = url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 لیستی پەخشکراوەکان", callback_data="cplaylist"),
                    InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="cmenu"),
                ],
                [
                    InlineKeyboardButton(text="🎬 یوتوب", url=f"{url}"),
                    InlineKeyboardButton(text="دابەزاندن 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="❌ داخستن", callback_data="ccls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))
    chat_id = chid
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
            caption=f"#⃣ تۆ گۆرانیەکەت داواکرد چوو بۆ ڕێزی {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = chid
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="▶️ **پەخشکردن** ئەو گۆرانییەی کە لە ڕێگەی مۆسیقای یوتۆبۆت داوای 😜 لە کەناڵی بەستراوو کراوە .".format(
                message.from_user.mention()
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command(["channeldplay","cdplay"]) & filters.group & ~filters.edited)
@authorized_users_only
async def deezer(client: Client, message_: Message):
    global que
    lel = await message_.reply("🔄 **پڕۆسەکە**")

    try:
      conchat = await client.get_chat(message_.chat.id)
      conid = conchat.linked_chat.id
      conv = conchat.linked_chat
      chid = conid
    except:
      await message_.reply("لینکی چات بەتسراوەتەوە")
      return
    try:
      administrators = await get_administrators(conv)
    except:
      await message.reply("من بەڕێوەبەرم لەکەناڵ") 
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
                        "<b>سەرەتا وەک بەڕێوەبەری کەناڵی یور زیادم بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە کەناڵەکەت</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ کەناڵەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر لە کەناڵ قەدەغە ناکرێت"
                                                " \n\n یان بە دەستی یاریدەدەرێک زیاد بکە بۆ گروپەکەت و دووبارە هەوڵ بدە</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} Userbot لەم کەناڵەدا نیە، داوا لە سەرپەرشتیار بکە بۆ یەکەمجار فەرمانی ناردن//play یان زیادکردن  {user.first_name} </i>"
        )
        return
    requested_by = message_.from_user.first_name

    text = message_.text.split(" ", 1)
    queryy = text[1]
    query=queryy
    res = lel
    await res.edit(f"گەران لە 👀👀👀 بۆ `{queryy}` deezer")
    try:
        songs = await arq.deezer(query,1)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        duration = songs.result[0].duration
        thumbnail = songs.result[0].thumbnail
    except:
        await res.edit("هیچ شتێکت نەدۆزیەوە، پێویستە لەسەر ئینگلیزیەکەت کار بکەی!")
        return
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەخشکراوەکان", callback_data="cplaylist"),
                InlineKeyboardButton("ڕێزەندەکان ⏯ ", callback_data="cmenu"),
            ],
            [InlineKeyboardButton(text="بینینی لە Deezer 🎬", url=f"{url}")],
            [InlineKeyboardButton(text="❌ داخستن", callback_data="ccls")],
        ]
    )
    file_path = await convert(wget.download(url))
    await res.edit("وێنەی بچوک درووستەکا")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = chid
    if chat_id in callsmusic.pytgcalls.active_calls:
        await res.edit("زیادکرا بۆ ڕێز")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"✯{bn}✯= #️⃣ ڕێزبەندی {position}")
    else:
        await res.edit_text(f"✯{bn}✯=▶️ پەخشکراوو.....")

        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"پەخشکرا [{title}]({url}) لە Deezer iلینکی کەناڵ",
    )
    os.remove("final.png")


@Client.on_message(filters.command(["channelsplay","csplay"]) & filters.group & ~filters.edited)
@authorized_users_only
async def jiosaavn(client: Client, message_: Message):
    global que
    lel = await message_.reply("🔄 **پڕۆسە**")
    try:
      conchat = await client.get_chat(message_.chat.id)
      conid = conchat.linked_chat.id
      conv = conchat.linked_chat
      chid = conid
    except:
      await message_.reply("لینکی چات نەبەستراوەە")
      return
    try:
      administrators = await get_administrators(conv)
    except:
      await message.reply("من بەڕێوەبەری کەناڵم")
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
                        "<b>یەکەم جار وەک بەڕێوەبەری گرووپی زیادم بکە</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە کەناڵەکەت</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} نەیتوانی بچێتە پاڵ کەناڵەکەت بەهۆی داواکاری ە قورسەکانی بەکارهێنەربۆت! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
                        " بە دەستی @music_hamabot گروپەکەت زیاد بکە و دووبارە هەوڵ بدە</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> یارمەتیدەر Userbot لەم کەناڵەدا نیە، پرسیار لە بەڕێوەبەری کەناڵەکە بکە بۆ ناردنی/play فەرمان بۆ یەکەم جار یان زیادکردنی یارمەتیدەر بە دەستی</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"گەڕان 👀👀👀 ە `{query}` ")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = "https://telegra.ph/file/f6086f8909fbfeb0844f2.png"
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("هیچ شتێک نەدۆزرایەوە!، پێویستە لەسەر ئینگلیزیەکەت کار بکەی.")
        print(str(e))
        return
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 لیستی پەشخراوەکان", callback_data="cplaylist"),
                InlineKeyboardButton("ڕێبەندەکان ⏯ ", callback_data="cmenu"),
            ],
            [
                InlineKeyboardButton(
                    text="Join Updates Channel", url=f"https://t.me/{updateschannel}"
                )
            ],
            [InlineKeyboardButton(text="❌ داخستن", callback_data="ccls")],
        ]
    )
    file_path = await convert(wget.download(slink))
    chat_id = chid
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
            caption=f"✯{bn}✯=#️⃣ ڕێزبەندی {position}",
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
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
    await res.edit(".")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"پەخشکراوو {sname}",
    )
    os.remove("final.png")


# Have u read all. If read RESPECT :-)
