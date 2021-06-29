from __future__ import unicode_literals

import asyncio
import math
import os
import time
from random import randint
from urllib.parse import urlparse

import aiofiles
import aiohttp
import requests
import wget
import youtube_dl
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import Message
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos

from VCPlayBot.config import DURATION_LIMIT
from VCPlayBot.modules.play import arq


@Client.on_message(filters.command("song") & ~filters.channel)
def song(client, message):

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    m = message.reply("🔎 گەران بۆ دۆزینەوەی گۆرانی...")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)

        duration = results[0]["duration"]
        results[0]["url_suffix"]
        results[0]["views"]

    except Exception as e:
        m.edit("❌ نەدۆزاراوە تکایەهەوڵبدە ناوی گۆرانی یاخود ناووی هوونەرمەند بەرووستی بنوسیت.")
        print(str(e))
        return
    m.edit("گۆرانیە دایەبەزێ ")
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_file = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)
        rep = "**🎵 هەڵگیرا لەلایەن **"
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(dur_arr[i]) * secmul
            secmul *= 60
        message.reply_audio(
            audio_file,
            caption=rep,
            thumb=thumb_name,
            parse_mode="md",
            title=title,
            duration=dur,
        )
        m.delete()
    except Exception as e:
        m.edit("❌ هەڵە ڕوویدا")
        print(e)

    try:
        os.remove(audio_file)
        os.remove(thumb_name)
    except Exception as e:
        print(e)


def get_text(message: Message) -> [None, str]:
    text_to_return = message.text
    if message.text is None:
        return None
    if " " in text_to_return:
        try:
            return message.text.split(None, 1)[1]
        except IndexError:
            return None
    else:
        return None


def humanbytes(size):
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


async def progress(current, total, message, start, type_of_ps, file_name=None):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        if elapsed_time == 0:
            return
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        progress_str = "{0}{1} {2}%\n".format(
            "".join(["🔴" for i in range(math.floor(percentage / 10))]),
            "".join(["🔘" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        tmp = progress_str + "{0} of {1}\nETA: {2}".format(
            humanbytes(current), humanbytes(total), time_formatter(estimated_total_time)
        )
        if file_name:
            try:
                await message.edit(
                    "{}\n**ناووی فایڵ:** `{}`\n{}".format(type_of_ps, file_name, tmp)
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass
        else:
            try:
                await message.edit("{}\n{}".format(type_of_ps, tmp))
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except MessageNotModified:
                pass


def get_user(message: Message, text: str) -> [int, str, None]:
    if text is None:
        asplit = None
    else:
        asplit = text.split(" ", 1)
    user_s = None
    reason_ = None
    if message.reply_to_message:
        user_s = message.reply_to_message.from_user.id
        reason_ = text if text else None
    elif asplit is None:
        return None, None
    elif len(asplit[0]) > 0:
        user_s = int(asplit[0]) if asplit[0].isdigit() else asplit[0]
        if len(asplit) == 2:
            reason_ = asplit[1]
    return user_s, reason_


def get_readable_time(seconds: int) -> int:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " ڕۆژ(s), ") if days else "")
        + ((str(hours) + " کاژمێر(s), ") if hours else "")
        + ((str(minutes) + " خوڵەک(s), ") if minutes else "")
        + ((str(seconds) + " چرکە(s), ") if seconds else "")
        + ((str(milliseconds) + " کۆی چرکەکان(s), ") if milliseconds else "")
    )
    return tmp[:-2]


ydl_opts = {
    "format": "bestaudio/best",
    "writethumbnail": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


def get_file_extension_from_url(url):
    url_path = urlparse(url).path
    basename = os.path.basename(url_path)
    return basename.split(".")[-1]


# Funtion To Download Song
async def download_song(url):
    song_name = f"{randint(6969, 6999)}.mp3"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(song_name, mode="wb")
                await f.write(await resp.read())
                await f.close()
    return song_name


is_downloading = False


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


@Client.on_message(filters.command("saavn") & ~filters.edited)
async def jssong(_, message):
    global is_downloading
    if len(message.command) < 2:
        await message.reply_text("/saavn پێویستی بە مشتومڕە.")
        return
    if is_downloading:
        await message.reply_text(
            "داگرتنێکی تر لە پەرەسەندندایە، پاش هەندێک جار دووبارە هەوڵ بدە."
        )
        return
    is_downloading = True
    text = message.text.split(None, 1)[1]
    query = text.replace(" ", "%20")
    m = await message.reply_text("گەڕانەکان...")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        await m.edit("Downloading")
        song = await download_song(slink)
        await m.edit("Uploading")
        await message.reply_audio(audio=song, title=sname, performer=ssingers)
        os.remove(song)
        await m.delete()
    except Exception as e:
        is_downloading = False
        await m.edit(str(e))
        return
    is_downloading = False


# Deezer Music


@Client.on_message(filters.command("deezer") & ~filters.edited)
async def deezsong(_, message):
    global is_downloading
    if len(message.command) < 2:
        await message.reply_text("/deezer پێویستی بە مشتوڕمە.")
        return
    if is_downloading:
        await message.reply_text(
            "داگرتنێکی تر لە پەرەسەندندایە، پاش هەندێک جار دووبارە هەوڵ بدە."
        )
        return
    is_downloading = True
    text = message.text.split(None, 1)[1]
    query = text.replace(" ", "%20")
    m = await message.reply_text("گەرانەکان...")
    try:
        songs = await arq.deezer(query, 1)
        if not songs.ok:
            await message.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        await m.edit("Downloading")
        song = await download_song(url)
        await m.edit("Uploading")
        await message.reply_audio(audio=song, title=title, performer=artist)
        os.remove(song)
        await m.delete()
    except Exception as e:
        is_downloading = False
        await m.edit(str(e))
        return
    is_downloading = False


@Client.on_message(filters.command(["vsong", "video"]))
async def ytmusic(client, message: Message):
    global is_downloading
    if is_downloading:
        await message.reply_text(
            "داگرتنێکی تر لە پەرەسەندندایە، پاش هەندێک جار دووبارە هەوڵ بدە."
        )
        return

    urlissed = get_text(message)

    pablo = await client.send_message(
        message.chat.id, f"`دەستکەوتن {urlissed} لە یۆتۆب سەرڤەر تکایه چاوەڕوان بکه.`"
    )
    if not urlissed:
        await pablo.edit("ڕستەی فرمان نادروستە، تکایە لیستی یارمەتی بپشکنە بۆ زانیاری زیاتر!")
        return

    search = SearchVideos(f"{urlissed}", offset=1, mode="dict", max_results=1)
    mi = search.result()
    mio = mi["search_result"]
    mo = mio[0]["link"]
    thum = mio[0]["title"]
    fridayz = mio[0]["id"]
    thums = mio[0]["channel"]
    kekme = f"https://img.youtube.com/vi/{fridayz}/hqdefault.jpg"
    await asyncio.sleep(0.6)
    url = mo
    sedlyf = wget.download(kekme)
    opts = {
        "format": "best",
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "outtmpl": "%(id)s.mp4",
        "logtostderr": False,
        "quiet": True,
    }
    try:
        is_downloading = True
        with youtube_dl.YoutubeDL(opts) as ytdl:
            infoo = ytdl.extract_info(url, False)
            duration = round(infoo["duration"] / 60)

            if duration > DURATION_LIMIT:
                await pablo.edit(
                    f"❌ ڕێگە بە ڤیدیۆکان درێژتر لە {DURATION_LIMIT} خولەک(s) نەدراوە، ڤیدیۆی دابینکراو {duration} خولەک(s)"
                )
                is_downloading = False
                return
            ytdl_data = ytdl.extract_info(url, download=True)

    except Exception:
        # await pablo.edit(event, f"**Failed To Download** \n**Error :** `{str(e)}`")
        is_downloading = False
        return

    c_time = time.time()
    file_stark = f"{ytdl_data['id']}.mp4"
    capy = f"**ناووی ڤیدیۆ ➠** `{thum}` \n**داواکاوە لە :** `{urlissed}` \n**کەناڵ :** `{thums}` \n**بەستەرە :** `{mo}`"
    await client.send_video(
        message.chat.id,
        video=open(file_stark, "rb"),
        duration=int(ytdl_data["duration"]),
        file_name=str(ytdl_data["title"]),
        thumb=sedlyf,
        caption=capy,
        supports_streaming=True,
        progress=progress,
        progress_args=(
            pablo,
            c_time,
            f"`بارکردنی {urlised} گۆرانی لە مۆسیقای یوتوب!`",
            file_stark,
        ),
    )
    await pablo.delete()
    is_downloading = False
    for files in (sedlyf, file_stark):
        if files and os.path.exists(files):
            os.remove(files)
