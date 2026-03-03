# Nika Finance Bug Bounty Report: DERC20 Inflation Compounding Bug

**Program**: Nika Finance $1M Bug Bounty  
**Scope**: Yield accrual and accounting, fee/inflation logic  
**Severity**: Medium–High  
**Date**: March 3, 2026

---

## Summary

The `mintInflation()` function in the verified DERC20 contract contains an **unintentional compounding bug** that causes extra token issuance beyond the documented "maximum 2% per year" cap when multiple years pass without calling `mintInflation()`.

**Contract**: [0x242d6aA030Cd98aaDFe44192E11013406673EBa3](https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code) (Base)

---

## Root Cause

The developer intended to "maintain inflation rate" across skipped years (catch-up logic). However, the `supply` variable is mutated inside the `while` loop, causing each full year to use the **inflated** supply as the base for the next year—i.e., compounding.

```solidity
// Handle any outstanding full years and updates to maintain inflation rate
while (block.timestamp > currentYearStart_ + 365 days) {
    timeLeftInCurrentYear = (currentYearStart_ + 365 days - lastMintTimestamp_);
    yearMint = (supply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
    supply += yearMint;          // ← BUG: creates compounding
    mintableAmount += yearMint;
    currentYearStart_ += 365 days;
    lastMintTimestamp_ = currentYearStart_;
}
```

**Documented intent** (contract NatSpec):
```solidity
/// @dev Maximum amount of tokens that can be minted in a year (% expressed in WAD)
uint256 constant MAX_YEARLY_MINT_RATE_WAD = 0.02 ether;
// Inflation can't be more than 2% of token supply per year
```

No mention of compounding anywhere. The bug contradicts the stated cap.

---

## Impact

| Years skipped | Advertised (2%/yr) | Actual minted | Extra to owner |
|---------------|--------------------|---------------|----------------|
| 1 year        | 2%                 | 2%            | 0              |
| 2 years       | 4%                 | 4.04%         | +1% over cap   |
| 3 years       | 6%                 | 6.12%         | +2% over cap   |
| 5 years       | 10%                | 10.41%        | +4% over cap   |

**At 100B Nika supply**: 2 years skipped → **40M extra tokens** to owner.

---

## Proof of Concept

### Python (exact integer math)

```bash
cd derc20-inflation-bug-proof && python3 poc_inflation_compounding.py
```

Output (2 years):
```
Actual minted   : 40,400.00 tokens (4.0400%)
Simple expected : 40,000.00 tokens (4.0000%)
EXTRA minted    : 400.00 tokens (+1.0000% over cap)
>>> BUG PROVEN
```

### On-chain (Foundry)

```bash
cd derc20-inflation-bug-proof/foundry-poc && forge test -vvv
```

---

## Affected Contracts

All DERC20 clones (26+ index tokens) use this template. Same bug in every instance.

---

## Recommendation

Use a **fixed base supply** for the catch-up loop instead of mutating `supply`:

```solidity
uint256 baseSupply = totalSupply();  // fixed at start
while (...) {
    yearMint = (baseSupply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
    // do NOT add to baseSupply
    mintableAmount += yearMint;
    ...
}
```

---

## Appendix: Contract Context

- **Template**: DERC20 (ERC20 + ERC20Votes + ERC20Permit + Ownable + vesting + inflation + pool lock)
- **Deployment**: TokenFactory pattern on Base
- **Current status**: Inflation not started (`currentYearStart = 0`), 0 economic impact to date—future risk only
