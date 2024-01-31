import os
from asyncio import sleep

import psutil
from aiogram import types
from aiogram.dispatcher import filters

from data.loader import dp, locale, cursor, sqlite, bot
from keyboards.edit_bot import edit_keyboard, edit_admin_keyboard, edit_messages_keyboard, edit_lang_keyboard, \
    payment_keyboard, payments_groups_keyboard, finance_keyboard
from keyboards.keyboards import cancel_keyboard, stop_keyboard, delete_keyboard, link_disable_keyboard, \
    ref_disable_keyboard
from keyboards.main import keyboard
from utils.states import BotEdit
from utils.utils import lang_user, bot_info


@dp.callback_query_handler(lambda call: call.data == 'edit_menu')
async def edit_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    text = bot_info(call.from_user.id, lang)
    keyb = edit_keyboard(lang)
    await call.message.edit_text(text, reply_markup=keyb)


@dp.callback_query_handler(lambda call: call.data.startswith('payment_group/'))
async def edit_bot(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)

    await call.message.edit_text(locale[lang]['payment_methods'], reply_markup=payment_keyboard(user_id, lang, data))


@dp.callback_query_handler(lambda call: call.data.startswith('edit/'))
async def edit_bot(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'token':
        await call.message.answer(locale[lang]['edit_token'], reply_markup=cancel_keyboard(lang))
        await BotEdit.token.set()
    elif data == 'payments':
        await call.message.edit_text(locale[lang]['payment_methods'], reply_markup=payments_groups_keyboard(lang))
    elif data == 'finance':
        await call.message.edit_text(locale[lang]["finance_text"], reply_markup=finance_keyboard(lang, user_id))
    elif data == 'can_send':
        status = bool(cursor.execute("SELECT can_user_transfer FROM bots WHERE id = ?", [user_id]).fetchone()[0])
        cursor.execute('UPDATE bots SET can_user_transfer = ? WHERE id = ?', [not status, user_id])
        sqlite.commit()
        await call.message.edit_reply_markup(reply_markup=finance_keyboard(lang, user_id))

        # await call.message.edit_text(locale[lang]['payment_methods'], reply_markup=payment_keyboard(user_id, lang))
    elif data == 'stop':
        await call.message.answer(locale[lang]['edit_stop'], reply_markup=stop_keyboard)
    elif data == 'delete':
        await call.message.edit_text(locale[lang]['edit_delete'], reply_markup=delete_keyboard)
    elif data == 'admins':
        await call.message.edit_reply_markup(reply_markup=edit_admin_keyboard(lang))
    elif data == 'invite':
        await call.message.answer(locale[lang]['edit_invite_id'], reply_markup=link_disable_keyboard(lang))
        await BotEdit.invite_id.set()
    elif data == 'referral':
        await call.message.answer(locale[lang]['edit_ref'], reply_markup=ref_disable_keyboard(lang))
        await BotEdit.referral.set()
    elif data == 'currency':
        await call.message.answer(locale[lang]['edit_currency_list'], reply_markup=cancel_keyboard(lang))
        await BotEdit.currency.set()
    elif data == 'locale':
        lang_req = cursor.execute('SELECT locale FROM bots WHERE id = ?', (user_id,)).fetchone()[0]
        if lang_req == 1:
            cursor.execute('UPDATE bots SET locale = 2 WHERE id = ?', (user_id,))
            new_lang = '🇷🇺Русский'
        elif lang_req == 2:
            cursor.execute('UPDATE bots SET locale = 3 WHERE id = ?', (user_id,))
            new_lang = '🇬🇧English/🇷🇺Русский'
        elif lang_req == 3:
            cursor.execute('UPDATE bots SET locale = 1 WHERE id = ?', (user_id,))
            new_lang = '🇬🇧English'
        sqlite.commit()
        await call.message.edit_text(bot_info(user_id, lang), reply_markup=edit_keyboard(lang))
        await call.message.answer(locale[lang]['lang_change'].format(new_lang))
    elif data == 'messages':
        req = cursor.execute('SELECT locale FROM bots WHERE id = ?', (user_id,)).fetchone()[0]
        text = locale[lang]['message_menu']
        if req == 3:
            text = locale[lang]['select_lang']
            keyb = edit_lang_keyboard(lang)
        elif req == 1:
            bot_lang = 'en'
            keyb = edit_messages_keyboard(lang, bot_lang)
        else:
            bot_lang = 'ru'
            keyb = edit_messages_keyboard(lang, bot_lang)
        await call.message.edit_text(text, reply_markup=keyb)
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('stop/'))
async def stop_bot(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'yes':
        req = cursor.execute('SELECT pid FROM bots WHERE id = ?', [user_id]).fetchone()
        if req[0] is not None:
            check_process = psutil.pid_exists(req[0])
            if check_process is True:
                os.kill(req[0], 2)
                await sleep(1)
        cursor.execute('UPDATE bots SET stopped = 1, pid = NULL WHERE id = ?', [user_id])
        sqlite.commit()
        await call.message.edit_text(locale[lang]['bot_stopped'])
    else:
        await call.message.edit_text(locale[lang]['canceled'])


@dp.callback_query_handler(lambda call: call.data.startswith('delete/'))
async def delete_bot(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'yes':
        pid = cursor.execute('SELECT pid FROM bots WHERE id = ?', [user_id]).fetchone()[0]
        if pid is not None:
            check_process = psutil.pid_exists(pid)
            if check_process is True:
                os.kill(pid, 2)
        cursor.execute('DELETE FROM bots WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM messages WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM admins WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM qiwi WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM payments WHERE id = ?', (user_id,))
        sqlite.commit()
        await sleep(3)
        try:
            os.remove(f'web3shop/shops/{user_id}.json')
        except:
            pass
        try:
            os.remove(f'web3shop/shops/{user_id}.db')
        except:
            pass
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        keyb = keyboard(lang, user_id)
        await bot.send_message(call.message.chat.id, locale[lang]['bot_deleted'], reply_markup=keyb)
    else:
        await call.message.edit_text(locale[lang]['canceled'])
