// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {OriginToken} from "../src/OriginToken.sol";

contract OriginTokenTest is Test {
    OriginToken internal token;

    function setUp() public {
        token = new OriginToken(address(this));
    }

    function testMint() public {
        token.mint(address(0xBEEF), 10 ether);
        assertEq(token.balanceOf(address(0xBEEF)), 10 ether);
    }
}
