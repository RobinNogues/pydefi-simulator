from collections import UserDict
from typing import TYPE_CHECKING, Any, Literal

from pydefi_simulator.logger import logger
from pydefi_simulator.utils.contants import MAX


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency


class WalletItem:
    """The class that represents a wallet item, which is a currency and an amount stored in a
    wallet.
    """

    def __init__(self, currency: "Currency", amount: float) -> None:
        """Initialize the WalletItem.

        Parameters
        ----------
        currency : Currency
            The currency of the wallet item.
        amount : float
            The amount of the currency in the wallet item.

        """
        self._currency = currency
        self._amount = amount

    def __repr__(self) -> str:
        """Return the currency's symbol and the amount.

        Returns
        -------
        str
            The currency's symbol and the amount.

        """
        return f"{self._amount} {self._currency.symbol}"

    @property
    def value(self) -> float:
        """The value of the wallet item, which is the currency's price multiplied by the amount.

        Returns
        -------
        float
            The value of the wallet item.

        """
        return self._currency.price * self._amount

    @property
    def amount(self) -> float:
        """The amount of the wallet item.

        Returns
        -------
        float
            The amount of the wallet item.

        """
        return self._amount

    @property
    def currency(self) -> "Currency":
        """The currency of the wallet item.

        Returns
        -------
        Currency
            The currency of the wallet item.

        """
        return self._currency

    def add(self, amount: float) -> None:
        """Add the given amount to the wallet item.

        Parameters
        ----------
        amount : float
            The amount to add.

        """
        self._amount += amount

    def sub(self, amount: float | Literal["max"]) -> None:
        """Subtract the given amount from the wallet item.

        Parameters
        ----------
        amount : float
            The amount to subtract.

        """
        amount = self._amount if amount == MAX else amount
        if not self.is_subtractable(amount):
            logger.error("Cannot substract more than the amount of the wallet item.")
            return
        self._amount -= amount

    def is_subtractable(self, amount: float) -> bool:
        """Check if the wallet item can be subtracted by the given amount.

        Parameters
        ----------
        amount : float
            The amount to subtract.

        Returns
        -------
        bool
            True if the wallet item can be subtracted by the given amount, False otherwise.

        """
        return self._amount - amount >= 0


class WalletCurrencies(UserDict["Currency", "WalletItem"]):
    """The class that represents a dictionary of wallet items, where the keys are currencies and
    the values are wallet items.
    """

    def __setitem__(self, key: "Currency", value: "WalletItem") -> None:
        """Set the value of the given key to the given value and raise a ValueError if the key is
        already present in the dictionary.

        Parameters
        ----------
        key : Currency
            The currency to set.
        value : WalletItem
            The wallet item to set.
        """
        if key in self.data:
            msg = f"Wallet already contains {key}."
            raise ValueError(msg)
        self.data[key] = value

    def get(self, key: "Currency", default: Any | None = None) -> "WalletItem | Any":
        """Get the wallet item for the given currency if it exists, else return a WalletItem with
        the given currency and 0 amount.

        Parameters
        ----------
        key : Currency
            The currency to get.
        default : Any | None
            The default value to return if the key is not found.

        Returns
        -------
        WalletItem | Any
            The wallet item for the given currency if it exists, else a WalletItem with the given
            currency and 0 amount, or the default value if provided.
        """
        return super().get(key, WalletItem(key, 0) if default is None else default)
