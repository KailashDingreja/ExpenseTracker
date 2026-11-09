import streamlit as st

from ledgify.models import parse_amount
from ledgify.repositories import budgets, categories
from ledgify.services import budget
from ledgify.ui.common import flash, init_page, money, month_options, this_month

conn, s = init_page("Budgets", "🎯")
flash()

month = st.selectbox("Month", month_options(), index=1)
statuses = budget.month_status(conn, month)

if not statuses:
    st.info("No budgets set for this month yet.")
for b in statuses:
    label = f"**{b.category}** — {money(b.spent_cents, s)} of {money(b.limit_cents, s)}"
    st.write(label)
    st.progress(min(b.fraction, 1.0))
    if b.state == "over":
        st.error(f"Over budget by {money(-b.remaining_cents, s)}")
    elif b.state == "warning":
        st.warning(f"Careful: only {money(b.remaining_cents, s)} left")
    else:
        st.caption(f"{money(b.remaining_cents, s)} left")

st.divider()
st.subheader("Set a limit")
cats = categories.list_categories(conn, "expense")
with st.form("set_budget"):
    cat = st.selectbox("Category", cats, format_func=lambda c: c["name"])
    limit = st.text_input(f"Monthly limit ({s['currency']})", placeholder="300")
    ok = st.form_submit_button("Save limit", type="primary")
if ok:
    try:
        budgets.set_limit(conn, cat["id"], month, parse_amount(limit, s["currency"]))
        flash(f"Limit saved for {cat['name']}."); st.rerun()
    except ValueError as e:
        st.error(str(e))

c1, c2 = st.columns(2)
with c1:
    if statuses:
        rm = st.selectbox("Remove a limit", statuses, index=None, placeholder="Select…",
                          format_func=lambda b: b.category)
        if rm and st.button("Remove limit"):
            budgets.remove(conn, rm.category_id, month)
            flash("Limit removed."); st.rerun()
with c2:
    prev = budget.prev_month(month)
    if st.button(f"Copy budgets from {prev}"):
        n = budgets.copy_forward(conn, prev, month)
        flash(f"Copied {n} limit(s). Existing limits were kept." if n else "Nothing new to copy.")
        st.rerun()
