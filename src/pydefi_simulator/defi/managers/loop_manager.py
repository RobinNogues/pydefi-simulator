from typing import TYPE_CHECKING

from pydefi_simulator.logger import logger
from pydefi_simulator.utils.contants import ALL, MAX


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency
    from pydefi_simulator.defi.position.defi_position import DefiPosition
    from pydefi_simulator.wallet import Wallet

    from .defi_manager import DefiManager


class LoopManager:
    """The class that automates lending / borrowing loops."""

    def __init__(self, position: "DefiPosition", defi_manager: "DefiManager") -> None:
        """Initialize the LoopManager.

        Parameters
        ----------
        position : DefiPosition
            The position of the customer.
        defi_manager : DefiManager
            The DefiManager to use.

        """
        self._position = position
        self._defi_manager = defi_manager

    def loop(
            self,
            main_wallet: "Wallet",
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
        main_wallet : Wallet
            The main wallet to use.
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
        if not loop_number > 0:
            logger.error("Trying to loop a negative number of times.")
            return
        if not self._position.platform.is_borrowable(borrowed_currency):
            logger.error(f"{borrowed_currency.symbol} is not borrowable on the platform.")
            return
        if not self._position.platform.is_lendable(lent_currency):
            logger.error(f"{lent_currency.symbol} is not lendable on the platform.")
            return

        collateral = [lent_currency] if restricted_collateral else ALL
        for _ in range(loop_number):
            borrowable = self._position.metrics.get_borrowable(borrowed_currency, collateral)
            if not borrowable:
                logger.error("Not enough collateral to loop.")
                return
            self._defi_manager.borrow(main_wallet, borrowed_currency, borrowable, collateral)
            main_wallet.swap(borrowed_currency, lent_currency, borrowable)
            to_lend = borrowed_currency.convert(lent_currency, borrowable)
            self._defi_manager.lend(main_wallet, lent_currency, to_lend)

    def loop_back(
            self,
            main_wallet: "Wallet",
            borrowed_currency: "Currency",
            lent_currency: "Currency",
            max_loop: int = 20,
    ) -> None:
        """Repays the loan using loops.

        A loop consists of repaying the maximum possible amount of a currency, swapping it for
        the lent currency which is then withdrawn and swapped back for the borrowed currency.

        Parameters
        ----------
        main_wallet : Wallet
            The main wallet to use.
        borrowed_currency : Currency
            The currency to borrow.
        lent_currency : Currency
            The currency to lend.
        max_loop : int, optional
            The maximum number of times to loop, default 20.

        """
        if not max_loop > 0:
            logger.error("Trying to loop a negative number of times.")
            return
        if not self._position.platform.is_borrowable(borrowed_currency):
            logger.error(f"{borrowed_currency.symbol} is not borrowable on the platform.")
            return
        if not self._position.platform.is_lendable(lent_currency):
            logger.error(f"{lent_currency.symbol} is not lendable on the platform.")
            return

        for loop in range(max_loop):
            borrowed_curr_amount = self._position.borrowed.get(borrowed_currency).amount
            if not borrowed_curr_amount:
                log = "There is nothing to repay." if loop == 0 else "Everything has been repaid."
                logger.info(log)
                return
            if self._position.metrics.get_repayable_amount(main_wallet, borrowed_currency):
                self._defi_manager.repay(main_wallet, borrowed_currency, MAX)
                continue
            withdrawable = self._position.metrics.get_withdrawable_amount(lent_currency)
            if not withdrawable:
                logger.error(f"Not enough {lent_currency} to loop back.")
                return
            # to not withdraw more than needed
            to_withdraw = min(
                withdrawable,
                borrowed_currency.convert(
                    other=lent_currency,
                    amount=borrowed_curr_amount,
                ),
            )
            self._defi_manager.withdraw(main_wallet, lent_currency, to_withdraw)
            main_wallet.swap(lent_currency, borrowed_currency, to_withdraw)
            self._defi_manager.repay(
                main_wallet,
                borrowed_currency,
                amount=lent_currency.convert(borrowed_currency, to_withdraw),
            )
        logger.info(
            f"There is still {self._position.borrowed.get(borrowed_currency).amount} "
            f"{borrowed_currency} to repay.",
        )
