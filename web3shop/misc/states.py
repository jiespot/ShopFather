from aiogram.dispatcher.filters.state import State, StatesGroup


# States
class GlobalMessage(StatesGroup):
    menu = State()
    add = State()

class CBot_Deposit(StatesGroup):
    amount = State()

class BalanceEditor(StatesGroup):
    id = State()
    change = State()


class ShopItemAdd(StatesGroup):
    start = State()
    category = State()
    sub_category=State()
    name = State()
    description = State()
    type = State()
    string = State()
    check = State()
    file = State()
    amount = State()
    price = State()


class ShopItemEdit(StatesGroup):
    category = State()
    name = State()
    description = State()
    type = State()
    string = State()
    check = State()
    file = State()
    amount = State()
    price = State()


class ShopCategoryAdd(StatesGroup):
    name = State()

class ShopSubCategoryAdd(StatesGroup):
    name = State()

class ShopCategoryEdit(StatesGroup):
    name = State()

class ShopSubCategoryEdit(StatesGroup):
    name = State()

class ShopPromoAdd(StatesGroup):
    type = State()
    percent = State()
    amount = State()
    count = State()
    code = State()


class ShopPromoEdit(StatesGroup):
    count = State()


class QiwiDeposit(StatesGroup):
    amount = State()


class YooDeposit(StatesGroup):
    amount = State()


class Promo(StatesGroup):
    promo = State()
    promo_discount = State()


class BuyMany(StatesGroup):
    amount = State()
