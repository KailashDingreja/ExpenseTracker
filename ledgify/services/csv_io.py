"""CSV export and import. Columns: date,type,category,amount,note,payment_method."""
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd

from ledgify import config
from ledgify.models import CategoryIn, TransactionIn, format_money, parse_amount
from ledgify.repositories import categories, transactions

COLUMNS = ["date", "type", "category", "amount", "note", "payment_method"]


def export_csv(rows, currency="USD") -> str:
    digits = config.CURRENCIES.get(currency, ("", 2))[1]
    out = [{
        "date": r["date"], "type": r["type"], "category": r["category"],
        "amount": f"{Decimal(r['amount']) / (10 ** digits):.{digits}f}",
        "note": r["note"], "payment_method": r["payment_method"],
    } for r in rows]
    return pd.DataFrame(out, columns=COLUMNS).to_csv(index=False)


@dataclass
class ImportPreview:
    valid: list = field(default_factory=list)      # (TransactionIn-like dict) rows
    errors: list = field(default_factory=list)     # (line_number, message)
    duplicates: list = field(default_factory=list)
    new_categories: list = field(default_factory=list)  # (name, type)


def parse_csv(conn, data: bytes, currency="USD") -> ImportPreview:
    prev = ImportPreview()
    try:
        df = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except Exception as e:
        prev.errors.append((0, f"Could not read the file as CSV: {e}"))
        return prev
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in COLUMNS[:4] if c not in df.columns]
    if missing:
        prev.errors.append((0, "Missing column(s): " + ", ".join(missing)))
        return prev
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    seen_new = set()
    for i, r in df.iterrows():
        line = i + 2
        try:
            d = datetime.strptime(r["date"].strip(), "%Y-%m-%d").date()
            t = r["type"].strip().lower()
            if t not in ("expense", "income"):
                raise ValueError("type must be 'expense' or 'income'")
            name = r["category"].strip()
            if not name:
                raise ValueError("category is empty")
            amount = parse_amount(r["amount"], currency)
        except ValueError as e:
            msg = str(e)
            if "time data" in msg or "does not match" in msg:
                msg = "date must look like 2026-01-31"
            prev.errors.append((line, msg))
            continue
        cat = categories.get_by_name(conn, name, t)
        cat_id = cat["id"] if cat else None
        if not cat and (name, t) not in seen_new:
            seen_new.add((name, t))
            prev.new_categories.append((name, t))
        row = dict(date=d, type=t, category=name, category_id=cat_id, amount=amount,
                   note=r["note"].strip(), payment_method=r["payment_method"].strip())
        if cat_id and _is_duplicate(conn, row):
            prev.duplicates.append(row)
        else:
            prev.valid.append(row)
    return prev


def _is_duplicate(conn, row) -> bool:
    return conn.execute(
        "SELECT 1 FROM transactions WHERE date=? AND amount=? AND category_id=? AND note=? LIMIT 1",
        (row["date"].isoformat(), row["amount"], row["category_id"], row["note"])).fetchone() is not None


def commit_import(conn, prev: ImportPreview, create_categories=True, include_duplicates=False) -> int:
    """Write all rows in one transaction; any failure rolls everything back."""
    rows = list(prev.valid) + (list(prev.duplicates) if include_duplicates else [])
    count = 0
    try:
        conn.execute("BEGIN")
        cache = {}
        for r in rows:
            cid = r["category_id"]
            if cid is None:
                if not create_categories:
                    continue
                key = (r["category"], r["type"])
                if key not in cache:
                    existing = categories.get_by_name(conn, *key)
                    if existing:
                        cache[key] = existing["id"]
                    else:
                        cur = conn.execute(
                            "INSERT INTO categories(name,type) VALUES (?,?)", key)
                        cache[key] = cur.lastrowid
                cid = cache[key]
            data = TransactionIn(date=r["date"], amount=r["amount"], type=r["type"],
                                 category_id=cid, note=r["note"], payment_method=r["payment_method"])
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            conn.execute(
                """INSERT INTO transactions(date,amount,type,category_id,note,payment_method,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (data.date.isoformat(), data.amount, data.type, data.category_id,
                 data.note, data.payment_method, now, now))
            count += 1
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return count
