"""Streamlit dashboard for Money Law."""

import streamlit as st
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from banking_laws import BANKING_LAWS, get_applicable_laws, fdic_coverage_optimizer, BSA_CASH_THRESHOLD, FDIC_COVERAGE_PER_BANK
from main import load_income, save_income, load_balances, save_balances, DATA_DIR, INCOME_FILE

st.set_page_config(page_title="Money Law", page_icon="⚖️", layout="wide")
st.title("⚖️ Money Law")
st.caption("Income is a game derived from labor or capital. Maximize banking law applicability.")

# Sidebar
st.sidebar.header("Add Data")
with st.sidebar.form("add_income"):
    amount = st.number_input("Amount ($)", min_value=0.0, step=100.0)
    source = st.selectbox("Source", ["labor", "capital"])
    sub_type = st.text_input("Type", placeholder="wages, dividends, salary, interest")
    desc = st.text_input("Description", placeholder="Optional")
    if st.form_submit_button("Add Income"):
        entries = load_income()
        entries.append({
            "amount": amount,
            "source": source,
            "sub_type": sub_type,
            "date": str(__import__("datetime").date.today()),
            "description": desc,
        })
        save_income(entries)
        st.success("Added!")

with st.sidebar.form("add_balance"):
    inst = st.text_input("Institution")
    bal = st.number_input("Balance ($)", min_value=0.0, step=1000.0)
    if st.form_submit_button("Set Balance"):
        balances = load_balances()
        balances[inst] = bal
        save_balances(balances)
        st.success("Updated!")

# Main
col1, col2, col3 = st.columns(3)

entries = load_income()
labor = sum(e["amount"] for e in entries if e.get("source") == "labor")
capital = sum(e["amount"] for e in entries if e.get("source") == "capital")
total = labor + capital

with col1:
    st.metric("Labor Income", f"${labor:,.0f}", f"{100*labor/total:.0f}%" if total else "0%")
with col2:
    st.metric("Capital Income", f"${capital:,.0f}", f"{100*capital/total:.0f}%" if total else "0%")
with col3:
    st.metric("Total", f"${total:,.0f}", "")

st.divider()
st.subheader("Banking Laws – Applicability")

for law in BANKING_LAWS:
    with st.expander(f"**{law.abbreviation}** – {law.name}"):
        st.write(law.description)
        if law.key_threshold:
            st.metric("Key Threshold", f"${law.key_threshold:,.0f}", "")

st.subheader("FDIC Coverage Optimizer")
balances = load_balances()
if balances:
    opt = fdic_coverage_optimizer(balances)
    st.write(f"**Covered:** ${opt['total_covered']:,.0f} | **Exposed:** ${opt['total_exposed']:,.0f}")
    st.info(opt["recommendation"])
    st.json(opt["by_institution"])
else:
    st.info("Add institution balances in the sidebar to optimize FDIC coverage.")

st.subheader("Recent Income")
if entries:
    st.table(entries[-10:])
else:
    st.caption("No entries yet. Add income in the sidebar.")
