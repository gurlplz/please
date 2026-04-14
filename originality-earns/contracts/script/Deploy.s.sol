// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console2} from "forge-std/Script.sol";
import {OriginToken} from "../src/OriginToken.sol";
import {RewardDistributor} from "../src/RewardDistributor.sol";

contract DeployScript is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(pk);

        address deployer = vm.addr(pk);
        OriginToken token = new OriginToken(deployer);
        RewardDistributor distributor = new RewardDistributor(deployer, token);

        // Fund the distributor for immediate testing; tune for production.
        token.mint(address(distributor), 1_000_000 ether);

        console2.log("ORIGIN_TOKEN=", address(token));
        console2.log("REWARD_DISTRIBUTOR=", address(distributor));

        vm.stopBroadcast();
    }
}
