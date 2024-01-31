from aiogram import types

from data.loader import dp, locale, cursor, sqlite
from keyboards.edit_bot import edit_admin_keyboard
from keyboards.keyboards import cancel_keyboard
from utils.states import BotEdit
from utils.utils import lang_user, text_to_file, bot_info

from aiogram.types import ChatType, Message

@dp.message_handler(chat_type=ChatType.SUPERGROUP)
async def bot_handler(message: Message):
    return


@dp.message_handler(chat_type=ChatType.GROUP)
async def bot_handler(message: Message):
    return


@dp.message_handler(chat_type=ChatType.CHANNEL)
async def bot_handler(message: Message):
    return


@dp.callback_query_handler(lambda call: call.data.startswith('admin/'))
async def edit_admin(call: types.CallbackQuery):
    data = call.data.split('/')[1]
    user_id = call.from_user.id
    lang = lang_user(user_id)
    if data == 'add':
        await call.message.answer(locale[lang]['add_admin'], reply_markup=cancel_keyboard(lang))
        await BotEdit.add_admin.set()
    elif data == 'remove':
        await call.message.answer(locale[lang]['remove_admin'], reply_markup=cancel_keyboard(lang))
        await BotEdit.remove_admin.set()
    elif data == 'list':
        req = cursor.execute('SELECT admin_id FROM admins WHERE id = ?', (user_id,)).fetchall()
        if bool(req) is False:
            return await call.answer()
        admins = ''
        for admin in req:
            admins += f'{admin[0]}\n'
        await call.message.answer_document(text_to_file(admins, 'admins'))
    elif data == 'clear':
        admins = cursor.execute('SELECT COUNT(*) FROM admins WHERE id = ?', (user_id,)).fetchone()[0]
        cursor.execute('DELETE FROM admins WHERE id = ?', (user_id,))
        sqlite.commit()
        if admins != 0:
            await call.message.edit_text(bot_info(call.from_user.id, lang), reply_markup=edit_admin_keyboard(lang))
        await call.message.answer(locale[lang]['clear_admins'])
    await call.answer()


@dp.message_handler(state=BotEdit.add_admin)
async def add_admin(message: types.Message):
    user_id = message.chat.id
    lang = lang_user(user_id)
    if message.text.isdigit() is False:
        return await message.answer(locale[lang]['not_id'])
    admin_id = int(message.text)
    req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM admins WHERE id = ? AND admin_id = ?)',
                              (user_id, admin_id)).fetchone()[0])
    if req:
        return await message.answer(locale[lang]['already_admin'])
    cursor.execute('INSERT INTO admins VALUES (?, ?)', (user_id, admin_id))
    sqlite.commit()
    await message.answer(locale[lang]['add_admin_ok'])


@dp.message_handler(state=BotEdit.remove_admin)
async def remove_admin(message: types.Message):
    user_id = message.chat.id
    lang = lang_user(user_id)
    if message.text.isdigit() is False:
        return await message.answer(locale[lang]['not_id'])
    admin_id = int(message.text)
    req = bool(cursor.execute('SELECT EXISTS(SELECT 1 FROM admins WHERE id = ? AND admin_id = ?)',
                              (user_id, admin_id)).fetchone()[0])
    if req is False:
        return await message.answer(locale[lang]['not_admin'])
    cursor.execute('DELETE FROM admins WHERE id = ? AND admin_id = ?', (user_id, admin_id))
    sqlite.commit()
    await message.answer(locale[lang]['remove_admin_ok'])
