"""Banking laws applicability - maps money activities to regulations."""

from dataclasses import dataclass, field
from typing import Optional

# Key thresholds from US banking regulations
BSA_CASH_THRESHOLD = 10_000  # USD - Currency Transaction Report
FDIC_COVERAGE_PER_BANK = 250_000  # USD per depositor per institution
NCUA_COVERAGE = 250_000  # Same for credit unions


@dataclass
class BankingLaw:
    """A banking law/regulation with applicability rules."""
    name: str
    abbreviation: str
    applies_to: list[str]
    key_threshold: Optional[float]
    description: str


BANKING_LAWS = [
    BankingLaw(
        name="Bank Secrecy Act",
        abbreviation="BSA",
        applies_to=["cash_deposit", "cash_withdrawal", "cash_transaction"],
        key_threshold=BSA_CASH_THRESHOLD,
        description="CTR required for cash transactions exceeding $10,000 aggregate per day",
    ),
    BankingLaw(
        name="FDIC Insurance",
        abbreviation="FDIC",
        applies_to=["deposit", "savings", "checking"],
        key_threshold=FDIC_COVERAGE_PER_BANK,
        description="Deposit insurance up to $250,000 per depositor per institution",
    ),
    BankingLaw(
        name="NCUA Insurance",
        abbreviation="NCUA",
        applies_to=["deposit", "savings", "share_draft"],
        key_threshold=NCUA_COVERAGE,
        description="Credit union share insurance up to $250,000",
    ),
    BankingLaw(
        name="Truth in Lending Act",
        abbreviation="TILA",
        applies_to=["credit", "loan", "mortgage", "credit_card"],
        key_threshold=None,
        description="Disclosure of charges, APR, and terms for consumer credit",
    ),
    BankingLaw(
        name="Truth in Savings Act",
        abbreviation="TISA",
        applies_to=["savings", "deposit", "cd", "money_market"],
        key_threshold=None,
        description="Uniform disclosure of fees, rates, and account terms",
    ),
    BankingLaw(
        name="Electronic Fund Transfer Act",
        abbreviation="EFTA",
        applies_to=["eft", "ach", "wire", "debit", "atm"],
        key_threshold=None,
        description="Consumer protections for electronic transfers",
    ),
]


def get_applicable_laws(activity_type: str, amount: float = 0) -> list[dict]:
    """Return laws applicable to a money activity."""
    applicable = []
    activity_lower = activity_type.lower()
    for law in BANKING_LAWS:
        if any(a in activity_lower for a in law.applies_to):
            info = {
                "name": law.name,
                "abbrev": law.abbreviation,
                "description": law.description,
                "threshold": law.key_threshold,
                "your_amount": amount,
                "within_threshold": True,
            }
            if law.key_threshold and amount >= law.key_threshold:
                info["within_threshold"] = False
                info["action"] = f"Exceeds ${law.key_threshold:,.0f} - review required"
            elif law.key_threshold:
                info["action"] = f"Within ${law.key_threshold:,.0f} limit"
            applicable.append(info)
    return applicable


def fdic_coverage_optimizer(balances: dict[str, float]) -> dict:
    """Optimize deposit placement for maximum FDIC coverage."""
    covered = 0
    exposed = 0
    by_institution = {}
    for inst, bal in balances.items():
        if bal <= FDIC_COVERAGE_PER_BANK:
            covered += bal
            by_institution[inst] = {"balance": bal, "status": "fully_covered"}
        else:
            covered += FDIC_COVERAGE_PER_BANK
            exposed += bal - FDIC_COVERAGE_PER_BANK
            by_institution[inst] = {
                "balance": bal,
                "status": "excess",
                "excess": bal - FDIC_COVERAGE_PER_BANK,
            }
    return {
        "total_covered": covered,
        "total_exposed": exposed,
        "by_institution": by_institution,
        "recommendation": "Spread excess across additional institutions" if exposed > 0 else "All deposits within FDIC limits",
    }
