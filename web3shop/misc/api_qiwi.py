# - *- coding: utf- 8 - *-
import asyncio
import json
import time

from aiohttp import ClientConnectorCertificateError
from async_class import AsyncClass
from data.config import qiwi_number, qiwi_nickname, qiwi_token, qiwi_private_key, locale
from keyboards.menu import main_keyboard
from misc.api_qiwip2p import QiwiAPIp2p
from misc.db import lang_user
from misc.utils import send_log

from data.loader import aSession


def ded(get_text: str):
    if get_text is not None:
        split_text = get_text.split("\n")
        if split_text[0] == "": split_text.pop(0)
        if split_text[-1] == "": split_text.pop(-1)
        save_text = []

        for text in split_text:
            while text.startswith(" "):
                text = text[1:]

            save_text.append(text)
        get_text = "\n".join(save_text)

    return get_text


# Апи работы с QIWI
class QiwiAPI(AsyncClass):
    async def __ainit__(self, dp, login=None, token=None, secret=None, add_pass=False,
                        check_pass=False, user_bill_pass=False, user_check_pass=False):
        if login is not None:
            self.login = login
            self.token = token
            self.secret = secret
        else:
            self.login = qiwi_number
            self.token = qiwi_token
            self.secret = qiwi_private_key

        self.base_url = "https://edge.qiwi.com/{}/{}/persons/{}/{}"
        self.headers = {"authorization": f"Bearer {self.token}"}
        self.nickname = qiwi_nickname
        self.user_check_pass = user_check_pass
        self.user_bill_pass = user_bill_pass
        self.check_pass = check_pass
        self.add_pass = add_pass
        self.dp = dp

    # Рассылка админам о нерабочем киви
    @staticmethod
    async def error_wallet():
        await send_log(content=f"<b>❌QIWI Error:</b> QIWI token doesn't work!")

    # Обязательная проверка перед каждым запросом
    async def pre_checker(self):
        if self.login != "None":
            if self.add_pass:
                status, response = await self.check_account()
            else:
                status, response, code = await self.check_logpass()
            await asyncio.sleep(0.5)
            if self.user_bill_pass:
                if not status:
                    await self.error_wallet()
                    raise
                    return False
            elif self.user_check_pass:
                if not status:
                    await self.error_wallet()
                    raise
                    return False
            elif not status:
                if not self.add_pass:
                    await self.error_wallet()
                    raise
                    return False

            return True
        else:
            if self.user_bill_pass:
                lang = await lang_user(self.dp.chat.id)
                await self.dp.delete()
                await self.dp.answer(
                    locale[lang]['method_error'], reply_markup=main_keyboard(self.dp.chat.id))
            await self.error_wallet()
            return False

    # Проверка баланса
    async def get_balance(self):
        response = await self.pre_checker()
        if response:
            status, response, code = await self._request(
                "funding-sources",
                "v2",
                "accounts",
            )
            save_balance = []
            for balance in response['accounts']:
                if "qw_wallet_usd" == balance['alias']:
                    save_balance.append(f"<code>{balance['balance']['amount']}$</code>")

                if "qw_wallet_rub" == balance['alias']:
                    save_balance.append(f"<code>{balance['balance']['amount']}₽</code>")

                if "qw_wallet_eur" == balance['alias']:
                    save_balance.append(f"<code>{balance['balance']['amount']}€</code>")

                if "qw_wallet_kzt" == balance['alias']:
                    save_balance.append(f"<code>{balance['balance']['amount']}₸</code>")

            save_balance = "\n".join(save_balance)
            await self.dp.answer(f'<b>💰The balance of the wallet <code>{self.login}</code> is:\n{save_balance}</b>')

    # Получение никнейма аккаунта
    async def get_nickname(self):
        response = await self.pre_checker()
        if response:
            status, response, code = await self._request(
                "qw-nicknames",
                "v1",
                "nickname",
            )

            if response['nickname'] is None:
                return False, "❗ На аккаунте отсутствует QIWI Никнейм. Установите его в настройках своего кошелька."
            else:
                return True, response['nickname']

        return False, ""

    # Проверка аккаунта (логпаса и п2п)
    async def check_account(self):
        status_history, response_history, code_history = await self.check_logpass()
        status_balance, response_balance, code_balance = await self._request(
            "funding-sources",
            "v2",
            "accounts"
        )

        if status_history and status_balance:
            if self.secret != "None":
                status_secret = await self.check_secret()
                if status_secret:
                    return True, "<b>🥝 QIWI кошелёк был успешно изменён ✅</b>"
                else:
                    return_message = ded(f"""
                                     <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>
                                     ▶ Код ошибки: <code>Неверный приватный ключ</code>
                                     ❕ Указывайте ПРИВАТНЫЙ КЛЮЧ, а не публичный.
                                     Приватный ключ заканчивается на =
                                     """)
            else:
                return True, "<b>🥝 QIWI кошелёк был успешно изменён ✅</b>"
        else:
            if 400 in [code_history, code_balance]:
                return_message = ded(f"""
                                 <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>
                                 ▶ Код ошибки: <code>Номер телефона указан в неверном формате</code>
                                 """)
            elif 401 in [code_history, code_balance]:
                return_message = ded(f"""
                                 <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>
                                 ▶ Код ошибки: <code>Неверный токен или истек срок действия токена API</code>
                                 """)
            elif 403 in [code_history, code_balance]:
                return_message = ded(f"""
                                 <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>
                                 ▶ <code>Ошибка: Нет прав на данный запрос (недостаточно разрешений у токена API)</code>
                                 """)
            elif "CERTIFICATE_VERIFY_FAILED" == code_history:
                return_message = ded(f"""
                                 <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>
                                 ▶ Код ошибки: <code>CERTIFICATE_VERIFY_FAILED certificate verify failed: self signed certificate in certificate chain</code>
                                 ❗ Ваш сервер/дедик/устройство блокирует запросы к QIWI. Отключите антивирус или другие блокирующие ПО.
                                 """)
            else:
                return_message = ded(f"""
                                 <b>🥝 Введённые QIWI данные не прошли проверку ❌</b>\n
                                 ▶ Код ошибки: <code>{code_history}/{code_balance}</code>
                                 """)

        return False, return_message

    # Проверка логпаса киви
    async def check_logpass(self):
        status, response, code = await self._request(
            "payment-history",
            "v2",
            "payments",
            {"rows": 1, "operation": "IN"},
        )

        if status:
            if "data" in response:
                return True, response, code
            else:
                return False, None, code
        else:
            return False, None, code

    # Проверка п2п ключа
    async def check_secret(self):
        try:
            qiwi_p2p = await QiwiAPIp2p(self.dp, self.secret)
            bill_id, bill_url = await qiwi_p2p.bill(3, lifetime=1)
            status = await qiwi_p2p.reject(bill_id=bill_id)
            return True
        except:
            return False

    # Создание платежа
    async def bill_pay(self, get_amount, get_way):
        response = await self.pre_checker()
        if response:
            bill_receipt = str(int(time.time() * 100))
            if get_way == "form":
                qiwi_p2p = await QiwiAPIp2p(self.dp, self.secret)
                bill_id, bill_url = await qiwi_p2p.bill(get_amount, bill_id=bill_receipt, lifetime=60)
                message_args = self.login
            elif get_way == "number":
                bill_url = f"https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={self.login}&amountInteger={get_amount}&amountFraction=0&extra%5B%27comment%27%5D={bill_receipt}&currency=643&blocked%5B0%5D=sum&blocked%5B1%5D=comment&blocked%5B2%5D=account"
                message_args = self.login
            elif get_way == "nickname":
                bill_url = f"https://qiwi.com/payment/form/99999?amountInteger={get_amount}&amountFraction=0&currency=643&extra%5B%27comment%27%5D={bill_receipt}&extra%5B%27account%27%5D={self.nickname}&blocked%5B0%5D=comment&blocked%5B1%5D=account&blocked%5B2%5D=sum&0%5Bextra%5B%27accountType%27%5D%5D=nickname"
                message_args = self.nickname
            return message_args, bill_url, bill_receipt
        return False, False, False

    # Проверка платежа по форме
    async def check_form(self, receipt):
        qiwi_p2p = await QiwiAPIp2p(self.dp, self.secret)
        bill_status, bill_amount = await qiwi_p2p.check(receipt)

        return bill_status, bill_amount

    # Проверка платежа по переводу
    async def check_send(self, receipt):
        response = await self.pre_checker()
        if response:
            status, response, code = await self._request(
                "payment-history",
                "v2",
                "payments",
                {"rows": 30, "operation": "IN"},
            )

            pay_status = False
            pay_amount = 0

            for check_pay in response['data']:
                if str(receipt) == str(check_pay['comment']):
                    if "643" == str(check_pay['sum']['currency']):
                        pay_status = True
                        pay_amount = int(float(check_pay['sum']['amount']))
                    else:
                        return_message = 1
                    break

            if pay_status:
                return_message = 3
            else:
                return_message = 2

            return return_message, pay_amount

        return 4, False

    # Сам запрос
    async def _request(self, action, version, get_way, params=None):
        url = self.base_url.format(action, version, self.login, get_way)

        session = await aSession.get_session()

        try:
            response = await session.get(url, params=params, headers=self.headers, ssl=False)
            return True, json.loads((await response.read()).decode()), response.status
        except ClientConnectorCertificateError:
            return False, None, "CERTIFICATE_VERIFY_FAILED"
        except:
            return False, None, response.status
