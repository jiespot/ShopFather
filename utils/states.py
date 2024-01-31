from aiogram.dispatcher.filters.state import StatesGroup, State


class BotAdmin(StatesGroup):
    id = State()


class GlobalMessage(StatesGroup):
    menu = State()
    add = State()


class BotSetup(StatesGroup):
    token = State()


class BotEdit(StatesGroup):
    token = State()
    bnb_wallet = State()
    cryptobot = State()
    yookassa = State()
    add_admin = State()
    lang = State()
    currency = State()
    currency_convert = State()
    invite_id = State()
    invite_link = State()
    add_admin = State()
    remove_admin = State()
    edit_message = State()
    referral = State()


class QiwiAdd(StatesGroup):
    number = State()
    token = State()
    private_key = State()
