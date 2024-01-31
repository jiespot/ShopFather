import sqlite3
sqlite = sqlite3.connect(f'shops/dev.db')
cursor = sqlite.cursor()


def categories_user_test():
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





print(categories_user_test())
