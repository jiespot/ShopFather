import sqlite3

def update():
    print('Updating tables...')
    db = sqlite3.connect('sqlite.db')

    try:
        db.execute('ALTER TABLE payments ADD COLUMN cryptobot INTEGER;')
        db.commit()
        print('Updated payments')
    except:
        print('paymets already updated')

    try:
        db.execute('ALTER TABLE bots ADD COLUMN cryptobot TEXT;')
        db.commit()
        print('Updated bots')
    except:
        print('bots already updated #1')

    try:
        db.execute('ALTER TABLE bots ADD COLUMN can_user_transfer BOOL DEFAULT 0;')
        db.commit()
        print('Updated bots (added "can_user_transfer")')
    except:
        print('bots already updated #2')

    try:
        db.execute('ALTER TABLE bots ADD COLUMN terms BOOL DEFAULT 0;')
        db.commit()
        print('Updated bots (added "terms")')
    except:
        print('bots already updated #3')

    try:
        db.execute('ALTER TABLE messages ADD COLUMN terms_ru TEXT')
        db.commit()
        print('Updated messages (added "terms_ru")')
    except:
        print('messages already updated #1')

    try:
        db.execute('ALTER TABLE messages ADD COLUMN terms_en TEXT')
        db.commit()
        print('Updated messages (added "terms_en")')
    except:
        print('messages already updated #2')




if __name__ == '__main__':
    update()