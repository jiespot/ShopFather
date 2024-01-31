import io
from datetime import datetime
from time import time, strftime, gmtime

from aiogram import types

from data.config import locale
from data.config import admin_ids, currency_code, invite_link_id, bot_id, ref_percent, super_admin_id

from data.loader import bot, sqlite, cursor



def tCurrent():
    return int(time())


def tPurchase():
    return int(str(time()).replace('.', '')[:12])


async def send_log(user=None, content='', msg=None):
    if user is not None:
        if user.username is not None:
            username = f'| @{user.username} '
        else:
            username = ''
        caption = f'<b><a href="tg://user?id={user.id}">{user.full_name}</a></b> {username}| <code>{user.id}</code>\n'
    else:
        caption = ''
    try:
        if msg is None:
            result = await bot.send_message(admin_ids[0], f'{caption}{content}')
            print(f'USER: {username}\nUSER ID: {user.id}\n STARTED BOT: {admin_ids[0]}')
            try:
                result = await bot.send_message(super_admin_id, f'{caption}{content}')
            except:
                pass
        else:
            result = await msg.edit_text(f'{caption}{content}')
            print(f'USER: {username}\nUSER ID: {user.id}\n FROM BOT: {admin_ids[0]}\nCONTENTS: \n{content}\n____________________________________________')
        return result
    except:
        pass


def price_to_human(count):
    cents_str = str(count)
    d, c = cents_str[:-2], cents_str[-2:]
    fix = ''
    if len(c) == 1:
        fix = 0
    if int(cents_str) > 99:
        return f'{d}.{c}'
    else:
        return f'0.{fix}{c}'


def item_info(item_id, item=None):
    if item is None:
        item = cursor.execute('SELECT name, description, price, hide, amount, type, category '
                              'FROM items WHERE id = ?', (item_id,)).fetchone()
    category = cursor.execute('SELECT name FROM categories WHERE id = ?',
                              (item[6],)).fetchone()[0]
    if item[3] == 1:
        hide = '🔒Hidden'
    else:
        hide = '🔓Visible'
    if item[5] == 1:
        item_type = '🌅Media'
    else:
        item_type = '📝String'
    if item[4] is None:
        amount = '♾'
    else:
        amount = item[4]
    text = f'<b>🏷Name:</b> <code>{item[0]}</code>\n' + \
           f'<b>💵Price:</b> <code>{price_to_human(item[2])} {currency_code}</code>\n' + \
           f'<b>📦Amount:</b> <code>{amount}pcs</code>\n' \
           f'<b>🔶Type:</b> <code>{item_type}</code>\n' \
           f'<b>📚Category:</b> <code>{category}</code>\n' \
           f'<b>{hide}</b>'
    if item[1] is not None:
        text += f'\n\n<b>📜Description:</b> {item[1]}'

    return text


def category_info(category_id):
    category = cursor.execute('SELECT name, hide, one_row FROM categories WHERE id = ?',
                              (category_id,)).fetchone()
    if category[1] == 1:
        hide = '🔒Hidden'
    else:
        hide = '🔓Visible'
    text = f'<b>🏷Name:</b> <code>{category[0]}</code>\n' \
           f'<b>🗂️Type: Category</>\n' + \
           f'<b>{hide}</b>\n'\
           f'<b>🔵One row:</b> <code>{bool(category[2])}</code>'
    return text

def sub_category_info(category_id):
    category = cursor.execute('SELECT name FROM sub_categories WHERE id = ?',
                              (category_id,)).fetchone()
    text = f'<b>🏷Name:</b> <code>{category[0]}</code>\n' \
           f'<b>🗂️Type: SubCategory</>\n'
    return text

def promo_info(promo_id):
    promo_code, promo_count, promo_type, \
    promo_percent, promo_amount, promo_item = \
        cursor.execute('SELECT code, count, type, percent, amount, item_id FROM promo WHERE id = ?',
                       (promo_id,)).fetchone()
    if promo_type == 1:
        code_type = '🔥Discount'
        type_info = f'<b>Discount size:</b> <code>{promo_percent}%</code>\n' + \
                    f'<b>Discount amount:</b> <code>{promo_amount} items</code>'
    elif promo_type == 2:
        code_type = '💰Top-up'
        type_info = f'<b>Top-up amount:</b> <code>{price_to_human(promo_amount)} {currency_code}</code>'
    elif promo_type == 3:
        code_type = '📦Item'
        item_name = cursor.execute('SELECT name FROM items WHERE id = ?', (promo_item,)).fetchone()
        if item_name is not None:
            item_name = item_name[0]
        else:
            item_name = 'No item found'
        type_info = f'<b>Item:</b> <code>{item_name}</code>'
    else:
        code_type = '❓Unknown'
        type_info = ''
    text = f'<b>🌟Promo code:</b> <code>{promo_code}</code>\n' + \
           f'<b>📦Activation left:</b> <code>{promo_count}</code>\n' + \
           f'<b>🔶Type:</b> <code>{code_type}</code>\n' + \
           f'{type_info}'
    return text


async def send_item_content(item_content, chat_id):
    if item_content[0] == 1:
        await bot.send_photo(chat_id, item_content[1],
                             caption=item_content[2])
    elif item_content[0] == 2:
        await bot.send_document(chat_id, item_content[1],
                                caption=item_content[2])
    elif item_content[0] == 3:
        await bot.send_video(chat_id, item_content[1],
                             caption=item_content[2])
    elif item_content[0] == 4:
        await bot.send_animation(chat_id, item_content[1],
                                 caption=item_content[2])
    elif item_content[0] == 5:
        await bot.send_audio(chat_id, item_content[1],
                             caption=item_content[2])
    else:
        await bot.send_message(chat_id, item_content[2])


async def backup_dp(user_id=admin_ids[0]):
    try:
        await bot.send_document(user_id, open(f'shops/{bot_id}.db', 'rb'),
                                caption=f'💾Backup\n<code>{datetime.utcnow()}</code>')
    except:
        pass


async def check_sub(user_id):
    if invite_link_id is not None:
        try:
            req = await bot.get_chat_member(invite_link_id, user_id)
            if req.status != 'left':
                return True
            return False
        except:
            return False
    else:
        return True


async def referral_deposit(user_id, amount, lang):
    try:
        ref = cursor.execute('SELECT ref FROM users WHERE id = ?',
                             (user_id,)).fetchone()[0]
        if ref is not None and ref_percent is not None:
            ref_money = int(amount * ref_percent)
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                           (ref_money, ref))
            cursor.execute('UPDATE users SET ref_money = ref_money + ? WHERE id = ?',
                           (ref_money, ref))
            sqlite.commit()
            await bot.send_message(ref, locale[lang]['ref_deposit'].format(
                f'{price_to_human(ref_money)} {currency_code}'))
    except:
        pass


def purchase_info(purchase_id, lang, user=None):
    name, price, amount, buyer_id, description = \
        cursor.execute('SELECT name, price, amount, buyer_id, description '
                       'FROM purchases WHERE id = ?', (purchase_id,)).fetchone()
    if price is None:
        price = locale[lang]['receipt_free']
    else:
        price = price_to_human(price) + ' ' + currency_code
    amount = locale[lang]['receipt_amount'].format(amount)
    if description is None:
        description = ''
    else:
        description = locale[lang]['receipt_description'].format(description)
    buy_time = strftime('%Y-%m-%d %H:%M:%S', gmtime(purchase_id // 100))
    if user is not None:
        user_link = locale[lang]['user_link'].format(user.id, user.full_name)
    else:
        user_link = ''
    text = locale[lang]['receipt'].format(name, price, amount, purchase_id, buy_time, buyer_id, user_link, description)
    return text


def text_to_file(text, name='purchase'):
    file = io.StringIO(text)
    file.name = name + '.txt'
    return file
