from pydefi_simulator.configs.aave.config_reader import get_platform_config
from pydefi_simulator.defi.information import DefiInfo
from pydefi_simulator.defi.platform import DefiPlatform

from .aave_factory import AaveFactory


class AaveV2Factory(AaveFactory):
    """Aave V2 Factory."""

    data_query = r"""
        {
            reserves(where: {isFrozen: false}) {
                symbol
                name
                usageAsCollateralEnabled
                borrowingEnabled
                liquidityRate
                variableBorrowRate
                baseLTVasCollateral
                reserveLiquidationThreshold
                price {
                    priceInEth
                }
            }
        }
    """

    def create_platform(
            self,
            market_name: str,
    ) -> "DefiPlatform":
        """Create a DefiPlatform object with AaveV2's data for a given market.

        Parameters
        ----------
        market_name : str
            The name of the market, e.g ethereum-core, polygon, etc.

        Returns
        -------
        DefiPlatform
            The platform with AaveV2 data.

        """
        config = get_platform_config(market_name, 2)
        name, subgraph_id = config["name"], config["subgraph_id"]
        reserves = self.thegraph.select(subgraph_id, self.data_query).get("reserves", [])
        if not reserves:
            return DefiPlatform(name=name)

        currencies_with_info = self._extract_defi_data_from_api_response(
            reserves=reserves,
        )
        return DefiPlatform(
            name=name,
            informations=currencies_with_info,
        )

    def _from_raw_data_to_defi_info(
            self,
            reserve: dict,
    ) -> "DefiInfo | None":
        borrow_enabled = reserve["borrowingEnabled"]
        collateral_enabled = reserve["usageAsCollateralEnabled"]
        if (not borrow_enabled and not collateral_enabled):
            return None

        return DefiInfo(
            collateral_enabled=collateral_enabled,
            borrow_enabled=borrow_enabled,
            max_ltv=float(reserve["baseLTVasCollateral"]) / 100,
            liquidation_ratio=float(reserve["reserveLiquidationThreshold"]) / 100,
            collateral_apy=self._from_ray_to_percent(float(reserve["liquidityRate"])),
            borrow_apy=-self._from_ray_to_percent(float(reserve["variableBorrowRate"])),
        )
