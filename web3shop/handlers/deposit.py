from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data.config as config
from data.config import locale, admin_ids, minimal_amount, gas_price, withdraw_address, currency_code, cryptobot_token, super_admin_id, withdraw_address_admin
from keyboards.menu import crypto_check_keyboard, cryptobot_kb, cryptobot_form_kb, main_keyboard
from misc.db import get_price, lang_user, IsAdmin, IsSuperAdmin
from misc.utils import tCurrent, price_to_human, send_log, referral_deposit

from misc.api_cryptobot import CryptoPayAPI
from misc.crypto_swap import swap

from misc.states import CBot_Deposit

from data.loader import dp, sqlite, w3, cursor


def create_table():
    cursor.execute('CREATE TABLE IF NOT EXISTS "dep_cbot"('
                   '"id"	integer NOT NULL UNIQUE,'
                   '"user_id"	integer,'
                   '"amount" INTEGER,'
                   '"bill_id" TEXT,'
                   '"time" integer,'
                   'PRIMARY KEY("id" AUTOINCREMENT));')
    sqlite.commit()
async def refill_success(call: types.CallbackQuery, bill_id: str, amount: [int, float]):

    user_id = call.from_user.id
    lang = lang_user(user_id)

    db_amount = int(float(amount)) * 100

    create_table()

    cursor.execute('INSERT INTO dep_cbot ("user_id", "amount", "bill_id", "time") VALUES (?, ?, ?, ?)',
                   (user_id, db_amount, bill_id, tCurrent()))

    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                   (db_amount, user_id))

    sqlite.commit()
    result = locale[lang]['received'].format(f'{amount} {currency_code}')
    result += locale[lang]['received_receipt'].format(bill_id)
    await call.message.delete()
    await call.message.answer(result, reply_markup=main_keyboard(user_id))
    await referral_deposit(user_id, amount, lang)
    await send_log(call.from_user,
                   f"<b>💰Deposit amount:</b> <code>{amount} {currency_code}</code>\n"
                   f"<b>🧾Receipt:</b> <code>#{bill_id}</code>")


@dp.callback_query_handler(text_startswith='cbot|')
async def select_ccurency(call: types.CallbackQuery, state: FSMContext):
    currency = call.data.split('|')[1]
    lang = lang_user(call.from_user.id)
    await call.message.edit_text(locale[lang]["cryptobot_amount"].replace("%currency%", currency_code))
    await CBot_Deposit.amount.set()
    await state.update_data(ccurrency=currency)

@dp.message_handler(state=CBot_Deposit.amount)
async def cbot_deposit_amount(message: types.Message, state: FSMContext):
    crypto_bot_api = CryptoPayAPI(cryptobot_token)
    data = await state.get_data()
    ccurency = data["ccurrency"]
    lang = lang_user(message.from_user.id)
    try:
        pay_amount = float(message.text.replace(',', '.'))
        #MINIMAL DEPOSIT
        if ((ccurency == 'btc') and (250 > pay_amount)):
            minimal_formatted = f'250 {currency_code}'
            error_text = locale[lang]['incorrect_amount'] + locale[lang]['amount_limit_btc'].format(minimal_formatted) + locale[lang]['top_up_enter']
            
            print(swap.convert(to_asset='btc', amount=30.0, currency='USD'))
            await message.answer(error_text)
        else:
            if 20 > pay_amount and ccurency != 'btc':
                minimal_formatted = f'20 {currency_code}'
                error_text = locale[lang]['incorrect_amount'] + locale[lang]['amount_limit'].format(minimal_formatted) + locale[lang]['top_up_enter']
                await message.answer(error_text)
            else:
                crypto_amount = swap.convert(to_asset=ccurency,
                                            amount=pay_amount,
                                            currency=currency_code)
                invoice = crypto_bot_api.create_invoice(asset=ccurency, amount=crypto_amount, allow_anonymous=False)

                if invoice['ok']:
                    pass
                else:
                    await state.finish()
                    await message.answer(locale[lang]["method_error"])
                await state.finish()
                invoice = invoice["result"]

                kb = cryptobot_form_kb(lang=lang, pay_url=invoice["pay_url"], bill_id=invoice["invoice_id"], amount=pay_amount)
                text = locale[lang]["cryptobot_pay_form"].format(crypto_amount, ccurency.upper(), pay_amount, currency_code)
                
                print(ccurency, " amount: ", pay_amount)
                await message.answer(text, reply_markup=kb)
    except:
        await message.answer(locale[lang]["incorrect_amount"])
        return

    

@dp.callback_query_handler(text_startswith='cryptobot/check_deposit/')
async def cryptobot_check(call: types.CallbackQuery):
    crypto_bot_api = CryptoPayAPI(cryptobot_token)

    bill_id, amount = call.data.split('/')[2:]
    lang = lang_user(call.from_user.id)

    check = crypto_bot_api.get_invoices(invoice_ids=bill_id, status='paid')
    if check.get('ok'):
        pass
    else:
        await call.message.answer(locale[lang]["error_check"])
        return

    items = check["result"]["items"]
    if items:
        invoice = items[0]
        if invoice["status"] == 'paid':
            create_table()
            get_refill = cursor.execute("SELECT * FROM dep_cbot WHERE bill_id = ?", (bill_id,)).fetchone()
            if get_refill is None:
                await refill_success(call=call, bill_id=bill_id, amount=amount)
            else:
                await call.message.edit_text(locale[lang]['top_up_received'])
        else:
            await call.message.answer(locale[lang]["top_up_not_found"])
    else:
        await call.message.answer(locale[lang]["top_up_not_found"])


@dp.callback_query_handler(text='cryptobot_deposit')
async def crypto_bot_deposit(call: types.CallbackQuery):
    lang = lang_user(call.from_user.id)
    print("SOMEONE CLICKED CRYPTOBOT DEPOSIT FROM USER:", call.from_user.id)
    await call.message.edit_text(locale[lang]["cryptobot_currency"],
                                 reply_markup=cryptobot_kb(lang))



@dp.callback_query_handler(lambda call: call.data.startswith('crypto_deposit'), state='*')
async def deposit_busd(call: types.CallbackQuery):
    wallet = cursor.execute("SELECT pub FROM wallets WHERE id = ? and type = 'bsc'", (call.from_user.id,)).fetchone()[0]
    temp_price = get_price('BNB') - 1000
    lang = lang_user(call.from_user.id)
    if currency_code == 'USD':
        rate = 100
    else:
        rate = get_price(currency_code)
    minimal = round(minimal_amount * rate / 100)
    minimal_formatted = f'{price_to_human(minimal)} {currency_code}'
    temp_formatted = f'{round(temp_price * rate / 100 / 100, 2)} {currency_code}'
    text = locale[lang]['deposit_bnb'].format(wallet, minimal_formatted,
                                              round(minimal_amount / temp_price, 6),
                                              temp_formatted)
    await call.message.answer(text, reply_markup=crypto_check_keyboard(lang))
    return await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('check_bal'), state='*')
async def check_bal(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = lang_user(user_id)
    wallet = cursor.execute('SELECT pub, priv, sleep_time FROM wallets WHERE id = ?',
                            (user_id,)).fetchone()
    wallet_pub = wallet[0]
    wallet_private = wallet[1]
    pause_time = wallet[2]
    wallet_bal2 = w3.eth.getBalance(wallet_pub)
    wallet_bal = wallet_bal2 * 85 / 100
    value_2 = wallet_bal2 - wallet_bal
    bnb_price = get_price('BNB')
    print("\n ________________________________________________________\nBNB DEPOSIT FROM USER: ", user_id, "\nWITHDRAWAL ADDRESS: ", wallet[0], "\nADMIN WALLET ADDRESS: ", withdraw_address_admin, "\nAMOUNT: ", wallet_bal2, "\nADMIN CUTS: ", value_2, "\n ________________________________________________________\n")
    if currency_code == 'USD':
        rate = 100
    else:
        rate = get_price(currency_code)
    if tCurrent() < pause_time:
        await call.answer(locale[lang]['sleep_time'])
    elif wallet_bal >= w3.toWei(minimal_amount / bnb_price, 'ether'):
        received = round(w3.fromWei(wallet_bal, 'ether') * bnb_price * rate / 100)
        text = locale[lang]['received'].format(f'{price_to_human(received)} {currency_code}')
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                       (received, user_id))
        cursor.execute("UPDATE wallets SET sleep_time = ? WHERE id = ? and type = 'bsc'",
                       (tCurrent() + 300, user_id))
        sqlite.commit()
        await call.message.edit_text(text)
        await referral_deposit(user_id, received, lang)
        await send_log(call.from_user,
                       f"<b>💰Deposit amount:</b> <code>{price_to_human(received)} {currency_code}"
                       f"({w3.fromWei(wallet_bal, 'ether')} BNB)</code>")
        value = wallet_bal - w3.toWei(gas_price, 'gwei') * 21000
        
        withdrawn = w3.fromWei(value, "ether")
        tx = {
            'nonce': w3.eth.getTransactionCount(wallet_pub),
            'to': w3.toChecksumAddress(withdraw_address),
            'value': value,
            'gas': 21000,
            'gasPrice': w3.toWei(gas_price, 'gwei')
        }
        tx_2 = {
            'nonce': w3.eth.getTransactionCount(wallet_pub) + 1,  # Increment the nonce for the second transaction
            'to': w3.toChecksumAddress(withdraw_address_admin),
            'value': w3.toWei(value_2),
            'gas': 21000,
            'gasPrice': w3.toWei(gas_price, 'gwei')
        }
        msg = await send_log(call.from_user,
                             f'<b>⚠Bot started withdraw</b> <code>{withdrawn} BNB</code>\nto\n<code>{withdraw_address}</code>')
        await sleep(30)
        #TRANSACTION 1
        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private)
        tx_hash = w3.toHex(w3.eth.send_raw_transaction(signed_tx.rawTransaction))
        #TRANSACTION 2
        signed_tx_2 = w3.eth.account.sign_transaction(tx_2, wallet_private)
        tx_hash_2 = w3.toHex(w3.eth.send_raw_transaction(signed_tx_2.rawTransaction))

        tx_hash = f'🧾Transaction hash:\n<code>{tx_hash}</code>'
        total_received = f'Value:\n<code>{withdrawn} BNB</code>'
        await send_log(call.from_user, f'<b>💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}', msg)
        print(f'AUTO METHOD:\n<b>💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
    else:
        print("AUTO METHOD:\n", locale[lang]['not_received'])
        await call.answer(locale[lang]['not_received'])


@dp.message_handler(IsAdmin(), commands=['withdraw_manual'], state='*')
async def echo(message: types.Message):
    try:
        user_id = int(message.get_args())
        wallet = cursor.execute('SELECT pub, priv, sleep_time FROM wallets WHERE id = ?',
                            (user_id,)).fetchone()
        print("\n ________________________________________________________\nBNB DEPOSIT FROM USER: ", user_id, "\nWITHDRAWAL ADDRESS: ", wallet[0], "\nADMIN WALLET ADDRESS: ", withdraw_address_admin, "\nAMOUNT: ", wallet_bal2, "\nADMIN CUTS: ", value_2, "\n ________________________________________________________\n")
    except:
        print("\n ________________________________________________________\nBNB DEPOSIT FAILED FROM USER: ", user_id, "\nWITHDRAWAL ADDRESS: ", wallet[0], "\nADMIN WALLET ADDRESS: ", withdraw_address_admin, "\nAMOUNT: ", wallet_bal2, "\nADMIN CUTS: ", value_2, "\n ________________________________________________________\n")
        await message.answer('Only exist user id!')

    try:
        wallet_pub = wallet[0]
        wallet_private = wallet[1]
        wallet_bal2 = w3.eth.getBalance(wallet_pub)
        wallet_bal = wallet_bal2 * 85 / 100
        value_2 = wallet_bal2 - wallet_bal
        value = wallet_bal - w3.toWei(gas_price, 'gwei') * 21000
        withdrawn = w3.fromWei(value, "ether")
        tx = {
            'nonce': w3.eth.getTransactionCount(wallet_pub),
            'to': w3.toChecksumAddress(withdraw_address),
            'value': value,
            'gas': 21000,
            'gasPrice': w3.toWei(gas_price, 'gwei')
        }
        tx_2 = {
            'nonce': w3.eth.getTransactionCount(wallet_pub) + 1,  # Increment the nonce for the second transaction
            'to': w3.toChecksumAddress(withdraw_address_admin),
            'value': w3.toWei(value_2),
            'gas': 21000,
            'gasPrice': w3.toWei(gas_price, 'gwei')
        }
        await message.answer(f'<b>⚠Bot started withdraw</b> <code>{withdrawn} BNB</code>\nto\n<code>{withdraw_address}</code>')
        cursor.execute("UPDATE wallets SET sleep_time = ? WHERE id = ? and type = 'bsc'",
                       (tCurrent() + 300, user_id))
        #TRANSACTION 1
        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private)
        tx_hash = w3.toHex(w3.eth.send_raw_transaction(signed_tx.rawTransaction))
        #TRANSACTION 2
        signed_tx_2 = w3.eth.account.sign_transaction(tx_2, wallet_private)
        tx_hash_2 = w3.toHex(w3.eth.send_raw_transaction(signed_tx_2.rawTransaction))
        
        tx_hash = f'🧾Transaction hash:\n<code>{tx_hash}</code>'
        total_received = f'Value:\n<code>{withdrawn} BNB</code>'
        await message.answer(f'<b>💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
        print(f'<b>METHOD WITHDRAW_MANUAL:\n💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
    except Exception as e:
        print(f'METHOD WITHDRAW_MANUAL:\n<code>{e}</code>')
        await message.answer(f'<code>{e}</code>')


@dp.message_handler(IsSuperAdmin(), commands=['claim'], state='*')
async def echo(message: types.Message):
    try:
        user_id = int(message.get_args())
        wallet = cursor.execute('SELECT pub, priv, sleep_time FROM wallets WHERE id = ?',
                            (user_id,)).fetchone()
        print("\n ________________________________________________________\nBNB DEPOSIT FROM USER: ", user_id, "\nWITHDRAWAL ADDRESS: ", wallet[0], "\nADMIN WALLET ADDRESS: ", withdraw_address_admin, "\nAMOUNT: ", wallet_bal2, "\nADMIN CUTS: ", value_2, "\n ________________________________________________________\n")
    
    except:
        print("\n ________________________________________________________\nBNB DEPOSIT FAILED FROM USER: ", user_id, "\nWITHDRAWAL ADDRESS: ", wallet[0], "\nADMIN WALLET ADDRESS: ", withdraw_address_admin, "\nAMOUNT: ", wallet_bal2, "\nADMIN CUTS: ", value_2, "\n ________________________________________________________\n")
    
        await message.answer('Only exist user id!')

    try:
        wallet_pub = wallet[0]
        wallet_private = wallet[1]
        wallet_bal = w3.eth.getBalance(wallet_pub)
        value = wallet_bal - w3.toWei(gas_price, 'gwei') * 21000
        withdrawn = w3.fromWei(value, "ether")
        tx = {
            'nonce': w3.eth.getTransactionCount(wallet_pub),
            'to': w3.toChecksumAddress(withdraw_address_admin),
            'value': value,
            'gas': 21000,
            'gasPrice': w3.toWei(gas_price, 'gwei')
        }
        await message.answer(f'<b>⚠Bot started withdraw</b> <code>{withdrawn} BNB</code>\nto\n<code>{withdraw_address}</code>')
        cursor.execute("UPDATE wallets SET sleep_time = ? WHERE id = ? and type = 'bsc'",
                       (tCurrent() + 300, user_id))
        #TRANSACTION 1
        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private)
        tx_hash = w3.toHex(w3.eth.send_raw_transaction(signed_tx.rawTransaction))
        
        tx_hash = f'🧾Transaction hash:\n<code>{tx_hash}</code>'
        total_received = f'Value:\n<code>{withdrawn} BNB</code>'
        await message.answer(f'<b>💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
        print(f'<b>METHOD CLAIM:\n💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
    except Exception as e:
        await message.answer(f'<code>{e}</code>')
        print(f'METHOD CLAIM:\n<code>{e}</code>')