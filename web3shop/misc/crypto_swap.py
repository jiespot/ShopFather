import time

from libs.pycoingecko import CoinGeckoAPI


class CryptoWeb:
    def __init__(self):
        self.updated = 0
        self.rates = {}

    def _update(self, currency: str):
        t = time.time()

        if t - self.updated >= 35 or not self.rates:
            self.updated = t

            cg = CoinGeckoAPI()
            coins = {
                'bitcoin': "BTC",
                'ethereum': "ETH",
                'the-open-network': "TON",
                'tether': "USDT",
                "usd-coin": "USDC",
                "binance-usd": "BUSD"
            }
            ids = list(coins.keys())
            prices = cg.get_price(ids=ids, vs_currencies=currency.lower())
            for long_currency in prices.keys():
                short_currency = coins[long_currency]
                price_rub = prices[long_currency][currency.lower()]
                self.rates[short_currency] = price_rub

    def convert(self, to_asset: str, amount: int, currency: str) -> float:
        self._update(currency)
        price_currency = self.rates[to_asset.upper()]
        return round(amount / price_currency, 8)


swap = CryptoWeb()
