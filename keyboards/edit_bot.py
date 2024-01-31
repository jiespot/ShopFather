from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.loader import locale, cursor

def finance_keyboard(lang, bot_id):
    q = cursor.execute("SELECT can_user_transfer FROM bots WHERE id = ?", [bot_id]).fetchone()
    if q:
        can_user_transfer = bool(q[0])
        can_user_transfer_symbol = '✅' if can_user_transfer else "❌"
    else:
        print(f"Can't find a bot with ID: {bot_id}")
        return

    keyb = InlineKeyboardMarkup()
    keyb.row(InlineKeyboardButton(text=locale[lang]["change_currency_button"], callback_data='edit/currency'))
    keyb.row(InlineKeyboardButton(text=f'{can_user_transfer_symbol}{locale[lang]["money_transfers_button"]}',
                                  callback_data='edit/can_send'))
    keyb.add(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))

    return keyb



def edit_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton(locale[lang]['inline_bot_token'], callback_data='edit/token'),
             InlineKeyboardButton(locale[lang]['inline_payment_methods'], callback_data='edit/payments'))
    keyb.row(InlineKeyboardButton(locale[lang]['currency_button'], callback_data='edit/currency'),
             InlineKeyboardButton(locale[lang]['referral_button'], callback_data='edit/referral'))
    keyb.row(InlineKeyboardButton(locale[lang]['inline_langs'], callback_data='edit/locale'),
             InlineKeyboardButton(locale[lang]['inline_messages'], callback_data='edit/messages'))
    keyb.row(InlineKeyboardButton(locale[lang]['inline_admins'], callback_data='edit/admins'),
             InlineKeyboardButton(locale[lang]['message_sub'], callback_data='edit/invite'))
    keyb.row(InlineKeyboardButton(locale[lang]['inline_stop'], callback_data='edit/stop'),
             InlineKeyboardButton(locale[lang]['inline_delete'], callback_data='edit/delete'))
    return keyb


def edit_admin_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton(locale[lang]['inline_add_admin'], callback_data='admin/add'),
             InlineKeyboardButton(locale[lang]['inline_remove_admin'], callback_data='admin/remove'))
    keyb.row(InlineKeyboardButton(locale[lang]['inline_list_admins'], callback_data='admin/list'),
             InlineKeyboardButton(locale[lang]['inline_clear_admins'], callback_data='admin/clear'))
    keyb.add(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))
    return keyb


def edit_messages_keyboard(lang, bot_lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton(locale[lang]['message_start'], callback_data=f'message/start/{bot_lang}'),
             InlineKeyboardButton(locale[lang]["edit_terms_button"], callback_data=f'message/terms_menu/{bot_lang}'))
    keyb.add(InlineKeyboardButton(locale[lang]['message_sub'], callback_data=f'message/invite/{bot_lang}'))
    keyb.row(InlineKeyboardButton(locale[lang]['message_help'], callback_data=f'message/help/{bot_lang}'),
             InlineKeyboardButton(locale[lang]['message_contact'], callback_data=f'message/contact/{bot_lang}'))
    keyb.row(InlineKeyboardButton(locale[lang]['button_help'], callback_data=f'message/help_button/{bot_lang}'),
             InlineKeyboardButton(locale[lang]['button_contact'], callback_data=f'message/contact_button/{bot_lang}'))
    keyb.add(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))
    return keyb

def edit_terms_kb(lang, bot_lang, bot_id):
    kb = InlineKeyboardMarkup()

    try:
        status = bool(cursor.execute('SELECT terms FROM bots WHERE id = ?', [bot_id]).fetchone()[0])
    except:
        return None

    text = locale[lang]["enabled"] if status else locale[lang]["disabled"]
    kb.row(InlineKeyboardButton(text=text, callback_data=f'terms/edit/{bot_lang}'))
    kb.row(InlineKeyboardButton(text=locale[lang]["edit_terms_button_1"], callback_data=f'message/terms/{bot_lang}'))
    kb.row(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))
    return kb


def edit_lang_keyboard(lang):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton('🇬🇧English', callback_data='message/lang/en'))
    keyb.add(InlineKeyboardButton('🇷🇺Русский', callback_data='message/lang/ru'))
    keyb.add(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))
    return keyb


def payments_groups_keyboard(lang):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(text=locale["en"]["qiwi_group"], callback_data='payment_group/qiwi_group'),
           InlineKeyboardButton(text=locale["en"]["yoomoney_group"], callback_data='payment_group/yoomoney_group'))
    kb.row(InlineKeyboardButton(text=locale["en"]["cryptobot_group"], callback_data='payment_group/cryptobot_group'),
           InlineKeyboardButton(text=locale["en"]["bnb_group"], callback_data='payment_group/bnb_group'))
    kb.row(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit_menu'))

    return kb

def payment_keyboard(user_id, lang, group):
    keyb = InlineKeyboardMarkup()
    bnb, qiwi_number, qiwi_p2p, qiwi_nickname, yookassa, cryptobot = \
        cursor.execute('SELECT bnb, qiwi_number, qiwi_p2p, qiwi_nickname, yookassa, cryptobot FROM payments WHERE id = ?',
                       (user_id,)).fetchone()
    symbol_bnb = '❌'
    symbol_qiwi_number = '❌'
    symbol_qiwi_nickname = '❌'
    symbol_qiwi_p2p = '❌'
    symbol_yookassa = '❌'
    symbol_cryptobot = '❌'
    if bool(bnb):
        symbol_bnb = '✅'
    if bool(qiwi_number):
        symbol_qiwi_number = '✅'
    if bool(qiwi_nickname):
        symbol_qiwi_nickname = '✅'
    if bool(qiwi_p2p):
        symbol_qiwi_p2p = '✅'
    if bool(yookassa):
        symbol_yookassa = '✅'
    if bool(cryptobot):
        symbol_cryptobot = '✅'
    if group == 'qiwi_group':
        keyb.row(
            InlineKeyboardButton(symbol_qiwi_number + locale[lang]['qiwi_number'], callback_data='payment/qiwi_number'),
            InlineKeyboardButton(symbol_qiwi_nickname + locale[lang]['qiwi_nickname'],
                                 callback_data='payment/qiwi_nickname'),
            InlineKeyboardButton(symbol_qiwi_p2p + 'QIWI P2P', callback_data='payment/qiwi_p2p'), )
        keyb.add(InlineKeyboardButton(locale[lang]['inline_qiwi_change'], callback_data='payment/edit/qiwi'))
    elif group == 'yoomoney_group':
        keyb.row(InlineKeyboardButton(symbol_yookassa + 'ЮKassa', callback_data='payment/yookassa'),
                 InlineKeyboardButton(locale[lang]['inline_yookassa_change'], callback_data='payment/edit/yookassa'))
    elif group == 'bnb_group':
        keyb.row(InlineKeyboardButton(symbol_bnb + locale[lang]['inline_bnb'], callback_data='payment/bnb'),
                 InlineKeyboardButton(locale[lang]['inline_bnb_change'], callback_data='payment/edit/bnb'))
    elif group == 'cryptobot_group':
        keyb.row(InlineKeyboardButton(symbol_cryptobot + locale[lang]['inline_cryptobot'], callback_data='payment/cryptobot'),
                 InlineKeyboardButton(locale[lang]['inline_cryptobot_change'], callback_data='payment/edit/cryptobot'))

    keyb.add(InlineKeyboardButton(locale[lang]['return_button'], callback_data='edit/payments'))
    return keyb
