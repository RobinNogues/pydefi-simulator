import requests

from pydefi_simulator.api.config import get_api_key
from pydefi_simulator.logger import logger
from pydefi_simulator.utils import SingletonMeta


class TheGraphAPI(metaclass=SingletonMeta):
    """The interface to do queries on TheGraph."""

    uncomplete_url = "https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the TheGraphAPI by setting the API key."""
        self.set_api_key(api_key or get_api_key("thegraph"))

    def select(
            self,
            subgraph_id: str,
            query: str,
            variables: dict[str, str] | None = None,
    ) -> dict:
        """Select data from a TheGraph subgraph.

        Parameters
        ----------
        subgraph_id : str
            The subgraph ID.
        query : str
            The GraphQL query. Parameters can be passed using the format {param}. Others `{}` must
            be escaped.
        variables : dict[str, str] | None, optional
            The variables that will replace {param} in the query, by default None.

        Returns
        -------
        dict
            The data returned by the query.

        """
        variables = variables or {}
        url = self.uncomplete_url.format(
            api_key=self._api_key,
            subgraph_id=subgraph_id,
        )
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "query": query.format(**variables) if variables else query,
        }
        response = requests.post(
            url=url,
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return {}
        return data.get("data", {})

    def set_api_key(self, api_key: str) -> None:
        """Set the API key to use."""
        self._api_key = api_key
