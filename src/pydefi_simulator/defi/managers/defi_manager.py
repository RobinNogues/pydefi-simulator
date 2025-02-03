from typing import TYPE_CHECKING, Literal

from pydefi_simulator.logger import logger
from pydefi_simulator.utils.contants import ALL, MAX


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi.position.defi_position import DefiPosition
    from pydefi_simulator.wallet import Wallet


class DefiManager:
    """The class that manages the lending and borrowing of a customer's position."""

    def __init__(self, position: "DefiPosition") -> None:
        """Initialize the DefiManager.

        Parameters
        ----------
        position : DefiPosition
            The position of the customer.

        """
        self._position = position

    def lend(
            self,
            customer_wallet: "Wallet",
            currency: "Currency",
            amount: float | Literal["max"],
    ) -> None:
        """Lends a currency and removes it from the customer's wallet.

        Parameters
        ----------
        customer_wallet : Wallet
            The customer's wallet.
        currency : Currency
            The currency to lend.
        amount : float
            The amount to lend.

        """
        amount = customer_wallet.get(currency).amount if amount == MAX else amount
        if not self._position.platform.is_lendable(currency):
            logger.error(f"{currency.symbol} cannot be used as collateral.")
            return
        if amount < 0:
            logger.error("Trying to lend a negative amount.")
            return
        if not customer_wallet.is_subtractable(currency, amount):
            logger.error("Trying to supply more than the amount on the main wallet.")
            return
        customer_wallet.send(self._position.lent, currency, amount, log=False)
        logger.info(
            f"Lended {amount} {currency.symbol}, new health ratio: "
            f"{self._position.metrics.get_health_ratio()}.",
        )

    def withdraw(
            self,
            customer_wallet: "Wallet",
            currency: "Currency",
            amount: float | Literal["max"],
    ) -> None:
        """Withdraws a currency and adds it to the customer's wallet.

        Parameters
        ----------
        customer_wallet : Wallet
            The customer's wallet.
        currency : Currency
            The currency to withdraw.
        amount : float | Literal["max"]
            The amount to withdraw. If "max", the maximum amount is withdrawn.

        """
        if not self._position.lent.get(currency).amount:
            logger.error(f"Cannot withdraw, no lent {currency.symbol}.")
            return
        withdrawable = self._position.metrics.get_withdrawable_amount(currency)
        amount = withdrawable if amount == MAX else amount
        if amount < 0:
            logger.error("Trying to withdraw a negative amount.")
            return
        if not self._position.lent.is_subtractable(currency, amount):
            logger.error("Trying to withdraw more than lent.")
            return
        if withdrawable < amount:
            logger.error("Cannot withdraw, you would have a negative health ratio.")
            return
        self._position.lent.send(customer_wallet, currency, amount, log=False)
        logger.info(
            f"Withdrawed {amount} {currency.symbol}, new health ratio: "
            f"{self._position.metrics.get_health_ratio()}.",
        )
        return

    def borrow(
            self,
            customer_wallet: "Wallet",
            currency: "Currency",
            amount: float | Literal["max"],
            collateral: list["Currency"] | Literal["all"] = ALL,
    ) -> None:
        """Borrows a currency and adds it to the customer's wallet.

        Parameters
        ----------
        customer_wallet : Wallet
            The customer's wallet.
        currency : Currency
            The currency to borrow.
        amount : float | Literal["max"]
            The amount to borrow. If "max", the maximum amount is borrowed.
        collateral : list[Currency] | Literal["all"]
            The list of lent currencies to use as collateral, or "all" to use all lent currencies,
            default "all".

        """
        if not self._position.platform.is_borrowable(currency):
            logger.error(f"{currency.symbol} is not borrowable on the platform.")
            return
        borrowable = self._position.metrics.get_borrowable(currency, collateral)
        amount = borrowable if amount == MAX else amount
        if amount < 0:
            logger.error("Trying to borrow a negative amount.")
            return
        if amount > borrowable:
            logger.error(f"Not enough collateral to borrow, {borrowable} can be borrowed.")
            return
        self._position.borrowed.add(currency, amount)
        customer_wallet.add(currency, amount)
        logger.info(
            f"Borrowed {amount} {currency.symbol}, new health ratio: "
            f"{self._position.metrics.get_health_ratio()}.",
        )

    def repay(
            self,
            customer_wallet: "Wallet",
            currency: "Currency",
            amount: float | Literal["max"],
    ) -> None:
        """Repays a currency and removes it from the customer's wallet.

        Parameters
        ----------
        customer_wallet : Wallet
            The customer's wallet.
        currency : Currency
            The currency to repay.
        amount : float | Literal["max"]
            The amount to repay.

        """
        if not self._position.borrowed.get(currency).amount:
            logger.error(f"Cannot repay, no borrowed {currency.symbol}.")
            return
        amount = (
            self._position.metrics.get_repayable_amount(customer_wallet, currency)
            if amount == MAX
            else amount
        )
        if amount < 0:
            logger.error("Trying to repay a negative amount.")
            return
        if not self._position.borrowed.is_subtractable(currency, amount):
            logger.error("Trying to repay more than the amount of borrowed currency.")
            return
        if not customer_wallet.is_subtractable(currency, amount):
            logger.error(f"Not enough {currency.symbol} on the main wallet.")
            return
        self._position.borrowed.sub(currency, amount)
        customer_wallet.sub(currency, amount)
        logger.info(
            f"Repaid {amount} {currency.symbol}, new health ratio: "
            f"{self._position.metrics.get_health_ratio()}.",
        )
