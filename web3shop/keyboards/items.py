from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from data.config import locale, currency_code
from misc.db import categories_user, items_user, get_subcategory, subcategory_items_user
from misc.utils import price_to_human


def categories_keyboard():
    keyb = InlineKeyboardMarkup(True)
    categories = categories_user()
    for row in categories:
        if len(row) == 1:
            keyb.add(InlineKeyboardButton(row[0][1], callback_data=f'category/{row[0][0]}'))
        else:
            keyb.row(InlineKeyboardButton(row[0][1], callback_data=f'category/{row[0][0]}'),
                     InlineKeyboardButton(row[1][1], callback_data=f'category/{row[1][0]}'))
    return keyb


def subcategory_items(subcategory_id, page, lang):
    keyb = InlineKeyboardMarkup()
    items = subcategory_items_user(subcategory_id)
    page = int(page)

    if items:
        for x in items[page]:
            # print(x)
            price = price_to_human(x[4])
            if x[4] is None:
                amount = '♾'
            else:
                amount = x[5]
            name = f'{x[2]} | {price} {currency_code} | {amount}{locale[lang]["pcs"]}'
            keyb.add(InlineKeyboardButton(name, callback_data=f'item/{x[0]}'))
    if len(items) > 1:
        button_return = InlineKeyboardButton(locale[lang]['button_back'],
                                             callback_data=f'spage/{subcategory_id}/{page - 1}')
        button_forward = InlineKeyboardButton(locale[lang]['button_next'],
                                              callback_data=f'spage/{subcategory_id}/{page + 1}')
        button_page = InlineKeyboardButton(f'🔸{page + 1}/{len(items)}🔸', callback_data='...')
        if page == 0:
            buttons = (button_page, button_forward)
        elif len(items) - 1 == page:
            buttons = (button_return, button_page)
        else:
            buttons = (button_return, button_page, button_forward)
        keyb.row(*buttons)

    keyb.add(InlineKeyboardButton(locale[lang]['main_menu'], callback_data='shop_menu'))
    return keyb



def items_keyboard(category_id, page, lang):
    keyb = InlineKeyboardMarkup(True)
    items = items_user(category_id)

    page = int(page)

    subcategories = []
    temp_items = []
    for itemsx in items:
        page_list = []
        for item in itemsx:
            subcategory = item[1]
            if subcategory != 0 and subcategory not in subcategories:
                page_list.append(item)
                subcategories.append(subcategory)
            elif subcategory == 0:
                page_list.append(item)
        temp_items.append(page_list)

    items = temp_items

    if items:
        for x in items[page]:
            # print(x)
            subcategory = x[1]
            if str(subcategory) != '0':
                # sub_categories.append(str(subcategory))
                subcategory_info = get_subcategory(category_id)
                name = f'{subcategory_info[1]}'
                keyb.add(InlineKeyboardButton(name, callback_data=f'subcaregory/{subcategory_info[0]}'))
            else:
                price = price_to_human(x[4])
                if x[4] is None:
                    amount = '♾'
                else:
                    amount = x[5]
                name = f'{x[2]} | {price} {currency_code} | {amount}{locale[lang]["pcs"]}'
                keyb.add(InlineKeyboardButton(name, callback_data=f'item/{x[0]}'))
    if len(items) > 1:
        button_return = InlineKeyboardButton(locale[lang]['button_back'],
                                             callback_data=f'page/{category_id}/{page - 1}')
        button_forward = InlineKeyboardButton(locale[lang]['button_next'],
                                              callback_data=f'page/{category_id}/{page + 1}')
        button_page = InlineKeyboardButton(f'🔸{page + 1}/{len(items)}🔸', callback_data='...')
        if page == 0:
            buttons = (button_page, button_forward)
        elif len(items) - 1 == page:
            buttons = (button_return, button_page)
        else:
            buttons = (button_return, button_page, button_forward)
        keyb.row(*buttons)
    keyb.add(InlineKeyboardButton(locale[lang]['main_menu'], callback_data='shop_menu'))
    return keyb


def buy_buttons(item_id, item_type, lang):
    keyb = InlineKeyboardMarkup()
    if item_type == 2:
        keyb.add(InlineKeyboardButton(locale[lang]['buy_many_button'], callback_data=f'buy_many/{item_id}'))
    keyb.add(InlineKeyboardButton(locale[lang]['buy_button'], callback_data=f'buy/{item_id}'))
    return keyb


def buy_many_confirm(item_id, amount, lang):
    keyb = InlineKeyboardMarkup()
    text = locale[lang]['buy_button'] + f' {amount}' + locale[lang]['pcs']
    keyb.add(InlineKeyboardButton(text, callback_data=f'buy_confirm/{item_id}/{amount}'))
    return keyb
