from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from data.loader import cursor, locale, admin_ids


def keyboard(lang, user_id):
    req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM bots WHERE id = ?)',
                              (user_id,)).fetchone()[0])
    keyb = ReplyKeyboardMarkup(True, resize_keyboard=True)
    if req:
        keyb.row(locale[lang]['edit_bot'])
        keyb.row(locale[lang]['restart_bot'])
    else:
        keyb.row(locale[lang]['create_bot'])
    if user_id in admin_ids:
        keyb.row(locale[lang]['admin_menu'])
    return keyb


lang_keyboard = InlineKeyboardMarkup(True)
lang_keyboard.add(InlineKeyboardButton('🇬🇧English', callback_data='lang/en'))
lang_keyboard.add(InlineKeyboardButton('🇷🇺Русский', callback_data='lang/ru'))


return_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
return_keyboard.row('↩Return')


def sub_button(lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton(locale[lang]['sub_text'], url=locale[lang]['sub_link']))
    return keyb
