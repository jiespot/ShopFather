import os
import re

import psutil
from aiogram import types
from aiogram.dispatcher import FSMContext, filters

from data.loader import dp, locale, cursor, sqlite, bot
from keyboards.edit_bot import edit_messages_keyboard, edit_terms_kb
from keyboards.keyboards import yes_no_keyboard, reset_keyboard
from keyboards.main import keyboard
from utils.db_tools import convert_prices
from utils.states import BotEdit
from utils.utils import lang_user, check_token, regex, get_price, price_to_human

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


@dp.message_handler(state=BotEdit.token)
async def edit_token(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    bot_tag = await check_token(message.text)
    if bool(bot_tag) is False:
        return await message.answer(locale[lang]['edit_token_error'])
    cursor.execute('UPDATE bots SET token = ?, bot_tag = ? WHERE id = ?',
                   [message.text, bot_tag, message.chat.id])
    sqlite.commit()
    keyb = keyboard(lang, message.chat.id)
    await bot.delete_message(message.chat.id, message.message_id)
    await message.answer(locale[lang]['edit_token_final'].format(bot_tag), reply_markup=keyb)
    await state.finish()


@dp.message_handler(state=BotEdit.referral)
async def edit_referral_percent(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    lang = lang_user(user_id)
    if message.text.isdigit():
        if 0 < int(message.text) <= 100:
            cursor.execute('UPDATE bots SET ref_percent = ? WHERE id = ?',
                           (int(message.text), user_id))
            sqlite.commit()
            keyb = keyboard(lang, user_id)
            await message.answer(locale[lang]['edit_ref_final'], reply_markup=keyb)
            await state.finish()
        else:
            await message.answer(locale[lang]['edit_ref_error'])
    elif message.text == locale[lang]['ref_disable_button']:
        cursor.execute('UPDATE bots SET ref_percent = NULL WHERE id = ?',
                       (user_id,))
        sqlite.commit()
        keyb = keyboard(lang, user_id)
        await message.answer(locale[lang]['edit_ref_off'], reply_markup=keyb)
        await state.finish()
    else:
        await message.answer(locale[lang]['edit_ref_error'])


@dp.message_handler(state=BotEdit.invite_id)
async def invite_link_id(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    if message.text == locale[lang]['link_disable_button']:
        cursor.execute('UPDATE bots SET invite_link_id = NULL, invite_link = NULL '
                       'WHERE id = ?', (message.chat.id,))
        sqlite.commit()
        await message.answer(locale[lang]['link_disable'], reply_markup=keyboard(lang, message.chat.id))
        await state.finish()
    if message.forward_from_chat is not None:
        async with state.proxy() as data:
            data['invite_id'] = message.forward_from_chat.id
        await message.answer(locale[lang]['edit_invite_link'])
        await BotEdit.invite_link.set()


@dp.message_handler(state=BotEdit.invite_link)
async def invite_link(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    if message.text == locale[lang]['link_disable_button']:
        cursor.execute('UPDATE bots SET invite_link_id = NULL, invite_link = NULL '
                       'WHERE id = ?', (message.chat.id,))
        sqlite.commit()
        await message.answer(locale[lang]['link_disable'], reply_markup=keyboard(lang, message.chat.id))
        await state.finish()
    if re.match(regex, message.text) is None:
        return await message.answer(locale[lang]['edit_invite_link'], disable_web_page_preview=True)
    async with state.proxy() as data:
        invite_id = data['invite_id']
    cursor.execute('UPDATE bots SET invite_link_id = ?, invite_link = ? WHERE id = ?',
                   (invite_id, message.text, message.chat.id))
    sqlite.commit()
    await message.answer(locale[lang]['edit_invite_success'], reply_markup=keyboard(lang, message.chat.id))
    await state.finish()


@dp.message_handler(state=BotEdit.currency)
async def edit_currency(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    lang = lang_user(user_id)
    currency = message.text.upper()
    currency_list = ['USD', 'EUR', 'RUB', 'QAR', 'UAH', 'GBP']
    current_currency = cursor.execute('SELECT currency FROM bots WHERE id = ?', (user_id,)).fetchone()[0]
    if currency == current_currency:
        await message.answer(locale[lang]['edit_currency_no_changes'].format(current_currency))
    elif currency in currency_list:
        if currency == 'USD':
            rate = 100
        else:
            rate = get_price(currency)
        if current_currency == 'USD':
            rate_formatted = price_to_human(rate)
            convert_rate = round(rate/100, 3)
        else:
            rate_current = get_price(current_currency)
            rate_formatted = round(rate / rate_current, 3)
            convert_rate = rate_formatted
        async with state.proxy() as data:
            data['currency'] = currency
            data['rate'] = convert_rate
        await BotEdit.currency_convert.set()
        await message.answer(locale[lang]['edit_currency_ask'].format(currency, current_currency, rate_formatted),
                             reply_markup=yes_no_keyboard(lang))
    else:
        await message.answer(locale[lang]['edit_currency_error'])


@dp.message_handler(state=BotEdit.currency_convert)
async def edit_currency_convert(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    lang = lang_user(user_id)
    async with state.proxy() as data:
        currency = data['currency']
        rate = data['rate']
    if message.text in ['✅Yes', '✅Да']:
        bot_pid = cursor.execute('SELECT pid FROM bots WHERE id = ?', (user_id,)).fetchone()[0]
        if bot_pid is not None:
            check_process = psutil.pid_exists(bot_pid)
            if check_process is True:
                os.kill(bot_pid, 2)
            cursor.execute('UPDATE bots SET stopped = 1, pid = NULL WHERE id = ?', (user_id,))
        convert_prices(f'web3shop/shops/{user_id}.db', rate)
    cursor.execute('UPDATE bots SET currency = ? WHERE id = ?', (currency, user_id))
    await state.finish()
    await message.answer(locale[lang]['edit_currency_final'].format(currency), reply_markup=keyboard(lang, user_id))

@dp.callback_query_handler(filters.Text(startswith='terms/'))
async def terms_handler(call: types.CallbackQuery):
    data_msg, bot_lang = call.data.split('/')[1:]
    user_id = call.from_user.id
    lang = lang_user(user_id)

    if data_msg == 'edit':
        status = int(not bool(cursor.execute('SELECT terms FROM bots WHERE id = ?', [user_id]).fetchone()[0]))
        cursor.execute('UPDATE bots SET terms = ? WHERE id = ?', [status, user_id])
        sqlite.commit()
        await call.message.edit_text(locale[lang]["edit_terms_text"], reply_markup=edit_terms_kb(lang, bot_lang,
                                                                                                 call.from_user.id))


@dp.callback_query_handler(lambda call: call.data.startswith('message/'))
async def edit_messages(call: types.CallbackQuery, state: FSMContext):
    data_msg = call.data.split('/')[1]
    user_id = call.from_user.id
    bot_lang = call.data.split('/')[2]
    lang = lang_user(user_id)
    if data_msg == 'lang':
        text = locale[lang]['message_menu']
        keyb = edit_messages_keyboard(lang, bot_lang)
        await call.message.edit_text(text, reply_markup=keyb)
    elif data_msg == 'terms_menu':
        await call.message.edit_text(locale[lang]["edit_terms_text"], reply_markup=edit_terms_kb(lang, bot_lang,
                                                                                                 call.from_user.id))
    else:
        async with state.proxy() as data:
            data['message'] = data_msg
            data['lang'] = bot_lang

        await BotEdit.edit_message.set()
        await call.message.answer(locale[lang]['message_send'].format(data_msg), reply_markup=reset_keyboard(lang))
    await call.answer()


@dp.message_handler(state=BotEdit.edit_message)
async def edit_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        message_to_edit = f"{data['message']}_{data['lang']}"
    user_id = message.chat.id
    lang = lang_user(message.chat.id)
    if message.text in [locale['en']['default_message'], locale['ru']['default_message']]:
        result_text = locale['shop'][message_to_edit]
    else:
        result_text = message.text
    cursor.execute(f'UPDATE messages SET {message_to_edit} = ? WHERE id = ? ', (result_text, user_id))
    sqlite.commit()
    await message.answer(locale[lang]['message_menu'], reply_markup=edit_messages_keyboard(lang, data['lang']))
    await message.answer(locale[lang]['message_final'], reply_markup=keyboard(lang, message.chat.id))
    await state.finish()

