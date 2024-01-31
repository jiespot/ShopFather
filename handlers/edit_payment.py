from aiogram import types
from aiogram.dispatcher import FSMContext
from web3 import Web3

import re

from data.loader import dp, cursor, sqlite, locale
from keyboards.edit_bot import payment_keyboard
from keyboards.keyboards import cancel_keyboard
from keyboards.main import keyboard
from utils.states import BotEdit, QiwiAdd
from utils.utils import lang_user

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


@dp.message_handler(state=BotEdit.cryptobot)
async def edit_bnb_wallet(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    if ':' in message.text:
        cursor.execute('UPDATE bots SET cryptobot = ? WHERE id = ?', [message.text, message.chat.id])
        sqlite.commit()
        keyb = keyboard(lang, message.chat.id)
        await message.answer(locale[lang]['edit_cryptobot_final'], reply_markup=keyb)
        await state.finish()
    else:
        await message.answer(locale[lang]['edit_cryptobot_error'])


@dp.message_handler(state=BotEdit.bnb_wallet)
async def edit_bnb_wallet(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    if Web3.isAddress(message.text):
        cursor.execute('UPDATE bots SET wallet = ? WHERE id = ?', [message.text, message.chat.id])
        sqlite.commit()
        keyb = keyboard(lang, message.chat.id)
        await message.answer(locale[lang]['edit_bnb_final'], reply_markup=keyb)
        await state.finish()
    else:
        await message.answer(locale[lang]['edit_bnb_error'])

@dp.message_handler(state=BotEdit.yookassa)
async def edit_bnb_wallet(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    cursor.execute('UPDATE bots SET yookassa = ? WHERE id = ?', (message.text, message.chat.id))
    cursor.execute('UPDATE payments SET yookassa = 1 WHERE id = ?', (message.chat.id,))
    sqlite.commit()
    keyb = keyboard(lang, message.chat.id)
    await message.answer(locale[lang]['edit_yookassa_final'], reply_markup=keyb)
    await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('payment/edit'))
async def edit_payment(call: types.CallbackQuery):
    data = call.data.split('/')[2]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'qiwi':
        await call.message.answer(locale[lang_user(call.from_user.id)]['qiwi_add_number'],
                                  reply_markup=cancel_keyboard(lang))
        await QiwiAdd.number.set()
        await call.answer()
    elif data == 'bnb':
        await call.message.answer(locale[lang]['edit_bnb'], reply_markup=cancel_keyboard(lang))
        await BotEdit.bnb_wallet.set()
        await call.answer()
    elif data == 'yookassa':
        await call.message.answer(locale[lang]['edit_yookassa'], reply_markup=cancel_keyboard(lang))
        await BotEdit.yookassa.set()
        await call.answer()
    elif data == 'cryptobot':
        await call.message.answer(locale[lang]['edit_cryptobot'], reply_markup=cancel_keyboard(lang))
        await BotEdit.cryptobot.set()
        await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('payment/'))
async def payment(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'qiwi_number':
        status = bool(cursor.execute('SELECT qiwi_number FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET qiwi_number = ? WHERE id = ?', (not status, user_id,))
    elif data == 'qiwi_p2p':
        status = bool(cursor.execute('SELECT qiwi_p2p FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET qiwi_p2p = ? WHERE id = ?', (not status, user_id,))
    elif data == 'qiwi_nickname':
        status = bool(cursor.execute('SELECT qiwi_nickname FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET qiwi_nickname = ? WHERE id = ?', (not status, user_id,))
    elif data == 'bnb':
        status = bool(cursor.execute('SELECT bnb FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET bnb = ? WHERE id = ?', (not status, user_id,))
    elif data == 'yookassa':
        status = bool(cursor.execute('SELECT yookassa FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET yookassa = ? WHERE id = ?', (not status, user_id,))
    elif data == 'cryptobot':
        status = bool(cursor.execute('SELECT cryptobot FROM payments WHERE id = ?', (user_id,)).fetchone()[0])
        cursor.execute('UPDATE payments SET cryptobot = ? WHERE id = ?', (not status, user_id,))
    else:
        return await call.answer()
    await call.message.edit_reply_markup(reply_markup=payment_keyboard(user_id, lang, data + '_group'))
    await call.answer(locale[lang]['restart_bot_warn'], True)
    sqlite.commit()
