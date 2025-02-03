from typing import TYPE_CHECKING, Literal

from pydefi_simulator.utils.contants import ALL
from pydefi_simulator.wallet import Wallet


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi.position.defi_position import DefiPosition


class BorrowingMetrics:
    """The class that computes the borrowing metrics of a position."""

    def __init__(self, position: "DefiPosition") -> None:
        """Initialize the BorrowingMetrics.

        Parameters
        ----------
        position : DefiPosition
            The position to compute the metrics for.

        """
        self._position = position

    def get_borrowed_value(self, currency: "Currency | Literal['all']" = ALL) -> float:
        """Returns the value of a borrowed currency or the total value of the borrowed
        currencies.
        """
        return (
            self._position.borrowed.value
            if currency == ALL
            else self._position.borrowed.get(currency).value
        )

    def get_borrowed_amount(self, currency: "Currency") -> float:
        """Returns the amount of borrowed currency."""
        return self._position.borrowed.get(currency).amount

    def get_borrow_apy(self, considering_currency_apy: bool = False) -> float:
        """Returns the borrow APY of the given position. The currencies APY can be considered."""
        borrowed_value = self._position.borrowed.value
        if not borrowed_value:
            return 0

        platform = self._position.platform
        weighted_sum_debt_apy = sum(
            (
                platform[item.currency].total_borrow_apy * item.value
                - (item.currency.apy * item.value if considering_currency_apy else 0)
            )
            for item in self._position.borrowed
        )
        return weighted_sum_debt_apy / borrowed_value

    def get_borrowable(
            self,
            currency: "Currency",
            collateral: list["Currency"] | Literal["all"] = ALL,
    ) -> float:
        """Returns how much of the given currency can be borrowed. The list of lent currencies to
        use as collateral can be provided. If "all" is provided, all lent currencies are used as
        collateral.
        """
        final_position = self._position
        if collateral != ALL:
            tmp_lending_wallet = Wallet()
            for _currency in collateral:
                tmp_lending_wallet.add(_currency, self._position.lent.get(_currency).amount)

            from pydefi_simulator.defi.position.defi_position import DefiPosition
            final_position = DefiPosition(
                self._position.platform,
                tmp_lending_wallet,
                self._position.borrowed,
            )
        borrowed_value = self.get_borrowed_value()
        lent_value = final_position.metrics.get_lent_value()
        max_ltv_ratio = final_position.metrics.get_max_ltv() / 100
        return (lent_value * max_ltv_ratio - borrowed_value) / currency.price

    def get_repayable_amount(self, customer_wallet: "Wallet", currency: "Currency") -> float:
        """Returns the amount that can be repaid by the customer."""
        return min(
            self._position.borrowed.get(currency).amount,
            customer_wallet.get(currency).amount,
        )
