from datetime import date

import pandas as pd
import streamlit as st

from ledgify import config
from ledgify.repositories import settings as settings_repo, transactions
from ledgify.services import backup, csv_io, sample_data
from ledgify.ui.common import TEXT_SIZES, flash, init_page

conn, s = init_page("Settings", "⚙️")
flash()

st.subheader("Look and feel")
with st.form("prefs"):
    cur = st.selectbox("Currency", list(config.CURRENCIES), index=list(config.CURRENCIES).index(s["currency"]),
                       format_func=lambda c: f"{c} ({config.CURRENCIES[c][0]})")
    size = st.selectbox("Text size", list(TEXT_SIZES), index=list(TEXT_SIZES).index(s["text_size"]))
    theme = st.selectbox("Colours", ["Light", "High contrast"], index=["Light", "High contrast"].index(s["theme"]))
    if st.form_submit_button("Save", type="primary"):
        for k, v in (("currency", cur), ("text_size", size), ("theme", theme)):
            settings_repo.set_value(conn, k, v)
        flash("Settings saved."); st.rerun()

st.divider()
st.subheader("Export to CSV")
rows = transactions.search(conn)
st.download_button("Download all entries (CSV)", csv_io.export_csv(rows, s["currency"]),
                   file_name=f"ledgify-export-{date.today()}.csv", mime="text/csv", disabled=not rows)

st.subheader("Import from CSV")
st.caption("Columns: date (YYYY-MM-DD), type (expense or income), category, amount, and optionally note, payment_method.")
up = st.file_uploader("Choose a CSV file", type="csv")
if up:
    prev = csv_io.parse_csv(conn, up.getvalue(), s["currency"])
    st.write(f"Ready to add: **{len(prev.valid)}** · Already in your records: **{len(prev.duplicates)}** · Problems: **{len(prev.errors)}**")
    if prev.errors:
        st.error("These rows have problems and will be skipped:")
        st.dataframe(pd.DataFrame(prev.errors, columns=["Line", "Problem"]), hide_index=True)
    if prev.new_categories:
        st.info("New categories will be created: " + ", ".join(n for n, _ in prev.new_categories))
    dups = st.checkbox("Also add the ones already in my records", disabled=not prev.duplicates)
    if prev.valid or (dups and prev.duplicates):
        if st.button("Import now", type="primary"):
            try:
                n = csv_io.commit_import(conn, prev, include_duplicates=dups)
                flash(f"Imported {n} entries."); st.rerun()
            except Exception as e:
                st.error(f"Nothing was imported. {e}")

st.divider()
st.subheader("Backup and restore")
folder = st.text_input("Backup folder", value=str(config.data_dir() / "backups"))
if st.button("Back up now"):
    try:
        st.success(f"Saved to {backup.backup_to(conn, folder)}")
    except Exception as e:
        st.error(f"Backup failed: {e}")
rest = st.file_uploader("Restore from a backup file", type="db", key="restore")
if rest:
    st.warning("Restoring replaces everything you have now. A safety copy is made first.")
    if st.checkbox("I understand") and st.button("Restore"):
        try:
            safety = backup.restore_from(conn, rest.getvalue())
            flash(f"Restored. Your previous data was saved to {safety}."); st.rerun()
        except ValueError as e:
            st.error(str(e))

st.divider()
st.subheader("Sample data")
st.caption("Adds example entries and budgets so you can try the app.")
if st.button("Load sample data"):
    n = sample_data.load(conn)
    flash(f"Added {n} example entries."); st.rerun()
