from datetime import datetime

from pydefi_simulator.configs.aave.config_reader import get_platform_config
from pydefi_simulator.configs.aave.position import AavePositionFactory
from pydefi_simulator.currency import CurrencyFactory
from pydefi_simulator.defi.information import DefiInfo
from pydefi_simulator.defi.platform import DefiPlatform
from pydefi_simulator.logger import logger

from .aave_factory import AaveFactory


SECONDS_IN_YEAR = 365 * 24 * 60 * 60


class AaveV3Factory(AaveFactory):
    """Aave V3 Factory."""

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
                decimals
                totalATokenSupply
                totalCurrentVariableDebt
                price {
                    priceInEth
                }
                eMode {
                    label
                    liquidationThreshold
                    ltv
                }
                aToken {
                    rewards {
                        distributionEnd
                        rewardTokenSymbol
                        rewardTokenDecimals
                        emissionsPerSecond
                    }
                }
                vToken {
                    rewards {
                        emissionsPerSecond
                        distributionEnd
                        rewardTokenDecimals
                        rewardTokenSymbol
                    }
                }
            }
        }
    """

    emode_query = r"""
        {
            emodeCategories {
                label
            }
        }
    """

    def create_platform(
            self,
            market_name: str,
            emode_label: str | None = None,
    ) -> "DefiPlatform":
        """Create a DefiPlatform object with AaveV3's data for a given market.

        Parameters
        ----------
        market_name : str
            The name of the market, e.g ethereum-core, polygon, ethereum-gho, etc.
        emode_label : str | None, optional
            Boosted ltv mode, e.g stablecoins, by default None

        Returns
        -------
        DefiPlatform
            The platform with AaveV3 data.

        """
        emode_label = emode_label.lower().strip() if emode_label else None
        self._check_valid_emode(market_name, emode_label)

        config = get_platform_config(market_name, 3)
        name, source = config["name"], config["source"]
        if source == "thegraph":
            aave_data = self.thegraph.select(config["subgraph_id"], self.data_query)
        elif source == "0xgraph":
            aave_data = self.zxgraph.select(config["endpoint"], self.data_query)

        if not aave_data:
            return DefiPlatform(name=name, position_factory=AavePositionFactory)

        currencies_with_info = self._extract_defi_data_from_api_response(
            reserves=aave_data.get("reserves", []),
            chosen_emode_label=emode_label,
        )
        return DefiPlatform(
            name=name,
            informations=currencies_with_info,
            position_factory=AavePositionFactory,
        )

    def _from_raw_data_to_defi_info(
            self,
            reserve: dict,
            chosen_emode_label: str | None,
    ) -> "DefiInfo | None":
        borrow_enabled = reserve["borrowingEnabled"]
        collateral_enabled = reserve["usageAsCollateralEnabled"]
        emode = reserve["eMode"] if chosen_emode_label else None
        emode_label = emode["label"].lower().strip() if emode else None
        if (
            (not borrow_enabled and not collateral_enabled)
                or (chosen_emode_label is not None and chosen_emode_label != emode_label)):
            return None
        if emode:
            max_ltv = float(emode["ltv"]) / 100
            liquidation_ratio = float(emode["liquidationThreshold"]) / 100
        else:
            max_ltv = float(reserve["baseLTVasCollateral"]) / 100
            liquidation_ratio = float(reserve["reserveLiquidationThreshold"]) / 100

        a_token_rewards = reserve["aToken"]["rewards"]
        v_token_rewards = reserve["vToken"]["rewards"]
        liquidity_bonus_apr = 0.0
        borrow_bonus_apr = 0.0

        liquidity_bonus_apr = self._get_bonus_reward_apr(
            rewards=a_token_rewards,
            reserve=reserve,
            total_used_token_field="totalATokenSupply",  # noqa: S106
        )
        borrow_bonus_apr = self._get_bonus_reward_apr(
            rewards=v_token_rewards,
            reserve=reserve,
            total_used_token_field="totalCurrentVariableDebt",  # noqa: S106
        )

        return DefiInfo(
            collateral_enabled=collateral_enabled,
            borrow_enabled=borrow_enabled,
            max_ltv=max_ltv,
            liquidation_ratio=liquidation_ratio,
            collateral_apy=self._from_ray_to_percent(float(reserve["liquidityRate"])),
            borrow_apy=-self._from_ray_to_percent(float(reserve["variableBorrowRate"])),
            liquidity_bonus_apr=liquidity_bonus_apr,
            borrow_bonus_apr=borrow_bonus_apr,
        )

    def _get_bonus_reward_apr(
            self,
            rewards: list[dict],
            reserve: dict,
            total_used_token_field: str,
    ) -> float:
        if not rewards:
            return 0.0
        bonus_apr = 0.0
        today_ts = datetime.today().timestamp()
        for reward in rewards:
            if not int(reward["distributionEnd"]) > today_ts:
                continue
            bonus_apr += self._from_emissions_per_second_to_apr(
                reward=reward,
                used_token_symbol=reserve["symbol"],
                used_token_decimals=int(reserve["decimals"]),
                used_token_total=int(reserve[total_used_token_field]),
            )
        return bonus_apr

    def _from_emissions_per_second_to_apr(
            self,
            reward: dict,
            used_token_symbol: str,
            used_token_decimals: int,
            used_token_total: int,
    ) -> float:
        reward_token_symbol = reward["rewardTokenSymbol"]
        tokens = CurrencyFactory().create_multiple_currencies(
            {"symbol": reward_token_symbol},
            {"symbol": used_token_symbol},
        )

        reward_token = tokens.get(reward_token_symbol)
        used_token = tokens.get(used_token_symbol)

        if not reward_token or not used_token or not reward_token.price or not used_token.price:
            logger.warning(
                f"Unable to get price for {reward_token_symbol} or {used_token_symbol}. "
                "Bonus APR cannot be computed.",
            )
            return 0

        total_used_token = used_token_total / 10**used_token_decimals
        emissions_per_sec = (
            int(reward["emissionsPerSecond"]) / 10**int(reward["rewardTokenDecimals"])
        )
        yearly_reward_usd = emissions_per_sec * reward_token.price * SECONDS_IN_YEAR
        total_used_usd = total_used_token * used_token.price
        return (yearly_reward_usd / total_used_usd) * 100

    def avalaible_emodes(self, market_name: str) -> list[str]:
        """Return the list of available emode labels for the given blockchain."""
        config = get_platform_config(market_name, 3)
        subgraph_id = config["subgraph_id"]
        emodes = self.thegraph.select(subgraph_id, self.emode_query).get("emodeCategories")
        if not emodes:
            return []
        return list(
            {
                r["label"].lower().strip()
                for r in emodes
            },
        )

    def _check_valid_emode(self, market_name: str, emode_label: str | None) -> None:
        if not emode_label:
            return
        available_emodes = self.avalaible_emodes(market_name)
        if emode_label not in available_emodes:
            msg = (
                f"The emode '{emode_label}' is not available for the market "
                f"'{market_name}'. Available emodes are : {available_emodes}."
            )
            raise ValueError(msg)
