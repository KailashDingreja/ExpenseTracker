from datetime import datetime, timezone

from ledgify.models import TransactionIn
from ledgify.repositories import categories


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _validate(conn, data: TransactionIn):
    cat = categories.get(conn, data.category_id)
    if cat is None:
        raise ValueError("That category does not exist")
    if cat["type"] != data.type:
        raise ValueError(f"'{cat['name']}' is a {cat['type']} category, not {data.type}")


def add(conn, data: TransactionIn) -> int:
    _validate(conn, data)
    now = _now()
    with conn:
        cur = conn.execute(
            """INSERT INTO transactions(date,amount,type,category_id,note,payment_method,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (data.date.isoformat(), data.amount, data.type, data.category_id,
             data.note, data.payment_method, now, now))
    return cur.lastrowid


def update(conn, tx_id: int, data: TransactionIn):
    _validate(conn, data)
    with conn:
        conn.execute(
            """UPDATE transactions SET date=?,amount=?,type=?,category_id=?,note=?,
               payment_method=?,updated_at=? WHERE id=?""",
            (data.date.isoformat(), data.amount, data.type, data.category_id,
             data.note, data.payment_method, _now(), tx_id))


def delete(conn, tx_id: int):
    with conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))


def get(conn, tx_id):
    return conn.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()


def search(conn, start=None, end=None, type=None, category_ids=None,
           min_cents=None, max_cents=None, text=None, limit=None):
    sql = """SELECT t.*, c.name AS category, c.colour AS colour
             FROM transactions t JOIN categories c ON c.id=t.category_id WHERE 1=1"""
    a = []
    if start:
        sql += " AND t.date>=?"; a.append(str(start))
    if end:
        sql += " AND t.date<=?"; a.append(str(end))
    if type:
        sql += " AND t.type=?"; a.append(type)
    if category_ids:
        sql += f" AND t.category_id IN ({','.join('?' * len(category_ids))})"; a += list(category_ids)
    if min_cents is not None:
        sql += " AND t.amount>=?"; a.append(min_cents)
    if max_cents is not None:
        sql += " AND t.amount<=?"; a.append(max_cents)
    if text:
        sql += " AND (t.note LIKE ? OR c.name LIKE ? OR t.payment_method LIKE ?)"
        a += [f"%{text}%"] * 3
    sql += " ORDER BY t.date DESC, t.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql, a).fetchall()


def monthly_totals(conn, months=12):
    """Rows of (month, type, total) for the most recent months with data."""
    return conn.execute(
        """SELECT substr(date,1,7) AS month, type, SUM(amount) AS total
           FROM transactions GROUP BY month, type ORDER BY month DESC LIMIT ?""",
        (months * 2,)).fetchall()


def category_totals(conn, month, type="expense"):
    return conn.execute(
        """SELECT c.id AS category_id, c.name AS category, c.colour AS colour, SUM(t.amount) AS total
           FROM transactions t JOIN categories c ON c.id=t.category_id
           WHERE substr(t.date,1,7)=? AND t.type=? GROUP BY c.id ORDER BY total DESC""",
        (month, type)).fetchall()


def month_summary(conn, month):
    rows = conn.execute(
        "SELECT type, SUM(amount) AS total FROM transactions WHERE substr(date,1,7)=? GROUP BY type",
        (month,)).fetchall()
    d = {r["type"]: r["total"] for r in rows}
    return {"income": d.get("income", 0), "expense": d.get("expense", 0)}
