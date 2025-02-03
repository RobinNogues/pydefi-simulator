from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydefi_simulator.defi.information import DefiInfo


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi.position import DefiPositionFactory


class DefiPlatformFactory(ABC):
    """Abstract class for creating DefiPlatform objects."""

    @abstractmethod
    def create_platform(self, *args, **kwargs) -> "DefiPlatform":
        """Create a DefiPlatform object."""
        ...


class DefiPlatform:
    """The class that contains the information of a lending platform. It stores lending and
    borrowing informations for each currencies.
    """

    def __init__(
            self,
            name: str,
            informations: dict["Currency", "DefiInfo"] | None = None,
            position_factory: "type[DefiPositionFactory] | None" = None,
    ) -> None:
        """Create a new DefiPlatform object. Informations can be provided.

        Parameters
        ----------
        name : str
            Name of the platform.
        informations : dict[Currency, DefiInfo] | None
            Informations for each currency.
        position_factory : type[DefiPositionFactory] | None
            The factory to use to create DefiPosition objects, by default None.

        """
        self.name = name
        self.currencies: dict[Currency, DefiInfo] = informations or {}
        self.position_factory = position_factory(self) if position_factory else None

    def is_lendable(self, currency: "Currency") -> bool:
        """Weither the given currency is lendable or not."""
        info = self.currencies.get(currency)
        return bool(info and info.collateral_enabled)

    def is_borrowable(self, currency: "Currency") -> bool:
        """Weither the given currency is borrowable or not."""
        info = self.currencies.get(currency)
        return bool(info and info.borrow_enabled)

    def set_info(self, currency: "Currency", info: "DefiInfo") -> None:
        """Change or add borrowing and lending informations for a currency."""
        self.currencies[currency] = info

    def get_info(self, currency: "Currency") -> "DefiInfo":
        """Get the platform's info for the given currency."""
        return self.currencies.get(currency, DefiInfo())

    def __repr__(self) -> str:
        """Return the platform's name."""
        return self.name

    def __getitem__(self, item: "Currency") -> "DefiInfo":
        """Get the platform's info for the given currency if it exists, else raise KeyError."""
        return self.currencies[item]
