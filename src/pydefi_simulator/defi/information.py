from dataclasses import dataclass


@dataclass
class DefiInfo:
    """The class that contains the information of a currency on a lending platform."""

    collateral_enabled: bool = True
    borrow_enabled: bool = True
    max_ltv: float = 0
    liquidation_ratio: float = 0
    collateral_apy: float = 0
    borrow_apy: float = 0
    liquidity_bonus_apr: float = 0
    borrow_bonus_apr: float = 0

    @property
    def total_borrow_apy(self) -> float:
        """Returns the total borrow APY of the platform."""
        return self.borrow_apy + self.borrow_bonus_apr

    @property
    def total_collateral_apy(self) -> float:
        """Returns the total collateral APY of the platform."""
        return self.collateral_apy + self.liquidity_bonus_apr
