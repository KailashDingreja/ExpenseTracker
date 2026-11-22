from datetime import date

import pytest

from ledgify.db import connection
from ledgify.models import CategoryIn, TransactionIn, format_money, parse_amount
from ledgify.repositories import budgets, categories, transactions
from ledgify.services import backup, budget, csv_io, sample_data


@pytest.fixture
def conn():
    c = connection.open_ready(":memory:")
    yield c
    c.close()


def cat(conn, name, type="expense"):
    return categories.get_by_name(conn, name, type)["id"]


def test_migrate_idempotent_and_seeded(conn):
    connection.migrate(conn)
    assert connection.current_version(conn) == 1
    assert len(categories.list_categories(conn)) >= 10


def test_parse_amount():
    assert parse_amount("12.50") == 1250
    assert parse_amount("1,000") == 100000
    assert parse_amount("0.005") == 1
    assert parse_amount("500", "JPY") == 500
    for bad in ["abc", "0", "-5", "", "nan"]:
        with pytest.raises(ValueError):
            parse_amount(bad)


def test_format_money():
    assert format_money(123456) == "$1,234.56"
    assert format_money(500, "JPY") == "¥500"


def test_transaction_crud_and_type_rule(conn):
    food = cat(conn, "Food & Groceries")
    tid = transactions.add(conn, TransactionIn(date=date(2026, 1, 5), amount=1250, type="expense", category_id=food, note="lunch"))
    assert transactions.get(conn, tid)["amount"] == 1250
    transactions.update(conn, tid, TransactionIn(date=date(2026, 1, 5), amount=2000, type="expense", category_id=food))
    assert transactions.get(conn, tid)["amount"] == 2000
    with pytest.raises(ValueError):
        transactions.add(conn, TransactionIn(date=date(2026, 1, 5), amount=100, type="income", category_id=food))
    transactions.delete(conn, tid)
    assert transactions.get(conn, tid) is None


def test_search_filters(conn):
    food, salary = cat(conn, "Food & Groceries"), cat(conn, "Salary", "income")
    transactions.add(conn, TransactionIn(date=date(2026, 1, 5), amount=1000, type="expense", category_id=food, note="pizza"))
    transactions.add(conn, TransactionIn(date=date(2026, 2, 5), amount=5000, type="expense", category_id=food, note="market"))
    transactions.add(conn, TransactionIn(date=date(2026, 2, 6), amount=90000, type="income", category_id=salary))
    assert len(transactions.search(conn, text="pizza")) == 1
    assert len(transactions.search(conn, start="2026-02-01")) == 2
    assert len(transactions.search(conn, type="expense", min_cents=2000)) == 1
    assert len(transactions.search(conn, category_ids=[salary])) == 1


def test_category_archive_and_restrict(conn):
    cid = categories.add(conn, CategoryIn(name="Pets", type="expense"))
    with pytest.raises(ValueError):
        categories.add(conn, CategoryIn(name="Pets", type="expense"))
    transactions.add(conn, TransactionIn(date=date(2026, 1, 1), amount=100, type="expense", category_id=cid))
    with pytest.raises(Exception):
        conn.execute("DELETE FROM categories WHERE id=?", (cid,))
    categories.set_archived(conn, cid, True)
    assert cid not in [c["id"] for c in categories.list_categories(conn)]
    assert categories.add(conn, CategoryIn(name="Pets", type="expense")) == cid


def test_budget_status_and_copy(conn):
    food = cat(conn, "Food & Groceries")
    budgets.set_limit(conn, food, "2026-01", 10000)
    for amt in (5000, 3500):
        transactions.add(conn, TransactionIn(date=date(2026, 1, 3), amount=amt, type="expense", category_id=food))
    s = budget.month_status(conn, "2026-01")[0]
    assert (s.spent_cents, s.remaining_cents, s.state) == (8500, 1500, "warning")
    transactions.add(conn, TransactionIn(date=date(2026, 1, 9), amount=2000, type="expense", category_id=food))
    assert budget.month_status(conn, "2026-01")[0].state == "over"
    assert budgets.copy_forward(conn, "2026-01", "2026-02") == 1
    assert budgets.copy_forward(conn, "2026-01", "2026-02") == 0
    assert budget.prev_month("2026-01") == "2025-12"


def test_csv_roundtrip_and_duplicates(conn):
    food = cat(conn, "Food & Groceries")
    transactions.add(conn, TransactionIn(date=date(2026, 1, 5), amount=1250, type="expense", category_id=food, note="lunch"))
    text = csv_io.export_csv(transactions.search(conn))
    assert "12.50" in text
    prev = csv_io.parse_csv(conn, text.encode())
    assert len(prev.duplicates) == 1 and not prev.valid
    bad = b"date,type,category,amount,note\n2026-13-01,expense,Food & Groceries,5,x\n2026-01-02,expense,NewCat,5.25,y\n"
    prev = csv_io.parse_csv(conn, bad)
    assert len(prev.errors) == 1 and prev.errors[0][0] == 2
    assert prev.new_categories == [("NewCat", "expense")]
    assert csv_io.commit_import(conn, prev) == 1
    assert categories.get_by_name(conn, "NewCat", "expense")


def test_csv_missing_columns(conn):
    prev = csv_io.parse_csv(conn, b"foo,bar\n1,2\n")
    assert prev.errors and not prev.valid


def test_backup_restore(conn, tmp_path):
    sample_data.load(conn, months=1)
    n = len(transactions.search(conn))
    assert n > 0
    path = backup.backup_to(conn, tmp_path)
    backup.validate_backup(path)
    for r in transactions.search(conn):
        transactions.delete(conn, r["id"])
    backup.restore_from(conn, path.read_bytes(), safety_dir=tmp_path / "safety")
    assert len(transactions.search(conn)) == n
    with pytest.raises(ValueError):
        backup.restore_from(conn, b"not a database", safety_dir=tmp_path / "safety")
