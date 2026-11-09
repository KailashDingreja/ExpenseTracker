"""Budget maths: spent vs limit per category for a month."""
from dataclasses import dataclass

from ledgify.repositories import budgets, transactions

WARN_AT = 0.8


@dataclass
class BudgetStatus:
    category_id: int
    category: str
    colour: str
    limit_cents: int
    spent_cents: int

    @property
    def remaining_cents(self):
        return self.limit_cents - self.spent_cents

    @property
    def fraction(self):
        return self.spent_cents / self.limit_cents if self.limit_cents else 0.0

    @property
    def state(self):
        if self.spent_cents > self.limit_cents:
            return "over"
        if self.fraction >= WARN_AT:
            return "warning"
        return "ok"


def month_status(conn, month):
    spent = {r["category_id"]: r["total"] for r in transactions.category_totals(conn, month)}
    return [
        BudgetStatus(b["category_id"], b["category"], b["colour"], b["limit_cents"],
                     spent.get(b["category_id"], 0))
        for b in budgets.for_month(conn, month)
    ]


def prev_month(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"
