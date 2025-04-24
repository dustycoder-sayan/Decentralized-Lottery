from scripts import deploy
from scripts import helper_scripts

from brownie import network, Contract, Lottery
import pytest
from time import sleep

def test_pick_winner():
    if network.show_active() in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    lottery_contract = deploy.deploy_lottery()
    account = helper_scripts.get_account()

    lottery_contract.startLottery({
        "from": account
    })
    lottery_contract.enter({
        "from": account,
        "value": lottery_contract.getEntranceFee()
    })
    helper_scripts.fund_contract_with_link(lottery_contract)
    lottery_contract.endLottery (
        {
            "from": account,
        }
    )

    sleep(60)
    assert lottery_contract.recentWinner() == account.address
    assert lottery_contract.balance() == 0
