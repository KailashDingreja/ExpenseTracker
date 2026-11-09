"""SQLite connection helper and migration runner."""
import re
import sqlite3
from pathlib import Path

from ledgify import config

DB_DIR = Path(__file__).parent
SCHEMA_FILE = DB_DIR / "schema.sql"
MIGRATIONS_DIR = DB_DIR / "migrations"


def _dict_factory(cursor, row):
    """Rows as plain dicts (Streamlit widgets need copyable options)."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def connect(path=None) -> sqlite3.Connection:
    """Open a connection. Use ':memory:' for tests."""
    target = str(path) if path is not None else str(config.db_path())
    conn = sqlite3.connect(target, check_same_thread=False, timeout=10)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    if target != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _migration_files():
    """schema.sql is version 1; files like 0002_name.sql follow."""
    found = []
    for f in MIGRATIONS_DIR.glob("*.sql"):
        m = re.match(r"(\d+)_", f.name)
        if m and int(m.group(1)) > 1:
            found.append((int(m.group(1)), f))
    return sorted(found)


def current_version(conn) -> int:
    has = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if not has:
        return 0
    row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    return row["v"] or 0


def latest_version() -> int:
    files = _migration_files()
    return files[-1][0] if files else 1


def migrate(conn) -> None:
    """Apply any pending migrations, each in its own transaction."""
    version = current_version(conn)
    steps = []
    if version < 1:
        steps.append((1, SCHEMA_FILE))
    steps += [(v, f) for v, f in _migration_files() if v > version]
    for v, f in steps:
        sql = f.read_text(encoding="utf-8")
        try:
            conn.executescript("BEGIN;\n" + sql + f"\nINSERT INTO schema_version(version) VALUES ({v});\nCOMMIT;")
        except Exception:
            conn.execute("ROLLBACK") if conn.in_transaction else None
            raise


def seed_defaults(conn) -> None:
    """Insert default categories and settings once."""
    if conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"] == 0:
        with conn:
            for name, colour in config.DEFAULT_EXPENSE_CATEGORIES:
                conn.execute(
                    "INSERT INTO categories(name,type,colour,is_default) VALUES (?,?,?,1)",
                    (name, "expense", colour))
            for name, colour in config.DEFAULT_INCOME_CATEGORIES:
                conn.execute(
                    "INSERT INTO categories(name,type,colour,is_default) VALUES (?,?,?,1)",
                    (name, "income", colour))
    with conn:
        for k, v in config.DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))


def open_ready(path=None) -> sqlite3.Connection:
    conn = connect(path)
    migrate(conn)
    seed_defaults(conn)
    return conn
