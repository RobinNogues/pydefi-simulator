from typing import TYPE_CHECKING, Literal

from pydefi_simulator.logger import logger
from pydefi_simulator.price import CryptoConverter
from pydefi_simulator.utils.contants import MAX

from .wallet_item import WalletItem


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency

    from .wallet import Wallet, WalletCurrencies


class WalletManager:
    """The class that can do operations on a wallet."""

    def __init__(self, currencies: "WalletCurrencies") -> None:
        """Initialize the WalletManager.

        Parameters
        ----------
        currencies : WalletCurrencies
            The wallet currencies to use.

        """
        self._currencies = currencies

    def add(
            self,
            currency: "Currency",
            amount: float,
    ) -> None:
        """Add the given amount of the given currency to the wallet.

        Parameters
        ----------
        currency : Currency
            The currency to add.
        amount : float
            The amount to add.

        """
        if currency not in self._currencies:
            self._currencies[currency] = WalletItem(currency, amount)
        else:
            self._currencies[currency].add(amount)

    def sub(
            self,
            currency: "Currency",
            amount: float | Literal["max"],
    ) -> None:
        """Subtract the given amount of the given currency from the wallet.

        Parameters
        ----------
        currency : Currency
            The currency to subtract.
        amount : float
            The amount to subtract.

        """
        self._currencies.get(currency).sub(amount)

    def send(
            self,
            dest: "Wallet",
            currency: "Currency",
            amount: float | Literal["max"],
            log: bool = True,
    ) -> None:
        """Send the given amount of the given currency to the given wallet.

        Parameters
        ----------
        dest : Wallet
            The wallet to send the currency to.
        currency : Currency
            The currency to send.
        amount : float
            The amount to send.
        log : bool, optional
            Log the action, by default True.

        """
        amount = self._currencies.get(currency).amount if amount == MAX else amount
        if not self._currencies.get(currency).is_subtractable(amount):
            if log:
                logger.error("Not enough funds on the wallet.")
            return
        self.sub(currency, amount)
        dest.add(currency, amount)
        if log:
            logger.info(f"Sent {amount} {currency.symbol} to {dest.address}.")

    def swap(
            self,
            from_currency: "Currency",
            to_currency: "Currency",
            amount: float | Literal["max"],
    ) -> None:
        """Swap the given amount of the given currency for another currency.

        Parameters
        ----------
        from_currency : Currency
            The currency to swap from.
        to_currency : Currency
            The currency to swap to.
        amount : float
            The amount to swap.

        Returns
        -------
        bool
            True if the swap was successful, False otherwise.

        """
        amount = self._currencies.get(from_currency).amount if amount == MAX else amount
        if not self._currencies.get(from_currency).is_subtractable(amount):
            logger.error(f"Wallet does not contain enough {from_currency}.")
            return

        converted_amount = CryptoConverter.convert(from_currency, to_currency, amount)
        self._currencies[from_currency].sub(amount)
        self.add(to_currency, converted_amount)
        logger.info(
            f"Swapped {amount} {from_currency} for {converted_amount} {to_currency}",
        )
