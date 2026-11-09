from datetime import date

import streamlit as st
from pydantic import ValidationError

from ledgify.models import TransactionIn, parse_amount
from ledgify.repositories import categories, transactions
from ledgify.ui.common import flash, init_page, money

conn, s = init_page("Add Transaction", "➕")
flash()

kind = st.radio("What is this?", ["Money spent", "Money received"], horizontal=True)
tx_type = "expense" if kind == "Money spent" else "income"
cats = categories.list_categories(conn, tx_type)

if not cats:
    st.warning("There are no categories yet. Add one on the Categories page first.")
    st.stop()

with st.form("add_tx", clear_on_submit=True):
    amount = st.text_input(f"Amount ({s['currency']})", placeholder="12.50")
    category = st.selectbox("Category", cats, format_func=lambda c: c["name"])
    when = st.date_input("Date", value=date.today())
    note = st.text_input("Note (optional)", placeholder="e.g. weekly groceries")
    method = st.selectbox("Paid with (optional)", ["", "Cash", "Card", "Bank transfer", "Other"])
    submitted = st.form_submit_button("Save", type="primary", use_container_width=True)

if submitted:
    try:
        cents = parse_amount(amount, s["currency"])
        data = TransactionIn(date=when, amount=cents, type=tx_type, category_id=category["id"],
                             note=note, payment_method=method)
        transactions.add(conn, data)
        flash(f"Saved: {money(cents, s)} in {category['name']}.")
        st.rerun()
    except (ValueError, ValidationError) as e:
        st.error(str(e).splitlines()[0] if isinstance(e, ValidationError) else str(e))
