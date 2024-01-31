from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from data.config import admin_ids, lang_list, admin_ids_global
from misc.utils import tCurrent, send_log

from data.loader import sqlite, w3, cursor, price_sql


async def new_user(user, ref):
    check_ref = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE id = ?)', (ref,)).fetchone()[0])
    if not check_ref:
        ref = None
    else:
        cursor.execute('UPDATE users SET referrals = referrals + 1 WHERE id = ?', (ref,))
    cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (user.id, user.username, 0, user.language_code, tCurrent(), ref, 0, 0, 0, 0, False))
    acc_gen = w3.eth.account.create()
    cursor.execute('INSERT INTO wallets VALUES (?, ?, ?, ?, ?)',
                   (user.id, 'bsc', acc_gen._address, acc_gen._private_key, 0))
    sqlite.commit()
    if user.id not in admin_ids_global:
        await send_log(user, '<b>🤖Started bot</b>')


def user_exist(user_id):
    req = cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE id = ?)',
                         (user_id,)).fetchone()[0]
    return bool(req)


def user_accepter_terms(user_id):
    if user_exist(user_id):
        req = cursor.execute('SELECT accepted_terms FROM users WHERE id = ?',
                             (user_id,)).fetchone()[0]
        return bool(req)
    else:
        return False


def agree_user(user_id):
    cursor.execute('UPDATE users SET accepted_terms = ? WHERE id = ?', [True, user_id])
    sqlite.commit()

class IsAdmin(BoundFilter):
    async def check(self, message: types.Message):
        if message.from_user.id in admin_ids:
            return True
        else:
            return False

class IsSuperAdmin(BoundFilter):
    async def check(self, message: types.Message):
        if message.from_user.id in admin_ids_global:
            return True
        else:
            return False


def categories_user():
    req = cursor.execute('SELECT id, name, one_row FROM categories WHERE hide = 0').fetchall()
    result = []
    temp = []
    for num, x in enumerate(req):
        if x[2] == 1:
            if temp:
                result.append(temp)
            result.append([x])
            temp = []
        elif len(temp) == 1:
            temp.append(x)
            result.append(temp)
            temp = []
        else:
            temp.append(x)
    if temp:
        result.append(temp)
    return result

def get_subcategories(category_id: int):
    req = cursor.execute('SELECT * FROM sub_categories WHERE category = ?', (category_id,)).fetchall()
    return req

def get_subcategory(subcategory_id: int):
    req = cursor.execute('SELECT * FROM sub_categories WHERE id = ?', (subcategory_id,)).fetchone()
    return req

def get_category(category_id: int):
    req = cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    return req

def add_subcategory(subcategory_name, category_id):
    cursor.execute(f'INSERT INTO sub_categories VALUES (?, ?, ?)',
                   (None, subcategory_name, category_id))
    sqlite.commit()

def categories_admin():
    req = cursor.execute('SELECT id, name, one_row, hide FROM categories').fetchall()
    result = []
    temp = []
    for num, x in enumerate(req):
        if x[2] == 1:
            if temp:
                result.append(temp)
            result.append([x])
            temp = []
        elif len(temp) == 1:
            temp.append(x)
            result.append(temp)
            temp = []
        else:
            temp.append(x)
    if temp:
        result.append(temp)
    return result


def promo_admin():
    req = cursor.execute('SELECT id, code, type, count FROM promo').fetchall()
    return [req[x:x + 2] for x in range(0, len(req), 2)]


def items_user(category_id):
    req = cursor.execute('SELECT id, sub_category, name, hide, price, amount, type FROM items WHERE hide = 0 and category = ?',
                         (category_id,)).fetchall()

    return [req[x:x + 5] for x in range(0, len(req), 5)]


def subcategory_items_user(subcategory_id):
    req = cursor.execute('SELECT id, sub_category, name, hide, price, amount, type FROM items WHERE hide = 0 and sub_category = ?',
                         (subcategory_id,)).fetchall()

    return [req[x:x + 5] for x in range(0, len(req), 5)]


def items_admin():
    req = cursor.execute('SELECT id, name, hide, price, amount, type FROM items').fetchall()
    return [req[x:x + 5] for x in range(0, len(req), 5)]


def get_price(symbol):
    req = price_sql.cursor().execute('SELECT price FROM prices WHERE symbol = ?',
                                     (symbol,)).fetchone()
    return req[0]


def lang_user(user_id):
    lang_req = cursor.execute("SELECT lang FROM users WHERE id = ?",
                              (user_id,)).fetchone()[0]
    if lang_req not in lang_list:
        lang = lang_list[0]
    else:
        lang = lang_req
    return lang
