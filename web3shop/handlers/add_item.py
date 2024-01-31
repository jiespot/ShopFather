from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.actions import cancel_keyboard, select_keyboard, noyes_keyboard, amount_keyboard, description_keyboard
from misc.states import ShopItemAdd
from misc.utils import item_info

from data.loader import dp, sqlite, bot, cursor
from keyboards.admin import admin_keyboard, categories_keyboard_admin, sub_categories_keyboard_admin

@dp.callback_query_handler(lambda call: call.data == 'add_item', state='*')
async def add_item(call: types.CallbackQuery):
    await call.message.answer('📚Select category of the item', reply_markup=categories_keyboard_admin(True))
    await ShopItemAdd.category.set()
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('select_category/'), state=ShopItemAdd.category)
async def select_category(call: types.CallbackQuery, state: FSMContext):
    category = call.data.split('/')[1]
    async with state.proxy() as data:
        data['category'] = category
    await call.message.delete()
    await call.message.answer('🗄️Select subCategorie of the item:', reply_markup=sub_categories_keyboard_admin(category))
    # await call.message.answer('🏷Write a name of the item', reply_markup=cancel_keyboard)
    await ShopItemAdd.sub_category.set()
    await call.answer()

@dp.callback_query_handler(filters.Text(startswith='asubcategory/'), state=ShopItemAdd.sub_category)
async def select_subcategory(call: types.CallbackQuery, state: FSMContext):
    sub_category = call.data.split('/')[1]
    async with state.proxy() as data:
        data['sub_category'] = sub_category
    await call.message.delete()
    await call.message.answer('🏷Write a name of the item', reply_markup=cancel_keyboard)
    await ShopItemAdd.name.set()
    await call.answer()


@dp.message_handler(state=ShopItemAdd.name)
async def add_item_name(message: types.Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer('⚠Name is too long, it must be less than 50 characters')
    else:
        async with state.proxy() as data:
            data['name'] = message.text
        await message.answer('📜Write a description of the item', reply_markup=description_keyboard)
        await ShopItemAdd.description.set()


@dp.message_handler(state=ShopItemAdd.description)
async def add_item_description(message: types.Message, state: FSMContext):
    if message.text == '✖No Description':
        description = None
    else:
        description = message.text
    async with state.proxy() as data:
        data['description'] = description
    await message.answer('🔶Select item type\n<b>📝String</b> - selling strings'
                         '\n<b>🌅Media</b> - selling one message(text/photo/video...)', reply_markup=select_keyboard)
    await ShopItemAdd.type.set()


@dp.message_handler(filters.Text(equals=['📝String']), state=ShopItemAdd.type)
async def add_item_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = 2
    await ShopItemAdd.string.set()
    await message.answer('📝Send file with strings or write it manually like:\n'
                         '<code>string1\nstring2\nstring3</code>', reply_markup=cancel_keyboard)


@dp.message_handler(filters.Text(equals=['🌅Media']), state=ShopItemAdd.type)
async def add_item_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = 1
    await ShopItemAdd.file.set()
    await message.answer('🌅Send a content of the item\n<code>text/photo/video/gif/audio/document</code>',
                         reply_markup=cancel_keyboard)


@dp.message_handler(content_types=['text', 'document'], state=ShopItemAdd.string)
async def add_item_string(message: types.Message, state: FSMContext):
    if message.document is not None:
        try:
            file = await bot.download_file_by_id(message.document.file_id)
            content = file.readlines()
            strings = []
            for x in content:
                strings.append(x.decode('utf8').rstrip())
            strings = list(filter(None, strings))
        except:
            await message.answer('⚠Bad file')
            return
    else:
        strings = message.text.split('\n')
    async with state.proxy() as data:
        data['content'] = strings
        data['amount'] = len(strings)
        await message.answer(f'⚠You add {data["amount"]} strings, is correct?', reply_markup=noyes_keyboard)
    await ShopItemAdd.check.set()


@dp.message_handler(state=ShopItemAdd.check)
async def add_item_check(message: types.Message):
    if message.text == '✅Yes':
        await message.answer('💵Write a price of the item(in cents)', reply_markup=cancel_keyboard)
        await ShopItemAdd.price.set()
    elif message.text == '❌No':
        await message.answer('📝Send file with strings or write it manually', reply_markup=cancel_keyboard)
        await ShopItemAdd.string.set()


# Add item content
@dp.message_handler(content_types=['text', 'photo', 'document', 'video', 'animation', 'audio'],
                    state=ShopItemAdd.file)
async def add_item_content(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'photo' in message:
            data['media_type'] = 1
            data['file_id'] = message.photo[-1].file_id
        elif 'document' in message:
            data['media_type'] = 2
            data['file_id'] = message.document.file_id
        elif 'video' in message:
            data['media_type'] = 3
            data['file_id'] = message.video.file_id
        elif 'animation' in message:
            data['media_type'] = 4
            data['file_id'] = message.animation.file_id
        elif 'audio' in message:
            data['media_type'] = 5
            data['file_id'] = message.audio.file_id
        else:
            data['media_type'] = 0
            data['file_id'] = None

        if 'text' in message:
            data['text'] = message.text
        else:
            data['text'] = message.caption
    await message.answer('📦Write amount of this product', reply_markup=amount_keyboard)
    await ShopItemAdd.amount.set()


@dp.message_handler(state=ShopItemAdd.amount)
async def add_item_count(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
    elif message.text == '♾No limit':
        amount = None
    else:
        await message.answer('⚠Invalid amount')
        return
    async with state.proxy() as data:
        data['amount'] = amount
    await message.answer('💵Write a price of the item(in cents)', reply_markup=cancel_keyboard)
    await ShopItemAdd.price.set()


@dp.message_handler(state=ShopItemAdd.price)
async def add_item_price(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        return await message.answer('⚠Price is a number')
    price = int(message.text)
    async with state.proxy() as data:
        data['price'] = price
        if data['type'] == 1:
            cursor.execute('INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (None, data['category'], data["sub_category"],
                            data['name'], data['description'], data['price'], data['amount'],
                            data['type'], 0, data['media_type'], data['file_id'], data['text']))
            item_id = cursor.execute('SELECT seq from sqlite_sequence WHERE name = ?', ['items']).fetchone()[0]
            sqlite.commit()
            keyb = InlineKeyboardMarkup(True).add(
                InlineKeyboardButton('🌅Show media', callback_data=f'show/{item_id}'))
        elif data['type'] == 2:
            cursor.execute('INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (None, data['category'], data["sub_category"], data['name'], data['description'],
                            data['price'], data['amount'],
                            data['type'], 0, None, None, None))
            item_id = cursor.execute('SELECT seq from sqlite_sequence WHERE name = ?', ['items']).fetchone()[0]
            for x in data['content']:
                cursor.execute('INSERT INTO strings VALUES (?, ?, ?)',
                               (None, item_id, x))
            sqlite.commit()
            keyb = None
        await message.answer(item_info(item_id), reply_markup=keyb)
    await message.answer('✅Done, item created', reply_markup=admin_keyboard)
    await state.finish()
