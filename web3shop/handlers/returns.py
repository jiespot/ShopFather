import sqlite3

from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from data.config import locale, ref_percent, currency_code, bot_id
from keyboards.items import categories_keyboard
from keyboards.menu import main_keyboard, profile_keyboard, deposit_keyboard, qiwi_keyboard, go_to_bot_kb, \
    approve_send_money_kb
from misc.db import lang_user, user_exist
from misc.states import GlobalMessage
from misc.utils import price_to_human

from data.loader import dp, cursor, sqlite
from keyboards.admin import admin_keyboard, advert_keyboard


@dp.message_handler(commands='send',
                    chat_type=[types.ChatType.SUPERGROUP, types.ChatType.GROUP, types.ChatType.PRIVATE])
async def bot_handler(message: types.Message):
    bot_me = await dp.bot.get_me()
    if user_exist(message.from_user.id):
        pass
    else:
        user_lang = message.from_user.language_code or 'en'

        if user_lang in ['ru', 'en']:
            pass
        else:
            user_lang = 'en'

        bot_username = bot_me.username
        await message.reply(locale[user_lang]["need_register"].format(bot_username))
        return

    # print(message)
    try:
        sql = sqlite3.connect('../sqlite.db')
        status = bool(sql.execute("SELECT can_user_transfer FROM bots WHERE id = ?", [bot_id]).fetchone()[0])
        sql.close()
    except Exception as e:
        print(e)
        return

    lang = lang_user(message.from_user.id)

    if status:
        pass
    else:
        await message.reply(locale[lang]["send_unavaliable"])
        return

    # print(lang, str(message.chat.type).lower(), '@qcazzqev' == '@qcazzqev')

    args = message.get_args()
    # print(f'args {args}')
    if args and " " in args:
        args = args.split(' ')
    else:
        if str(message.chat.type).lower() in ['group', 'supergroup']:
            args = [args]
        else:
            return

    if str(message.chat.type).lower() == 'private':
        if len(args) < 2:
            return

        userid = args[0]
        amount = args[1]

        if userid.isdigit():
            usertype = 'id'
            if userid == bot_me.id:
                return
            if int(userid) == message.from_user.id:
                return
        else:
            usertype = 'username'
            if userid == bot_me.username:
                return
            if message.from_user.username:
                if userid == message.from_user.username:
                    return
            userid = userid.replace('@', '')

    elif str(message.chat.type).lower() in ['group', 'supergroup']:
        if message.reply_to_message:
            pass

        if len(args) < 1:
            return

        userid = message.reply_to_message.from_id
        if userid == bot_me.id:
            return
        if userid == message.from_user.id:
            return
        usertype = 'id'
        amount = args[0]
    else:
        # print(message.chat.type)
        return

    if amount.isdigit():
        amount = int(amount)
    else:
        return

    if amount < 1:
        await message.answer(locale[lang]["min_amount"])


    sender = cursor.execute('SELECT balance FROM users WHERE id = ?', [message.from_user.id]).fetchone()
    # print(sender)
    if sender:
        sender_balance = int(sender[0]) / 100
    else:
        return

    if usertype == 'id':
        receiver = cursor.execute('SELECT lang, username FROM users WHERE id = ?', [userid]).fetchone()
        if receiver:
            receiver_id = int(userid)
            reciever_lang = receiver[0]
            receiver_username = f'@{receiver[1]}' if receiver[1] else receiver_id
        else:
            bot_username = bot_me.username
            await message.reply(locale[lang]['receiver_not_exists'].format(bot_username))
            return
    else:
        receiver = cursor.execute('SELECT lang, id FROM users WHERE username = ?', [userid]).fetchone()
        if receiver:
            reciever_lang = receiver[0]
            receiver_id = int(receiver[1])
            receiver_username = f'@{userid}'
        else:
            bot_username = bot_me.username
            await message.reply(locale[lang]['receiver_not_exists'].format(bot_username))
            return

    # print(sender_balance)
    if amount <= sender_balance:
        if str(message.chat.type).lower() in ['group', 'supergroup']:
            kb = go_to_bot_kb(lang=lang, reciever=receiver_id, amount=amount, chat_id=message.chat.id,
                              bot_username=bot_me.username, message_id=message.message_id+1)
            await message.reply(locale[lang]["message_sent_dm"].format(amount, currency_code, receiver_username),
                                reply_markup=kb)
        elif str(message.chat.type).lower() == 'private':
            kb = approve_send_money_kb(lang=lang, reciever=receiver_id, amount=amount,
                                       chat_id=message.chat.id, message_id=message.message_id+1)
            await message.reply(locale[lang]["confirm_send_money"].format(receiver_username, amount, currency_code), reply_markup=kb)


    else:
        await message.answer(locale[lang]["not_enough_money"])


@dp.message_handler(filters.Text(contains='approve_send_money_'))
async def approve_send_money_command(message: types.Message):
    lang = lang_user(message.from_user.id)
    receiver_id, amount, chat_id, message_id = message.get_args().split('_')[3:]

    receiver = cursor.execute('SELECT lang, username FROM users WHERE id = ?', [receiver_id]).fetchone()
    if receiver:
        receiver_username = f'@{receiver[1]}' if receiver[1] else receiver_id
    else:
        return

    kb = approve_send_money_kb(lang=lang, reciever=receiver_id, amount=amount, chat_id=chat_id, message_id=message_id)
    await message.reply(locale[lang]["confirm_send_money"].format(receiver_username, amount, currency_code),
                        reply_markup=kb)


@dp.callback_query_handler(filters.Text(startswith='send_money/'))
async def send_money(call: types.CallbackQuery):
    command = call.data.split('/')[1]
    lang = lang_user(call.from_user.id)

    if command == 'yes':
        receiver_id, amount, chat_id, message_id = call.data.split('/')[2].split(':')
        sender = cursor.execute('SELECT balance FROM users WHERE id = ?', [call.from_user.id]).fetchone()
        if sender:
            sender_balance = int(sender[0]) / 100
        else:
            return
        if sender_balance < int(amount):
            await call.message.answer(locale[lang]["not_enough_money"])
            return

        receiver = cursor.execute('SELECT lang, username FROM users WHERE id = ?', [receiver_id]).fetchone()
        if receiver:
            reciever_lang = receiver[0]
            receiver_username = f'@{receiver[1]}' if receiver[1] else receiver_id

            cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?',
                           (int(amount) * 100, call.from_user.id))
            sqlite.commit()
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                           (int(amount) * 100, receiver_id))
            sqlite.commit()

            try:
                await dp.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                pass

            await dp.bot.send_message(chat_id,
                                      locale[lang]["money_sent_to_user"].format(receiver_username, amount, currency_code))
            try:
                await call.message.delete()
            except:
                pass
            sender_username = f'@{call.from_user.username}' if call.from_user.username else f'{call.from_user.id}'
            try:
                await dp.bot.send_message(receiver_id, locale[reciever_lang]["recieved_money"].format(amount, currency_code,
                                                                                                      sender_username))
            except:
                pass
    else:
        await call.message.delete()


@dp.message_handler(
    filters.Text(equals=['return', 'back', '↩return', '↩назад', '↩вернуться', '❌cancel', '❌отмена'], ignore_case=True),
    state='*')
@dp.message_handler(commands=["stop", "cancel", "back"], state='*')
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.storage.get_state(user=message.chat.id)
    if current_state == 'GlobalMessage:add':
        await message.answer('You have returned to global message menu', reply_markup=advert_keyboard)
        return await GlobalMessage.menu.set()
    elif current_state == 'GlobalMessage:menu':
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    elif current_state in ['ShopItemAdd:name', 'ShopItemAdd:description', 'ShopItemAdd:content', 'ShopItemAdd:price',
                           'ShopPromoAdd:type', 'ShopPromoAdd:percent', 'ShopPromoAdd:amount', 'ShopPromoAdd:count',
                           'ShopPromoAdd:code']:
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    elif current_state in ['ShopItemEdit:name', 'ShopItemEdit:description', 'ShopItemEdit:content',
                           'ShopItemEdit:price', 'ShopPromoEdit:count', 'BalanceEditor:change', 'BalanceEditor:id']:
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    elif current_state in ['QiwiDeposit:amount']:
        await state.finish()
        lang = lang_user(message.chat.id)
        await message.answer(locale[lang]['return'], reply_markup=main_keyboard(message.chat.id))
    else:
        lang = lang_user(message.from_user.id)
        await message.answer(locale[lang]['return'], reply_markup=main_keyboard(message.chat.id))
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'shop_menu', state='*')
async def shop_menu(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    await call.message.edit_text(locale[lang]['select_category'], reply_markup=categories_keyboard())


@dp.callback_query_handler(lambda call: call.data == '...', state='*')
async def three_dots(call: types.CallbackQuery):
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == 'cancel', state='*')
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
    await state.finish()
    await call.answer()


# Close reply markup
@dp.callback_query_handler(lambda call: call.data == 'close')
async def close_menu(call: types.CallbackQuery):
    await call.message.edit_reply_markup()


@dp.callback_query_handler(lambda call: call.data.startswith('return/'), state='*')
async def return_menu(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('/')[1]
    user_id = call.message.chat.id
    if data == 'profile':
        req = cursor.execute('SELECT id, balance FROM users WHERE id = ?', (user_id,)).fetchone()
        lang = lang_user(user_id)
        text = locale[lang]['profile'].format(req[0], f'{price_to_human(req[1])} {currency_code}')
        if ref_percent is not None:
            referrals, ref_money = cursor.execute('SELECT referrals, ref_money FROM users WHERE id = ?',
                                                  (user_id,)).fetchone()
            text += locale[lang]['profile_ref'].format(referrals, f'{price_to_human(ref_money)} {currency_code}')
        await call.message.edit_text(text, reply_markup=profile_keyboard(lang))
    elif data == 'deposit':
        lang = lang_user(call.from_user.id)
        await call.message.edit_text(locale[lang]['deposit_select'], reply_markup=deposit_keyboard(lang))
        await call.answer()
    elif data == 'qiwi':
        await state.finish()
        lang = lang_user(call.from_user.id)
        keyb = qiwi_keyboard(lang)
        await call.message.edit_text(locale[lang]['qiwi_select'], reply_markup=keyb)
