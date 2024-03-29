


























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import filters

from data.loader import dp, bot, cursor
from keyboards.admin import advert_keyboard
from keyboards.main import return_keyboard
from utils.states import GlobalMessage

from aiogram.types import ChatType, Message

@dp.message_handler(chat_type=ChatType.SUPERGROUP)
async def bot_handler(message: Message):
    return


@dp.message_handler(chat_type=ChatType.GROUP)
async def bot_handler(message: Message):
    return


@dp.message_handler(chat_type=ChatType.CHANNEL)
async def bot_handler(message: Message):
    return

adv_text = []


@dp.message_handler(filters.Text(equals=["👁‍🗨Check message", "📢Send message", "✏Change message"],
                                 ignore_case=True), state=GlobalMessage.menu)
async def adb_check(message: types.Message):
    if message.text == '✏Change message':
        await message.answer('Write a new message\n<code>text/photo/gif</code>', reply_markup=return_keyboard)
        return await GlobalMessage.add.set()
    if adv_text != []:
        if message.text == '👁‍🗨Check message':
            if adv_text[0] == 'text':
                await message.answer(adv_text[1], reply_markup=adv_text[2],
                                     disable_web_page_preview=True,
                                     entities=adv_text[4])
            elif adv_text[0] == 'photo':
                await message.answer_photo(adv_text[3], caption=adv_text[1],
                                           reply_markup=adv_text[2],
                                           caption_entities=adv_text[4])
            elif adv_text[0] == 'gif':
                await message.answer_animation(adv_text[3],
                                               caption=adv_text[1],
                                               reply_markup=adv_text[2],
                                               caption_entities=adv_text[4])
        elif message.text == '📢Send message':
            msg = await message.answer('<code>Newsletter started</code>')
            users = cursor.execute("SELECT id from users").fetchall()
            num = 0
            for x in users:
                try:
                    if adv_text[0] == 'text':
                        await bot.send_message(x[0], adv_text[1],
                                               reply_markup=adv_text[2],
                                               disable_web_page_preview=True,
                                               entities=adv_text[4])
                    elif adv_text[0] == 'photo':
                        await bot.send_photo(x[0], adv_text[3], caption=adv_text[1],
                                             reply_markup=adv_text[2],
                                             caption_entities=adv_text[4])
                    elif adv_text[0] == 'gif':
                        await bot.send_animation(x[0], adv_text[3],
                                                 caption=adv_text[1],
                                                 reply_markup=adv_text[2],
                                                 caption_entities=adv_text[4])
                    num += 1
                except:
                    pass
                await sleep(0.1)
            await msg.delete()
            await message.answer(f'Message received by <b>{num}</b> users')
    else:
        await message.answer('You have not added a message')


@dp.message_handler(content_types=['text', 'photo', 'animation'], state=GlobalMessage.add)
async def notify_text(message: types.Message):
    global adv_text
    if 'photo' in message:
        adv_text = ['photo', message['caption'], message.reply_markup,
                    message.photo[-1].file_id,
                    message.caption_entities]
    elif 'animation' in message:
        adv_text = ['gif', message['caption'], message.reply_markup,
                    message.animation.file_id,
                    message.caption_entities]
    else:
        adv_text = ['text', message['text'], message.reply_markup, None,
                    message.entities]
    await message.answer('Message added', reply_markup=advert_keyboard)
    await GlobalMessage.menu.set()
