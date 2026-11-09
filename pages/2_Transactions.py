from datetime import date

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from ledgify.models import TransactionIn, parse_amount
from ledgify.repositories import categories, transactions
from ledgify.ui.common import flash, init_page, money

conn, s = init_page("Transactions", "📒")
flash()

all_cats = categories.list_categories(conn, include_archived=True)
with st.expander("Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    today = date.today()
    rng = c1.date_input("Dates", value=(today.replace(day=1), today))
    kind = c2.selectbox("Type", ["All", "Money spent", "Money received"])
    chosen = c3.multiselect("Categories", all_cats, format_func=lambda c: f"{c['name']} ({c['type']})")
    c4, c5, c6 = st.columns(3)
    lo = c4.text_input("Smallest amount")
    hi = c5.text_input("Largest amount")
    text = c6.text_input("Search notes")

try:
    min_c = parse_amount(lo, s["currency"]) if lo.strip() else None
    max_c = parse_amount(hi, s["currency"]) if hi.strip() else None
except ValueError as e:
    st.error(str(e)); st.stop()

start, end = (rng[0], rng[1]) if isinstance(rng, tuple) and len(rng) == 2 else (None, None)
rows = transactions.search(
    conn, start=start, end=end,
    type={"All": None, "Money spent": "expense", "Money received": "income"}[kind],
    category_ids=[c["id"] for c in chosen], min_cents=min_c, max_cents=max_c, text=text.strip() or None)

spent = sum(r["amount"] for r in rows if r["type"] == "expense")
got = sum(r["amount"] for r in rows if r["type"] == "income")
st.write(f"**{len(rows)}** entries · money out **{money(spent, s)}** · money in **{money(got, s)}**")

if not rows:
    st.info("Nothing matches. Try widening the dates or clearing a filter.")
    st.stop()

st.dataframe(pd.DataFrame([{
    "Date": r["date"], "Category": r["category"],
    "Amount": ("-" if r["type"] == "expense" else "+") + money(r["amount"], s),
    "Note": r["note"], "Paid with": r["payment_method"],
} for r in rows]), hide_index=True, use_container_width=True)

st.subheader("Change or remove an entry")
pick = st.selectbox("Choose an entry", rows, index=None, placeholder="Select…",
                    format_func=lambda r: f"{r['date']} · {r['category']} · {money(r['amount'], s)} · {r['note']}")
if pick:
    cats = categories.list_categories(conn, pick["type"])
    if pick["category_id"] not in [c["id"] for c in cats]:
        cats = cats + [categories.get(conn, pick["category_id"])]
    idx = [c["id"] for c in cats].index(pick["category_id"])
    with st.form(f"edit_{pick['id']}"):
        amount = st.text_input("Amount", value=f"{pick['amount'] / 100:.2f}" if s["currency"] != "JPY" else str(pick["amount"]))
        cat = st.selectbox("Category", cats, index=idx, format_func=lambda c: c["name"])
        when = st.date_input("Date", value=date.fromisoformat(pick["date"]))
        note = st.text_input("Note", value=pick["note"])
        method = st.text_input("Paid with", value=pick["payment_method"])
        save = st.form_submit_button("Save changes", type="primary")
    if save:
        try:
            transactions.update(conn, pick["id"], TransactionIn(
                date=when, amount=parse_amount(amount, s["currency"]), type=pick["type"],
                category_id=cat["id"], note=note, payment_method=method))
            flash("Entry updated."); st.rerun()
        except (ValueError, ValidationError) as e:
            st.error(str(e).splitlines()[0])
    confirm = st.checkbox("Yes, I want to delete this entry", key=f"c_{pick['id']}")
    if st.button("Delete entry", disabled=not confirm):
        transactions.delete(conn, pick["id"])
        flash("Entry deleted."); st.rerun()
