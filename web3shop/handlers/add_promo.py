from aiogram import types
from aiogram.dispatcher import FSMContext
from keyboards.actions import cancel_keyboard, promo_type_keyboard
from misc.states import ShopPromoAdd
from misc.utils import promo_info

from data.loader import dp, cursor, sqlite
from keyboards.admin import admin_keyboard


@dp.callback_query_handler(lambda call: call.data == 'add_promo', state='*')
async def add_item(call: types.CallbackQuery):
    await call.message.answer('🌟Select type of promo code', reply_markup=promo_type_keyboard)
    await ShopPromoAdd.type.set()
    await call.answer()


@dp.message_handler(state=ShopPromoAdd.type)
async def add_promo_type(message: types.Message, state: FSMContext):
    if message.text == '🔥Discount':
        promo_type = 1
        await ShopPromoAdd.percent.set()
        await message.answer('🔥Write a discount size(%)', reply_markup=cancel_keyboard)
    else:
        promo_type = 2
        await ShopPromoAdd.amount.set()
        await message.answer('💰Write a top-up amount(in cents)', reply_markup=cancel_keyboard)
    async with state.proxy() as data:
        data['type'] = promo_type


@dp.message_handler(state=ShopPromoAdd.percent)
async def add_promo_percents(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        percents = int(message.text)
        if 0 < percents <= 100:
            async with state.proxy() as data:
                data['percent'] = percents
            await ShopPromoAdd.amount.set()
            await message.answer('📦Write amount of items which can be purchased with a discount',
                                 reply_markup=cancel_keyboard)
        else:
            await message.answer('⚠Discount must be more than 0% and less than 100%')
    else:
        await message.answer('⚠Discount must be a number')


@dp.message_handler(state=ShopPromoAdd.amount)
async def add_promo_amount(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
        async with state.proxy() as data:
            data['amount'] = amount
        await ShopPromoAdd.count.set()
        await message.answer('📦Write count of promo activations', reply_markup=cancel_keyboard)
    else:
        await message.answer('⚠Amount must be a number')


@dp.message_handler(state=ShopPromoAdd.count)
async def add_promo_count(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
        async with state.proxy() as data:
            data['count'] = amount
        await ShopPromoAdd.code.set()
        await message.answer('🌟Send new promo code', reply_markup=cancel_keyboard)
    else:
        await message.answer('⚠Amount must be a number')


@dp.message_handler(state=ShopPromoAdd.code)
async def add_promo_code(message: types.Message, state=FSMContext):
    promo_code = message.text
    check_code = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM promo WHERE code = ?)',
                                     (promo_code,)).fetchone()[0])
    if check_code:
        return await message.answer('⚠This promo code already exists')
    else:
        async with state.proxy() as data:
            promo_type = data['type']
            promo_percent = None
            promo_item = None
            promo_amount = None
            if promo_type == 1:
                promo_amount = data['amount']
                promo_percent = data['percent']
            elif promo_type == 2:
                promo_amount = data['amount']
            elif promo_type == 3:
                promo_item = data['item_id']
            promo_count = data['count']
        cursor.execute('INSERT INTO promo VALUES  (?, ?, ?, ?, ?, ?, ?)',
                       (None, promo_code, promo_count, promo_type,
                        promo_percent, promo_amount, promo_item))
        sqlite.commit()
        promo_id = cursor.execute('SELECT seq from sqlite_sequence WHERE name = ?', ['promo']).fetchone()[0]
        await message.answer(promo_info(promo_id))
        await message.answer('✅Done, item created', reply_markup=admin_keyboard)
        await state.finish()
