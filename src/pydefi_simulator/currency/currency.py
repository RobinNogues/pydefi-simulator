from typing import ClassVar

from pydefi_simulator.api import CoinGeckoApi
from pydefi_simulator.price import CryptoConverter


class MetaCurrency(type):
    """Metaclass for the Currency class."""

    _registered_currencies: ClassVar[dict[str, "Currency"]] = {}

    def __call__(cls, symbol: str, *args, **kwargs) -> "Currency":
        """Create a new instance of the Currency class. If the symbol is already registered,
        return the existing instance.
        """
        symbol = symbol.upper().strip()
        if symbol in cls._registered_currencies:
            return cls._registered_currencies[symbol]
        instance = super().__call__(symbol, *args, **kwargs)
        cls._registered_currencies[symbol] = instance
        return instance


class Currency(metaclass=MetaCurrency):
    """The class that represents a cryptocurrency."""

    _price_api = CoinGeckoApi()

    def __init__(
            self,
            symbol: str,
            custom_price: float | None = None,
            apy: float = 0,
            related_to: "Currency | None" = None,
    ) -> None:
        """Initialize a cryptocurrency.

        Parameters
        ----------
        symbol : str
            The symbol of the cryptocurrency (e.g. ETH, USDT, etc.).
        custom_price : float | None, optional
            The custom price of the cryptocurrency, by default None.
        apy : float, optional
            The APY of the cryptocurrency, by default 0.
        related_to : Currency | None, optional
            The currency related to the cryptocurrency (e.g. ETH for WSTETH). This is a one-way
            relation, by default None.

        """
        self._price: float | None
        self._symbol = symbol.upper()
        self.set_custom_price(custom_price)
        self.set_apy(apy)
        self.set_currency_relation(related_to)

    def __repr__(self) -> str:
        """Return the currency's symbol."""
        return self._symbol

    @property
    def price(self) -> float:
        """Return the currency's price. If a custom price is set, return the custom price. Else,
        fetch the price from the price finder and return it.
        """
        if self._price is not None:
            return self._price
        self._price = self._price_api.get_price_by_symbol(self._symbol)
        return self._price

    @property
    def symbol(self) -> str:
        """The currency's symbol."""
        return self._symbol

    @property
    def apy(self) -> float:
        """The currency's APY (e.g 3 for 3%)."""
        return self._apy or 0

    @property
    def related_to(self) -> "Currency | None":
        """The currency's relation to another currency (e.g ETH for WSTETH)."""
        return self._related_to

    def set_custom_price(self, price: float | None) -> None:
        """Set the currency's custom price."""
        self._price = price

    def set_apy(self, apy: float) -> None:
        """Set the currency's APY (e.g 3 for 3%)."""
        self._apy = apy

    def set_currency_relation(self, currency: "Currency | None") -> None:
        """Set the currency's relation to another currency (e.g. ETH for WSTETH)."""
        self._related_to = currency

    def reset_price(self) -> None:
        """Reset the currency's custom price."""
        self._price = None

    def conversion_ratio(self, other: "Currency") -> float:
        """Return the conversion ratio between the two currencies. For example, if the conversion
        if BTC/USD (self) is 10,000 and ETH/USD (other) is 4,000, the conversion ratio BTC/ETH is
        2.5.

        Parameters
        ----------
        other : Currency
            The currency to compare the conversion ratio with.

        Returns
        -------
        float
            The conversion ratio self/other.

        """
        return CryptoConverter.conversion_ratio(self, other)

    def convert(self, other: "Currency", amount: float) -> float:
        """Convert the given amount from the current currency to the other currency.

        Parameters
        ----------
        other : Currency
            The currency to convert to.
        amount : float
            The amount to convert.

        Returns
        -------
        float
            The converted amount.

        """
        return CryptoConverter.convert(self, other, amount)

    @staticmethod
    def get_all_currencies() -> dict[str, "Currency"]:
        """Return all registered currencies."""
        return Currency._registered_currencies

    @staticmethod
    def get_currency(symbol: str) -> "Currency | None":
        """Return the currency with the given symbol."""
        return Currency._registered_currencies.get(symbol.upper())

    @staticmethod
    def reset_all_prices() -> None:
        """Reset all registered currencies' prices."""
        for currency in Currency._registered_currencies.values():
            currency.reset_price()
