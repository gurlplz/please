#!/usr/bin/env python3
"""
Proof-of-Concept: DERC20 Inflation Compounding Bug
Nika Finance - Verified Contract: 0x242d6aA030Cd98aaDFe44192E11013406673EBa3 (Base)
https://basescan.org/address/0x242d6aA030Cd98aaDFe44192E11013406673EBa3#code

This script replicates the EXACT integer math from mintInflation() to prove
the supply += yearMint line creates unintended compounding beyond the 2%/year cap.
"""

WAD = 10**18
SEC_PER_YEAR = 365 * 86400


def simulate_nika_inflation(
    initial_supply: int, rate_wad: int, seconds_elapsed: int
) -> tuple[int, int, int]:
    """
    Exact replication of DERC20 mintInflation() logic.
    Returns (mintable, expected_simple, extra)
    """
    supply = initial_supply
    mintable = 0
    current_start = 0
    last_mint = 0
    now = seconds_elapsed

    local_supply = supply
    local_current = current_start
    local_last = last_mint
    local_rate = rate_wad

    # Handle any outstanding full years (same while loop as contract)
    while now > local_current + SEC_PER_YEAR:
        time_left = local_current + SEC_PER_YEAR - local_last
        year_mint = (local_supply * local_rate * time_left) // (WAD * SEC_PER_YEAR)
        local_supply += year_mint  # ← BUG: compounding line
        mintable += year_mint
        local_current += SEC_PER_YEAR
        local_last = local_current

    # Handle partial current year
    if now > local_last:
        partial_time = now - local_last
        partial_mint = (local_supply * local_rate * partial_time) // (WAD * SEC_PER_YEAR)
        mintable += partial_mint

    # Simple expected (no compounding): 2% per year linear
    expected_simple = (initial_supply * rate_wad * seconds_elapsed) // (WAD * SEC_PER_YEAR)
    extra = mintable - expected_simple

    return mintable, expected_simple, extra


def show_work(initial_supply: int, rate_wad: int, years: float):
    """Step-by-step derivation showing the compounding bug."""
    S = initial_supply
    R = rate_wad
    SEC = int(years * SEC_PER_YEAR)
    now = SEC

    print("\n" + "=" * 70)
    print(f"STEP-BY-STEP WORK: {years} years elapsed")
    print("=" * 70)
    print(f"  Initial supply S₀ = {S / 10**18:,.0f} tokens")
    print(f"  Rate r = 2% (WAD)")
    print(f"  Formula: yearMint = supply × r × time / (1e18 × 365 days)")
    print()

    supply = S
    mintable = 0
    local_current = 0
    local_last = 0
    iter_num = 0

    while now > local_current + SEC_PER_YEAR:
        iter_num += 1
        time_left = local_current + SEC_PER_YEAR - local_last
        year_mint = (supply * R * time_left) // (WAD * SEC_PER_YEAR)

        print(f"  --- Iteration {iter_num} (Year {iter_num}) ---")
        print(f"      supply (base for this year) = {supply / 10**18:,.2f}")
        print(f"      timeLeftInCurrentYear      = {time_left} sec (= 1 year)")
        print(f"      yearMint = {supply / 10**18:,.0f} × 0.02 × {time_left} / (1e18 × {SEC_PER_YEAR})")
        print(f"             = {year_mint / 10**18:,.2f} tokens")
        print(f"      supply += yearMint  →  supply = {supply / 10**18:,.2f} + {year_mint / 10**18:,.2f} = {(supply + year_mint) / 10**18:,.2f}  ← BUG: inflated for next iter")
        print()

        supply += year_mint
        mintable += year_mint
        local_current += SEC_PER_YEAR
        local_last = local_current

    if now > local_last:
        partial_time = now - local_last
        partial_mint = (supply * R * partial_time) // (WAD * SEC_PER_YEAR)
        print(f"  --- Partial year (remaining {partial_time} sec) ---")
        print(f"      supply (now INFLATED) = {supply / 10**18:,.2f}")
        print(f"      partialMint = {supply / 10**18:,.0f} × 0.02 × {partial_time} / (1e18 × {SEC_PER_YEAR})")
        print(f"                 = {partial_mint / 10**18:,.2f} tokens")
        mintable += partial_mint

    expected_simple = (S * R * SEC) // (WAD * SEC_PER_YEAR)
    extra = mintable - expected_simple

    print()
    print("  --- RESULT ---")
    print(f"      Actual minted (with bug)  : {mintable / 10**18:,.2f} tokens")
    print(f"      Simple expected (2%×yr)   : {expected_simple / 10**18:,.2f} tokens")
    print(f"      EXTRA (compounding effect): {extra / 10**18:,.2f} tokens")
    print()


def run_poc():
    S = 1_000_000 * 10**18  # 1M tokens initial supply
    R = int(0.02 * 10**18)  # 2% WAD rate (MAX_YEARLY_MINT_RATE_WAD)

    print("=" * 70)
    print("DERC20 INFLATION COMPOUNDING BUG - PROOF OF CONCEPT")
    print("=" * 70)
    print(f"Initial supply: {S / 10**18:,.0f} tokens")
    print(f"Yearly rate: 2% (WAD: {R})")
    print()

    # Show step-by-step work for 2-year case (clearest proof)
    show_work(S, R, 2.0)

    test_cases = [
        (1, "exactly 1 year"),
        (2, "exactly 2 years"),
        (1.5, "1.5 years"),
        (3, "3 years"),
        (5, "5 years"),
    ]

    print("=" * 70)
    print("SUMMARY (all test cases)")
    print("=" * 70)
    for years, desc in test_cases:
        seconds = int(years * SEC_PER_YEAR)
        mintable, expected, extra = simulate_nika_inflation(S, R, seconds)

        pct_actual = (mintable * 100) / S
        pct_expected = (expected * 100) / S
        print(f"After {years} year(s) ({desc}):")
        print(f"  Actual minted   : {mintable / 10**18:,.2f} tokens ({pct_actual:.4f}%)")
        print(f"  Simple expected : {expected / 10**18:,.2f} tokens ({pct_expected:.4f}%)")
        print(f"  EXTRA minted    : {extra / 10**18:,.2f} tokens (+{extra * 100 / expected:.4f}% over cap)")
        if extra > 0:
            print(f"  >>> BUG PROVEN: {extra / 10**18:,.0f} tokens issued beyond documented 2%/year cap")
        print()

    # Scale to 100B Nika (live token supply)
    print("=" * 70)
    print("SCALED TO LIVE NIKA TOKEN (100 billion supply)")
    print("=" * 70)
    S_100B = 100_000_000_000 * 10**18
    for years in [2, 3, 5]:
        seconds = int(years * SEC_PER_YEAR)
        mintable, expected, extra = simulate_nika_inflation(S_100B, R, seconds)
        print(f"After {years} years skipped: {extra / 10**18:,.0f} extra tokens to owner")
    print()


if __name__ == "__main__":
    run_poc()
