from os.path import dirname

from pydefi_simulator.utils import read_yaml


def get_platform_config(market_name: str, aave_version: int) -> dict:
    """Get the configuration used by the factory to create a DefiPlatform object.

    Parameters
    ----------
    market_name : str
        The name of the market, e.g ethereum-core, ethereum-lido, polygon, etc.
    aave_version : int
        The version of Aave (2 or 3).

    Returns
    -------
    dict
        The configuration used by the factory to create a DefiPlatform object.

    """
    config = read_yaml(f"{dirname(__file__)}/config.yaml")
    if aave_version not in config:
        msg = (
            f"The version '{aave_version}' of Aave doesn't exist. Please select one of "
            f"{list(config.keys())}."
        )
        raise KeyError(msg)
    config = config[aave_version]
    if market_name not in config:
        msg = (
            f"The Aave config file does not contain the blockchain '{market_name}'. "
            f"Please select on of {list(config.keys())}."
        )
        raise KeyError(msg)
    return config[market_name]


def get_platform_config_from_name(platform_name: str) -> dict:
    """Get the configuration used by the factory to create a DefiPlatform object."""
    all_configurations = read_yaml(f"{dirname(__file__)}/config.yaml")
    for version, configs in all_configurations.items():
        for market_name, config in configs.items():
            if config["name"].lower() == platform_name.lower():
                config["aave_version"] = version
                config["market_name"] = market_name
                return config

    msg = f"The platform '{platform_name}' is not represented in the config file."
    raise KeyError(msg)
