import os
from asyncio import sleep

import psutil
from aiogram import types
from aiogram.dispatcher import filters

from data.loader import dp, admin_ids, cursor, sqlite, locale
from keyboards.admin import admin_keyboard
from keyboards.edit_bot import edit_keyboard
from keyboards.keyboards import cancel_keyboard
from keyboards.main import keyboard, lang_keyboard, sub_button
from utils.states import BotSetup
from utils.utils import send_log, lang_user, check_sub, bot_info, tCurrent, update_config, start_slave_bot

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


@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    req = cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE id = ?)',
                         [message.chat.id]).fetchone()[0]
    if req == 0:
        lang = message.from_user.language_code
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (message.chat.id, lang, 0, tCurrent()))
        sqlite.commit()
        await send_log(message.chat, 'Started bot')
        keyb = keyboard(lang, message.chat.id)
    else:
        lang = lang_user(message.chat.id)
        keyb = keyboard(lang, message.chat.id)
    await message.answer(locale[lang]['start'], reply_markup=keyb, disable_web_page_preview=True)
    await message.answer(locale[lang]['lang_start'])


@dp.message_handler(filters.Text(equals=["🤖Create Shop", "🤖Создать магазин"], ignore_case=True))
async def create_bot(message: types.Message):
    req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM bots WHERE id = ?)',
                              [message.chat.id]).fetchone()[0])
    lang = lang_user(message.chat.id)
    if req is False:
        check = await check_sub(message.chat.id)
        if check is True:
            await message.answer(locale[lang]['setup_msg'], reply_markup=cancel_keyboard(lang))
            await BotSetup.token.set()
        else:
            await message.answer(locale[lang]['no_sub'], reply_markup=sub_button(lang), disable_web_page_preview=True)


@dp.message_handler(filters.Text(equals=["✏Edit Bot", "✏Редактировать бота", "🤖Admin Menu", "🤖Админ меню"]), state='*')
async def edit_bot_and_admin(message: types.Message):
    if message.text in ['✏Edit Bot', '✏Редактировать бота']:
        req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM bots WHERE id = ?)',
                                  (message.chat.id,)).fetchone()[0])
        lang = lang_user(message.chat.id)
        if req:
            text = bot_info(message.chat.id, lang)
            keyb = edit_keyboard(lang)
        else:
            text = locale[lang]['return_to_menu']
            keyb = keyboard(lang, message.chat.id)
        await message.answer(text, reply_markup=keyb)
    elif message.text in ['🤖Admin Menu', '🤖Админ меню'] and message.chat.id in admin_ids:
        await message.answer('You have opened the admin menu', reply_markup=admin_keyboard)


@dp.message_handler(filters.Text(equals=["🔄Restart Bot", "🔄Перезапустить бота"]), state='*')
async def restart_bot(message: types.Message):
    lang = lang_user(message.chat.id)
    req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM bots WHERE id = ?)',
                              (message.chat.id,)).fetchone()[0])
    if req is False:
        return
    msg = await message.answer(locale[lang]['bot_restarting'])
    user_id = message['from']['id']
    check = await check_sub(user_id)
    if check is False:
        return await msg.edit_text(locale[lang]['no_sub_restart'], reply_markup=sub_button(lang),
                                    disable_web_page_preview=True)
    user_req = cursor.execute('SELECT sleep FROM users WHERE id = ?', [user_id]).fetchone()
    if user_req[0] > tCurrent():
        return await msg.edit_text(locale[lang]['wait_15'])
    cursor.execute('UPDATE users SET sleep = ? WHERE id = ?', [tCurrent() + 15, user_id])
    update_config(user_id)
    req = cursor.execute('SELECT pid, stopped FROM bots WHERE id = ?', (user_id,)).fetchone()
    if req[0] is not None:
        check_process = psutil.pid_exists(req[0])
        if check_process is True:
            os.kill(req[0], 2)
            await sleep(1)
    await start_slave_bot(user_id)
    await msg.edit_text(locale[lang]['bot_restarted'])


@dp.message_handler(commands=['lang'], state='*')
async def lang_change(message: types.Message):
    await message.answer('Select language:', reply_markup=lang_keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('lang/'), state='*')
async def inline_lang(call: types.CallbackQuery):
    lang = call.data.lstrip('lang/')
    cursor.execute('UPDATE users SET lang = ? WHERE id = ?',
                   (lang, call.from_user.id))
    sqlite.commit()
    await call.message.delete()
    user_id = call.from_user.id
    keyb = keyboard(lang, user_id)
    await call.message.answer(locale[lang]['lang_select'], reply_markup=keyb)
