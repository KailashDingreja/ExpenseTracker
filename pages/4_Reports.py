from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from ledgify.repositories import transactions
from ledgify.ui.common import init_page, money

conn, s = init_page("Reports", "📈")

today = date.today()
rng = st.date_input("Period", value=(date(today.year, 1, 1), today))
if not (isinstance(rng, tuple) and len(rng) == 2):
    st.info("Pick a start and an end date."); st.stop()

rows = transactions.search(conn, start=rng[0], end=rng[1])
if not rows:
    st.info("No entries in this period."); st.stop()

df = pd.DataFrame([dict(r) for r in rows])
df["amount"] = df["amount"] / 100
df["month"] = df["date"].str[:7]
exp, inc = df[df.type == "expense"], df[df.type == "income"]

c1, c2, c3 = st.columns(3)
c1.metric("Money in", money(int(round(inc.amount.sum() * 100)), s))
c2.metric("Money out", money(int(round(exp.amount.sum() * 100)), s))
months = max(df.month.nunique(), 1)
c3.metric("Average spent per month", money(int(round(exp.amount.sum() * 100 / months)), s))

st.subheader("Spending by month")
if not exp.empty:
    m = exp.groupby("month", as_index=False).amount.sum()
    st.plotly_chart(px.bar(m, x="month", y="amount", labels={"amount": "Spent", "month": "Month"}),
                    use_container_width=True)

st.subheader("Spending by category")
if not exp.empty:
    cat = exp.groupby(["category", "colour"], as_index=False).amount.sum().sort_values("amount")
    fig = px.bar(cat, x="amount", y="category", orientation="h", color="category",
                 color_discrete_map=dict(zip(cat.category, cat.colour)),
                 labels={"amount": "Spent", "category": ""})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Biggest single expenses")
    big = exp.sort_values("amount", ascending=False).head(5)
    st.dataframe(big[["date", "category", "amount", "note"]].rename(
        columns={"date": "Date", "category": "Category", "amount": "Amount", "note": "Note"}),
        hide_index=True, use_container_width=True)
