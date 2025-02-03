from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydefi_simulator.api import CoinGeckoApi, TheGraphAPI, ZxGraphAPI
from pydefi_simulator.currency import Currency, CurrencyFactory
from pydefi_simulator.defi.platform import DefiPlatformFactory
from pydefi_simulator.logger import logger


if TYPE_CHECKING:
    from pydefi_simulator.defi.information import DefiInfo
    from pydefi_simulator.defi.platform.defi_platform import DefiPlatform


class AaveFactory(DefiPlatformFactory, ABC):
    """Aave V3 Factory."""

    thegraph = TheGraphAPI()
    zxgraph = ZxGraphAPI()
    price_api = CoinGeckoApi()

    @property
    @abstractmethod
    def data_query(self) -> str:
        """The query to use to fetch the data from the subgraph."""

    @abstractmethod
    def create_platform(self, market_name: str, *args, **kwargs) -> "DefiPlatform":
        """Create a DefiPlatform object with Aave's data."""
        ...

    @abstractmethod
    def _from_raw_data_to_defi_info(self, *args, **kwargs) -> "DefiInfo | None":
        """Convert the aave raw data to a DefiInfo object."""

    def _extract_defi_data_from_api_response(
            self,
            reserves: list[dict],
            **raw_data_to_defi_info_kwargs,
    ) -> dict["Currency", "DefiInfo"]:
        """Convert the API data to DefiData objects.

        Parameters
        ----------
        reserves : list[dict]
            List of metadatas for each found currencies to be converted.
        raw_data_to_defi_info_kwargs : dict[str, Any]
            Optional arguments to pass to _from_raw_data_to_defi_info method.

        Returns
        -------
        dict[Currency, DefiInfo]
            Defi information related to each currency.

        """
        currencies_with_info = {}
        currencies = CurrencyFactory().create_multiple_currencies(
            *[{"symbol": reserve["symbol"]} for reserve in reserves],
        )

        price_from_aave = set()
        no_prices_found = set()
        for reserve in reserves:
            symbol = reserve["symbol"]
            currency = currencies.get(symbol)
            if not currency:
                price = float(reserve["price"]["priceInEth"]) / 1e8
                if not price:
                    no_prices_found.add(symbol)
                    continue
                price_from_aave.add(symbol)
                currency = Currency(symbol, custom_price=price)
            info = self._from_raw_data_to_defi_info(reserve, **raw_data_to_defi_info_kwargs)
            if not info:
                continue
            currencies_with_info[currency] = info
        if price_from_aave:
            logger.warning(
                f"{price_from_aave} prices from the Aave API are used because they were not found"
                f" on {self.price_api.source_name} (they can be wrong).",
            )
        if no_prices_found:
            logger.warning(
                f"Prices for {no_prices_found} symbols could not be found either on "
                f" {self.price_api.source_name} or on the Aave API. They are set to 0.",
            )
        return currencies_with_info

    def _from_ray_to_percent(self, ray: float) -> float:
        """Convertion given by Aave.
        See https://github.com/aave/protocol-subgraphs?tab=readme-ov-file#reserve-summary.
        """
        return (((1 + ((ray / 10**27) / 31536000))**31536000) - 1) * 100
