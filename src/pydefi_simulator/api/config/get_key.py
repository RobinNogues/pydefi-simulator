from os.path import exists

from pydefi_simulator.api.config import path
from pydefi_simulator.utils.yaml_reader import read_yaml


def get_api_key(api_name: str) -> str:
    """Get an API key from the api_keys.yaml file.

    Parameters
    ----------
    api_name : str
        The name of the API key to get.

    Returns
    -------
    str
        The API key.

    """
    api_keys_path = path.API_KEYS_PATH
    if not exists(api_keys_path):
        msg = (
            f"No API key file found at this location: '{api_keys_path}'. Set you API keys in the "
            "template api/api_keys.yaml.template and rename it to api_keys.yaml, or make your own "
            "yaml file (see README)."
        )
        raise FileNotFoundError(msg)
    keys = read_yaml(api_keys_path)
    if api_name not in keys:
        msg = f"Key '{api_name}' not found in {api_keys_path}, please add it."
        raise KeyError(msg)
    return keys[api_name]
