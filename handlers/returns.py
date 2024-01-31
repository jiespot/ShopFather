from aiogram import types
from aiogram.dispatcher import FSMContext, filters

from data.loader import dp, locale
from keyboards.admin import advert_keyboard, admin_keyboard
from keyboards.main import keyboard
from utils.states import GlobalMessage
from utils.utils import lang_user

dp.message_handler(chat_type=types.ChatType.SUPERGROUP)
async def bot_handler(message: types.Message):
    return


@dp.message_handler(chat_type=types.ChatType.GROUP)
async def bot_handler(message: types.Message):
    return


@dp.message_handler(chat_type=types.ChatType.CHANNEL)
async def bot_handler(message: types.Message):
    return


@dp.message_handler(filters.Text(equals=['↩назад', '❌отмена', '↩return', '❌cancel'], ignore_case=True), state='*')
@dp.message_handler(commands=["stop", "cancel", "back"], state='*')
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.storage.get_state(user=message.chat.id)
    lang = lang_user(message.chat.id)
    if current_state == 'GlobalMessage:add':
        await message.answer('You have returned to global message menu', reply_markup=advert_keyboard)
        await GlobalMessage.menu.set()
    elif current_state in ['GlobalMessage:menu', 'BotAdmin:id']:
        await message.answer('You have returned to admin menu', reply_markup=admin_keyboard)
        await state.finish()
    elif current_state in ['BotEdit:add_admin', 'BotEdit:remove_admin']:
        keyb = keyboard(lang, message.chat.id)
        await message.answer(locale[lang]['admins_done'], reply_markup=keyb)
        await state.finish()
    else:
        keyb = keyboard(lang, message.chat.id)
        await message.answer(locale[lang]['return_to_menu'], reply_markup=keyb)
        await state.finish()
