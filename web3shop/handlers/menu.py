from asyncio import sleep

from aiogram import types

from aiogram.dispatcher import filters, FSMContext
from data.config import locale, lang_list, ref_percent, currency_code, terms_status
from keyboards.actions import return_button
from keyboards.actions import sub_keyboard
from keyboards.items import categories_keyboard
from keyboards.menu import main_keyboard, profile_keyboard, lang_keyboard, deposit_keyboard, purchases_keyboard, \
    view_button, terms_accept
from misc.db import new_user, user_exist, lang_user, user_accepter_terms, agree_user
from misc.utils import price_to_human, send_item_content, check_sub, purchase_info, text_to_file

from data.loader import dp, sqlite, cursor, bot

from aiogram.types import ChatType


@dp.callback_query_handler(filters.Text(startswith='agree/terms'))
async def agree_terms(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = lang_user(user_id) if user_exist(user_id) else call.from_user.language_code
    ref = call.data.split('/')[2]

    if not user_accepter_terms(user_id):
        agree_user(user_id)
        if user_exist(user_id) is False:
            await new_user(call.from_user, ref)
        check = await check_sub(user_id)
        if check is False:
            return await call.message.edit_text(locale[lang]['invite'], reply_markup=sub_keyboard(lang))

        await call.message.delete()
        await call.message.answer(locale[lang]['start_message'], reply_markup=main_keyboard(user_id),
                                  disable_web_page_preview=True)
        if len(lang_list) > 1:
            await call.message.edit_text(locale[lang]['lang_start'])


@dp.message_handler(commands=['start'], state='*', chat_type=ChatType.PRIVATE)
async def send_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    lang = lang_user(user_id) if user_exist(user_id) else message.from_user.language_code
    another_lang = 'en' if lang == 'ru' else 'ru'

    ref = message.get_args()

    if terms_status and not user_accepter_terms(user_id):
        if locale[lang]["terms"]:
            text_terms = locale[lang]["terms"]
        else:
            text_terms = locale[another_lang]["terms"]
        kb = terms_accept(lang, ref)
        await message.answer(text_terms, reply_markup=kb, disable_web_page_preview=True)
        return

    if user_exist(user_id) is False:
        await new_user(message.from_user, ref)
    check = await check_sub(user_id)
    if check is False:
        return await message.answer(locale[lang]['invite'], reply_markup=sub_keyboard(lang))
    await message.answer(locale[lang]['start_message'], reply_markup=main_keyboard(user_id),
                         disable_web_page_preview=True)
    if len(lang_list) > 1:
        await message.answer(locale[lang]['lang_start'])
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'check_sub', state='*', chat_type=ChatType.PRIVATE)
async def check_su_inline(call: types.CallbackQuery):
    user_id = call.from_user.id
    check = await check_sub(user_id)
    if check is False:
        await sleep(1)
        return await call.answer()
    await call.message.delete()
    if user_exist(user_id) is False:
        await new_user(call.from_user)
    lang = lang_user(user_id)
    await call.message.answer(locale[lang]['start_message'], reply_markup=main_keyboard(user_id),
                              disable_web_page_preview=True)
    if len(lang_list) > 1:
        await call.message.answer(locale[lang]['lang_start'])


@dp.message_handler(filters.Text(equals=["/shop", "/store"]), state='*', chat_type=ChatType.PRIVATE)
@dp.message_handler(filters.Text(equals=["🛍Shop", "🛍Магазин"]), state='*')
async def shop_msg(message: types.Message):
    if user_exist(message.from_user.id):
        lang = lang_user(message.chat.id)
        await message.answer(locale[lang]['select_category'], reply_markup=categories_keyboard())


@dp.message_handler(filters.Text(equals=["/profile"]), state='*', chat_type=ChatType.PRIVATE)
@dp.message_handler(filters.Text(equals=["👤Profile", "👤Профиль"]), state='*')
async def profile_msg(message: types.Message):
    usr_id = message.chat.id
    if user_exist(usr_id):
        req = cursor.execute('SELECT id, balance FROM users WHERE id = ?', (usr_id,)).fetchone()
        lang = lang_user(usr_id)
        text = locale[lang]['profile'].format(req[0], f'{price_to_human(req[1])} {currency_code}')
        if ref_percent is not None:
            referrals, ref_money = cursor.execute('SELECT referrals, ref_money FROM users WHERE id = ?',
                                                  (usr_id,)).fetchone()
            text += locale[lang]['profile_ref'].format(referrals, f'{price_to_human(ref_money)} {currency_code}')
        await message.answer(text, reply_markup=profile_keyboard(lang))


@dp.message_handler(filters.Text(equals=["/help"]), state='*', chat_type=ChatType.PRIVATE)
@dp.message_handler(filters.Text(equals=locale['buttons']['help']), state='*')
async def help_msg(message: types.Message):
    if user_exist(message.from_user.id):
        lang = lang_user(message.chat.id)
        await message.answer(locale[lang]['help_message'], disable_web_page_preview=True)


@dp.message_handler(filters.Text(equals=["/contact"]), state='*', chat_type=ChatType.PRIVATE)
@dp.message_handler(filters.Text(equals=locale['buttons']['contact']), state='*')
async def contact_msg(message: types.Message):
    if user_exist(message.from_user.id):
        lang = lang_user(message.chat.id)
        await message.answer(locale[lang]['contact_message'], disable_web_page_preview=True)


@dp.message_handler(commands=['lang'], state='*', chat_type=ChatType.PRIVATE)
async def lang_change(message: types.Message):
    if user_exist(message.from_user.id):
        await message.answer('Select language:', reply_markup=lang_keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('lang/'), state='*', chat_type=ChatType.PRIVATE)
async def inline_lang(call: types.CallbackQuery):
    lang = call.data.lstrip('lang/')
    cursor.execute('UPDATE users SET lang = ? WHERE id = ?',
                   (lang, call.from_user.id))
    sqlite.commit()
    await call.message.delete()
    await call.message.answer(locale[lang]['lang_select'], reply_markup=main_keyboard(call.from_user.id))


@dp.callback_query_handler(lambda call: call.data == 'deposit', state='*', chat_type=ChatType.PRIVATE)
async def deposit_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    await call.message.edit_text(locale[lang]['deposit_select'], reply_markup=deposit_keyboard(lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == 'referral', state='*', chat_type=ChatType.PRIVATE)
async def referral_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = lang_user(user_id)
    percent = int(ref_percent * 100)
    bot_tag = await bot.get_me()
    bot_tag = bot_tag.username
    link = f'https://t.me/{bot_tag}?start={user_id}'
    await call.message.edit_text(locale[lang]['referral_text'].format(percent, link),
                                 reply_markup=return_button(lang, 'profile'))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == 'purchases', chat_type=ChatType.PRIVATE)
async def purchases_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = lang_user(user_id)
    total_purchases = cursor.execute('SELECT COUNT(id) FROM purchases WHERE buyer_id = ?', (user_id,)).fetchone()[0]
    total_pages = total_purchases // 5
    if total_pages * 5 < total_purchases or total_pages == 0:
        total_pages += 1
    await call.message.answer(locale[lang]['purchases'].format(total_purchases, 1, total_pages),
                              reply_markup=purchases_keyboard(user_id, 0, total_purchases, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('ppage/'), chat_type=ChatType.PRIVATE)
async def purchases_page(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = lang_user(user_id)
    offset = int(call.data.lstrip('ppage/'))
    total_purchases = cursor.execute('SELECT COUNT(id) FROM purchases WHERE buyer_id = ?', (user_id,)).fetchone()[0]
    total_pages = total_purchases // 5
    if total_pages * 5 < total_purchases:
        total_pages += 1
    page = offset // 5 + 1
    await call.message.edit_text(locale[lang]['purchases'].format(total_purchases, page, total_pages),
                                 reply_markup=purchases_keyboard(user_id, offset, total_purchases, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('purchase/'), chat_type=ChatType.PRIVATE)
async def purchase_info_handler(call: types.CallbackQuery):
    purchases_id = int(call.data.split('/')[1])
    offset = int(call.data.split('/')[2])
    user_id = call.from_user.id
    lang = lang_user(user_id)
    text = purchase_info(purchases_id, lang)
    await call.message.edit_text(text, reply_markup=view_button(purchases_id, offset, lang))
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('show_purchase/'), chat_type=ChatType.PRIVATE)
async def show_purchase_handler(call: types.CallbackQuery):
    purchases_id = int(call.data.lstrip('show_purchase/'))
    user_id = call.from_user.id
    lang = lang_user(user_id)
    media_type, item_name = cursor.execute('SELECT media_type, name FROM purchases WHERE id = ?',
                                           (purchases_id,)).fetchone()
    if media_type is None:
        strings = cursor.execute('SELECT strings FROM purchases WHERE id = ?', (purchases_id,)).fetchone()[0]
        if len(strings.split('\n')) > 1:
            await call.message.answer_document(text_to_file(strings, item_name))
        else:
            await call.message.answer(locale[lang]['string_result'].format(strings))
    else:
        item_content = cursor.execute('SELECT media_type, file_id, text FROM purchases WHERE id = ?',
                                      (purchases_id,)).fetchone()
        await send_item_content(item_content, user_id)
    await call.answer()
