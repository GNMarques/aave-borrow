from brownie.network import web3
from scripts.helpfull_scripts import get_account
from scripts.get_weth import get_weth
from brownie import config, network, interface
from web3 import Web3

# 0.1
AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork-dev"]:
        get_weth()
    lending_pool = get_lending_pool()
    print(lending_pool)
    # Aprove sending out the ERC20 token
    aprove_ERC20(lending_pool.address, AMOUNT, erc20_address, account)
    print("Depositing....")
    tx = lending_pool.deposit(erc20_address, AMOUNT,
                              account.address, 0, {"from": account})
    tx.wait(1)
    print("Deposited!!!!")
    # How much?
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"])
    amount_dai_to_borrow = (1/dai_eth_price)*(borrowable_eth*0.95)
    converted_amount_dai_to_borrow = Web3.toWei(amount_dai_to_borrow, "ether")
    # Convert borrowable eth into DAI * 95%
    print(f"We are going to borrow {amount_dai_to_borrow}")
    # Now we will borrow
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        converted_amount_dai_to_borrow,
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(lending_pool, account)
    repay_all(AMOUNT, lending_pool, account)
    print("You just deposited, borrowed, and repayed with Aave, Brownie, and Chainlink!")


def repay_all(amount, lending_pool, account):
    aprove_ERC20(
        lending_pool,
        Web3.toWei(amount, "ether"),
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid!")


def get_asset_price(price_feed_address):
    # ABI
    # Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (total_colateral_eth, total_debt_eth, available_borrow_eth, current_Liquidation_Threshold,
     ltv, health_Factor) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_colateral_eth = Web3.fromWei(total_colateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"YOU HAVE {total_colateral_eth} total of ETH DEPOSITEd")
    print(f"YOU HAVE {total_debt_eth} total of ETH Borrowed")
    print(f"YOU HAVE {available_borrow_eth} available ETH to borrow")
    return (float(available_borrow_eth), float(total_debt_eth))


def aprove_ERC20(spender, amount, erc20_address, account):
    print("Aproving")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"])
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
