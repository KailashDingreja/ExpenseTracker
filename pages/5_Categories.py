import streamlit as st
from pydantic import ValidationError

from ledgify.models import CategoryIn
from ledgify.repositories import categories
from ledgify.ui.common import flash, init_page

conn, s = init_page("Categories", "🏷️")
flash()

st.subheader("Add a category")
with st.form("add_cat", clear_on_submit=True):
    name = st.text_input("Name")
    kind = st.radio("Used for", ["Money spent", "Money received"], horizontal=True)
    colour = st.color_picker("Colour", "#4c78a8")
    ok = st.form_submit_button("Add", type="primary")
if ok:
    try:
        categories.add(conn, CategoryIn(name=name, type="expense" if kind == "Money spent" else "income", colour=colour))
        flash(f"Added '{name.strip()}'."); st.rerun()
    except (ValueError, ValidationError) as e:
        st.error("Please enter a name (up to 40 letters)." if isinstance(e, ValidationError) else str(e))

st.divider()
for heading, t in (("Money spent", "expense"), ("Money received", "income")):
    st.subheader(heading)
    for c in categories.list_categories(conn, t):
        with st.expander(f"● {c['name']}", expanded=False):
            with st.form(f"cat_{c['id']}"):
                new_name = st.text_input("Name", value=c["name"])
                new_col = st.color_picker("Colour", c["colour"])
                a, b = st.columns(2)
                save = a.form_submit_button("Save")
                arch = b.form_submit_button("Hide (archive)")
            if save:
                try:
                    categories.rename(conn, c["id"], new_name, new_col)
                    flash("Saved."); st.rerun()
                except ValueError as e:
                    st.error(str(e))
            if arch:
                categories.set_archived(conn, c["id"], True)
                flash(f"'{c['name']}' is hidden. Past entries keep it."); st.rerun()

archived = [c for c in categories.list_categories(conn, include_archived=True) if c["is_archived"]]
if archived:
    st.divider()
    st.subheader("Hidden categories")
    for c in archived:
        if st.button(f"Show '{c['name']}' again ({c['type']})", key=f"un_{c['id']}"):
            categories.set_archived(conn, c["id"], False)
            flash("Category is back."); st.rerun()
