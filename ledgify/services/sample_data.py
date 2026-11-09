"""Generate demo transactions and budgets."""
import random
from datetime import date

from ledgify.models import TransactionIn
from ledgify.repositories import budgets, categories, transactions


def _shift(d: date, months: int) -> date:
    idx = d.year * 12 + d.month - 1 - months
    return date(idx // 12, idx % 12 + 1, 1)


def load(conn, months=4, seed=42) -> int:
    rnd = random.Random(seed)
    cats = {c["name"]: c["id"] for c in categories.list_categories(conn)}
    spend = [("Food & Groceries", 40, 120, 8), ("Transport", 5, 40, 6), ("Entertainment", 10, 60, 3),
             ("Shopping", 15, 150, 3), ("Health", 10, 80, 1), ("Utilities", 40, 120, 2)]
    today = date.today()
    n = 0
    for back in range(months):
        first = _shift(today, back)
        last_day = today.day if back == 0 else 28
        month = first.strftime("%Y-%m")
        def tx(day, name, amt, typ, note):
            nonlocal n
            if day > last_day or name not in cats:
                return
            transactions.add(conn, TransactionIn(
                date=first.replace(day=day), amount=amt, type=typ,
                category_id=cats[name], note=note, payment_method=rnd.choice(["Card", "Cash", "Bank"])))
            n += 1
        tx(1, "Salary", 400000, "income", "Monthly salary")
        tx(1, "Rent & Housing", 120000, "expense", "Rent")
        for name, lo, hi, count in spend:
            for _ in range(count):
                tx(rnd.randint(1, 28), name, rnd.randint(lo, hi) * 100, "expense", "Sample")
        for name, limit in [("Food & Groceries", 70000), ("Transport", 15000),
                            ("Entertainment", 10000), ("Shopping", 20000)]:
            if name in cats:
                budgets.set_limit(conn, cats[name], month, limit)
    return n
