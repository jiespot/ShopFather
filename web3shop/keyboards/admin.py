from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from data.config import qiwi_token
from misc.db import categories_admin, promo_admin, get_subcategories, get_subcategory

from data.loader import sqlite

admin_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
admin_keyboard.row('✏Edit items', '📚Edit categories')
admin_keyboard.row('🌟Edit promo codes', '👤User info')
if qiwi_token is not None:
    admin_keyboard.row('🥝QIWI Balance', '🌐Global message')
else:
    admin_keyboard.row('🌐Global message')
admin_keyboard.row('↩Return')

advert_keyboard = ReplyKeyboardMarkup(True, resize_keyboard=True)
advert_keyboard.row('👁‍🗨Check message')
advert_keyboard.row('✏Change message')
advert_keyboard.row('📢Send message')
advert_keyboard.row('↩Return')


def edit_keyboard(item_id):
    item_type = sqlite.cursor().execute('SELECT type FROM items WHERE id = ?',
                                        (item_id,)).fetchone()[0]
    keyb = InlineKeyboardMarkup(True)
    if item_type == 1:
        keyb.row(InlineKeyboardButton('🌅Show content', callback_data=f'show/{item_id}'),
                 InlineKeyboardButton('✏Edit content', callback_data=f'edit/{item_id}/content'))
        keyb.row(InlineKeyboardButton('📦Edit amount', callback_data=f'edit/{item_id}/amount'),
                 InlineKeyboardButton('🌟Create promo code', callback_data=f'edit/{item_id}/promo'))
    else:
        keyb.row(InlineKeyboardButton('📝Add strings', callback_data=f'edit/{item_id}/strings'),
                 InlineKeyboardButton('🌟Create promo code', callback_data=f'edit/{item_id}/promo'))
    keyb.row(InlineKeyboardButton('🏷Edit name', callback_data=f'edit/{item_id}/name'),
             InlineKeyboardButton('📜Edit description', callback_data=f'edit/{item_id}/description'))
    keyb.row(InlineKeyboardButton('💵Edit price', callback_data=f'edit/{item_id}/price'),
             InlineKeyboardButton('📚Change category', callback_data=f'edit/{item_id}/category'))
    keyb.row(InlineKeyboardButton('🔒Hide/show item', callback_data=f'edit/{item_id}/hide'),
             InlineKeyboardButton('🗑Delete item', callback_data=f'edit/{item_id}/delete'))
    keyb.add(InlineKeyboardButton('⬅Return', callback_data='return'))
    return keyb


def delete_item_keyboad(item_id):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton('✅Yes', callback_data=f'delete/{item_id}'),
             InlineKeyboardButton('❌No', callback_data='del_cancel'))
    return keyb


def delete_promo_keyboad(promo_id):
    keyb = InlineKeyboardMarkup(True)
    keyb.row(InlineKeyboardButton('✅Yes', callback_data=f'pdelete/{promo_id}'),
             InlineKeyboardButton('❌No', callback_data='del_cancel'))
    return keyb


def category_kb(category_id):
    sub_categories = get_subcategories(category_id)
    kb = InlineKeyboardMarkup()

    for sub_category in sub_categories:
        kb.add(InlineKeyboardButton(text=sub_category[1], callback_data=f'asubcategory/{sub_category[0]}'))

    kb.row(InlineKeyboardButton(text='➕ Add subCategory', callback_data=f'add_subcategory/{category_id}'))
    kb.row(InlineKeyboardButton(text='📝 Edit category', callback_data=f'acategory/{category_id}'))
    kb.row(InlineKeyboardButton(text='🔙Back', callback_data='creturn'))

    return kb


def categories_keyboard_admin(add_mode=False):
    keyb = InlineKeyboardMarkup(True)
    categories = categories_admin()
    for row in categories:
        if row[0][3] == 1:
            name1 = f'🔒 {row[0][1]}'
        else:
            name1 = row[0][1]
        if len(row) == 1:
            # keyb.add(InlineKeyboardButton(name1, callback_data=f'acategory/{row[0][0]}'))
            keyb.add(InlineKeyboardButton(name1, callback_data=f'select_category/{row[0][0]}'))
        else:
            if row[1][3] == 1:
                name2 = f'🔒 {row[1][1]}'
            else:
                name2 = row[1][1]
            # keyb.row(InlineKeyboardButton(name1, callback_data=f'acategory/{row[0][0]}'),
            #          InlineKeyboardButton(name2, callback_data=f'acategory/{row[1][0]}'))
            keyb.row(InlineKeyboardButton(name1, callback_data=f'select_category/{row[0][0]}'),
                     InlineKeyboardButton(name2, callback_data=f'select_category/{row[1][0]}'))
    if add_mode:
        keyb.add(InlineKeyboardButton('❌Cancel', callback_data='cancel'))
    else:
        keyb.add(InlineKeyboardButton('➕Add category', callback_data='add_category'))
    return keyb

def sub_categories_keyboard_admin(category_id):
    sub_categories = get_subcategories(category_id)
    kb = InlineKeyboardMarkup()

    for sub_category in sub_categories:
        kb.add(InlineKeyboardButton(text=sub_category[1], callback_data=f'asubcategory/{sub_category[0]}'))

    kb.add(InlineKeyboardButton('🚫 Add item without subCategory', callback_data='asubcategory/0'))
    kb.add(InlineKeyboardButton('❌Cancel', callback_data='cancel'))
    return kb

def promo_keyboard_admin(add_mode=False):
    keyb = InlineKeyboardMarkup(True)
    promos = promo_admin()
    for row in promos:
        promo_code = row[0][1]
        promo_type = row[0][2]
        promo_amount = row[0][3]
        if promo_type == 1:
            emoji = '🔥'
        elif promo_type == 2:
            emoji = '💰'
        else:
            emoji = '📦'
        name1 = f'{emoji} | {promo_code} | {promo_amount} left'
        if len(row) == 1:
            keyb.add(InlineKeyboardButton(name1, callback_data=f'apromo/{row[0][0]}'))
        else:
            promo_code = row[1][1]
            promo_type = row[1][2]
            promo_amount = row[1][3]
            if promo_type == 1:
                emoji = '🔥'
            elif promo_type == 2:
                emoji = '💰'
            else:
                emoji = '📦'
            name2 = f'{emoji} | {promo_code} | {promo_amount} left'
            keyb.row(InlineKeyboardButton(name1, callback_data=f'apromo/{row[0][0]}'),
                     InlineKeyboardButton(name2, callback_data=f'apromo/{row[1][0]}'))
    if add_mode:
        keyb.add(InlineKeyboardButton('❌Cancel', callback_data='cancel'))
    else:
        keyb.add(InlineKeyboardButton('➕Add promo code', callback_data='add_promo'))
    return keyb


def edit_categories_keyboard(category_id):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton('🏷Edit name', callback_data=f'cedit/{category_id}/name'))
    keyb.add(InlineKeyboardButton('🔒Hide/show category', callback_data=f'cedit/{category_id}/hide'))
    keyb.add(InlineKeyboardButton('🔵On/Off one row', callback_data=f'cedit/{category_id}/one_row'))
    keyb.add(InlineKeyboardButton('⬅Return', callback_data='creturn'))
    return keyb

def edit_sub_categories_keyboard(sub_category_id):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('🏷Edit name', callback_data=f'scedit/{sub_category_id}/name'))
    keyb.add(InlineKeyboardButton('⬅Return', callback_data='creturn'))
    return keyb

def edit_promo_keyboard(promo_id):
    keyb = InlineKeyboardMarkup(True)
    keyb.add(InlineKeyboardButton('📦Edit activations count', callback_data=f'pedit/{promo_id}/count'))
    keyb.add(InlineKeyboardButton('🗑Delete promo code', callback_data=f'pedit/{promo_id}/delete'))
    keyb.add(InlineKeyboardButton('⬅Return', callback_data='preturn'))
    return keyb
