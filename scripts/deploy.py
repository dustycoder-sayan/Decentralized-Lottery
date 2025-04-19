from brownie import Lottery, config, network
from scripts import helper_scripts
from time import sleep

def deploy_lottery():
    print("Deploying Contract...")
    account = helper_scripts.get_account()
    lottery_contract = Lottery.deploy(
        helper_scripts.get_contract(config["contracts"]["ETH_USD_PRICE_FEED"]).address,
        helper_scripts.get_contract(config["contracts"]["VRF_COORDINATOR"]).address,
        helper_scripts.get_contract(config["contracts"]["LINK_TOKEN"]).address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyHash"],
        {
            "from": account
        },
        publish_source=config["networks"][network.show_active()].get("verify", False)
    )
    print("Contract Deployed !")
    return lottery_contract

def start_lottery():
    account = helper_scripts.get_account()
    lottery = Lottery[-1]
    starting_txn = lottery.startLottery (
        {
            "from": account
        }
    )
    starting_txn.wait(1)

    print("Lottery Started !")

def enter_lottery():
    account = helper_scripts.get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 1000000
    enter_txn = lottery.enter(
        {
           "from": account,
           "value": value
        }
    )
    enter_txn.wait(1)

    print("You have successfully entered the lottery !")

def end_lottery():
    account = helper_scripts.get_account()
    lottery = Lottery[-1]
    # funding contract
    fund_txn = helper_scripts.fund_contract_with_link(lottery.address)
    fund_txn.wait(1)
    end_txn = lottery.endLottery (
        {
            "from": account
        }
    )
    end_txn.wait(1)
    sleep(60)    # sleep for 1 minute to allow the chainlink node to generate the random number and call the callback function
    print(f"The winner is {lottery.recentWinner()}")
    print("Lottery ended successfully")

def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()