"""Shared page setup, theme/text-size CSS and small widgets."""
from datetime import date

import streamlit as st

from ledgify.db import connection
from ledgify.models import format_money
from ledgify.repositories import settings as settings_repo

TEXT_SIZES = {"Normal": 16, "Large": 20, "Extra large": 24}


@st.cache_resource
def get_conn():
    return connection.open_ready()


def _css(s: dict) -> str:
    px = TEXT_SIZES.get(s["text_size"], 16)
    css = f"""
    html, body, [class*="st-"], .stMarkdown, label, input, textarea, button, p {{ font-size: {px}px !important; }}
    h1 {{ font-size: {px * 2}px !important; }} h2 {{ font-size: {int(px * 1.5)}px !important; }}
    [data-testid="stMetricValue"] {{ font-size: {int(px * 1.8)}px !important; }}
    button {{ min-height: {int(px * 2.2)}px; }}
    """
    if s["theme"] == "High contrast":
        css += """
        .stApp, [data-testid="stSidebar"] { background: #000 !important; color: #fff !important; }
        .stApp *, [data-testid="stSidebar"] * { color: #fff !important; }
        input, textarea, [data-baseweb="select"] > div { background: #111 !important; border: 2px solid #ffeb3b !important; }
        button { border: 2px solid #ffeb3b !important; background: #000 !important; }
        a { color: #ffeb3b !important; }
        """
    return f"<style>{css}</style>"


def init_page(title: str, icon: str = "💰"):
    """Call first on every page. Returns (connection, settings dict)."""
    st.set_page_config(page_title=f"{title} · Ledgify", page_icon=icon, layout="wide")
    conn = get_conn()
    s = settings_repo.get_all(conn)
    st.markdown(_css(s), unsafe_allow_html=True)
    st.title(f"{icon} {title}")
    return conn, s


def money(cents, s):
    return format_money(cents, s["currency"])


def this_month() -> str:
    return date.today().strftime("%Y-%m")


def month_options(back=24, ahead=1):
    today = date.today()
    out = []
    for i in range(-ahead, back):
        idx = today.year * 12 + today.month - 1 - i
        out.append(f"{idx // 12}-{idx % 12 + 1:02d}")
    return out


def flash(msg=None, error=False):
    """Show a message once after a rerun."""
    if msg:
        st.session_state["_flash"] = (msg, error)
        return
    item = st.session_state.pop("_flash", None)
    if item:
        (st.error if item[1] else st.success)(item[0])
