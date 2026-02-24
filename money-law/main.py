#!/usr/bin/env python3
"""
Money Law – Maximize banking law applicability to your money management.

Income is a game derived from labor or capital.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from banking_laws import BANKING_LAWS, get_applicable_laws, fdic_coverage_optimizer
from models import IncomeEntry, IncomeSource, LaborType, CapitalType, classify_income


DATA_DIR = Path(__file__).parent / "data"
INCOME_FILE = DATA_DIR / "income.jsonl"
BALANCES_FILE = DATA_DIR / "balances.json"
ACTIVITIES_FILE = DATA_DIR / "activities.jsonl"


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_income() -> list[dict]:
    if not INCOME_FILE.exists():
        return []
    return [json.loads(line) for line in INCOME_FILE.read_text().splitlines() if line.strip()]


def save_income(entries: list[dict]):
    ensure_data_dir()
    INCOME_FILE.write_text("\n".join(json.dumps(e) for e in entries))


def load_balances() -> dict:
    if not BALANCES_FILE.exists():
        return {}
    return json.loads(BALANCES_FILE.read_text())


def save_balances(balances: dict):
    ensure_data_dir()
    BALANCES_FILE.write_text(json.dumps(balances, indent=2))


def cmd_add_income(args):
    """Add income entry (labor or capital)."""
    entries = load_income()
    entry = {
        "amount": args.amount,
        "source": args.source,
        "sub_type": args.sub_type,
        "date": args.date,
        "description": args.description or "",
    }
    entries.append(entry)
    save_income(entries)
    laws = get_applicable_laws("deposit", args.amount)
    print(f"Added: ${args.amount:,.2f} ({args.source}/{args.sub_type})")
    if laws:
        print("  Applicable laws:", ", ".join(l["abbrev"] for l in laws))


def cmd_add_balance(args):
    """Set balance for an institution (for FDIC optimization)."""
    balances = load_balances()
    balances[args.institution] = args.amount
    save_balances(balances)
    print(f"Set {args.institution}: ${args.amount:,.2f}")


def cmd_summary(args):
    """Show income breakdown (labor vs capital) and applicable laws."""
    entries = load_income()
    labor_total = sum(e["amount"] for e in entries if e.get("source") == "labor")
    capital_total = sum(e["amount"] for e in entries if e.get("source") == "capital")
    total = labor_total + capital_total

    print("\n=== INCOME (Labor vs Capital) ===")
    print(f"  Labor:  ${labor_total:,.2f} ({100*labor_total/total:.1f}%)" if total else "  Labor:  $0")
    print(f"  Capital: ${capital_total:,.2f} ({100*capital_total/total:.1f}%)" if total else "  Capital: $0")
    print(f"  Total:  ${total:,.2f}")

    print("\n=== BANKING LAWS APPLICABLE ===")
    for law in BANKING_LAWS:
        print(f"  {law.abbreviation}: {law.name}")
        print(f"    → {law.description}")

    balances = load_balances()
    if balances:
        print("\n=== FDIC COVERAGE OPTIMIZER ===")
        opt = fdic_coverage_optimizer(balances)
        print(f"  Covered: ${opt['total_covered']:,.2f}")
        print(f"  Exposed: ${opt['total_exposed']:,.2f}")
        print(f"  {opt['recommendation']}")
        for inst, info in opt["by_institution"].items():
            print(f"    {inst}: ${info['balance']:,.2f} – {info['status']}")


def cmd_laws(args):
    """Check which laws apply to an activity."""
    laws = get_applicable_laws(args.activity, args.amount or 0)
    print(f"\nLaws applicable to '{args.activity}' (amount: ${args.amount or 0:,.2f}):\n")
    for l in laws:
        print(f"  {l['abbrev']} – {l['name']}")
        print(f"    {l['description']}")
        if l.get("action"):
            print(f"    → {l['action']}")
        print()


def cmd_dashboard(args):
    """Run interactive dashboard (requires streamlit)."""
    try:
        import subprocess
        import sys
        app = Path(__file__).parent / "app.py"
        if app.exists():
            subprocess.run([sys.executable, "-m", "streamlit", "run", str(app), "--server.headless", "true"])
        else:
            print("Run: python main.py summary")
    except ImportError:
        print("Install streamlit for dashboard: pip install streamlit")
        cmd_summary(args)


def main():
    parser = argparse.ArgumentParser(
        description="Money Law – Maximize banking law applicability. Income = labor + capital."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # add-income
    p = sub.add_parser("add-income", help="Add income (labor or capital)")
    p.add_argument("amount", type=float)
    p.add_argument("source", choices=["labor", "capital"])
    p.add_argument("sub_type", help="e.g. wages, dividends, salary, interest")
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--description", "-d", default="")
    p.set_defaults(func=cmd_add_income)

    # add-balance
    p = sub.add_parser("add-balance", help="Set institution balance (for FDIC)")
    p.add_argument("institution")
    p.add_argument("amount", type=float)
    p.set_defaults(func=cmd_add_balance)

    # summary
    p = sub.add_parser("summary", help="Income breakdown + applicable laws")
    p.set_defaults(func=cmd_summary)

    # laws
    p = sub.add_parser("laws", help="Check laws for an activity")
    p.add_argument("activity", help="e.g. deposit, cash_deposit, credit")
    p.add_argument("--amount", type=float, default=0)
    p.set_defaults(func=cmd_laws)

    # dashboard
    p = sub.add_parser("dashboard", help="Web dashboard")
    p.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
