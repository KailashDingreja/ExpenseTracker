"""Backup (SQLite backup API) and validated restore."""
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from ledgify import config
from ledgify.db import connection

REQUIRED_TABLES = {"categories", "transactions", "budgets", "settings", "schema_version"}


def backup_to(conn, folder) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"ledgify-{datetime.now():%Y%m%d-%H%M%S}.db"
    out = sqlite3.connect(str(dest))
    try:
        conn.backup(out)
    finally:
        out.close()
    return dest


def validate_backup(path) -> None:
    """Raise ValueError if the file is not a usable Ledgify database."""
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not REQUIRED_TABLES <= tables:
                raise ValueError("This file is not a Ledgify backup.")
            v = c.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
        finally:
            c.close()
    except sqlite3.DatabaseError:
        raise ValueError("This file is not a valid database.")
    if v > connection.latest_version():
        raise ValueError("This backup was made by a newer version of Ledgify.")


def restore_from(conn, uploaded: bytes, safety_dir=None) -> Path:
    """Validate, back up the current DB, then copy the backup into the live DB. Returns safety backup."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp) / "restore.db"
        tmp_file.write_bytes(uploaded)
        validate_backup(tmp_file)
        safety = backup_to(conn, safety_dir or config.data_dir() / "backups")
        src = sqlite3.connect(str(tmp_file))
        try:
            src.backup(conn)    # overwrite live database in place
        finally:
            src.close()
    connection.migrate(conn)
    return safety
