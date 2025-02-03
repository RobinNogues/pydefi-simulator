from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydefi_simulator.defi.metrics import DefiMetrics
from pydefi_simulator.wallet import Wallet


if TYPE_CHECKING:
    from pydefi_simulator.defi.platform.defi_platform import DefiPlatform


class DefiPositionFactory(ABC):
    """The class that represents a factory for creating DefiPosition objects from a customer
    address.
    """

    def __init__(self, platform: "DefiPlatform") -> None:
        """Initialize the DefiPositionFactory.

        Parameters
        ----------
        platform : DefiPlatform
            The platform of the position.

        """
        self._platform = platform

    @abstractmethod
    def create_position_from_address(
            self,
            address: str,
    ) -> "DefiPosition":
        """Create a DefiPosition object."""
        ...


class DefiPosition:
    """The class that represents a position on a lending platform. It is defined by the platform
    information, the lent and borrowed currencies.
    """

    def __init__(
            self,
            platform: "DefiPlatform",
            lent: "Wallet | None" = None,
            borrowed: "Wallet | None" = None,
    ) -> None:
        """Initialize the DefiPosition.

        Parameters
        ----------
        platform : DefiPlatform
            The platform of the position.
        lent : Wallet, optional
            The lent wallet of the position, by default None.
        borrowed : Wallet, optional
            The borrowed wallet of the position, by default None.

        """
        self.platform = platform
        self.lent = lent or Wallet()
        self.borrowed = borrowed or Wallet()
        self.metrics = DefiMetrics(self)

    def __repr__(self) -> str:
        """Show the details of the position, lent and borrowed currencies."""
        return f"Positions(L{self.lent.content} B{self.borrowed.content})"
