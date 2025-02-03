from pydefi_simulator.api import CoinGeckoApi

from .currency import Currency


class CurrencyFactory:
    """The factory class for the Currency class."""

    price_api = CoinGeckoApi()

    def create_multiple_currencies(self, *currencies_kwargs) -> dict[str, "Currency"]:
        """Create several currencies at once, to avoid calling the price API multiple times.

        Parameters
        ----------
        *currencies_kwargs : list[dict]
            Keyword arguments to pass to the Currency class.

        Returns
        -------
        dict[str, Currency]
            A dictionary of the created currencies.

        """
        unkown_currencies = {}
        currencies = {}
        for currency_kwargs in currencies_kwargs:
            currency = Currency.get_currency(currency_kwargs["symbol"])
            if currency:
                currencies[currency_kwargs["symbol"]] = currency
            else:
                unkown_currencies[currency_kwargs["symbol"]] = currency_kwargs
        prices = self.price_api.get_prices_by_symbols(list(unkown_currencies.keys()))
        for currency_symbol, currency_price in prices.items():
            currency_kwargs = unkown_currencies[currency_symbol]
            currency_kwargs["custom_price"] = currency_price
            currencies[currency_symbol] = Currency(**currency_kwargs)
        return currencies
