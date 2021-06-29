from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
import asyncio
from VCPlayBot.helpers.decorators import authorized_users_only, errors
from VCPlayBot.services.callsmusic.callsmusic import client as USER
from VCPlayBot.config import SUDO_USERS

@Client.on_message(filters.command(["userbotjoin"]) & ~filters.private & ~filters.bot)
@authorized_users_only
@errors
async def addchannel(client, message):
    chid = message.chat.id
    try:
        invitelink = await client.export_chat_invite_link(chid)
    except:
        await message.reply_text(
            "<b>سەرەتا وەک بەڕێوەبەر زیادی گرووم بکە</b>",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = "music_hamabot"

    try:
        await USER.join_chat(invitelink)
        await USER.send_message(message.chat.id, "من لێرە بەشداریم کرد وەک تۆ داوات کرد")
    except UserAlreadyParticipant:
        await message.reply_text(
            "<b>یارمەتیدەر لە چاتەکەت</b>",
        )
    except Exception as e:
        print(e)
        await message.reply_text(
            f"<b>🛑 Flood Wait Error 🛑 \n User {user.first_name} نەیتوانی بچێتە پاڵ گروپەکەت بەهۆی داواکاریەکانی پەیوەندی قورس بۆ userbot! دڵنیابە لەوەی بەکارهێنەر قەدەغە نەکراوە لە گروپدا."
             " بە دەستی ززیاد @music_hama گروپەکەت و دووبارە هەوڵ بدە</b>",
        )
        return
    await message.reply_text(
        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە چاتەکەتەوە</b>",
    )


@USER.on_message(filters.group & filters.command(["userbotleave"]))
@authorized_users_only
async def rem(USER, message):
    try:
        await USER.leave_chat(message.chat.id)
    except:
        await message.reply_text(
            f"<b>بەکارهێنەر نەیتوانی گروپەکەت بەجێبهێڵێت! لەوانەیە چاوەروانکردنی لافاو بێت بە دەستی لە گروپەکەتەوە پێم بدە</b>",
        )
        return
    
@Client.on_message(filters.command(["userbotleaveall"]))
async def bye(client, message):
    if message.from_user.id in SUDO_USERS:
        left=0
        failed=0
        lol = await message.reply("یارمەتیدەر هەموو چاتەکانی جێ دەهێلێ")
        async for dialog in USER.iter_dialogs():
            try:
                await USER.leave_chat(dialog.chat.id)
                left = left+1
                await lol.edit(f"یاریدەدەری ڕۆیشتن چەپ: {left} چات سەرکەوتوو نەبوو: {failed} چات.")
            except:
                failed=failed+1
                await lol.edit(f"یاریدەری ڕۆیشتن چەپ :  {left} چات سەرکەوتوو نەبوو: {failed} چات.")
            await asyncio.sleep(0.7)
        await client.send_message(message.chat.id, f"ڕۆشتنی {left} چات. سەرکەووتوونەبوو {failed} .")
    
    
@Client.on_message(filters.command(["userbotjoinchannel","ubjoinc"]) & ~filters.private & ~filters.bot)
@authorized_users_only
@errors
async def addcchannel(client, message):
    try:
      conchat = await client.get_chat(message.chat.id)
      conid = conchat.linked_chat.id
      chid = conid
    except:
      await message.reply("چات تەنانەت بەستراوە")
      return    
    chat_id = chid
    try:
        invitelink = await client.export_chat_invite_link(chid)
    except:
        await message.reply_text(
            "<b>سەرەتا وەک بەڕێوەبەری کەناڵی یور زیادم بکە</b>",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = "music_hamabot"

    try:
        await USER.join_chat(invitelink)
        await USER.send_message(message.chat.id, "من لێرە بەشداریم کرد وەک تۆ داوات کرد")
    except UserAlreadyParticipant:
        await message.reply_text(
            "<b>یارمەتیدەر لە کەناڵەکەتدا</b>",
        )
        return
    except Exception as e:
        print(e)
        await message.reply_text(
            f"<b>🛑 Flood Wait Error 🛑 \n User {user.first_name} نەیتوانی بچێتە پاڵ کەناڵەکەت بەهۆی داواکاریەکانی پەیوەندی قورس بۆ userbot! دڵنیابە لەوەی بەکارهێنەر لە کەناڵ قەدەغە ناکرێت"
             " بە دەستی زیاد @music_hamabot گروپەکەت و دووبارە هەوڵ بدە</b>",
        )
        return
    await message.reply_text(
        "<b>یارمەتیدەری بەکارهێنەربۆت پەیوەندی کرد بە کەناڵەکەت</b>",
    )
    
