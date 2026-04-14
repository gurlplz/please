// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title $ORIGIN — lightweight ERC-20 used for weekly originality rewards on Base.
contract OriginToken is ERC20, Ownable {
    /// @notice Optional faucet for Base Sepolia demos (disabled on unknown chains).
    mapping(address => bool) public demoMintUsed;

    constructor(address initialOwner) ERC20("Originality Earns", "ORIGIN") Ownable(initialOwner) {}

    /// @dev Minting is owner-only for the MVP. The owner is typically a multisig or deployer wallet.
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @dev One-time demo mint for connected testers on Base Sepolia (chain id 84532).
    function demoMint() external {
        require(block.chainid == 84532, "OriginToken: demo disabled");
        require(!demoMintUsed[msg.sender], "OriginToken: already used");
        demoMintUsed[msg.sender] = true;
        _mint(msg.sender, 1_000 ether);
    }
}
