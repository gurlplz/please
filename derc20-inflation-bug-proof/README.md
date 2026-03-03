# DERC20 Inflation Compounding Bug - Proof

**Nika Finance** — $1M Bug Bounty Program  
**Verified Contract**: [0x242d6aA030Cd98aaDFe44192E11013406673EBa3](https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code) (Base)

## Summary

The `mintInflation()` function in `DERC20` contains an **unintentional compounding bug** that causes extra token issuance beyond the documented "maximum 2% per year" cap when multiple years pass without calling `mintInflation()`.

### Root Cause

```solidity
while (block.timestamp > currentYearStart_ + 365 days) {
    timeLeftInCurrentYear = (currentYearStart_ + 365 days - lastMintTimestamp_);
    yearMint = (supply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
    supply += yearMint;          // ← BUG: compounding line
    mintableAmount += yearMint;
    currentYearStart_ += 365 days;
    lastMintTimestamp_ = currentYearStart_;
}
```

The `supply += yearMint` mutates the base supply for the next iteration, creating intra-transaction compounding.

### Documented Intent (Contract NatSpec)

```solidity
/// @dev Maximum amount of tokens that can be minted in a year (% expressed in WAD)
uint256 constant MAX_YEARLY_MINT_RATE_WAD = 0.02 ether;
// Inflation can't be more than 2% of token supply per year
```

No mention of compounding or APY anywhere.

## Proof of Concept

### 1. Python (Exact Integer Math Replication)

```bash
python poc_inflation_compounding.py
```

**Expected output (2 years skipped):**
- Actual minted: 40,400 tokens (4.04%)
- Simple expected: 40,000 tokens (4.00%)
- **EXTRA: 400 tokens (+1.0% over cap)**

### 2. On-Chain (Foundry)

```bash
cd foundry-poc && forge test -vvv
```

### 3. Impact Summary

| Years skipped | Advertised mint | Actual mint | Extra to owner |
|---------------|-----------------|-------------|----------------|
| 1 year        | 2%              | 2%          | 0              |
| 2 years       | 4%              | 4.04%       | +40M tokens    |
| 3 years       | 6%              | 6.12%       | +121M tokens   |
| 5 years       | 10%             | 10.41%      | +408M tokens   |

(At 100B supply)

## Bounty Relevance

- **Scope**: "yield accrual and accounting", "fee/inflation logic"
- **Severity**: Medium–High (extra dilution beyond stated cap)
- **Affected**: All DERC20 clones (26+ index tokens)

## Files

- `poc_inflation_compounding.py` — Python PoC (exact math)
- `foundry-poc/` — Foundry test for on-chain reproduction
- `BOUNTY_REPORT.md` — Full report text for submission
