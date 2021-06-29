from os import path

from youtube_dl import YoutubeDL

from VCPlayBot.config import DURATION_LIMIT
from VCPlayBot.helpers.errors import DurationLimitError

ydl_opts = {
    "format": "bestaudio[ext=m4a]",
    "geo-bypass": True,
    "nocheckcertificate": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
}

ydl = YoutubeDL(ydl_opts)


def download(url: str) -> str:
    info = ydl.extract_info(url, False)
    duration = round(info["duration"] / 60)

    if duration > DURATION_LIMIT:
        raise DurationLimitError(
            f"❌ ڕێگە بە ڤیدیۆکان درێژتر لە {DURATION_LIMIT} خولەک(s) نەدراوە، ڤیدیۆی دابینکراو {duration} خولەک(s)"
        )
    try:
        ydl.download([url])
    except:
        raise DurationLimitError(
            f"❌ ڕێگە بە ڤیدیۆکان درێژتر لە {DURATION_LIMIT} خولەک(s) نەدراوە، ڤیدیۆی دابینکراو {duration} خولەک(s)"
        )
    return path.join("downloads", f"{info['id']}.{info['ext']}")
