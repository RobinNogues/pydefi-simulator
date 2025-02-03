from collections.abc import Iterator
from typing import TYPE_CHECKING

from pydefi_simulator.utils import random_eth_address

from .manager import WalletManager
from .wallet_item import WalletCurrencies, WalletItem


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency


class Wallet:
    """The class that represents a wallet."""

    def __init__(self, public_address: str | None = None) -> None:
        """Initialize the Wallet. If no public address is given, a random one is generated."""
        self._currencies = WalletCurrencies()
        self._address = public_address or random_eth_address()
        self._manager = WalletManager(self._currencies)

    def __repr__(self) -> str:
        """Return a string representation of the wallet."""
        return f"Wallet({self._address[:4]}...{self._address[-4:]})"

    @property
    def address(self) -> str:
        """The address of the wallet."""
        return self._address

    @property
    def content(self) -> list["WalletItem"]:
        """The list of wallet items in the wallet."""
        return [c for c in self._currencies.values() if c.amount]

    @property
    def currencies(self) -> list["Currency"]:
        """The list of currencies in the wallet."""
        return [item.currency for item in self.content if item.amount]

    @property
    def value(self) -> float:
        """The value of the wallet, which is the sum of the value of the stored currencies."""
        return sum(item.value for item in self.content)

    def __iter__(self) -> Iterator["WalletItem"]:
        """Iterate over the wallet's items."""
        yield from self.content

    def __getitem__(self, item: "Currency") -> WalletItem:
        """Get the wallet's item for the given currency if it exists, else raise KeyError."""
        return self._currencies[item]

    def get(self, item: "Currency") -> WalletItem:
        """Get the wallet's item for the given currency if it exists, else return a WalletItem with
        the given currency and 0 amount.
        """
        return self._currencies.get(item)

    def send(self, to: "Wallet", currency: "Currency", amount: float, log: bool = True) -> None:
        """Send the given amount of the given currency to the given wallet."""
        self._manager.send(to, currency, amount, log)

    def add(self, currency: "Currency", amount: float) -> None:
        """Add the given amount of the given currency to the wallet."""
        self._manager.add(currency, amount)

    def sub(self, currency: "Currency", amount: float) -> None:
        """Subtract the given amount of the given currency from the wallet."""
        self._manager.sub(currency, amount)

    def is_subtractable(self, currency: "Currency", amount: float) -> bool:
        """Check if the wallet can be subtracted by the given amount of the given currency.

        Parameters
        ----------
        currency : Currency
            The currency to subtract.
        amount : float
            The amount to subtract.

        Returns
        -------
        bool
            True if the wallet can be subtracted by the given amount of the given currency,
            False otherwise.

        """
        return self._currencies.get(currency).is_subtractable(amount)

    def swap(
            self,
            from_currency: "Currency",
            to_currency: "Currency",
            amount: float,
    ) -> None:
        """Swap the given amount of the given currency for another currency."""
        self._manager.swap(from_currency, to_currency, amount)
