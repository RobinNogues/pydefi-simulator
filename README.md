# pydefi-simulator

A defi simulator that allows you to create fake positions on a fake lending/borrowing dapp and get statistics about it.

With this simulator, it is possible to :

- fetch cryptocurrency prices from CoinGecko
- create a fake wallet
- create a fake lending / borrowing platform or from an existing platform (Aave V2 and V3 for now)
- do the basics lending and borrowing transactions and more complex ones (loops)
- give all defi statistics (LTV, health_factor, APY, net_value, etc.)

This project does not pretend to be a perfect representation of a defi platform, but a tool to help you test your defi strategy.

## Currencies

You can create currency objects with the `Currency` class.

For each currency, you can set optional parameters :

- custom_price : the custom price of the currency
- apy : the annual percentage yield of the currency
- related_to : a currency related to the currency (e.g. ETH for WSTETH)

Changing these 3 parameters will affect defi metrics.

Without custom price, the price is retrieved from the CoinGecko API. APY (like staking rewards) and related to another currency are not fetched automatically.

When the price of a symbol is retrieved from the CoinGecko API, it returns the price of the token with the largest market cap (because currencies can have the same symbol).

## Main Wallet

To use defi protols, you need a wallet to interact with. The wallet is represented by the `Wallet` class.

With a wallet, it is possible to add, remove, send and convert currencies.

It takes a public Ethereum address as a parameter. Otherwise a random address is generated. This address can be used for the `DefiWallet` object (see below).

## Lending / Borrowing platform

To use defi protocols you need a lend / borrow platform. The platform is represented by the `DefiPlatform` class.
Each currency on a defi platform has borrowing and lending information, represented by the `DefiInfo` class.

A `DefiPlatform` object can be created from scratch with custom `DefiInfo` for each listed currency, or created from an existing platform using APIs.

Currently only Aave markets (V2 and V3) can be created using the TheGraph API (and 0xGraph for the Metis market).

### Aave V3

Bonus rewards APR will be taken into account for the total APR of a position, and an emode can be specified.

The TheGraph API for Aave data is not perfect, there are some known issues :
- Wrong end of reward distribution, which may ignore current rewards (Avalanche market)
- Emode not specified for some currencies when they actually have an emode (Gnosis market)
- Price given by Aave in the TheGraph API can be wrong (they are used when the price is not found on CoinGecko)

## Defi Wallet

The `DefiWallet` class is used to interact with a lending / borrowing platform and the main wallet.

### Creation

The `DefiWallet` can be instantiated with an empty `DefiPosition` or with positions from an address. The main wallet address is used to retrieve positions from the Defi platform. At the moment only existing positions from Aave (V2 and V3) can be created.

### Operations

User positions are stored in a `DefiWallet` object which can be used to lend, borrow, repay, withdraw currencies or perform defi loops.

These operations will modify the `DefiPosition` objects stored in the `DefiWallet` object and the main wallet.

### Statistics

The aim of this program is to return basic or advanced statistics of the lending and borrowing positions:
- Health ratio
- Leverage
- Net APY (%)
- Net value
- Borrowing power used (%)
- ...

The loop APY uses the `related_to` field to calculate the global APY of the base currency, taking into account the staked token APY and the lending and borrowing APY.
For example, if you have lent WEETH and WSTETH and borrowed WETH, it will return the global ETH APY.

All statistics are calculated using the `DefiMetrics` object and can be accessed using the `DefiWallet` object.

The currency APY can be considered in various APY statistics, since the APY of a staked token is typically not included.

## Configuration

There are three ways to configure the API keys used by the library.
- Put the API keys in the `api/config/api_keys.yaml.template` file and rename it to `api_keys.yaml`.
- Create your own `api_keys.yaml` file with the API keys and change the `path.API_KEYS_PATH` variable to point to your file.
- Instantiate the `CoinGeckoApi` and `TheGraphAPI` objects with your API keys as parameters a first time, as both objects are singletons, your instances will be reused.

The library is designed to be easily customisable. You are free to create your own platform factory and position factory to retrieve data from another defi protocol.

Add your configuration to `pydefi/configs` in the same way as Aave configurations.

## Code examples

```python
from pydefi_simulator.currency import Currency
from pydefi_simulator.wallet import Wallet
from pydefi_simulator.defi import DefiWallet
from pydefi_simulator.configs.aave import AaveV3Factory


WETH = Currency("WETH")
WSTETH = Currency("WSTETH", apy=3.1, related_to=WETH)
CBBTC = Currency("cbBTC")
USDC = Currency("USDC")
WETH.price, WSTETH.price, CBBTC.price, USDC.price  # >> (2615.14, 3109.41, 95353, 0.999994)

main_wallet = Wallet()
main_wallet.add(WSTETH, 5)
main_wallet.add(USDC, 10000)
main_wallet.swap(USDC, CBBTC, 1000)
main_wallet.content  # >> [5 WSTETH, 9000 USDC, 0.010487284091743312 CBBTC]

aave_base = AaveV3Factory().create_platform("base")
defi_wallet = DefiWallet(main_wallet, aave_base)
aave_base.currencies[WSTETH]  # >> DefiInfo(collateral_enabled=True, borrow_enabled=True, max_ltv=75.0, liquidation_ratio=79.0, collateral_apy=0.06676704258916644, borrow_apy=-1.0508996717138341, ...)

defi_wallet.lend(WSTETH, 4)
defi_wallet.loop(WETH, WSTETH, loop_number=5)
defi_wallet.lend(CBBTC, 0.01)
defi_wallet.show_positions  # >> Positions(L[13.152343750000002 WSTETH, 0.01 CBBTC] B[10.882166606639608 WETH])
defi_wallet.metrics.get_health_ratio()  # >> 1.16
defi_wallet.metrics.get_loop_apy(WETH)  # >> 5.061820221211224

defi_wallet.withdraw(CBBTC, "max")
defi_wallet.loop_back(WETH, WSTETH)
main_wallet.content  # >> [0.9999999999999996 WSTETH, 9000 USDC, 0.010487284091743312 CBBTC]
defi_wallet.show_positions  # >> Positions(L[3.9999999999999996 WSTETH] B[])

```

## Issues

Due to the approximate representation of floating point numbers in binary (see above), rounding errors can occur in swaps. This is a choice not to handle rounding errors and may be improved in the future.

## Possibilities

- Create a UI to
  - Create or modify a fake platform
  - Fake transactions
- Alerts when a strategy is close to liquidation
- Graphical representation of the evolution of the APY as a function of the number of loops

## Licence

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
