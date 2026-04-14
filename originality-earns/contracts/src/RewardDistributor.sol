// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title RewardDistributor — owner-only weekly payouts from a pre-funded balance.
contract RewardDistributor is Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable token;

    event Distributed(address indexed recipient, uint256 amount);

    constructor(address initialOwner, IERC20 token_) Ownable(initialOwner) {
        token = token_;
    }

    /// @notice Pull-based claim for recipients configured by the owner each week.
    mapping(address => uint256) public claimable;

    /// @dev Owner sets the weekly claimable map (MVP: replaces prior entries per recipient passed).
    function setWeeklyClaims(address[] calldata recipients, uint256[] calldata amounts) external onlyOwner {
        require(recipients.length == amounts.length, "RewardDistributor: length mismatch");
        for (uint256 i = 0; i < recipients.length; i++) {
            claimable[recipients[i]] = amounts[i];
        }
    }

    /// @notice Push model weekly payout — requires this contract to hold sufficient $ORIGIN.
    function distribute(address[] calldata recipients, uint256[] calldata amounts) external onlyOwner {
        require(recipients.length == amounts.length, "RewardDistributor: length mismatch");
        for (uint256 i = 0; i < recipients.length; i++) {
            token.safeTransfer(recipients[i], amounts[i]);
            emit Distributed(recipients[i], amounts[i]);
        }
    }

    /// @notice Transfer configured rewards to the caller if they have a non-zero claimable balance.
    function claim() external {
        uint256 amount = claimable[msg.sender];
        require(amount > 0, "RewardDistributor: nothing to claim");
        claimable[msg.sender] = 0;
        token.safeTransfer(msg.sender, amount);
        emit Distributed(msg.sender, amount);
    }

    /// @dev Escape hatch if the owner prefunds this contract but needs to recover tokens.
    function rescue(address to, uint256 amount) external onlyOwner {
        token.safeTransfer(to, amount);
    }
}
