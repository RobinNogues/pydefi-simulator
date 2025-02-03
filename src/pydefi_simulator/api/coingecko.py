from dataclasses import dataclass

import requests

from pydefi_simulator.api.config.get_key import get_api_key
from pydefi_simulator.logger import logger
from pydefi_simulator.utils import SingletonMeta


@dataclass
class BaseCoinInfo:
    """Metadata of a coin."""

    id: str
    symbol: str
    name: str
    contract_addresses: dict[str, str]


class CoinGeckoApi(metaclass=SingletonMeta):
    """Simple interface to CoinGecko API."""

    source_name = "CoinGecko"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the CoinGeckoApi. Only one instance exists."""
        self.set_api_key(api_key or get_api_key("coingecko"))
        self._headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": self._api_key,
        }
        self._by_ids: dict[str, BaseCoinInfo] = {}
        self._by_symbols: dict[str, list[BaseCoinInfo]] = {}
        self._platforms: set[str] = set()
        self._set_listed_coins()

    def _set_listed_coins(self) -> None:
        url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
        response = requests.get(url, headers=self._headers, timeout=10)

        for _coin in response.json():
            _coin["contract_addresses"] = _coin.pop("platforms")
            coin = BaseCoinInfo(**_coin)
            self._platforms.update(coin.contract_addresses.keys())
            self._by_ids[coin.id] = coin
            if coin.symbol not in self._by_symbols:
                self._by_symbols[coin.symbol] = [coin]
            else:
                self._by_symbols[coin.symbol].append(coin)

    def get_prices_by_ids(self, coingecko_ids: list[str]) -> dict[str, float]:
        """Return prices for each given coingecko ids."""
        url = "https://api.coingecko.com/api/v3/simple/price"

        batchs = [coingecko_ids[i:i+250] for i in range(0, len(coingecko_ids), 250)]
        result = {}
        for batch in batchs:
            response = requests.get(
                url,
                headers=self._headers,
                params={
                    "vs_currencies": "usd",
                    "ids": ",".join(batch),
                },
                timeout=10,
            )
            result.update(response.json())
        result = {coin_id: price["usd"] for coin_id, price in result.items() if price}
        absent_ids = set(coingecko_ids) - set(result.keys())
        if absent_ids:
            logger.warning(f"No price found for {absent_ids}.")
        return result

    def get_prices_by_symbols(self, symbols: list[str]) -> dict[str, float]:
        """Return prices for each given symbols, choosing the price depending on the market cap
        (currencies can have the same symbol).
        """
        if not symbols:
            return {}
        formatted_symbol_mapping = {symbol.lower(): symbol for symbol in symbols}
        ids = [
            c.id for symbol in formatted_symbol_mapping
            for c in self._by_symbols.get(symbol, [])
        ]
        listed_prices = self.list_prices_by_ids(ids)
        prices: dict[str, float] = {}
        absent_symbols = set(formatted_symbol_mapping.values())
        for price in listed_prices:
            init_symbol = formatted_symbol_mapping[price["symbol"]]
            if not absent_symbols:
                break
            if init_symbol in prices or not price["current_price"]:
                continue
            prices[init_symbol] = price["current_price"]
            absent_symbols.remove(init_symbol)
        if absent_symbols:
            logger.warning(f"No price found for {absent_symbols}.")
        return prices

    def get_price_by_symbol(self, symbol: str) -> float:
        """Return the price of the currency with the given symbol, choosing the price of the
        currency that has the biggest market cap (currencies can have the same symbol).
        """
        formatted_symbol = symbol.lower()
        return self.get_prices_by_symbols([formatted_symbol]).get(formatted_symbol, 0)

    def list_prices_by_ids(self, coingecko_ids: list[str]) -> list[dict]:
        """List prices for each given coingecko ids, sorted by descending market cap."""
        url = "https://api.coingecko.com/api/v3/coins/markets"

        batchs = [coingecko_ids[i:i+250] for i in range(0, len(coingecko_ids), 250)]
        res = []
        for batch in batchs:
            response = requests.get(
                url,
                headers=self._headers,
                params={
                    "vs_currency": "usd",
                    "ids": ",".join(batch),
                    "per_page": "250",  # max authorized
                },
                timeout=10,
            )
            res.extend(response.json())
        return res

    def get_price_by_id(self, coingecko_id: str) -> float:
        """Get the price of a currency with the given coingecko id."""
        return self.get_prices_by_ids([coingecko_id]).get(coingecko_id, 0)

    def set_api_key(self, api_key: str) -> None:
        """Set the API key to use."""
        self._api_key = api_key
