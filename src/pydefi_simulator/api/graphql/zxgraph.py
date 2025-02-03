import requests

from pydefi_simulator.logger import logger
from pydefi_simulator.utils import SingletonMeta


class ZxGraphAPI(metaclass=SingletonMeta):
    """The interface to do queries on 0xGraph."""

    def select(self, url: str, query: str, variables: dict[str, str] | None = None) -> dict:
        """Select data from a 0xGraph subgraph.

        Parameters
        ----------
        url : str
            The URL of the 0xGraph subgraph.
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
