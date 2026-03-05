// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";

/**
 * @title DERC20 Inflation Compounding Bug - Proof of Concept
 * @notice Reproduces the exact mintInflation() logic from verified DERC20
 *         Contract: 0x242d6aA030Cd98aaDFe44192E11013406673EBa3 (Base)
 * @dev Run: forge test -vvv
 */
contract DERC20InflationBugTest is Test {
    uint256 constant WAD = 1 ether;
    uint256 constant SEC_PER_YEAR = 365 days;
    uint256 constant MAX_YEARLY_MINT_RATE_WAD = 0.02 ether;

    function test_InflationCompoundingBug_2Years() public {
        uint256 initialSupply = 1_000_000 * 1e18;
        uint256 rate = MAX_YEARLY_MINT_RATE_WAD;
        uint256 currentYearStart = 0;
        uint256 lastMintTimestamp = 0;
        uint256 supply = initialSupply;

        // Simulate 2 years passing
        vm.warp(2 * SEC_PER_YEAR);
        uint256 now_ = block.timestamp;

        uint256 mintableAmount;
        uint256 currentYearStart_ = currentYearStart;
        uint256 lastMintTimestamp_ = lastMintTimestamp;
        uint256 yearlyMintRate_ = rate;

        // Exact contract logic (buggy)
        while (now_ > currentYearStart_ + SEC_PER_YEAR) {
            uint256 timeLeftInCurrentYear = (currentYearStart_ + SEC_PER_YEAR - lastMintTimestamp_);
            uint256 yearMint = (supply * yearlyMintRate_ * timeLeftInCurrentYear) / (WAD * SEC_PER_YEAR);
            supply += yearMint;  // BUG: compounding
            mintableAmount += yearMint;
            currentYearStart_ += SEC_PER_YEAR;
            lastMintTimestamp_ = currentYearStart_;
        }

        if (now_ > lastMintTimestamp_) {
            uint256 partialYearMint = (supply * yearlyMintRate_ * (now_ - lastMintTimestamp_)) / (WAD * SEC_PER_YEAR);
            mintableAmount += partialYearMint;
        }

        // Expected: simple 2% * 2 years = 4%
        uint256 expectedSimple = (initialSupply * rate * (2 * SEC_PER_YEAR)) / (WAD * SEC_PER_YEAR);

        assertGt(mintableAmount, expectedSimple, "Bug: actual should exceed simple expected");
        assertEq(expectedSimple, 40_000 * 1e18, "Expected 40k tokens for 4%");
        assertEq(mintableAmount, 40_400 * 1e18, "Actual is 40.4k due to compounding");
    }

    function test_CorrectLogic_NoCompounding() public pure {
        // Correct approach: use fixed base supply for each year
        uint256 initialSupply = 1_000_000 * 1e18;
        uint256 rate = MAX_YEARLY_MINT_RATE_WAD;
        uint256 yearsElapsed = 2;

        uint256 correctMint = (initialSupply * rate * yearsElapsed * SEC_PER_YEAR) / (WAD * SEC_PER_YEAR);
        assertEq(correctMint, 40_000 * 1e18, "Correct: 4% = 40k");
    }
}
