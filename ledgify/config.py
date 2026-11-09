"""Paths and defaults. The data folder can be overridden with LEDGIFY_DATA_DIR."""
import os
from pathlib import Path

APP_NAME = "Ledgify"

DEFAULT_SETTINGS = {
    "currency": "USD",
    "text_size": "Normal",   # Normal | Large | Extra large
    "theme": "Light",        # Light | High contrast
}

# currency code -> (symbol, minor-unit digits)
CURRENCIES = {
    "USD": ("$", 2), "EUR": ("€", 2), "GBP": ("£", 2), "INR": ("₹", 2),
    "AUD": ("A$", 2), "CAD": ("C$", 2), "JPY": ("¥", 0),
}

DEFAULT_EXPENSE_CATEGORIES = [
    ("Food & Groceries", "#e4572e"), ("Rent & Housing", "#4c78a8"),
    ("Transport", "#f2a900"), ("Utilities", "#59a14f"),
    ("Health", "#b07aa1"), ("Entertainment", "#ff9da7"),
    ("Shopping", "#76b7b2"), ("Education", "#9c755f"),
    ("Other", "#8c8c8c"),
]
DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "#2e7d32"), ("Other income", "#66a61e"),
]


def data_dir() -> Path:
    env = os.environ.get("LEDGIFY_DATA_DIR")
    if env:
        base = Path(env)
    else:
        root = os.environ.get("APPDATA") or str(Path.home() / ".local" / "share")
        base = Path(root) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return data_dir() / "ledgify.db"
