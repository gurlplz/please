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


def run_poc():
    S = 1_000_000 * 10**18  # 1M tokens initial supply
    R = int(0.02 * 10**18)  # 2% WAD rate (MAX_YEARLY_MINT_RATE_WAD)

    print("=" * 70)
    print("DERC20 INFLATION COMPOUNDING BUG - PROOF OF CONCEPT")
    print("=" * 70)
    print(f"Initial supply: {S / 10**18:,.0f} tokens")
    print(f"Yearly rate: 2% (WAD: {R})")
    print()

    test_cases = [
        (1, "exactly 1 year"),
        (2, "exactly 2 years"),
        (1.5, "1.5 years"),
        (3, "3 years"),
        (5, "5 years"),
    ]

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
