# - *- coding: utf- 8 - *-
import asyncio
import json

from aiohttp import ClientConnectorCertificateError
from async_class import AsyncClass

from data.loader import aSession, locale
from keyboards.edit_bot import payment_keyboard
from keyboards.main import keyboard
from utils.api_qiwip2p import QiwiAPIp2p
from utils.utils import update_qiwi, update_qiwi_nickname


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
    async def __ainit__(self, dp, login=None, token=None, secret=None, lang='en'):
        self.login = login
        self.token = token
        self.secret = secret
        self.base_url = "https://edge.qiwi.com/{}/{}/persons/{}/{}"
        self.headers = {"authorization": f"Bearer {self.token}"}
        self.dp = dp
        self.lang = lang

    # Обязательная проверка перед каждым запросом
    async def pre_checker(self):
        user_id = self.dp.chat.id
        status, response = await self.check_account()
        await asyncio.sleep(0.5)
        if status:
            update_qiwi(user_id, self.login, self.token, self.secret)
            await self.get_nickname()
            await self.dp.edit_text(locale[self.lang]['inline_payment_methods'],
                                    reply_markup=payment_keyboard(user_id, self.lang))
            await self.dp.answer(response, reply_markup=keyboard(self.lang, user_id))
        else:
            return False
        return True

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
                    save_balance.append(f"🇺🇸 Долларов: <code>{balance['balance']['amount']}$</code>")

                if "qw_wallet_rub" == balance['alias']:
                    save_balance.append(f"🇷🇺 Рублей: <code>{balance['balance']['amount']}₽</code>")

                if "qw_wallet_eur" == balance['alias']:
                    save_balance.append(f"🇪🇺 Евро: <code>{balance['balance']['amount']}€</code>")

                if "qw_wallet_kzt" == balance['alias']:
                    save_balance.append(f"🇰🇿 Тенге: <code>{balance['balance']['amount']}₸</code>")

            save_balance = "\n".join(save_balance)
            await self.dp.answer(f"<b>🥝 Баланс кошелька <code>{self.login}</code> составляет:</b>\n"
                                 f"{save_balance}")

    # Получение никнейма аккаунта
    async def get_nickname(self):
        status, response, code = await self._request(
            "qw-nicknames",
            "v1",
            "nickname",
        )
        if response['nickname'] is not None:
            return update_qiwi_nickname(self.dp.chat.id, response['nickname'])

    # Проверка аккаунта (логпаса и п2п)
    async def check_account(self):
        status_history, response_history, code_history = await self.check_logpass()
        status_balance, response_balance, code_balance = await self._request(
            "funding-sources",
            "v2",
            "accounts"
        )
        lang = self.lang
        if status_history and status_balance:
            if self.secret is not None:
                status_secret = await self.check_secret()
                if status_secret:
                    return True, locale[lang]['qiwi_successful']
                else:
                    return_message = locale[lang]['qiwi_error_header'] + locale[lang]['qiwi_error_p2p']
            else:
                return True, locale[lang]['qiwi_successful']
        else:
            if 400 in [code_history, code_balance]:
                return_message = locale[lang]['qiwi_error_header'] + locale[lang]['qiwi_error_number']
            elif 401 in [code_history, code_balance]:
                return_message = locale[lang]['qiwi_error_header'] + locale[lang]['qiwi_error_token']
            elif 403 in [code_history, code_balance]:
                return_message = locale[lang]['qiwi_error_header'] + locale[lang]['qiwi_error_permission']
            else:
                return_message = locale[lang]['qiwi_error_header'] + locale[lang]['qiwi_error_custom'].format(
                    code_history, code_balance)

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
