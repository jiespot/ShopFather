from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

admin_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
admin_keyboard.row('🤖Bot Admin')
admin_keyboard.row('🌐Global message')
admin_keyboard.row('↩Return')

advert_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
advert_keyboard.row('👁‍🗨Check message')
advert_keyboard.row('✏Change message')
advert_keyboard.row('📢Send message')
advert_keyboard.row('↩Return')


def admin_bot_keyboard(user_id):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton('⭐On/Off Ad', callback_data=f'advert/{user_id}'))
    keyb.row(InlineKeyboardButton('🔄Restart Bot', callback_data=f'restart/{user_id}'))
    return keyb
