from pydefi_simulator.api import TheGraphAPI
from pydefi_simulator.currency import Currency
from pydefi_simulator.defi.position import DefiPosition, DefiPositionFactory
from pydefi_simulator.wallet import Wallet

from .config_reader import get_platform_config_from_name


class AavePositionFactory(DefiPositionFactory):
    """The class that create a DefiPosition objects depending on the open positions of an address
    on Aave.
    """

    query = """
    {{
        user(id: "{address}") {{
            id
            reserves {{
                currentATokenBalance
                currentVariableDebt
                reserve {{
                    symbol
                    decimals
                }}
            }}
        }}
    }}
    """
    thegraph = TheGraphAPI()

    def create_position_from_address(
            self,
            address: str,
    ) -> "DefiPosition":
        """Create a DefiPosition object.

        Parameters
        ----------
        platform : DefiPlatform
            Any Aave market.
        address : str
            An address with open positions

        Returns
        -------
        DefiPosition
            The position of the given address.

        """
        config = get_platform_config_from_name(self._platform.name)
        api_response = self.thegraph.select(
            subgraph_id=config["subgraph_id"],
            query=self.query,
            variables={
                "address": address,
            },
        ).get("user", {})
        return self._get_positions_from_api_response(api_response)

    def _get_positions_from_api_response(
            self,
            api_response: dict,
    ) -> "DefiPosition":
        if not api_response or not api_response.get("reserves"):
            return DefiPosition(self._platform)

        lent = Wallet()
        borrowed = Wallet()
        for reserve in api_response["reserves"]:
            currency = Currency.get_currency(reserve["reserve"]["symbol"])
            if not currency:
                continue
            decimals = int(reserve["reserve"]["decimals"])
            lent_amount = float(reserve["currentATokenBalance"]) / 10**decimals
            borrowed_amount = float(reserve["currentVariableDebt"]) / 10**decimals
            if lent_amount:
                lent.add(currency, lent_amount)
            if borrowed_amount:
                borrowed.add(currency, borrowed_amount)
        return DefiPosition(self._platform, lent=lent, borrowed=borrowed)
