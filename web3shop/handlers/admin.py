from sys import exit

from aiogram import types
from aiogram.dispatcher import filters, FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data.config import currency_code
from keyboards.actions import cancel_keyboard
from misc.api_qiwi import QiwiAPI
from misc.db import IsAdmin, items_admin
from misc.states import BalanceEditor, GlobalMessage
from misc.utils import price_to_human, backup_dp, category_info, check_sub, promo_info, text_to_file, sub_category_info

from data.loader import dp, sqlite, bot
from keyboards.admin import admin_keyboard, advert_keyboard, categories_keyboard_admin, edit_categories_keyboard, \
    promo_keyboard_admin, edit_promo_keyboard, edit_sub_categories_keyboard


@dp.message_handler(IsAdmin(), filters.Text(equals=["🤖Admin Menu"]), state='*')
@dp.message_handler(IsAdmin(), commands=['admin'], state='*')
async def admin_command(message: types.Message):
    await message.answer('You have opened the admin menu', reply_markup=admin_keyboard)


@dp.message_handler(IsAdmin(), commands=['export'], state='*')
async def export_command(message: types.Message):
    users = sqlite.cursor().execute('SELECT id FROM users').fetchall()
    bot_tag = await bot.me
    file_name = f'shops/{bot_tag.username}.txt'
    with open(file_name, 'w') as f:
        for x in users:
            f.write(str(x[0]) + '\n')
    await message.answer_document(open(file_name, 'rb'), caption='Users list')


@dp.message_handler(IsAdmin(), commands=['stats'], state='*')
async def stats_command(message: types.Message):
    users = sqlite.cursor().execute("SELECT COUNT(id) FROM users").fetchall()[0][0]
    await message.answer(f'Users: <b>{users}</b>')


@dp.message_handler(IsAdmin(), commands=['shutdown', 'poweroff'])
async def shutdown(message: types.Message):
    await message.answer('Shutdown...')
    sqlite.close()
    exit()


@dp.message_handler(IsAdmin(), commands=['backup'], state='*')
async def backup_command(message: types.Message):
    await backup_dp(message.from_user.id)


@dp.message_handler(IsAdmin(), commands=['state'], state='*')
async def state_command(message: types.Message, state: FSMContext):
    current_state = await state.storage.get_state(user=message.chat.id)
    await message.answer(f'State: <b>{current_state}</b>')


@dp.callback_query_handler(lambda call: call.data == 'return')
@dp.message_handler(IsAdmin(), filters.Text(equals=["✏Edit items"]))
async def edit_items(message):
    if 'text' in message:
        text = message.text
    else:
        text = 'return'
    if text in ['✏Edit items', 'return']:
        items = items_admin()
        keyb = InlineKeyboardMarkup(True)
        if items != []:
            for x in items[0]:
                price = price_to_human(x[3])
                if x[4] is None:
                    amount = '♾'
                else:
                    amount = x[4]
                name = f'{x[1]} | {price} {currency_code} | {amount}pcs'
                if x[2] == 1:
                    name = '🔒' + name
                keyb.add(InlineKeyboardButton(name, callback_data=f'edit_item/{x[0]}'))
        keyb.row(InlineKeyboardButton('➕Add item', callback_data='add_item'))
        if len(items) > 1:
            page_text = f'\nPage: 1'
            keyb.row(InlineKeyboardButton('➡️', callback_data='apage/1'))
        else:
            page_text = ''
        if text == 'return':
            await message.message.edit_text('<b>📁Shop Items:</b>' + page_text, reply_markup=keyb)
        else:
            await message.answer('<b>📁Shop Items:</b>' + page_text, reply_markup=keyb)


@dp.callback_query_handler(lambda call: call.data.startswith('apage/'), state='*')
async def apage(call: types.CallbackQuery):
    page = int(call.data.split('/')[1])
    keyb = InlineKeyboardMarkup(True)
    items_list = items_admin()
    text_header = '<b>📁Shop Items:</b>'
    for x in items_list[page]:
        price = price_to_human(x[3])
        if x[4] is None:
            amount = '♾'
        else:
            amount = x[4]
        name = f'{x[1]} | {price} {currency_code} | {amount}pcs'
        if x[2] == 1:
            name = '🔒' + name
        keyb.add(InlineKeyboardButton(name, callback_data=f'edit_item/{x[0]}'))
    button_return = InlineKeyboardButton('⬅️', callback_data=f'apage/{page - 1}')
    button_forward = InlineKeyboardButton('➡️', callback_data=f'apage/{page + 1}')
    keyb.row(InlineKeyboardButton('➕Add item', callback_data='add_item'))
    if page == 0:
        keyb.row(button_forward)
    elif len(items_list) - 1 == page:
        keyb.row(button_return)
    else:
        keyb.row(button_return, button_forward)
    if len(items_list) > 1:
        page_text = f'\nPage: {page + 1}'
    else:
        page_text = ''
    try:
        await bot.edit_message_text(text_header + page_text, call.from_user.id, call.message.message_id,
                                    reply_markup=keyb)
    except:
        await call.answer('Please slower')


@dp.message_handler(IsAdmin(), filters.Text(equals=["📚Edit categories"]))
async def edit_categories(message: types.Message):
    await message.answer('📚Select category to edit', reply_markup=categories_keyboard_admin())


@dp.message_handler(IsAdmin(), filters.Text(equals=["🌟Edit promo codes"]))
async def edit_promos(message: types.Message):
    await message.answer('🌟Select promo code to edit', reply_markup=promo_keyboard_admin())


@dp.callback_query_handler(lambda call: call.data == 'creturn')
async def return_to_edit_categories(call: types.CallbackQuery):
    await call.message.edit_text('📚Select category to edit', reply_markup=categories_keyboard_admin())


@dp.callback_query_handler(lambda call: call.data == 'preturn')
async def return_to_edit_categories(call: types.CallbackQuery):
    await call.message.edit_text('Select promo code to edit', reply_markup=promo_keyboard_admin())


@dp.callback_query_handler(lambda call: call.data.startswith('acategory/'))
async def edit_category(call: types.CallbackQuery):
    category = call.data.split('/')[1]
    text = category_info(category)
    await call.message.edit_text(text, reply_markup=edit_categories_keyboard(category))
    await call.answer()

@dp.callback_query_handler(lambda call: call.data.startswith('asubcategory/'))
async def edit_sub_category(call: types.CallbackQuery):
    sub_category = call.data.split('/')[1]
    text = sub_category_info(sub_category)
    await call.message.edit_text(text, reply_markup=edit_sub_categories_keyboard(sub_category))
    await call.answer()

@dp.callback_query_handler(lambda call: call.data.startswith('apromo/'))
async def edit_category(call: types.CallbackQuery):
    promo = call.data.split('/')[1]
    text = promo_info(promo)
    await call.message.edit_text(text, reply_markup=edit_promo_keyboard(promo))
    await call.answer()


@dp.message_handler(IsAdmin(), filters.Text(equals=["👤User info"]))
async def user_info(message: types.Message):
    await message.answer('Send id of user you want to check', reply_markup=cancel_keyboard)
    await BalanceEditor.id.set()


@dp.message_handler(IsAdmin(), filters.Text(equals=["🌐Global message"]))
async def global_message(message: types.Message):
    await message.answer('You have opened the global message menu', reply_markup=advert_keyboard)
    await GlobalMessage.menu.set()


@dp.message_handler(commands=['check'], state='*')
async def check(message: types.Message, state: FSMContext):
    await message.answer(await check_sub(message.from_user.id))


@dp.message_handler(IsAdmin(), filters.Text(equals=["🥝QIWI Balance"]))
@dp.message_handler(IsAdmin(), commands=['balance'], state="*")
async def payment_qiwi_balance(message: types.Message, state: FSMContext):
    await (await QiwiAPI(message)).get_balance()


@dp.message_handler(IsAdmin(), commands=['test'], state='*')
async def test_command(message: types.Message, state: FSMContext):
    file = text_to_file(4096 * 'a')
    await message.answer_document(file)
