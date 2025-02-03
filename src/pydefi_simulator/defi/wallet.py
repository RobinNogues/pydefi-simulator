from typing import TYPE_CHECKING, Literal

from pydefi_simulator.utils.contants import ALL

from .managers import DefiManager, LoopManager
from .position.defi_position import DefiPosition


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.wallet import Wallet

    from .metrics import DefiMetrics
    from .platform.defi_platform import DefiPlatform


class DefiWallet:
    """The class that represents positions on a lending platform."""

    def __init__(
            self,
            main_wallet: "Wallet",
            defi_platform: "DefiPlatform",
            create_from_address: bool = False,
    ) -> None:
        """Initialize the DefiWallet.

        Parameters
        ----------
        main_wallet : Wallet
            The main wallet of the customer linked to the positions.
        defi_platform : DefiPlatform
            The platform of the position.
        create_from_address : bool, optional
            Create the actual position from the address of the main wallet, by default False.

        """
        self._main_wallet = main_wallet
        self._position = (
            defi_platform.position_factory.create_position_from_address(main_wallet.address)
            if create_from_address and defi_platform.position_factory
            else DefiPosition(defi_platform)
        )
        self._defi_manager = DefiManager(self._position)
        self._loop_manager = LoopManager(self._position, self._defi_manager)

    @property
    def metrics(self) -> "DefiMetrics":
        """The metrics of the position."""
        return self._position.metrics

    @property
    def show_positions(self) -> str:
        """Show the details of the position, lent and borrowed currencies."""
        return self._position.__repr__()

    def lend(self, currency: "Currency", amount: float | Literal["max"]) -> None:
        """Lends a currency and removes it from the customer's wallet.

        Parameters
        ----------
        currency : Currency
            The currency to lend.
        amount : float
            The amount to lend.

        """
        return self._defi_manager.lend(self._main_wallet, currency, amount)

    def borrow(
            self,
            currency: "Currency",
            amount: float | Literal["max"],
            collateral: list["Currency"] | Literal["all"] = ALL,
    ) -> None:
        """Borrows a currency and adds it to the customer's wallet.

        Parameters
        ----------
        currency : Currency
            The currency to borrow.
        amount : float | Literal["max"]
            The amount to borrow. If "max", the maximum amount is borrowed.
        collateral : list[Currency] | Literal["all"]
            The list of lent currencies to use as collateral, or "all" to use all lent currencies,
            default "all".

        """
        self._defi_manager.borrow(self._main_wallet, currency, amount, collateral)

    def repay(self, currency: "Currency", amount: float | Literal["max"]) -> None:
        """Repays a currency and removes it from the customer's wallet.

        Parameters
        ----------
        currency : Currency
            The currency to repay.
        amount : float | Literal["max"]
            The amount to repay. If "max", the maximum amount is repayed.

        """
        self._defi_manager.repay(self._main_wallet, currency, amount)

    def withdraw(self, currency: "Currency", amount: float | Literal["max"]) -> None:
        """Withdraws a currency and adds it to the customer's wallet.

        Parameters
        ----------
        currency : Currency
            The currency to withdraw.
        amount : float | Literal["max"]
            The amount to withdraw. If "max", the maximum amount is withdrawn.

        """
        self._defi_manager.withdraw(self._main_wallet, currency, amount)

    def loop(
            self,
            borrowed_currency: "Currency",
            lent_currency: "Currency",
            loop_number: int,
            restricted_collateral: bool = True,
    ) -> None:
        """Loop the given number of times.

        A loop consists of borrowing the maximum possible amount of a currency, swapping it for
        another currency which is then deposited as collateral.

        Parameters
        ----------
        borrowed_currency : Currency
            The currency to borrow.
        lent_currency : Currency
            The currency to lend.
        loop_number : int
            The number of times to loop.
        restricted_collateral : bool, optional
            Restrict collateral to currency deposited or use all available collateral,
            default True.

        """
        self._loop_manager.loop(
            main_wallet=self._main_wallet,
            borrowed_currency=borrowed_currency,
            lent_currency=lent_currency,
            loop_number=loop_number,
            restricted_collateral=restricted_collateral,
        )

    def loop_back(
            self,
            borrowed_currency: "Currency",
            lent_currency: "Currency",
            max_loop: int = 20,
    ) -> None:
        """Repays the loan using loops.

        A loop consists of repaying the maximum possible amount of a currency, swapping it for
        the lent currency which is then withdrawn and swapped back for the borrowed currency.

        Parameters
        ----------
        borrowed_currency : Currency
            The currency to borrow.
        lent_currency : Currency
            The currency to lend.
        max_loop : int, optional
            The maximum number of times to loop, default 20.

        """
        return self._loop_manager.loop_back(
            main_wallet=self._main_wallet,
            borrowed_currency=borrowed_currency,
            lent_currency=lent_currency,
            max_loop=max_loop,
        )
