from math import inf
from typing import TYPE_CHECKING, Literal

from pydefi_simulator.utils.contants import ALL
from pydefi_simulator.wallet import Wallet

from .borrowing_metrics import BorrowingMetrics
from .lending_metrics import LendingMetrics


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi import DefiPosition


class DefiMetrics:
    """The class that computes global metrics, borrowing and lending metrics, for a position."""

    def __init__(self, position: "DefiPosition") -> None:
        """Initialize the DefiMetrics.

        Parameters
        ----------
        position : DefiPosition
            The position to compute the metrics for.

        """
        self._position = position
        self.borrowing_metrics = BorrowingMetrics(position)
        self.lending_metrics = LendingMetrics(position)

    def get_health_ratio(self, ndigits: int = 2) -> float:
        """Returns the health ratio of the position. The result can be rounded."""
        borrowed_value = self.get_borrowed_value()
        if borrowed_value == 0:
            return inf

        w_liquidation = self.get_ltv_liquidation() / 100
        lent_value = self.get_lent_value()
        health_ratio = lent_value * w_liquidation / borrowed_value
        return round(health_ratio, ndigits) if ndigits is not None else health_ratio

    def get_net_value(self) -> float:
        """Returns the net value of the position (lent_value - borrowed_value)."""
        return self._position.lent.value - self._position.borrowed.value

    def get_borrowed_value(self, currency: "Currency | Literal['all']" = ALL) -> float:
        """Returns the value of a borrowed currency or the total value of the borrowed
        currencies.
        """
        return self.borrowing_metrics.get_borrowed_value(currency)

    def get_lent_value(self, currency: "Currency | Literal['all']" = ALL) -> float:
        """Returns the value of a lent currency or the total value of the lent currencies."""
        return self.lending_metrics.get_lent_value(currency)

    def get_borrowed_amount(self, currency: "Currency") -> float:
        """Returns the amount of borrowed currency."""
        return self.borrowing_metrics.get_borrowed_amount(currency)

    def get_lent_amount(self, currency: "Currency") -> float:
        """Returns the amount of lent currency."""
        return self.lending_metrics.get_lent_amount(currency)

    def get_ltv(self) -> float:
        """Returns the LTV of the position."""
        lent_value = self.get_lent_value()
        return (
            100 * self._position.borrowed.value / lent_value
            if lent_value
            else inf
        )

    def get_ltv_liquidation(self) -> float:
        """Returns the ltv that triggers the start of liquidation of the position, depending on the
        position's lent value.
        """
        return self.lending_metrics.get_ltv_liquidation()

    def get_max_ltv(self) -> float:
        """Returns the max ltv allowed depending on the position's lent value."""
        return self.lending_metrics.get_max_ltv()

    def get_borrow_power_used(self, ndigits: int = 2) -> float:
        """Returns the amount of borrow power used by the position."""
        res = 100 * self.get_ltv() / self.get_max_ltv()
        return round(res, ndigits) if ndigits is not None else res

    def get_leverage(self) -> float:
        """Returns the leverage of the position."""
        lent_value = self.get_lent_value()
        borrowed_value = self.get_borrowed_value()
        if not borrowed_value:
            return 0
        if not lent_value:
            return inf
        return (lent_value + borrowed_value) / lent_value

    def get_net_apy(self, with_currency_apy: bool = False) -> float:
        """Returns the net APY of the position. The currencies APY can be considered or ignored."""
        net_value = self.get_net_value()

        if net_value == 0:
            return 0
        return (
            (self.get_borrow_apy(with_currency_apy) * self.get_borrowed_value()
             + self.get_lend_apy(with_currency_apy) * self.get_lent_value())
            / net_value
        )

    def get_loop_apy(self, currency: "Currency") -> float:
        """Returns the loop APY of the position for the given currency. The loop APY compute the
        net APY by focusing on a currency and its related currency (e.g ETH and WSTETH).
        """
        from pydefi_simulator.defi.position.defi_position import DefiPosition  # loop import
        lended_staked = Wallet()
        borrowed = Wallet()
        borrowed.add(currency, self._position.borrowed.get(currency).amount)
        for _currency in self._position.lent.currencies:
            if _currency.related_to == currency:
                lended_staked.add(_currency, self._position.lent[_currency].amount)
        loop_position = DefiPosition(self._position.platform, lended_staked, borrowed)
        return loop_position.metrics.get_net_apy(True)

    def get_borrow_apy(self, with_currency_apy: bool = False) -> float:
        """Returns the borrow APY of the position. The currencies APY can be considered or
        ignored.
        """
        return self.borrowing_metrics.get_borrow_apy(with_currency_apy)

    def get_lend_apy(self, with_currency_apy: bool = False) -> float:
        """Returns the lend APY of the position. The currencies APY can be considered or
        ignored.
        """
        return self.lending_metrics.get_lend_apy(with_currency_apy)

    def get_borrowable(
            self,
            currency: "Currency",
            collateral: list["Currency"] | Literal["all"] = ALL,
    ) -> float:
        """Returns how much of the given currency can be borrowed. The list of lent currencies to
        use as collateral can be provided. If "all" is provided, all lent currencies are used as
        collateral.
        """
        return self.borrowing_metrics.get_borrowable(currency, collateral)

    def get_repayable_amount(self, customer_wallet: "Wallet", currency: "Currency") -> float:
        """Returns the amount that can be repaid by the customer."""
        return self.borrowing_metrics.get_repayable_amount(customer_wallet, currency)

    def get_withdrawable_amount(self, currency: "Currency") -> float:
        """Returns the amount that can be withdrawn for the given currency."""
        return self.lending_metrics.get_withdrawable_amount(currency)
