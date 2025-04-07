// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import {AggregatorV3Interface} from "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";
import {VRFConsumerBase} from "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is Ownable, VRFConsumerBase {
    enum LOTTERY_STATE {
        OPEN,                   // 0
        CLOSED,                 // 1
        CALCULATING_WINNER      // 2
    }

    address payable[] public players;
    address payable public recentWinner;
    uint256 public feeInUsd;
    AggregatorV3Interface priceFeed;
    LOTTERY_STATE public lotteryState;
    uint256 public fee;
    bytes32 public keyHash;

    // VRFConsumerBase constructor also called 
    // 0 - chainlink contract address which gives random number (VRF Consumer address)
    // 1 - link token payment address for chainlink
    constructor(
        address _priceFeedAddress,  
        address _vrfCoordinator,    // address of the chainlink contract on chain
        address _link,              // address of the link token of chainlink on the corresponding network
        uint256 _fee,                // fee to be paid to the chainlink contract in terms of link
        bytes32 _keyHash
        )
        public
        VRFConsumerBase(
            _vrfCoordinator,
            _link
        ) 
    {
        feeInUsd = 50 * (10 ** 18);
        priceFeed = AggregatorV3Interface(_priceFeedAddress);
        lotteryState = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyHash = _keyHash;
    }

    // function to allow users to enter to the lottery by paying a certain fee
    function enter() public payable {
        require(lotteryState == LOTTERY_STATE.OPEN, "Lottery is closed !");
        uint256 amountSentInWei = msg.value;
        uint256 requiredFeeInUsd = getEntranceFee(); 
        require(amountSentInWei >= requiredFeeInUsd, "Not enough ETH !");
        players.push(payable(msg.sender));
    }

    // Get the entrance fee of the lottery
    function getEntranceFee() public view returns(uint256) {
        uint256 costToEnter = (feeInUsd * 10**18) / getEthValueInUsd();
        return costToEnter;
    }

    // Start the lottery (by admin only)
    function startLottery() public onlyOwner {
        require(lotteryState == LOTTERY_STATE.CLOSED, "Lottery is already open !");
        lotteryState = LOTTERY_STATE.OPEN;
    }

    // End the lottery (by admin only)
    function endLottery() public onlyOwner {
        lotteryState = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyHash, fee);

    }

    function getEthValueInUsd() public view returns(uint256) {
        (,int256 price,,,) = priceFeed.latestRoundData();
        return uint256(price) * (10**11);
    }

    function pickRandomWinner() private view returns(address) {
        
    }

    // override the fulfillRandomness function
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override {
        require(lotteryState == LOTTERY_STATE.CALCULATING_WINNER, "You aren't there yet !");
        require(_randomness > 0, "Random Number not found !");

        uint256 randomPlayer = _randomness % players.length;
        recentWinner = players[randomPlayer];

        // Transfer all amount of the contract to the winner
        recentWinner.transfer(address(this).balance);

        players = new address payable[](0);
        lotteryState = LOTTERY_STATE.CLOSED;
    }
}