import logging
import sqlite3


def create_tables(sqlite):
    cursor = sqlite.cursor()
    cursor.execute('''CREATE TABLE "categories" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT,
	"hide"	INTEGER,
	"one_row"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
)''')

    cursor.execute('''CREATE TABLE  "sub_categories" (
    "id" INTEGER NOT NULL UNIQUE,
    "name" TEXT,
    "category" INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT)
    )''')

    cursor.execute('''CREATE TABLE "items" (
	"id"	INTEGER NOT NULL UNIQUE,
	"category"	INTEGER,
	"sub_category" INTEGER,
	"name"	TEXT,
	"description"	TEXT,
	"price"	INTEGER,
	"amount"	INTEGER,
	"type"	INTEGER,
	"hide"	INTEGER,
	"media_type"	INTEGER,
	"file_id"	TEXT,
	"text"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
    cursor.execute('''CREATE TABLE "purchases" (
	"id"	INTEGER,
	"item_id"	INTEGER,
	"buyer_id"	INTEGER,
	"amount"	INTEGER,
	"strings"	TEXT,
	"media_type"	INTEGER,
	"file_id"	TEXT,
	"text"	TEXT,
	"name"	TEXT,
	"description"	TEXT,
	"price"	INTEGER
);''')
    cursor.execute('''CREATE TABLE "strings" (
	"id"	INTEGER NOT NULL UNIQUE,
	"item_id"	INTEGER,
	"data"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
    cursor.execute('''CREATE TABLE "wallets" (
	"id"	INTEGER,
	"type"	TEXT,
	"pub"	TEXT,
	"priv"	TEXT,
	"sleep_time"	INTEGER
);''')
    cursor.execute('''CREATE TABLE "users" (
	"id"	INTEGER UNIQUE,
	"username" TEXT DEFAULT "",
	"balance"	INTEGER,
	"lang"	TEXT,
	"join_time"	INTEGER,
	"ref"	INTEGER,
	"referrals"	INTEGER,
	"ref_money"	INTEGER,
	"discount_amount"	INTEGER,
	"discount"	INTEGER,
	"accepted_terms" BOOL DEFAULT 0
)''')
    cursor.execute('''CREATE TABLE "dep_qiwi" (
	"id"	integer NOT NULL UNIQUE,
	"user_id"	integer,
	"usd"	INTEGER,
	"rub"	INTEGER,
	"receipt"	integer,
	"way"	text,
	"time"	integer,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
    cursor.execute('''CREATE TABLE "promo" (
	"id"	INTEGER NOT NULL UNIQUE,
	"code"	TEXT,
	"count"	INTEGER,
	"type"	INTEGER,
	"percent"	INTEGER,
	"amount"	INTEGER,
	"item_id"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
)''')
    cursor.execute('''CREATE TABLE "promo_activations" (
	"id"	INTEGER,
	"user_id"	INTEGER,
	"promo_id"	INTEGER,
	"code"	TEXT)
''')
    cursor.execute('CREATE TABLE IF NOT EXISTS "dep_cbot"('
                   '"id"	integer NOT NULL UNIQUE,'
                   '"user_id"	integer,'
                   '"amount" INTEGER,'
                   '"bill_id" TEXT,'
                   '"time" integer,'
                   'PRIMARY KEY("id" AUTOINCREMENT));')
    sqlite.commit()


def sqlite_init(db_name):
    try:
        sqlite = sqlite3.connect(db_name, timeout=20)
        logging.info('SQLite connected')
        return sqlite
    except sqlite3.Error as error:
        logging.error('Error while connecting to SQLite', error)
        return exit()


def convert_prices(db_name, rate):
    temp_sqlite = sqlite3.connect(db_name, timeout=20)
    temp_cursor = temp_sqlite.cursor()
    items = temp_cursor.execute('SELECT id, price FROM items').fetchall()
    for item in items:
        temp_cursor.execute('UPDATE items SET price = ? WHERE id = ?', (int(item[1] * rate), item[0]))
    promo = temp_cursor.execute('SELECT id, amount FROM promo WHERE type = 2').fetchall()
    for promo_item in promo:
        temp_cursor.execute('UPDATE promo SET amount = ? WHERE id = ?', (int(promo_item[1] * rate), promo_item[0]))
    purchases = temp_cursor.execute('SELECT id, price FROM purchases').fetchall()
    for purchase in purchases:
        temp_cursor.execute('UPDATE purchases SET price = ? WHERE id = ?', (int(purchase[1] * rate), purchase[0]))
    users = temp_cursor.execute('SELECT id, balance, ref_money FROM users').fetchall()
    for user in users:
        temp_cursor.execute('UPDATE users SET balance = ?, ref_money = ? WHERE id = ?',
                            (int(user[1] * rate), int(user[2] * rate), user[0]))
    temp_sqlite.commit()
