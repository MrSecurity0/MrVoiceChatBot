from pyrogram import Client
import asyncio
from VCPlayBot.config import SUDO_USERS, PMPERMIT
from pyrogram import filters
from pyrogram.types import Message
from VCPlayBot.services.callsmusic.callsmusic import client as USER

PMSET =True
pchats = []

@USER.on_message(filters.text & filters.private & ~filters.me & ~filters.bot)
async def pmPermit(client: USER, message: Message):
    if PMPERMIT == "ENABLE":
        if PMSET:
            chat_id = message.chat.id
            if chat_id in pchats:
                return
            await USER.send_message(
                message.chat.id,"سڵاو، ئەمە خزمەتگوزاری یاریدەری مۆسیقایە .\n\n\ ❗️ یاساکان:\n - هیچ چاتکردنێک ڕێگە پێدراو نیە\n - هیچ سپامێک رێگەپێدراو نییە \n 👉**ناردنی لینکی بانگهێشتکردنی گرووپەکەت یان ناوی بەکارهێنەر لێرە @teamkurdishchat ئەگەر USERBOT نناتوانێت بچێتە ناو گروپەکەتەوە.**\n ⚠️  ئەگەر پێویستت بە هەر یارمەتییەک هەیە دواتر پەیوەندی بکە بە گروپی پشتگیری :- @teamkurdishchat - ئەم بەکارهێنەرە زیاد مەکە بۆ گروپە نهێنیەکان.\n - زانیاری تایبەتی لێرە بەش مکە\n",
            )
            return

    

@Client.on_message(filters.command(["/pmpermit"]))
async def bye(client: Client, message: Message):
    if message.from_user.id in SUDO_USERS:
        global PMSET
        text = message.text.split(" ", 1)
        queryy = text[1]
        if queryy == "on":
            PMSET = True
            await message.reply_text("مۆڵەتی نیوەڕۆ هەڵکرا")
            return
        if queryy == "off":
            PMSET = None
            await message.reply_text("مۆڵەتی نیوەڕۆ کوژاوەتەوە")
            return

@USER.on_message(filters.text & filters.private & filters.me)        
async def autopmPermiat(client: USER, message: Message):
    chat_id = message.chat.id
    if not chat_id in pchats:
        pchats.append(chat_id)
        await message.reply_text("خەمڵاندن بۆ PM بەهۆی نامە رۆیشکراوەکان")
        return
    message.continue_propagation()    
    
@USER.on_message(filters.command("a", [".", ""]) & filters.me & filters.private)
async def pmPermiat(client: USER, message: Message):
    chat_id = message.chat.id
    if not chat_id in pchats:
        pchats.append(chat_id)
        await message.reply_text("بە سەر پی ئێم دا دەکێشت")
        return
    message.continue_propagation()    
    

@USER.on_message(filters.command("da", [".", ""]) & filters.me & filters.private)
async def rmpmPermiat(client: USER, message: Message):
    chat_id = message.chat.id
    if chat_id in pchats:
        pchats.remove(chat_id)
        await message.reply_text("نابەزبۆوبۆپ")
        return
    message.continue_propagation()    
