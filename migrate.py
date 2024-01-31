import sqlite3

sqlite = sqlite3.connect('sqlite.db')
cursor = sqlite.cursor()

ids = cursor.execute('SELECT id FROM bots').fetchall()

for x in ids:
    id = x[0]
    temp_sql = sqlite3.connect(f'web3shop/shops/{id}.db')
    curs = temp_sql.cursor()
    curs.execute('ALTER TABLE categories ADD one_row INTEGER;')
    curs.execute('UPDATE categories SET one_row = 0;')
    temp_sql.commit()
