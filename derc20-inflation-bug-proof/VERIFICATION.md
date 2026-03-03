# Live Contract Verification

**Contract**: `0x242d6aA030Cd98aaDFe44192E11013406673EBa3` (Base)  
**Verified**: March 3, 2026

---

## 1. Verified Source Code (Basescan)

Fetched from: https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code

**mintInflation() — exact lines from verified source:**

```solidity
function mintInflation() public {
    require(currentYearStart != 0, MintingNotStartedYet());
    ...
    // Handle any outstanding full years and updates to maintain inflation rate
    while (block.timestamp > currentYearStart_ + 365 days) {
        timeLeftInCurrentYear = (currentYearStart_ + 365 days - lastMintTimestamp_);
        yearMint = (supply * yearlyMintRate_ * timeLeftInCurrentYear) / (1 ether * 365 days);
        supply += yearMint;          // ← BUG: compounding line (CONFIRMED)
        mintableAmount += yearMint;
        currentYearStart_ += 365 days;
        lastMintTimestamp_ = currentYearStart_;
    }
    ...
}
```

**Confirmed**: The line `supply += yearMint` exists in the live verified contract.

---

## 2. On-Chain State (RPC: mainnet.base.org)

| Variable          | Value              | Interpretation                    |
|-------------------|--------------------|-----------------------------------|
| `currentYearStart`| `0`                | Inflation not started             |
| `totalSupply`     | `100,000,000,000` (× 10¹⁸) | 100B tokens              |
| `yearlyMintRate`  | `0.02 ether`       | 2% WAD (MAX_YEARLY_MINT_RATE)     |

---

## 3. Conclusion

- **Source**: Buggy `supply += yearMint` line is present in the verified Basescan source.
- **State**: Contract matches expected configuration (100B supply, 2% rate, inflation inactive).
- **PoC**: Python simulation reproduces the compounding behavior with the same logic.

**Verification status: CONFIRMED**
