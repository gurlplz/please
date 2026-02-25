"""Income classification: labor vs capital. Core economic model."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class IncomeSource(Enum):
    """Income derived from labor or capital."""
    LABOR = "labor"      # Wages, salary, freelance, tips
    CAPITAL = "capital"  # Dividends, interest, rent, gains, royalties


class LaborType(Enum):
    """Labor income subcategories."""
    WAGES = "wages"
    SALARY = "salary"
    FREELANCE = "freelance"
    CONTRACTOR = "contractor"
    TIPS = "tips"
    BONUS = "bonus"
    COMMISSION = "commission"


class CapitalType(Enum):
    """Capital income subcategories."""
    DIVIDENDS = "dividends"
    INTEREST = "interest"
    RENT = "rent"
    CAPITAL_GAINS = "capital_gains"
    ROYALTIES = "royalties"
    BUSINESS_PROFIT = "business_profit"
    CRYPTO = "crypto"


@dataclass
class IncomeEntry:
    """Single income transaction."""
    amount: float
    source: IncomeSource
    sub_type: str  # LaborType or CapitalType value
    date: date
    description: str = ""
    institution: str = ""

    @property
    def is_labor(self) -> bool:
        return self.source == IncomeSource.LABOR

    @property
    def is_capital(self) -> bool:
        return self.source == IncomeSource.CAPITAL


@dataclass
class MoneyActivity:
    """Money movement that may trigger banking regulations."""
    amount: float
    activity_type: str  # deposit, withdrawal, transfer, cash
    date: date
    institution: str = ""
    description: str = ""


def classify_income(amount: float, sub_type: str, date: date, **kwargs) -> IncomeEntry:
    """Classify income as labor or capital."""
    labor_types = [e.value for e in LaborType]
    capital_types = [e.value for e in CapitalType]
    if sub_type.lower() in labor_types:
        source = IncomeSource.LABOR
    elif sub_type.lower() in capital_types:
        source = IncomeSource.CAPITAL
    else:
        source = IncomeSource.LABOR  # default
    return IncomeEntry(amount=amount, source=source, sub_type=sub_type, date=date, **kwargs)
