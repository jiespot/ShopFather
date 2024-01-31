from aiogram.dispatcher import FSMContext

from data.config import locale, yookassa_token, currency_code
from data.loader import dp, bot, cursor, sqlite
from aiogram import types
from aiogram.types.message import ContentTypes
from aiogram.utils import executor

from keyboards.actions import user_return_keyboard
from keyboards.menu import main_keyboard
from misc.db import lang_user, get_price
from misc.states import YooDeposit
from misc.utils import price_to_human, tCurrent, referral_deposit, send_log


@dp.callback_query_handler(text_startswith="yoo/", state="*")
async def refill_way_choice(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    data = call.data.split('/')[1]
    if data == 'kassa' and yookassa_token is None:
        return await call.answer(locale[lang]['qiwi_method_disabled'], True)
    await YooDeposit.amount.set()
    await call.message.answer(locale[lang]['top_up_enter'], reply_markup=user_return_keyboard(lang))
    await call.answer()


@dp.message_handler(state=YooDeposit.amount)
async def refill_get(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = lang_user(user_id)
    try:
        pay_amount = int(float(message.text.replace(',', '.'))*100)

        if currency_code == 'USD':
            rate = 100
        else:
            rate = get_price(currency_code)

        if currency_code != 'RUB':
            rate_usd = get_price('RUB')
            pay_amount_rub = round(pay_amount / rate * rate_usd)
        else:
            pay_amount_rub = pay_amount
        amount_formatted = f'{price_to_human(pay_amount)} {currency_code}'

        minimal_amount = 60
        max_amount = 250000
        if minimal_amount*100 <= pay_amount_rub <= max_amount*100:
            await state.finish()

            await bot.send_invoice(message.chat.id, title=locale[lang]['yoo_deposit'],
                                   description=locale[lang]['yoo_deposit_amount'].format(amount_formatted),
                                   provider_token=yookassa_token,
                                   currency='rub',
                                   prices=[types.LabeledPrice(label=locale[lang]['yoo_deposit'], amount=pay_amount_rub)],
                                   payload=tCurrent())

        else:
            if currency_code != 'RUB':
                minimal_amount = price_to_human(round(minimal_amount / rate_usd * rate * 100))
                max_amount = round(max_amount / rate_usd * rate)
            minimal_formatted = f'{minimal_amount} {currency_code}'
            max_formatted = f'{max_amount} {currency_code}'
            error_text = locale[lang]['incorrect_amount'] + locale[lang]['amount_limit'].format(minimal_formatted,
                                                                                                max_formatted) + \
                         locale[lang]['top_up_enter']
            await message.answer(error_text)
    except:
        await message.answer(locale[lang]['method_error'], reply_markup=main_keyboard(user_id))


@dp.pre_checkout_query_handler(lambda query: True)
async def checkout(pre_checkout_query: types.PreCheckoutQuery):
    user_id = pre_checkout_query.from_user.id
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                        error_message=locale[lang_user(user_id)]['yoo_deposit_error'])


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def got_payment(message: types.Message):
    user_id = message.from_user.id
    lang = lang_user(user_id)
    payment = message.successful_payment
    rub_amount = payment.total_amount

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
        final_amount = rub_amount
        rub_formatted = ''

    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                   (final_amount, user_id))
    sqlite.commit()
    result = locale[lang]['received'].format(f'{price_to_human(final_amount)} {currency_code}')
    await message.answer(result, reply_markup=main_keyboard(user_id))
    await referral_deposit(user_id, final_amount, lang)
    await send_log(message.from_user,
                   f"<b>💰Deposit amount:</b> <code>{price_to_human(final_amount)} {currency_code}{rub_formatted}</code>")
