import time

from pycoingecko import CoinGeckoAPI


class CryptoWeb:
    def __init__(self):
        self.updated = 0
        self.rates = {}

    def _update(self):
        t = time.time()

        if t - self.updated >= 60 or not self.rates:
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
            prices = cg.get_price(ids=ids, vs_currencies='rub')

            for long_currency in prices.keys():
                short_currency = coins[long_currency]
                price_rub = prices[long_currency]["rub"]
                self.rates[short_currency] = price_rub

    def convert(self, to_asset: str, rub: int) -> float:
        self._update()
        price_rub = self.rates[to_asset.upper()]
        return round(rub / price_rub, 7)


swap = CryptoWeb()
