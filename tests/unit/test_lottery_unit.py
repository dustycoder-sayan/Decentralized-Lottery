from scripts import deploy
from scripts import helper_scripts

from brownie import network, exceptions, config
from web3 import Web3
import pytest

def test_get_entrance_fee():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery_contract = deploy.deploy_lottery()
    # Action
    entrance_fee = lottery_contract.getEntranceFee()
    # Assert
    # We can count on this value to be constant during testing because starting value specified in entrance fee call is 2000 usd / eth ==> 50 usd = 0.025 eth
    expected_entrance_fee = Web3.to_wei(0.025, "ether")
    assert entrance_fee == expected_entrance_fee

def test_cant_enter_unless_started():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery_contract = deploy.deploy_lottery()
    # Action and Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery_contract.enter({
            "from": helper_scripts.get_account(),
            "value": lottery_contract.getEntranceFee()
        })

def test_start_of_lottery():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery_contract = deploy.deploy_lottery()
    # Action
    lottery_contract.startLottery({
        "from": helper_scripts.get_account()
    })
    # Assert
    lottery_state = lottery_contract.lotteryState()
    assert lottery_state == 0

def test_can_enter_when_started_but_does_not_have_enough_fee():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery_contract = deploy.deploy_lottery()
    # Send $40 to the contract as fee
    value_to_send = lottery_contract.getEntranceFee() - Web3.to_wei(0.02, "ether")
    lottery_contract.startLottery({
        "from": helper_scripts.get_account()
    })
    # Action and Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery_contract.enter({
            "from": helper_scripts.get_account(),
            "value": value_to_send
        })

def test_can_enter_when_started_and_has_enough_fee():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    account = helper_scripts.get_account()
    lottery_contract = deploy.deploy_lottery()
    lottery_contract.startLottery({
        "from": helper_scripts.get_account()
    })
    # Action
    lottery_contract.enter({
        "from": account,
        "value": lottery_contract.getEntranceFee()
    })
    # Assert
    assert account.address == lottery_contract.players(0)

def test_can_end_lottery():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    account = helper_scripts.get_account()
    lottery_contract = deploy.deploy_lottery()
    lottery_contract.startLottery({
        "from": account
    })
    lottery_contract.enter({
        "from": account,
        "value": lottery_contract.getEntranceFee()
    })
    helper_scripts.fund_contract_with_link(lottery_contract, amount=10**18)
    lottery_contract.endLottery(
        {
            "from": account
        }
    )
    assert lottery_contract.lotteryState() == 2

def test_can_pick_winner_correctly():
    if network.show_active() not in helper_scripts.DEVELOPMENT_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    account = helper_scripts.get_account()
    lottery_contract = deploy.deploy_lottery()
    lottery_contract.startLottery({
        "from": account
    })
    lottery_contract.enter({
        "from": account,
        "value": lottery_contract.getEntranceFee()
    })
    lottery_contract.enter({
        "from": helper_scripts.get_account(account_index=1),
        "value": lottery_contract.getEntranceFee()
    })
    lottery_contract.enter({
        "from": helper_scripts.get_account(account_index=2),
        "value": lottery_contract.getEntranceFee()
    })
    lottery_contract.enter({
        "from": helper_scripts.get_account(account_index=3),
        "value": lottery_contract.getEntranceFee()
    })

    helper_scripts.fund_contract_with_link(lottery_contract)
    txn = lottery_contract.endLottery (
        {
            "from": account
        }
    )
    
    # retrieve the requestedRandomness Event and mock the node response
    request_id = txn.events["RequestedRandomness"]["requestId"]
    STATIC_RANDOM_NUMBER_FOR_TEST = 789
    
    expected_winner = helper_scripts.get_account(account_index=1)

    prev_account_balance = expected_winner.balance()
    contract_balance = lottery_contract.balance()

    helper_scripts.get_contract(config["contracts"]["VRF_COORDINATOR"]).callBackWithRandomness(
        request_id, 
        STATIC_RANDOM_NUMBER_FOR_TEST, 
        lottery_contract.address,
        {
            "from": account
        }
    )

    assert lottery_contract.recentWinner() == expected_winner.address
    assert expected_winner.balance() == (prev_account_balance + contract_balance)
    assert lottery_contract.balance() == 0