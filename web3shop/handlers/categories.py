from aiogram import types
from aiogram.dispatcher import FSMContext, filters

from keyboards.actions import cancel_keyboard

from misc.states import ShopCategoryAdd, ShopCategoryEdit, ShopSubCategoryAdd, ShopSubCategoryEdit
from misc.utils import category_info
from misc.db import get_subcategories, get_category, add_subcategory

from data.loader import dp, sqlite, cursor
from keyboards.admin import edit_categories_keyboard, admin_keyboard, categories_keyboard_admin, category_kb, edit_sub_categories_keyboard


@dp.callback_query_handler(filters.Text(startswith='select_category/'))
async def select_category(call: types.CallbackQuery):
    category = call.data.split('/')[1]
    category_info = get_category(category)

    await call.message.edit_text(f'📚Selected Category: {category_info[1]}', reply_markup=category_kb(category))


@dp.callback_query_handler(lambda call: call.data == 'add_category', state='*')
async def add_item(call: types.CallbackQuery):
    await call.message.answer('🏷Write a name of the category', reply_markup=cancel_keyboard)
    await ShopCategoryAdd.name.set()
    await call.answer()

@dp.callback_query_handler(filters.Text(startswith="add_subcategory"), state='*')
async def add_item(call: types.CallbackQuery, state: FSMContext):
    category_id = call.data.split('/')[1]
    await call.message.answer('🏷Write a name of the subcategory', reply_markup=cancel_keyboard)
    await ShopSubCategoryAdd.name.set()
    await state.update_data(category_id=category_id)
    await call.answer()


@dp.message_handler(state=ShopSubCategoryAdd.name)
async def add_item_name(message: types.Message, state: FSMContext):
    category_id = (await state.get_data())['category_id']
    if len(message.text) > 50:
        await message.answer('⚠Name is too long, it must be less than 50 characters')
    else:
        add_subcategory(subcategory_name=message.text, category_id=category_id)
        await message.answer('📚Select category to edit', reply_markup=category_kb(category_id))
        await message.answer('✅Done, subcategory created', reply_markup=admin_keyboard)
        await state.finish()


@dp.message_handler(state=ShopCategoryAdd.name)
async def add_item_name(message: types.Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer('⚠Name is too long, it must be less than 50 characters')
    else:
        cursor.execute(f'INSERT INTO categories VALUES (?, ?, ?, ?)',
                                (None, message.text, 0, 0))
        sqlite.commit()
        await message.answer('📚Select category to edit', reply_markup=categories_keyboard_admin())
        await message.answer('✅Done, category created', reply_markup=admin_keyboard)
        await state.finish()

@dp.callback_query_handler(filters.Text(startswith='scedit/'), state='*')
async def edit_subcategory(call: types.CallbackQuery, state: FSMContext):
    subcategory_id = call.data.split('/')[1]
    action = call.data.split('/')[2]
    if action == 'name':
        await call.message.answer('🏷Write a new name of the sub category', reply_markup=cancel_keyboard)
        await ShopSubCategoryEdit.name.set()
        await state.update_data(id=subcategory_id)


@dp.message_handler(state=ShopSubCategoryEdit.name)
async def add_category_name(message: types.Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer('⚠Name is too long, it must be less than 50 characters')
    else:
        async with state.proxy() as data:
            cursor.execute("UPDATE sub_categories SET name = ? WHERE id = ?", (message.text, data['id']))
            sqlite.commit()
        text = category_info(data['id'])
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=edit_sub_categories_keyboard(data['id']))
        await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('cedit/'), state='*')
async def add_category(call: types.CallbackQuery, state: FSMContext):
    category = call.data.split('/')[1]
    action = call.data.split('/')[2]
    if action == 'name':
        await call.message.answer('🏷Write a new name of the category', reply_markup=cancel_keyboard)
        await ShopCategoryEdit.name.set()
    elif action == 'hide':
        req = cursor.execute('SELECT hide FROM categories WHERE id = ?', (category,)).fetchone()
        cursor.execute('UPDATE categories SET hide = ? WHERE id = ?', (not req[0], category))
        sqlite.commit()
        text = category_info(category)
        await call.message.edit_text(text, reply_markup=edit_categories_keyboard(category))
        return await call.answer()
    elif action == 'one_row':
        req = cursor.execute('SELECT one_row FROM categories WHERE id = ?', (category,)).fetchone()
        cursor.execute('UPDATE categories SET one_row = ? WHERE id = ?', (not req[0], category))
        sqlite.commit()
        text = category_info(category)
        await call.message.edit_text(text, reply_markup=edit_categories_keyboard(category))
        return await call.answer()
    async with state.proxy() as data:
        data['id'] = category
    await call.answer()


@dp.message_handler(state=ShopCategoryEdit.name)
async def add_category_name(message: types.Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer('⚠Name is too long, it must be less than 50 characters')
    else:
        async with state.proxy() as data:
            cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (message.text, data['id']))
            sqlite.commit()
        text = category_info(data['id'])
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await message.answer(text, reply_markup=edit_categories_keyboard(data['id']))
        await state.finish()
