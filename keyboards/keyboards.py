from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from data.loader import locale


def reset_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['default_message'])
    keyb.row(locale[lang]['cancel_button'])
    return keyb


def skip_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['skip_button'])
    keyb.row(locale[lang]['cancel_button'])
    return keyb


def cancel_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['cancel_button'])
    return keyb


def link_disable_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['link_disable_button'])
    keyb.row(locale[lang]['cancel_button'])
    return keyb


def ref_disable_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['ref_disable_button'])
    keyb.row(locale[lang]['cancel_button'])
    return keyb


delete_keyboard = InlineKeyboardMarkup(True)
delete_keyboard.row(InlineKeyboardButton('✅Yes', callback_data='delete/yes'),
                    InlineKeyboardButton('❌No', callback_data='delete/no'))

stop_keyboard = InlineKeyboardMarkup(True)
stop_keyboard.row(InlineKeyboardButton('✅Yes', callback_data='stop/yes'),
                  InlineKeyboardButton('❌No', callback_data='stop/no'))


def yes_no_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['yes'], locale[lang]['no'])
    keyb.row(locale[lang]['cancel_button'])
    return keyb


def crypto_bot_menu():
    amount_rub = '0'
    crypto_bot_kb = InlineKeyboardMarkup(row_width=3)
    cb_btc_btn = InlineKeyboardButton(text='BTC', callback_data=f'cbot|btc|{amount_rub}')
    cb_ton_btn = InlineKeyboardButton(text='TON', callback_data=f'cbot|ton|{amount_rub}')
    cb_eth_btn = InlineKeyboardButton(text='ETH', callback_data=f'cbot|eth|{amount_rub}')
    cb_usdt_btn = InlineKeyboardButton(text='USDT', callback_data=f'cbot|usdt|{amount_rub}')
    cb_usdc_btn = InlineKeyboardButton(text='USDC', callback_data=f'cbot|usdc|{amount_rub}')

    crypto_bot_kb.row(cb_btc_btn, cb_ton_btn, cb_eth_btn)
    crypto_bot_kb.row(cb_usdt_btn, cb_usdc_btn)
    return crypto_bot_kb
