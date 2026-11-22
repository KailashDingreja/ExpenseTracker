def set_limit(conn, category_id, month, limit_cents):
    with conn:
        conn.execute(
            """INSERT INTO budgets(category_id,month,limit_cents) VALUES (?,?,?)
               ON CONFLICT(category_id,month) DO UPDATE SET limit_cents=excluded.limit_cents""",
            (category_id, month, limit_cents))


def remove(conn, category_id, month):
    with conn:
        conn.execute("DELETE FROM budgets WHERE category_id=? AND month=?", (category_id, month))


def for_month(conn, month):
    return conn.execute(
        """SELECT b.category_id, b.limit_cents, c.name AS category, c.colour AS colour
           FROM budgets b JOIN categories c ON c.id=b.category_id
           WHERE b.month=? ORDER BY c.name""", (month,)).fetchall()


def copy_forward(conn, from_month, to_month) -> int:
    """Copy budgets without overwriting ones already set. Returns rows added."""
    with conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO budgets(category_id,month,limit_cents)
               SELECT category_id, ?, limit_cents FROM budgets WHERE month=?""",
            (to_month, from_month))
    return cur.rowcount
