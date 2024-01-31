from aiogram import types
from aiogram.dispatcher import FSMContext
from data.config import currency_code
from keyboards.actions import cancel_keyboard
from misc.states import BalanceEditor
from misc.utils import price_to_human

from data.loader import dp, sqlite, cursor
from keyboards.admin import admin_keyboard


@dp.callback_query_handler(lambda call: call.data.startswith('changebal/'))
async def change_balance(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split('/')[1])
    await call.message.answer('Send new balance in cents', reply_markup=cancel_keyboard)
    async with state.proxy() as data:
        data['user_id'] = user_id
    await BalanceEditor.change.set()
    await call.answer()


@dp.message_handler(state=BalanceEditor.id)
async def adv_balance_id(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        return await message.answer('Invalid id')
    user_id = int(message.text)
    req = cursor.execute("SELECT balance, id FROM users WHERE id = ?", (user_id,)).fetchone()
    if req is not None:
        wallet = cursor.execute("SELECT pub FROM wallets WHERE id = ? and type = 'bsc'", (user_id,)).fetchone()[0]
        keyb = types.InlineKeyboardMarkup()
        keyb.add(types.InlineKeyboardButton('💲Change balance', callback_data=f'changebal/{user_id}'))
        text = f'<b>👤User info</b>\n' \
               '➖➖➖➖➖➖➖➖\n' \
               f'<b>🔑ID:</b> <code>{user_id}</code>\n' \
               f'<b>💳Balance:</b> <code>{price_to_human(req[0])} {currency_code}</code>\n' \
               f'<b>💰Wallet:</b> <code>{wallet}</code>'
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=keyb)
        await state.finish()
    else:
        await message.answer('User not found')


@dp.message_handler(state=BalanceEditor.change)
async def adv_balance_change(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = data['user_id']
        if message.text.isdigit() is False:
            return await message.answer('Invalid balance')
        balance = int(message.text)
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (balance, user_id))
        sqlite.commit()
        req = cursor.execute("SELECT balance, id FROM users WHERE id = ?", (user_id,)).fetchone()
        wallet = cursor.execute("SELECT pub FROM wallets WHERE id = ? and type = 'bsc'", (user_id,)).fetchone()[0]
        keyb = types.InlineKeyboardMarkup()
        keyb.add(types.InlineKeyboardButton('Change balance', callback_data=f'changebal/{user_id}'))
        text = f'<b>👤User info</b>\n' \
               '➖➖➖➖➖➖➖➖\n' \
               f'<b>🔑ID:</b> <code>{user_id}</code>\n' \
               f'<b>💳Balance:</b> <code>{price_to_human(req[0])} {currency_code}</code>\n' \
               f'<b>💰Wallet:</b> <code>{wallet}</code>'
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=keyb)
        await state.finish()
