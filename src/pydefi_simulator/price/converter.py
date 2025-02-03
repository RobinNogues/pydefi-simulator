from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pydefi_simulator.currency import Currency


class CryptoConverter:
    """The class that converts cryptocurrencies."""

    @staticmethod
    def convert(
            from_currency: "Currency",
            to_currency: "Currency",
            amount: float,
    ) -> float:
        """Convert the given amount from a cryptocurrency to another.

        Parameters
        ----------
        from_currency : Currency
            The currency to convert from.
        to_currency : Currency
            The currency to convert to.
        amount : float
            The amount to convert.

        Returns
        -------
        float
            The converted amount.

        """
        return amount * from_currency.conversion_ratio(to_currency)

    @staticmethod
    def conversion_ratio(from_currency: "Currency", to_currency: "Currency") -> float:
        """Return the conversion ratio between two cryptocurrencies.

        Parameters
        ----------
        from_currency : Currency
            The currency to convert from.
        to_currency : Currency
            The currency to convert to.

        Returns
        -------
        float
            The conversion ratio.

        """
        return from_currency.price / to_currency.price
