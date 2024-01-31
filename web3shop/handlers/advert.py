from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import filters
from keyboards.actions import cancel_keyboard
from misc.states import GlobalMessage

from data.loader import dp, bot, sqlite
from keyboards.admin import advert_keyboard

advert_data = []


@dp.message_handler(filters.Text(equals=["✏Change message"]), state=GlobalMessage.menu)
async def change_message(message: types.Message):
    await message.answer('Write a new message\n<code>text/photo/gif</code>', reply_markup=cancel_keyboard)
    return await GlobalMessage.add.set()


@dp.message_handler(filters.Text(equals=["👁‍🗨Check message"]), state=GlobalMessage.menu)
async def check_message(message: types.Message):
    if advert_data != []:
        if advert_data[0] == 'text':
            await message.answer(advert_data[1], reply_markup=advert_data[2],
                                 disable_web_page_preview=True,
                                 entities=advert_data[4])
        elif advert_data[0] == 'photo':
            await message.answer_photo(advert_data[3], caption=advert_data[1],
                                       reply_markup=advert_data[2],
                                       caption_entities=advert_data[4])
        elif advert_data[0] == 'gif':
            await message.answer_animation(advert_data[3],
                                           caption=advert_data[1],
                                           reply_markup=advert_data[2],
                                           caption_entities=advert_data[4])
    else:
        await message.answer('⚠You have not added a message')


@dp.message_handler(filters.Text(equals=["📢Send message"]), state=GlobalMessage.menu)
async def send_message(message: types.Message):
    if advert_data != []:
        msg = await message.answer('<code>Newsletter started</code>')
        users = sqlite.cursor().execute("SELECT id from users").fetchall()
        num = 0
        for x in users:
            try:
                if advert_data[0] == 'text':
                    await bot.send_message(x[0], advert_data[1],
                                           reply_markup=advert_data[2],
                                           disable_web_page_preview=True,
                                           entities=advert_data[4])
                elif advert_data[0] == 'photo':
                    await bot.send_photo(x[0], advert_data[3], caption=advert_data[1],
                                         reply_markup=advert_data[2],
                                         caption_entities=advert_data[4])
                elif advert_data[0] == 'gif':
                    await bot.send_animation(x[0], advert_data[3],
                                             caption=advert_data[1],
                                             reply_markup=advert_data[2],
                                             caption_entities=advert_data[4])
                num += 1
            except:
                pass
            await sleep(0.05)
        await msg.delete()
        await message.answer(f'Message received by <b>{num}</b> users')
    else:
        await message.answer('⚠You have not added a message')


# Global message add content
@dp.message_handler(content_types=['text', 'photo', 'animation'], state=GlobalMessage.add)
async def notify_text(message: types.Message):
    global advert_data
    if 'photo' in message:
        advert_data = ['photo', message['caption'], message.reply_markup,
                       message.photo[-1].file_id,
                       message.caption_entities]
    elif 'animation' in message:
        advert_data = ['gif', message['caption'], message.reply_markup,
                       message.animation.file_id,
                       message.caption_entities]
    else:
        advert_data = ['text', message['text'], message.reply_markup, None,
                       message.entities]
    await message.answer('✅Message added', reply_markup=advert_keyboard)
    await GlobalMessage.menu.set()
