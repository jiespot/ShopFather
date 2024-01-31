from aiogram import types
from aiogram.dispatcher import FSMContext
from keyboards.actions import cancel_keyboard
from misc.states import ShopPromoEdit
from misc.utils import promo_info

from data.loader import dp, cursor, sqlite
from keyboards.admin import delete_promo_keyboad, admin_keyboard, edit_promo_keyboard


@dp.callback_query_handler(lambda call: call.data.startswith('pedit/'), state='*')
async def add_category(call: types.CallbackQuery, state: FSMContext):
    promo_id = call.data.split('/')[1]
    action = call.data.split('/')[2]
    if action == 'count':
        async with state.proxy() as data:
            data['promo_id'] = promo_id
        await ShopPromoEdit.count.set()
        await call.message.answer('📦Write a new amount of available activations', reply_markup=cancel_keyboard)
    elif action == 'delete':
        await call.message.answer('⚠Are you sure you want to delete this promo code?\n'
                                  '<i>If you create new promo with the same name, user can activate it again</i>',
                                  reply_markup=delete_promo_keyboad(promo_id))
    await call.answer()


@dp.message_handler(state=ShopPromoEdit.count)
async def add_item_count(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        count = int(message.text)
    else:
        return await message.answer('⚠Invalid amount')
    async with state.proxy() as data:
        promo_id = data['promo_id']
    cursor.execute('UPDATE promo SET count = ? WHERE id = ?', (count, promo_id))
    sqlite.commit()
    text = promo_info(promo_id)
    await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    await message.answer(text, reply_markup=edit_promo_keyboard(promo_id))
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'del_cancel', state='*')
async def del_cancel(call: types.CallbackQuery):
    await call.message.edit_text('❌Deletion canceled')


@dp.callback_query_handler(lambda call: call.data.startswith('pdelete/'), state='*')
async def delete_item(call: types.CallbackQuery, state: FSMContext):
    promo_id = call.data.split('/')[1]
    cursor.execute('DELETE FROM promo WHERE id = ?', (promo_id,))
    sqlite.commit()
    await call.message.edit_text('✅Promo code deleted!')
    await state.finish()
