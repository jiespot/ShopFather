from aiogram import types
from aiogram.dispatcher import FSMContext
from data.config import locale, qiwi_by_number, qiwi_nickname, qiwi_private_key, currency_code
from keyboards.actions import user_return_keyboard
from keyboards.menu import qiwi_keyboard, main_keyboard, qiwi_check_keyboard
from misc.api_qiwi import QiwiAPI
from misc.db import get_price, lang_user
from misc.states import QiwiDeposit
from misc.utils import tCurrent, price_to_human, send_log, referral_deposit

from data.loader import dp, sqlite, cursor


@dp.callback_query_handler(lambda call: call.data == 'qiwi_deposit', state='*')
async def refill_way(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    keyb = qiwi_keyboard(lang)
    await call.message.edit_text(locale[lang]['qiwi_select'], reply_markup=keyb)


@dp.callback_query_handler(text_startswith="qiwi/", state="*")
async def refill_way_choice(call: types.CallbackQuery, state: FSMContext):
    lang = lang_user(call.from_user.id)
    data = call.data.split('/')[1]
    if data == 'number' and qiwi_by_number is False:
        return await call.answer(locale[lang]['qiwi_method_disabled'], True)
    elif data == 'nickname' and qiwi_nickname is None:
        return await call.answer(locale[lang]['qiwi_method_disabled'], True)
    elif data == 'form' and qiwi_private_key is None:
        return await call.answer(locale[lang]['qiwi_method_disabled'], True)
    await state.update_data(here_pay_way=data)
    await QiwiDeposit.amount.set()
    await call.message.answer(locale[lang]['top_up_enter'], reply_markup=user_return_keyboard(lang))
    await call.answer()


@dp.message_handler(state=QiwiDeposit.amount)
async def refill_get(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = lang_user(user_id)
    try:
        pay_amount = float(message.text.replace(',', '.'))
        cache_message = await message.answer(locale[lang]['payment_generating'])

        if currency_code == 'USD':
            rate = 100
        else:
            rate = get_price(currency_code)

        if currency_code != 'RUB':
            rate_usd = get_price('RUB')
            pay_amount_rub = round(pay_amount / rate * rate_usd)
            amount_formatted = f'{pay_amount_rub} RUB({pay_amount} {currency_code})'
        else:
            pay_amount_rub = round(pay_amount)
            amount_formatted = f'{pay_amount_rub} RUB'

        minimal_amount_qiwi = 5
        max_amount_qiwi = 300000
        if minimal_amount_qiwi <= pay_amount_rub <= max_amount_qiwi:
            get_way = (await state.get_data())['here_pay_way']
            await state.finish()
            message_args, get_link, receipt = await (
                await QiwiAPI(cache_message, user_bill_pass=True)
            ).bill_pay(pay_amount_rub, get_way)

            if message_args:
                if get_way == 'form':
                    finn_message = locale[lang]['qiwi_bill_form'].format(amount_formatted)
                else:
                    finn_message = locale[lang][f'qiwi_bill_{get_way}'].format(message_args, receipt, amount_formatted)
                await cache_message.edit_text(finn_message,
                                              reply_markup=qiwi_check_keyboard(get_link, receipt, get_way, lang))
        else:
            if currency_code != 'RUB':
                minimal_amount_qiwi = price_to_human(round(5 / rate_usd * rate * 100))
                max_amount_qiwi = round(300000 / rate_usd * rate)
            minimal_formatted = f'{minimal_amount_qiwi} {currency_code}'
            max_formatted = f'{max_amount_qiwi} {currency_code}'
            error_text = locale[lang]['incorrect_amount'] + locale[lang]['amount_limit'].format(minimal_formatted,
                                                                                                max_formatted) + \
                         locale[lang]['top_up_enter']
            await cache_message.edit_text(error_text)
    except ValueError as ve:
        if str(ve) == 'Invalid private key':
            await cache_message.delete()
            await message.answer(locale[lang]['method_error'], reply_markup=main_keyboard(user_id))
            await send_log(message.from_user, f"<b>❌QIWI Error:</b> <code>{get_way}</code> method doesn't work")
        else:
            await message.answer(locale[lang]['incorrect_amount'] + locale[lang]['top_up_enter'])
    except:
        await cache_message.delete()
        await message.answer(locale[lang]['method_error'], reply_markup=main_keyboard(user_id))


@dp.callback_query_handler(text_startswith="pay/form")
async def refill_check_form(call: types.CallbackQuery):
    receipt = call.data.split("/")[2]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    try:
        pay_status, pay_amount = await (
            await QiwiAPI(call, user_check_pass=True)
        ).check_form(receipt)
    except:
        return await call.message.answer(locale[lang]['method_error'], reply_markup=main_keyboard(user_id))

    if pay_status == "PAID":
        get_refill = cursor.execute("SELECT * FROM dep_qiwi WHERE receipt = ?", (receipt,)).fetchone()
        if get_refill is None:
            await refill_success(call, receipt, pay_amount, "Form")
        else:
            await call.message.edit_text(locale[lang]['top_up_received'])
    elif pay_status == "EXPIRED":
        await call.message.edit_text(locale[lang]['top_up_expired'])
    elif pay_status == "WAITING":
        await call.answer(locale[lang]['top_up_not_found'], True, cache_time=5)
    elif pay_status == "REJECTED":
        await call.message.edit_text(locale[lang]['top_up_rejected'])


@dp.callback_query_handler(text_startswith=['pay/number', 'pay/nickname'])
async def refill_check_send(call: types.CallbackQuery):
    way_pay = call.data.split("/")[1]
    receipt = call.data.split("/")[2]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    try:
        pay_status, pay_amount = await (
            await QiwiAPI(call, user_check_pass=True)
        ).check_send(receipt)
    except:
        return await call.message.answer(locale[lang]['method_error'], reply_markup=main_keyboard(user_id))

    if pay_status == 1:
        await call.answer(locale[lang]['top_up_error_currency'], True, cache_time=5)
    elif pay_status == 2:
        await call.answer(locale[lang]['top_up_not_found'], True, cache_time=5)
    elif pay_status == 4:
        pass
    else:
        get_refill = cursor.execute("SELECT * FROM dep_qiwi WHERE receipt = ?", (receipt,)).fetchone()
        if get_refill is None:
            await refill_success(call, receipt, pay_amount, way_pay)
        else:
            await call.message.edit_text(locale[lang]['top_up_received'])


async def refill_success(call: types.CallbackQuery, receipt, amount, get_way):
    user_id = call.from_user.id
    lang = lang_user(user_id)
    rub_amount = round(amount * 100)

    if currency_code == 'USD':
        rate = 100
    elif currency_code != 'RUB':
        rate = get_price(currency_code)

    if currency_code != 'RUB':
        rate_usd = get_price('RUB')
        usd_amount = round(rub_amount / rate_usd * rate)
        final_amount = usd_amount
        rub_formatted = f'({price_to_human(rub_amount)} RUB)'
    else:
        rub_formatted = ''
        usd_amount = None
        final_amount = rub_amount

    cursor.execute("INSERT INTO dep_qiwi VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (None, user_id, usd_amount, rub_amount, receipt, get_way, tCurrent()))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                   (final_amount, user_id))
    sqlite.commit()
    result = locale[lang]['received'].format(f'{price_to_human(final_amount)} {currency_code}')
    result += locale[lang]['received_receipt'].format(receipt)
    await call.message.delete()
    await call.message.answer(result, reply_markup=main_keyboard(user_id))
    await referral_deposit(user_id, final_amount, lang)
    await send_log(call.from_user,
                   f"<b>💰Deposit amount:</b> <code>{price_to_human(final_amount)} {currency_code}{rub_formatted}</code>\n"
                   f"<b>🧾Receipt:</b> <code>#{receipt}</code>")
