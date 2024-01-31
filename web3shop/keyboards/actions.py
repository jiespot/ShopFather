from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from data.config import locale, invite_link

select_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
select_keyboard.row('📝String', '🌅Media')
select_keyboard.row('❌Cancel')

promo_type_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
promo_type_keyboard.row('🔥Discount', '💰Top-up')
promo_type_keyboard.row('❌Cancel')

description_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
description_keyboard.row('✖No Description')
description_keyboard.row('❌Cancel')

amount_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
amount_keyboard.row('♾No limit')
amount_keyboard.row('❌Cancel')

noyes_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
noyes_keyboard.row('✅Yes', '❌No')
noyes_keyboard.row('❌Cancel')

back_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
back_keyboard.row('↩Return')

cancel_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
cancel_keyboard.row('❌Cancel')


def return_button(lang, menu):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton(locale[lang]['button_back'], callback_data=f'return/{menu}'))
    return keyb


def user_return_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['button_return'])
    return keyb


def user_noyes_keyboard(lang):
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    keyb.row(locale[lang]['yes'], locale[lang]['no'])
    return keyb


def sub_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    try:
        keyb.row(InlineKeyboardButton(locale[lang]['invite_button'], url=invite_link))
    except:
        pass
    keyb.row(InlineKeyboardButton(locale[lang]['check_sub'], callback_data='check_sub'))
    return keyb
