from yaml import safe_load


def read_yaml(file_path: str) -> dict:
    """Read a YAML file and return its content as a dictionary."""
    with open(file_path) as file:
        return safe_load(file)
