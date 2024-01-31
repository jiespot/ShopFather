from aiogram import types
from aiogram.dispatcher import FSMContext
from data.config import locale, currency_code
from keyboards.actions import user_return_keyboard, user_noyes_keyboard
from keyboards.menu import main_keyboard
from misc.db import lang_user
from misc.states import Promo
from misc.utils import tPurchase, price_to_human, send_item_content, send_log, purchase_info

from data.loader import dp, cursor, sqlite


@dp.callback_query_handler(lambda call: call.data == 'promo', state='*')
async def promo(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    await call.message.answer(locale[lang]['promo_write'], reply_markup=user_return_keyboard(lang))
    await Promo.promo.set()
    await call.answer()


@dp.message_handler(state=Promo.promo)
async def promo_input(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    lang = lang_user(user_id)
    promo_data = cursor.execute("SELECT * FROM promo WHERE code = ?", (message.text,)).fetchone()
    if promo_data is not None:
        promo_id = promo_data[0]
        promo_code = promo_data[1]
        promo_count = promo_data[2]
        promo_type = promo_data[3]

        if promo_count <= 0:
            return await message.answer(locale[lang]['promo_expired'])

        used_check = bool(
            cursor.execute("SELECT EXISTS(SELECT 1 FROM promo_activations WHERE user_id = ? AND promo_id = ?)",
                           (user_id, promo_id)).fetchone()[0])
        if used_check:
            return await message.answer(locale[lang]['promo_used'])

        if promo_type == 1:
            async with state.proxy() as data:
                data['promo_id'] = promo_id
            promo_percent = promo_data[4]
            amount = promo_data[5]
            await message.answer(locale[lang]['promo_discount_conf'].format(promo_percent, amount),
                                 reply_markup=user_noyes_keyboard(lang))
            return await Promo.promo_discount.set()

        elif promo_type == 2:
            amount = promo_data[5]
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                           (amount, user_id))
            text = locale[lang]['received'].format(price_to_human(amount))
            await message.answer(text, reply_markup=main_keyboard(user_id))
            await send_log(message.from_user, f'<b>🌟Activate code <code>{promo_code}</code> '
                                              f'for</b>: <code>{price_to_human(amount)} {currency_code}</code>')

        elif promo_type == 3:
            item_id = promo_data[6]
            item_check = cursor.execute('SELECT amount, type, name FROM items WHERE id = ?',
                                        (item_id,)).fetchone()
            if item_check is None:
                return await message.answer(locale[lang]['promo_expired'])
            item_amount, item_type, item_name = item_check
            if item_amount is not None and item_amount <= 0:
                return await message.answer(locale[lang]['promo_item_error'])
            if item_amount is not None:
                cursor.execute('UPDATE items SET amount = amount - 1 WHERE id = ?', [item_id])
            purchase_id = tPurchase()
            if item_type == 1:
                item_content = cursor.execute('SELECT media_type, file_id, text, name, description '
                                              'FROM items WHERE id = ?', (item_id,)).fetchone()
                cursor.execute('INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (tPurchase(), item_id, user_id, 1, None, item_content[0],
                                item_content[1], item_content[2], item_content[3], item_content[4], None))
                await message.answer(locale[lang]['string_result'].format(''), reply_markup=main_keyboard(user_id))
                await send_item_content(item_content, user_id)

            elif item_type == 2:
                string = cursor.execute('SELECT id, data FROM strings WHERE item_id = ?', (item_id,)).fetchone()
                item_content = cursor.execute('SELECT name, description FROM items WHERE id = ?',
                                              (item_id,)).fetchone()
                cursor.execute('DELETE FROM strings WHERE id = ?', (string[0],))
                cursor.execute('INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (tPurchase(), item_id, user_id, 1, string[1], None,
                                None, None, item_content[0], item_content[1], None))
                await message.answer(locale[lang]['string_result'].format(string[1]),
                                     reply_markup=main_keyboard(user_id))
            await message.answer(purchase_info(purchase_id, lang, message.from_user))
            pur_info = purchase_info(purchase_id, 'en', message.from_user)
            await send_log(message.from_user, f'<b>🌟Activate code <code>{promo_code}</code> '
                                              f'for item</b>: <code>{item_name}</code>\n\n{pur_info}')

        cursor.execute('UPDATE promo SET count = count - 1 WHERE id = ?', (promo_id,))
        cursor.execute('INSERT INTO promo_activations VALUES (?, ?, ?, ?)',
                       (tPurchase(), user_id, promo_id, promo_code))
        sqlite.commit()
        await state.finish()
    else:
        return await message.answer('❌<b>Invalid promo code</b>')


@dp.message_handler(state=Promo.promo_discount)
async def promo_discount_input(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        promo_id = data['promo_id']
    user_id = message.chat.id
    lang = lang_user(user_id)
    if message.text in ['❌No', '❌Нет']:
        await state.finish()
        return await message.answer(locale[lang]['return'], reply_markup=main_keyboard(user_id))
    elif message.text in ['✅Yes', '✅Да']:
        promo_data = cursor.execute("SELECT code, count, percent, amount FROM promo WHERE id = ?",
                                    (promo_id,)).fetchone()
        promo_code, promo_count, promo_percent, promo_amount = promo_data
        cursor.execute('UPDATE users SET discount = ?, discount_amount = ? WHERE id = ?',
                       (promo_percent, promo_amount, user_id))
        cursor.execute('UPDATE promo SET count = count - 1 WHERE id = ?', (promo_id,))
        cursor.execute('INSERT INTO promo_activations VALUES (?, ?, ?, ?)',
                       (tPurchase(), user_id, promo_id, promo_code))
        sqlite.commit()
        await message.answer(locale[lang]['promo_discount'].format(promo_amount, promo_percent),
                             reply_markup=main_keyboard(user_id))
        await state.finish()
        await send_log(message.from_user, f'<b>🌟Activate code <code>{promo_code}</code> '
                                          f'for <code>{promo_percent}%</code></b> discount '
                                          f'for next <code>{promo_amount}</code> purchases')
