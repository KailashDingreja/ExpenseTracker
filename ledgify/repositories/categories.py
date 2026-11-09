import sqlite3

from ledgify.models import CategoryIn


def list_categories(conn, type=None, include_archived=False):
    sql = "SELECT * FROM categories WHERE 1=1"
    args = []
    if type:
        sql += " AND type=?"
        args.append(type)
    if not include_archived:
        sql += " AND is_archived=0"
    return conn.execute(sql + " ORDER BY type, name", args).fetchall()


def get(conn, category_id):
    return conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()


def get_by_name(conn, name, type):
    return conn.execute(
        "SELECT * FROM categories WHERE lower(name)=lower(?) AND type=?", (name.strip(), type)
    ).fetchone()


def add(conn, data: CategoryIn) -> int:
    existing = get_by_name(conn, data.name, data.type)
    if existing:
        if existing["is_archived"]:
            with conn:
                conn.execute("UPDATE categories SET is_archived=0, colour=? WHERE id=?",
                             (data.colour, existing["id"]))
            return existing["id"]
        raise ValueError(f"A {data.type} category called '{data.name}' already exists")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO categories(name,type,colour) VALUES (?,?,?)",
                (data.name, data.type, data.colour))
    except sqlite3.IntegrityError as e:
        raise ValueError(str(e))
    return cur.lastrowid


def rename(conn, category_id, name, colour):
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty")
    cat = get(conn, category_id)
    dup = get_by_name(conn, name, cat["type"])
    if dup and dup["id"] != category_id:
        raise ValueError(f"A category called '{name}' already exists")
    with conn:
        conn.execute("UPDATE categories SET name=?, colour=? WHERE id=?", (name, colour, category_id))


def set_archived(conn, category_id, archived: bool):
    with conn:
        conn.execute("UPDATE categories SET is_archived=? WHERE id=?", (int(archived), category_id))
