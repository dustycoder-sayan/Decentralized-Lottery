from brownie import (
    accounts, 
    network, 
    config, 
    MockV3Aggregator, 
    VRFCoordinatorMock, 
    LinkToken, 
    Contract,
    interface
)

DEVELOPMENT_ENVIRONMENTS = [
    "development",
    "ganache-local"
]

FORKED_ENVIRONMENTS = [
    "mainnet-fork"
]

NAME_TO_CONTRACT_MAP = {
    config["contracts"]["ETH_USD_PRICE_FEED"]: MockV3Aggregator,
    config["contracts"]["VRF_COORDINATOR"]: VRFCoordinatorMock,
    config["contracts"]["LINK_TOKEN"]: LinkToken,
}

AGGREGATOR_DECIMALS = 8
AGGREGATOR_STARTING_ANSWER = 20_000_000_000

def get_account(account_index=None, account_id=None):
    if account_index:
        return accounts[account_index]
    if account_id:
        return accounts.load(account_id)
    
    if network.show_active() in DEVELOPMENT_ENVIRONMENTS or network.show_active() in FORKED_ENVIRONMENTS:
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])

def get_contract(contract_name):
    contract_type = NAME_TO_CONTRACT_MAP.get(contract_name, None)
    if contract_type != None:
        if network.show_active() in DEVELOPMENT_ENVIRONMENTS:
            # If on a development network, deploy a mock on local chain if not yet mocked, else get the most recently deployed mock
            if len(contract_type) <= 0:
                deploy_mocks()
            contract = contract_type[-1]
        else:
            # If on a testnet or mainnet, get address of already deployed contract
            contract_address = config["networks"][network.show_active()][contract_name]
            contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)      # Deploy the contract using contract name, address and abi
        return contract
    raise ValueError(f"No contract named {contract_name} exists")

def deploy_mocks(decimals=AGGREGATOR_DECIMALS, starting_ans=AGGREGATOR_STARTING_ANSWER):
    print("Deploying Mocks...")
    MockV3Aggregator.deploy(
        decimals, 
        starting_ans, 
        {
            "from": get_account()
        }
    )
    link_contract = LinkToken.deploy(
        {
            "from": get_account()
        }
    )
    VRFCoordinatorMock.deploy(
        link_contract.address, 
        {
            "from": get_account()
        }
    )
    print("Mocks deployment Successful !")

def fund_contract_with_link(contract_address, account=None, link_token=None, amount=10 ** 17):
    account = account if account else get_account()
    # directly using the link token contract
    link_token_contract = link_token if link_token else get_contract(config["contracts"]["LINK_TOKEN"])

    # using the link token interface
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    
    txn = link_token_contract.transfer(
        contract_address, 
        amount, 
        {
            "from": account
        }
    )
    txn.wait(1)

    print("Smart contract funded with LINK !")
    return txn