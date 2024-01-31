from aiogram import types
from aiogram.dispatcher import FSMContext

from data.loader import dp, locale, sqlite, cursor, bot
from keyboards.main import keyboard
from utils.db_tools import sqlite_init, create_tables
from utils.states import BotSetup
from utils.utils import lang_user, check_token, tCurrent, start_slave_bot, update_config, send_log

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


@dp.message_handler(state=BotSetup.token)
async def bot_token(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    bot_tag = await check_token(message.text)
    if bool(bot_tag) is False:
        return await message.answer(locale[lang]['edit_token_error'])
    token = message.text
    user_id = message.chat.id
    if lang == 'ru':
        bot_lang = 2
    else:
        bot_lang = 1
    await bot.delete_message(message.chat.id, message.message_id)
    cursor.execute('INSERT INTO bots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (user_id, tCurrent(), None, 1, token,
                    bot_tag, 0, None, bot_lang, None, None, None, 'USD', None, None, None, False))
    messages = locale['shop']
    cursor.execute('INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (user_id, messages['start_en'], messages['start_ru'], messages['help_en'],
                    messages['help_ru'], messages['contact_en'], messages['contact_ru'],
                    messages['help_button_en'], messages['help_button_ru'], messages['contact_button_en'],
                    messages['contact_button_ru'], messages['invite_en'], messages['invite_ru'],
                    messages["terms_ru"], messages["terms_en"]))
    cursor.execute('INSERT INTO qiwi VALUES (?, ?, ?, ?, ?)', (user_id, None, None, None, None))
    cursor.execute('INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, 0, 0, 0, 0, 0, 0))
    sqlite.commit()
    db_create = sqlite_init(f'web3shop/shops/{user_id}.db')
    create_tables(db_create)
    db_create.close()
    update_config(user_id)
    await send_log(message.chat, f'Create a bot @{bot_tag}')
    await state.finish()
    await message.answer(locale[lang]['bot_created'].format(bot_tag), reply_markup=keyboard(lang, user_id))
    try:
        await start_slave_bot(user_id)
        await message.answer(locale[lang]['bot_started'])
    except:
        pass
