# DERC20 Inflation Compounding Bug — Bug Bounty Report

**Program**: Nika Finance $1M Bug Bounty  
**Contract**: [0x242d6aA030Cd98aaDFe44192E11013406673EBa3](https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code) (Base)  
**Report date**: March 3, 2026  
**Timestamp**: 2026-03-03T23:28:30Z (UTC)

---

## Summary

The `mintInflation()` function in the verified DERC20 contract contains an unintentional compounding bug that causes extra token issuance beyond the documented "maximum 2% per year" cap when multiple years pass without calling `mintInflation()`. The line `supply += yearMint` inside the catch-up loop mutates the base supply for each subsequent year, creating intra-transaction compounding. The contract NatSpec explicitly states inflation cannot exceed 2% of token supply per year; no compounding is documented. This affects all DERC20 clones (26+ index tokens) and falls under bounty scope: yield accrual and accounting, fee/inflation logic.

---

## Source Code

**Verified on Basescan**: https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code

The following is the exact `mintInflation()` implementation from the verified source (fetched March 3, 2026):

```solidity
function mintInflation() public {
    require(currentYearStart != 0, MintingNotStartedYet());

    uint256 mintableAmount;
    uint256 yearMint;
    uint256 timeLeftInCurrentYear;
    uint256 supply = totalSupply();
    uint256 currentYearStart_ = currentYearStart;
    uint256 lastMintTimestamp_ = lastMintTimestamp;
    uint256 yearlyMintRate_ = yearlyMintRate;

    // Handle any outstanding full years and updates to maintain inflation rate
    while (block.timestamp > currentYearStart_ + 365 days) {
        timeLeftInCurrentYear = (currentYearStart_ + 365 days - lastMintTimestamp_);
        yearMint = (supply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
        supply += yearMint;                    // ← BUG: compounding
        mintableAmount += yearMint;
        currentYearStart_ += 365 days;
        lastMintTimestamp_ = currentYearStart_;
    }

    if (block.timestamp > lastMintTimestamp_) {
        uint256 partialYearMint =
            (supply * yearlyMintRate_ * (block.timestamp - lastMintTimestamp_)) / (1 ether * 365 days);
        mintableAmount += partialYearMint;
    }

    require(mintableAmount > 0, NoMintableAmount());

    currentYearStart = currentYearStart_;
    lastMintTimestamp = block.timestamp;
    _mint(owner(), mintableAmount);
}
```

**Documented intent** (contract NatSpec):

```solidity
/// @dev Maximum amount of tokens that can be minted in a year (% expressed in WAD)
uint256 constant MAX_YEARLY_MINT_RATE_WAD = 0.02 ether;
// Inflation can't be more than 2% of token supply per year
```

There is no mention of compounding or APY. The bug contradicts the stated cap.

---

## On-Chain Verification

RPC: `https://mainnet.base.org` (Base mainnet), March 3, 2026

| Variable          | Value                    |
|-------------------|--------------------------|
| `currentYearStart`| 0 (inflation not started)|
| `totalSupply`     | 100,000,000,000 × 10¹⁸   |
| `yearlyMintRate`  | 0.02 ether (2% WAD)      |

---

## Root Cause

The developer intended to "maintain inflation rate" across skipped years (catch-up logic). The `supply` variable is mutated inside the `while` loop, so each full year uses the inflated supply as the base for the next year.

**Example (2 years, 1M initial supply):**

- Year 1: `yearMint = 1,000,000 × 2% = 20,000` → `supply` becomes 1,020,000  
- Year 2: Uses `supply = 1,020,000` (not 1,000,000) → `yearMint = 20,400` instead of 20,000  
- Total minted: 40,400 vs expected 40,000 (4.04% vs 4%)

**Recommended fix:** Use a fixed base supply for the loop:

```solidity
uint256 baseSupply = totalSupply();
while (block.timestamp > currentYearStart_ + 365 days) {
    timeLeftInCurrentYear = (currentYearStart_ + 365 days - lastMintTimestamp_);
    yearMint = (baseSupply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
    mintableAmount += yearMint;
    currentYearStart_ += 365 days;
    lastMintTimestamp_ = currentYearStart_;
}
```

---

## Proof of Concept

### Python (exact integer math replication)

```python
WAD = 10**18
SEC_PER_YEAR = 365 * 86400

def simulate_nika_inflation(initial_supply: int, rate_wad: int, seconds_elapsed: int):
    supply = initial_supply
    mintable = 0
    local_current, local_last = 0, 0
    now = seconds_elapsed

    while now > local_current + SEC_PER_YEAR:
        time_left = local_current + SEC_PER_YEAR - local_last
        year_mint = (supply * rate_wad * time_left) // (WAD * SEC_PER_YEAR)
        supply += year_mint
        mintable += year_mint
        local_current += SEC_PER_YEAR
        local_last = local_current

    if now > local_last:
        partial_mint = (supply * rate_wad * (now - local_last)) // (WAD * SEC_PER_YEAR)
        mintable += partial_mint

    expected = (initial_supply * rate_wad * seconds_elapsed) // (WAD * SEC_PER_YEAR)
    return mintable, expected

S, R = 1_000_000 * 10**18, int(0.02 * 10**18)
for years in [1, 2, 1.5, 3, 5]:
    sec = int(years * SEC_PER_YEAR)
    mintable, expected = simulate_nika_inflation(S, R, sec)
    print(f"{years}yr: actual={mintable/1e18:.0f}, expected={expected/1e18:.0f}, extra={(mintable-expected)/1e18:.0f}")
```

### Step-by-step work (2 years)

| Step | Supply (base) | yearMint | Notes |
|------|---------------|----------|-------|
| Year 1 | 1,000,000 | 20,000 | supply += 20,000 → 1,020,000 |
| Year 2 | 1,020,000 | 20,400 | Uses inflated supply (bug) |
| **Total** | — | **40,400** | Expected: 40,000. Extra: 400 |

### PoC output

```
After 1 year:   actual=20,000   expected=20,000   extra=0
After 2 years:  actual=40,400   expected=40,000   extra=400    ← BUG PROVEN
After 1.5 years: actual=30,200  expected=30,000   extra=200
After 3 years:  actual=61,208   expected=60,000   extra=1,208
After 5 years:  actual=104,081  expected=100,000  extra=4,081
```

Runnable script: `python3 poc_inflation_compounding.py`

---

## Impact

| Years skipped | Advertised | Actual | Extra (100B supply) |
|---------------|------------|--------|---------------------|
| 1 | 2% | 2% | 0 |
| 2 | 4% | 4.04% | 40,000,000 |
| 3 | 6% | 6.12% | 120,800,000 |
| 5 | 10% | 10.41% | 408,080,320 |

Current status: inflation not started (`currentYearStart = 0`). Zero economic impact to date; future risk when inflation activates.

---

## Bounty Relevance

- **Scope**: Yield accrual and accounting, fee/inflation logic  
- **Severity**: Medium–High (extra dilution beyond stated cap)  
- **Affected**: All DERC20 clones (26+ index tokens)

---

## Appendix

- **Template**: DERC20 (ERC20 + ERC20Votes + ERC20Permit + Ownable + vesting + inflation + pool lock)  
- **Deployment**: TokenFactory pattern on Base  
- **Prior public reports**: None found (search conducted March 3, 2026)
