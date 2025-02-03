import secrets


def random_eth_address() -> str:
    """Generate a random Ethereum address."""
    return "0x" + secrets.token_hex(20)
