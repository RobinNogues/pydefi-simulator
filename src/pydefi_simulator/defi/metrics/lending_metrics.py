from typing import TYPE_CHECKING, Literal

from pydefi_simulator.utils.contants import ALL


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi import DefiPosition


class LendingMetrics:
    """The class that computes the lending metrics of a position."""

    def __init__(self, position: "DefiPosition") -> None:
        """Initialize the LendingMetrics.

        Parameters
        ----------
        position : DefiPosition
            The position to compute the metrics for.

        """
        self._position = position

    def get_lent_value(self, currency: "Currency | Literal['all']" = ALL) -> float:
        """Returns the value of a lent currency or the total value of the lent currencies."""
        return (
            self._position.lent.value
            if currency == ALL
            else self._position.lent.get(currency).value
        )

    def get_lent_amount(self, currency: "Currency") -> float:
        """Returns the amount of lent currency."""
        return self._position.lent.get(currency).amount

    def get_lend_apy(self, with_currency_apy: bool = False) -> float:
        """Returns the borrow APY of the given position. The currencies APY can be considered."""
        lent_value = self._position.lent.value
        if not lent_value:
            return 0

        platform = self._position.platform
        weighted_sum_apy = sum(
            (
                platform[_item.currency].total_collateral_apy * _item.value
                + (_item.currency.apy * _item.value if with_currency_apy else 0)
            )
            for _item in self._position.lent
        )
        return weighted_sum_apy / lent_value

    def get_ltv_liquidation(self) -> float:
        """Returns the ltv that triggers the start of liquidation of the position, depending on the
        position's lent value.
        """
        lent_value = self._position.lent.value
        if not lent_value:
            return 0

        weighted_sum = sum(
            self._position.platform[_item.currency].liquidation_ratio * _item.value
            for _item in self._position.lent
        )
        return weighted_sum / lent_value

    def get_max_ltv(self) -> float:
        """Returns the max ltv allowed depending on the position's lent value."""
        lent_value = self.get_lent_value()
        if not lent_value:
            return 0

        weighted_sum = sum(
            self._position.platform[_item.currency].max_ltv * _item.value
            for _item in self._position.lent
        )
        return weighted_sum / lent_value

    def get_withdrawable_amount(self, currency: "Currency") -> float:
        """Returns the amount that can be withdrawn for the given currency."""
        lent = self.get_lent_value()
        max_ltv_ratio = self.get_max_ltv() / 100
        borrowed = self._position.metrics.get_borrowed_value()
        currency_max_ltv_ratio = self._position.platform[currency].max_ltv / 100
        res = (lent * max_ltv_ratio - borrowed) / (currency.price * currency_max_ltv_ratio)
        return min(res, self._position.lent.get(currency).amount)
