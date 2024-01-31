from aiogram import types
from aiogram.dispatcher import FSMContext
from keyboards.actions import cancel_keyboard, noyes_keyboard, amount_keyboard, description_keyboard
from misc.states import ShopItemEdit, ShopPromoAdd
from misc.utils import item_info, send_item_content

from data.loader import sqlite, dp, bot, cursor
from keyboards.admin import admin_keyboard
from keyboards.admin import edit_keyboard, categories_keyboard_admin, delete_item_keyboad


@dp.callback_query_handler(lambda call: call.data.startswith('edit_item/'), state='*')
async def edit_item(call: types.CallbackQuery):
    item_id = call.data.split('/')[1]
    text = item_info(item_id)
    try:
        await call.message.edit_text(text, reply_markup=edit_keyboard(item_id))
    except:
        await call.message.edit_text(text, reply_markup=edit_keyboard(item_id), parse_mode='None')
    await call.answer()


# Item Editor
@dp.callback_query_handler(lambda call: call.data.startswith('edit/'), state='*')
async def edit_item(call: types.CallbackQuery, state: FSMContext):
    item_id = call.data.split('/')[1]
    edit_type = call.data.split('/')[2]
    if edit_type == 'name':
        await call.message.answer('🏷Write a new name of the item', reply_markup=cancel_keyboard)
        await ShopItemEdit.name.set()
    elif edit_type == 'description':
        await call.message.answer('📜Write a new description of the item\n<i>(you can use html formatting)</i>',
                                  reply_markup=description_keyboard)
        await ShopItemEdit.description.set()
    elif edit_type == 'content':
        await call.message.answer('🌅Send a content of the item\n<code>text/photo/video/gif/audio/document</code>',
                                  reply_markup=cancel_keyboard)
        await ShopItemEdit.file.set()
    elif edit_type == 'strings':
        await call.message.answer('📝Send file with strings or write it manually', reply_markup=cancel_keyboard)
        await ShopItemEdit.string.set()
    elif edit_type == 'amount':
        await call.message.answer('📦Write a new amount of the item', reply_markup=amount_keyboard)
        await ShopItemEdit.amount.set()
    elif edit_type == 'price':
        await call.message.answer('💵Write a new price of the item(in cents)', reply_markup=cancel_keyboard)
        await ShopItemEdit.price.set()
    elif edit_type == 'category':
        await call.message.edit_text('📚Select category of the item', reply_markup=categories_keyboard_admin(True))
        await ShopItemEdit.category.set()
    elif edit_type == 'promo':
        async with state.proxy() as data:
            data['type'] = 3
            data['item_id'] = item_id
        await ShopPromoAdd.count.set()
        await call.message.answer('📦Write count of promo activations', reply_markup=cancel_keyboard)
    elif edit_type == 'delete':
        await call.message.answer('⚠Are you sure you want to delete this item?',
                                  reply_markup=delete_item_keyboad(item_id))
    elif edit_type == 'hide':
        req = cursor.execute('SELECT hide FROM items WHERE id = ?', (item_id,)).fetchone()
        if req[0] == 1:
            hide = 0
        else:
            hide = 1
        cursor.execute('UPDATE items SET hide = ? WHERE id = ?', (hide, item_id))
        sqlite.commit()
        await call.message.edit_text(item_info(item_id), reply_markup=edit_keyboard(item_id))
        return await call.answer()
    async with state.proxy() as data:
        data['item_id'] = item_id
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == 'del_cancel', state='*')
async def del_cancel(call: types.CallbackQuery):
    await call.message.edit_text('❌Deletion canceled')


@dp.callback_query_handler(lambda call: call.data.startswith('delete/'), state='*')
async def delete_item(call: types.CallbackQuery, state: FSMContext):
    item_id = call.data.split('/')[1]
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    cursor.execute('DELETE FROM strings WHERE item_id = ?', (item_id,))
    cursor.execute('DELETE FROM promo WHERE item_id = ?', (item_id,))
    sqlite.commit()
    await call.message.edit_text('✅Item deleted!')
    await state.finish()


# Edit item name
@dp.message_handler(state=ShopItemEdit.name)
async def edit_item_name(message: types.Message, state: FSMContext):
    if len(message.text) > 35:
        await message.answer('⚠Name is too long')
    else:
        async with state.proxy() as data:
            cursor.execute('UPDATE items SET name = ? WHERE id = ?', (message.text, data['item_id']))
            sqlite.commit()
        text = item_info(data['item_id'])
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=edit_keyboard(data['item_id']))
        await state.finish()


# Edit item description
@dp.message_handler(state=ShopItemEdit.description)
async def edit_item_description(message: types.Message, state: FSMContext):
    if message.text == '✖No Description':
        description = None
    else:
        description = message.text
    async with state.proxy() as data:
        item_id = data['item_id']
    item = list(cursor.execute('SELECT name, price, hide, amount, type, category '
                               'FROM items WHERE id = ?', (item_id,)).fetchone())
    item.insert(1, description)
    text = item_info(item_id, item)
    try:
        await message.answer(text, reply_markup=edit_keyboard(item_id))
        cursor.execute('UPDATE items SET description = ? WHERE id = ?', (description, item_id))
        sqlite.commit()
    except:
        return await message.answer('⚠Description is incorrect')
    await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    await state.finish()


# Edit item content
@dp.message_handler(content_types=['text', 'photo', 'document', 'video', 'animation', 'audio'],
                    state=ShopItemEdit.file)
async def edit_item_content(message: types.Message, state: FSMContext):
    if 'photo' in message:
        content_type = 1
        file_id = message.photo[-1].file_id
        text = message.caption
    elif 'document' in message:
        content_type = 2
        file_id = message.document.file_id
        text = message.caption
    else:
        content_type = 0
        file_id = None
        text = message.text
    async with state.proxy() as data:
        cursor.execute('UPDATE items SET media_type = ?, file_id = ?, text = ? WHERE id = ?',
                       (content_type, file_id, text, data['item_id']))
        sqlite.commit()
    await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    item_content = cursor.execute('SELECT media_type, file_id, text FROM items WHERE id = ?',
                                  [data['item_id']]).fetchone()
    await send_item_content(item_content, message.chat.id)
    await message.answer(item_info(data['item_id']), reply_markup=edit_keyboard(data['item_id']))
    await state.finish()


@dp.message_handler(state=ShopItemEdit.amount)
async def add_item_count(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
    elif message.text == '♾No limit':
        amount = None
    else:
        await message.answer('⚠Invalid amount')
        return
    async with state.proxy() as data:
        cursor.execute('UPDATE items SET amount = ? WHERE id = ?', (amount, data['item_id']))
        sqlite.commit()
    text = item_info(data['item_id'])
    await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    await message.answer(text, reply_markup=edit_keyboard(data['item_id']))
    await state.finish()


@dp.message_handler(content_types=['text', 'document'], state=ShopItemEdit.string)
async def add_item_string(message: types.Message, state: FSMContext):
    if message.document is not None:
        try:
            file = await bot.download_file_by_id(message.document.file_id)
            content = file.readlines()
            strings = []
            for x in content:
                strings.append(x.decode('utf8').rstrip())
            strings = list(filter(None, strings))
            async with state.proxy() as data:
                data['content'] = strings
                data['amount'] = len(strings)
                await message.answer(f'⚠You add {data["amount"]} strings, is correct?', reply_markup=noyes_keyboard)
        except:
            await message.answer('⚠Bad file')
            return
    else:
        strings = message.text.split('\n')
        async with state.proxy() as data:
            data['content'] = strings
            data['amount'] = len(strings)
            await message.answer(f'⚠You add {data["amount"]} strings, is correct?', reply_markup=noyes_keyboard)
    await ShopItemEdit.check.set()


@dp.message_handler(state=ShopItemEdit.check)
async def add_item_check(message: types.Message, state: FSMContext):
    if message.text == '✅Yes':
        async with state.proxy() as data:
            cursor.execute('UPDATE items SET amount = amount + ? WHERE id = ?',
                           (data['amount'], data['item_id']))
            for x in data['content']:
                cursor.execute('INSERT INTO strings VALUES (?, ?, ?)',
                               (None, data['item_id'], x))
            sqlite.commit()
        text = item_info(data['item_id'])
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=edit_keyboard(data['item_id']))
        await state.finish()
    elif message.text == '❌No':
        await message.answer('📝Send file with strings or write it manually', reply_markup=cancel_keyboard)
        await ShopItemEdit.string.set()


# Edit item price
@dp.message_handler(state=ShopItemEdit.price)
async def edit_item_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
    except:
        await message.answer('⚠Price is a number')
        return
    async with state.proxy() as data:
        cursor.execute('UPDATE items SET price = ? WHERE id = ?', (price, data['item_id']))
        sqlite.commit()
    text = item_info(data['item_id'])
    await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    await message.answer(text, reply_markup=edit_keyboard(data['item_id']))
    await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('acategory/'), state=ShopItemEdit.category)
async def select_category(call: types.CallbackQuery, state: FSMContext):
    category = call.data.split('/')[1]
    async with state.proxy() as data:
        cursor.execute('UPDATE items SET category = ? WHERE id = ?', (category, data['item_id']))
        sqlite.commit()
    text = item_info(data['item_id'])
    await call.message.edit_text(text, reply_markup=edit_keyboard(data['item_id']))
    await state.finish()
    await call.answer()
