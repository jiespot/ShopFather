from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import FSMContext

from data.loader import dp, locale
from keyboards.keyboards import cancel_keyboard, skip_keyboard
from utils.api_qiwi import QiwiAPI
from utils.states import QiwiAdd
from utils.utils import lang_user

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


@dp.message_handler(state=QiwiAdd.number)
async def add_qiwi_number(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    if message.text.startswith("+"):
        await state.update_data(number=message.text)
        await QiwiAdd.token.set()
        await message.answer(locale[lang]['qiwi_add_token'], reply_markup=cancel_keyboard(lang),
                             disable_web_page_preview=True)
    else:
        await message.answer(locale[lang]['qiwi_edit_error'])


@dp.message_handler(state=QiwiAdd.token)
async def add_qiwi_number(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    await state.update_data(token=message.text)
    await QiwiAdd.private_key.set()
    await message.answer(locale[lang]['qiwi_add_p2p'], reply_markup=skip_keyboard(lang),
                         disable_web_page_preview=True)
    await message.delete()


@dp.message_handler(state=QiwiAdd.private_key)
async def add_qiwi_number(message: types.Message, state: FSMContext):
    lang = lang_user(message.chat.id)
    async with state.proxy() as data:
        number = data['number']
        token = data['token']
    if message.text in ['⏭Пропустить', '⏭Skip']:
        private_key = None
    else:
        private_key = message.text

    await state.finish()
    cache_message = await message.answer(locale[lang]['qiwi_check'])
    await sleep(0.5)
    await (await QiwiAPI(cache_message, number, token, private_key, lang)).pre_checker()
    await message.delete()
