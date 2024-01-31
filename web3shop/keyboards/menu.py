from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from data.config import admin_ids, lang_list, locale, withdraw_address, qiwi_token, qiwi_nickname, qiwi_private_key, \
    qiwi_by_number, ref_percent, yookassa_token, cryptobot_token
from misc.db import lang_user

from data.loader import cursor


def main_keyboard(user_id):
    lang = lang_user(user_id)
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['button_shop'], locale[lang]['button_profile'])
    keyb.row(locale[lang]['button_help'], locale[lang]['button_contact'])
    if user_id in admin_ids:
        keyb.row('🤖Admin Menu')
    return keyb


def profile_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    purchases = InlineKeyboardButton(locale[lang]['my_purchases'], callback_data='purchases')
    promo = InlineKeyboardButton(locale[lang]['promo_button'], callback_data='promo')
    if ref_percent is not None:
        referral = InlineKeyboardButton(locale[lang]['referral_button'], callback_data='referral')
        keyb.row(referral, promo)
    else:
        keyb.row(promo)
    if qiwi_token is not None or withdraw_address is not None or yookassa_token is not None or cryptobot_token is not None:
        refill = InlineKeyboardButton(locale[lang]['button_deposit'], callback_data='deposit')
        keyb.row(purchases, refill)
    else:
        keyb.row(purchases)
    return keyb


def qiwi_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    if qiwi_token is not None:
        if qiwi_by_number:
            keyb.add(InlineKeyboardButton(locale[lang]['button_qiwi_number'], callback_data='qiwi/number'))
        if qiwi_nickname is not None:
            keyb.add(InlineKeyboardButton(locale[lang]['button_qiwi_nickname'], callback_data='qiwi/nickname'))
        if qiwi_private_key is not None:
            keyb.add(InlineKeyboardButton(locale[lang]['button_qiwi_form'], callback_data='qiwi/form'))
    keyb.add(InlineKeyboardButton(locale[lang]['button_back'], callback_data='return/deposit'))
    return keyb

def cryptobot_form_kb(lang, pay_url: str, bill_id: str, amount: [float, int]):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(text=locale[lang]["go_to_pay"], url=pay_url))
    kb.row(InlineKeyboardButton(text=locale[lang]["button_checkv2"], callback_data=f'cryptobot/check_deposit/{bill_id}/{str(amount)}'),
           InlineKeyboardButton(text=locale[lang]["button_cancel"], callback_data='return/deposit'))

    return kb

def cryptobot_kb(lang):
    crypto_bot_kb = InlineKeyboardMarkup(row_width=3)
    cb_btc_btn = InlineKeyboardButton(text='🌐 BTC', callback_data='cbot|btc')
    cb_ton_btn = InlineKeyboardButton(text='💠 TON', callback_data='cbot|ton')
    cb_eth_btn = InlineKeyboardButton(text='📬 ETH', callback_data='cbot|eth')
    cb_usdt_btn = InlineKeyboardButton(text='💶 USDT', callback_data='cbot|usdt')
    cb_usdc_btn = InlineKeyboardButton(text='💎 USDC', callback_data='cbot|usdc')
    
    #cb_busd_btn = InlineKeyboardButton(text='🍭BUSD', callback_data='cbot|busd')

    crypto_bot_kb.row(cb_btc_btn, cb_ton_btn, cb_eth_btn)
    crypto_bot_kb.row(cb_usdt_btn, cb_usdc_btn)
    #This removes after BUSD will removed source by binance
    #crypto_bot_kb.row(cb_usdt_btn, cb_usdc_btn, cb_busd_btn)

    crypto_bot_kb.add(InlineKeyboardButton(locale[lang]['button_back'], callback_data='return/deposit'))
    return crypto_bot_kb


def qiwi_check_keyboard(send_requests, get_receipt, get_way, lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton(locale[lang]['to_checkout'], url=send_requests))
    keyb.add(InlineKeyboardButton(locale[lang]['button_check'], callback_data=f"pay/{get_way}/{get_receipt}"))
    return keyb


def deposit_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    if withdraw_address is not None:
        keyb.add(InlineKeyboardButton(locale[lang]['button_deposit_bnb'], callback_data='crypto_deposit'))
    if qiwi_token is not None:
        keyb.add(InlineKeyboardButton('🥝QIWI', callback_data='qiwi_deposit'))
    if yookassa_token is not None:
        keyb.add(InlineKeyboardButton(locale[lang]["button_deposit_ymoney"], callback_data='yoo/kassa'))
    if cryptobot_token is not None:
        keyb.add(InlineKeyboardButton('💎CryptoBot', callback_data='cryptobot_deposit'))
    keyb.add(InlineKeyboardButton(locale[lang]['button_back'], callback_data='return/profile'))
    return keyb


def crypto_check_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton(locale[lang]['button_check'], callback_data='check_bal'))
    return keyb


lang_keyboard = InlineKeyboardMarkup(True)
for lang in lang_list:
    lang_keyboard.add(InlineKeyboardButton(locale[lang]['lang_name'], callback_data=f'lang/{lang}'))


def purchases_keyboard(user_id, offset, total, lang):
    purchases = cursor.execute('SELECT id, name, amount FROM purchases '
                               'WHERE buyer_id = ? ORDER BY id DESC LIMIT ?, 5',
                               (user_id, offset)).fetchall()
    keyb = InlineKeyboardMarkup(True)
    for item in purchases:
        text = f'{item[1]} | {item[2]}{locale[lang]["pcs"]}'
        keyb.add(InlineKeyboardButton(text, callback_data=f'purchase/{item[0]}/{offset}'))
    buttons = []
    if offset - 5 >= 0:
        buttons.append(InlineKeyboardButton(locale[lang]['button_back'], callback_data=f'ppage/{offset - 5}'))
    if offset + 5 < total:
        buttons.append(InlineKeyboardButton(locale[lang]['button_next'], callback_data=f'ppage/{offset + 5}'))
    keyb.row(*buttons)
    return keyb


def view_button(purchase_id, offset, lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton(locale[lang]['view_product'], callback_data=f'show_purchase/{purchase_id}'))
    keyb.add(InlineKeyboardButton(locale[lang]['button_back'], callback_data=f'ppage/{offset}'))
    return keyb


def approve_send_money_kb(lang, reciever, amount, chat_id, message_id):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(text=locale[lang]['yes'], callback_data=f'send_money/yes/{reciever}:{amount}:{chat_id}:{message_id}'),
           InlineKeyboardButton(text=locale[lang]['no'], callback_data=f'send_money/no/{reciever}:{amount}:{chat_id}{message_id}'))
    return kb

def go_to_bot_kb(lang, reciever, amount, chat_id, bot_username, message_id):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(text=locale[lang]["go_to_bot"], url=f't.me/{bot_username}?'
                                                                    f'start=approve_send_money_{reciever}_{amount}_{chat_id}_{message_id}'))
    return kb


def terms_accept(lang, invited=None):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(text=locale[lang]["agree"], callback_data=f'agree/terms/{invited or 0}'))
    return kb
