"""Ledgify — Dashboard (Streamlit entry point)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from ledgify.repositories import transactions
from ledgify.services import budget
from ledgify.ui.common import flash, init_page, money, month_options, this_month

conn, s = init_page("Dashboard", "📊")
flash()

month = st.selectbox("Month", month_options(), index=1)
summary = transactions.month_summary(conn, month)
net = summary["income"] - summary["expense"]

c1, c2, c3 = st.columns(3)
c1.metric("Money in", money(summary["income"], s))
c2.metric("Money out", money(summary["expense"], s))
c3.metric("Left over", money(net, s))

if transactions.search(conn, limit=1) == []:
    st.info("You have no entries yet. Open **Add Transaction** in the left menu to record your first one, "
            "or load sample data in **Settings**.")
    st.stop()

left, right = st.columns(2)
with left:
    st.subheader("Where the money went")
    rows = transactions.category_totals(conn, month)
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df["amount"] = df["total"] / 100
        fig = px.pie(df, names="category", values="amount", hole=0.45,
                     color="category", color_discrete_map=dict(zip(df["category"], df["colour"])))
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No spending recorded this month.")
with right:
    st.subheader("Last months")
    data = transactions.monthly_totals(conn, 6)
    if data:
        df = pd.DataFrame([dict(r) for r in data])
        df["amount"] = df["total"] / 100
        df["type"] = df["type"].map({"expense": "Money out", "income": "Money in"})
        fig = px.bar(df.sort_values("month"), x="month", y="amount", color="type", barmode="group",
                     color_discrete_map={"Money out": "#d1495b", "Money in": "#2e7d32"},
                     labels={"amount": "Amount", "month": "Month", "type": ""})
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

statuses = budget.month_status(conn, month)
alerts = [b for b in statuses if b.state != "ok"]
if alerts:
    st.subheader("Budget alerts")
    for b in alerts:
        if b.state == "over":
            st.error(f"**{b.category}**: over budget by {money(-b.remaining_cents, s)}")
        else:
            st.warning(f"**{b.category}**: {int(b.fraction * 100)}% used, {money(b.remaining_cents, s)} left")

st.subheader("Latest entries")
latest = transactions.search(conn, limit=8)
st.dataframe(pd.DataFrame([{
    "Date": r["date"], "Category": r["category"],
    "Amount": ("-" if r["type"] == "expense" else "+") + money(r["amount"], s), "Note": r["note"],
} for r in latest]), hide_index=True, use_container_width=True)
