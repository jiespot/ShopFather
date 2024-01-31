from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from data.config import admin_ids, locale, currency_code
from keyboards.actions import user_return_keyboard
from keyboards.items import items_keyboard, buy_buttons, buy_many_confirm, subcategory_items
from keyboards.menu import main_keyboard
from misc.db import lang_user
from misc.states import BuyMany
from misc.utils import price_to_human, send_log, send_item_content, tPurchase, purchase_info, text_to_file

from data.loader import sqlite, bot, dp, cursor


@dp.callback_query_handler(lambda call: call.data.startswith('category/'))
async def category_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    category = call.data.split('/')[1]
    await call.message.edit_text(locale[lang]['select_item'], reply_markup=items_keyboard(category, 0, lang))
    await call.answer()


@dp.callback_query_handler(filters.Text(startswith='subcaregory'))
async def subcaregory_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    category = call.data.split('/')[1]
    await call.message.edit_text(locale[lang]['select_item'], reply_markup=subcategory_items(category, 0, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('page/'))
async def page_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    category = call.data.split('/')[1]
    page = call.data.split('/')[2]
    await call.message.edit_text(locale[lang]['select_item'], reply_markup=items_keyboard(category, page, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('spage/'))
async def spage_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    scategory = call.data.split('/')[1]
    page = call.data.split('/')[2]
    await call.message.edit_text(locale[lang]['select_item'], reply_markup=subcategory_items(scategory, page, lang))
    await call.answer()


# Show item content
@dp.callback_query_handler(lambda call: call.data.startswith('item/') or call.data.startswith('show/'),
                           state='*')
async def item_menu(call: types.CallbackQuery):
    item_id = int(call.data.split('/')[1])
    user_id = call.from_user.id
    check = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM purchases WHERE buyer_id = ? and item_id = ?)',
                                (user_id, item_id)).fetchone()[0])
    if call.data.startswith('item/'):
        lang = lang_user(user_id)
        item_name, item_description, item_price, item_amount, item_type = cursor.execute(
            'SELECT name, description, price, amount, type FROM items WHERE id = ?',
            (item_id,)).fetchone()
        if item_amount is None:
            amount = '♾'
        else:
            amount = item_amount
        price = item_price
        discount, discount_amount = cursor.execute('SELECT discount, discount_amount FROM users WHERE id = ?',
                                                   (user_id,)).fetchone()
        if discount_amount is not None and discount_amount > 0:
            price = item_price * (100 - discount) // 100
            price_formatted = f'{price_to_human(price)}(-{discount}%)'
        else:
            price_formatted = price_to_human(price)
        text = locale[lang]['item_info'].format(item_name, f'{price_formatted} {currency_code}', amount)
        if item_description is not None:
            text += locale[lang]['description'].format(item_description)
        await call.message.answer(text, reply_markup=buy_buttons(item_id, item_type, lang))
    elif check or user_id in admin_ids:
        item_content = cursor.execute('SELECT media_type, file_id, text FROM items WHERE id = ?',
                                      [item_id]).fetchone()
        await send_item_content(item_content, user_id)
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('buy_many/'))
async def buy_many(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    item_id = int(call.data.split('/')[1])
    lang = lang_user(user_id)
    async with state.proxy() as data:
        data['item_id'] = item_id
    await BuyMany.amount.set()
    await call.message.answer(locale[lang]['enter_amount'], reply_markup=user_return_keyboard(lang))
    await call.answer()


@dp.message_handler(state=BuyMany.amount)
async def buy_many_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = lang_user(user_id)
    amount = message.text
    if not amount.isdigit():
        return await message.answer(locale[lang]['wrong_amount'])
    amount = int(amount)
    if amount <= 0:
        return await message.answer(locale[lang]['wrong_amount'])
    async with state.proxy() as data:
        item_id = data['item_id']
    item_name, item_description, item_price, item_amount = cursor.execute(
        'SELECT name, description, price, amount FROM items WHERE id = ?',
        (item_id,)).fetchone()
    if amount > item_amount:
        return await message.answer(locale[lang]['not_enough_amount'])
    price = price_to_human(item_price * amount)
    text = locale[lang]['item_info'].format(item_name, f'{price} {currency_code}', amount)
    if item_description is not None:
        text += locale[lang]['description'].format(item_description)
    await message.answer(locale[lang]['confirmation'], reply_markup=main_keyboard(user_id))
    await message.answer(text, reply_markup=buy_many_confirm(item_id, amount, lang))
    await state.finish()


# Buy item
@dp.callback_query_handler(lambda call: call.data.startswith('buy/'))
async def buy_item(call: types.CallbackQuery):
    item_id = int(call.data.split('/')[1])
    user_id = call.from_user.id
    lang = lang_user(user_id)
    item_price, item_amount, item_type, item_name = \
        cursor.execute('SELECT price, amount, type, name FROM items WHERE id = ?',
                       (item_id,)).fetchone()
    if item_amount is not None and item_amount <= 0:
        await call.message.answer(locale[lang]['out_of_stock'])
        return await call.answer()
    discount, discount_amount = cursor.execute('SELECT discount, discount_amount FROM users WHERE id = ?',
                                               (user_id,)).fetchone()
    if discount_amount is not None and discount_amount > 0:
        item_price = item_price * (100 - discount) // 100
    if item_price <= cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()[0]:
        if item_amount is not None:
            cursor.execute('UPDATE items SET amount = amount - 1 WHERE id = ?', (item_id,))
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (item_price, user_id))
        if discount_amount is not None and discount_amount > 0:
            cursor.execute('UPDATE users SET discount_amount = discount_amount - 1 WHERE id = ?', (user_id,))
        purchase_id = tPurchase()
        if item_type == 1:
            item_content = cursor.execute('SELECT media_type, file_id, text, name, description FROM items WHERE id = ?',
                                          (item_id,)).fetchone()
            cursor.execute('INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (purchase_id, item_id, user_id, 1, None, item_content[0],
                            item_content[1], item_content[2], item_content[3], item_content[4], item_price))
            sqlite.commit()
            await bot.delete_message(user_id, call.message.message_id)
            await call.message.answer(locale[lang]['string_result'].format(''))
            await send_item_content(item_content, user_id)
        elif item_type == 2:
            string = cursor.execute('SELECT id, data FROM strings WHERE item_id = ?', (item_id,)).fetchone()
            item_content = cursor.execute('SELECT name, description FROM items WHERE id = ?',
                                          (item_id,)).fetchone()
            cursor.execute('DELETE FROM strings WHERE id = ?', (string[0],))
            cursor.execute('INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (purchase_id, item_id, user_id, 1, string[1], None,
                            None, None, item_content[0], item_content[1], item_price))
            sqlite.commit()
            await call.message.answer(locale[lang]['string_result'].format(string[1]))
        await call.message.answer(purchase_info(purchase_id, lang, call.from_user))
        pur_info = purchase_info(purchase_id, 'en', call.from_user)
        await send_log(call.message.chat, pur_info)
    else:
        await call.message.answer(locale[lang]['not_enough_money'])
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('buy_confirm/'))
async def buy_item(call: types.CallbackQuery):
    item_id = int(call.data.split('/')[1])
    amount = int(call.data.split('/')[2])
    user_id = call.from_user.id
    lang = lang_user(user_id)
    item_price, item_amount, item_type, item_name = \
        cursor.execute('SELECT price, amount, type, name FROM items WHERE id = ?',
                       (item_id,)).fetchone()
    if item_amount <= amount:
        await call.message.answer(locale[lang]['out_of_stock'])
        return await call.answer()
    price = item_price * amount
    if price <= cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()[0]:
        if item_amount is not None:
            cursor.execute('UPDATE items SET amount = amount - ? WHERE id = ?', (amount, item_id))
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (price, user_id))
        purchase_id = tPurchase()
        strings = cursor.execute('SELECT id, data FROM strings WHERE item_id = ? LIMIT ?', (item_id, amount)).fetchall()
        string_ids = []
        strings_data = ''
        for string in strings:
            string_ids.append(string[0])
            strings_data += string[1] + '\n'
        item_content = cursor.execute('SELECT name, description FROM items WHERE id = ?',
                                      (item_id,)).fetchone()
        for x in string_ids:
            cursor.execute('DELETE FROM strings WHERE id = ?', (x,))
        cursor.execute('INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (purchase_id, item_id, user_id, amount, strings_data, None,
                        None, None, item_content[0], item_content[1], price))
        sqlite.commit()
        file = text_to_file(strings_data, item_name)
        await call.message.answer_document(file, caption=locale[lang]['string_result'].format(''))
        await call.message.answer(purchase_info(purchase_id, lang, call.from_user))
        pur_info = purchase_info(purchase_id, 'en', call.from_user)
        await send_log(call.message.chat, pur_info)
    else:
        await call.message.answer(locale[lang]['not_enough_money'])
    await call.answer()
