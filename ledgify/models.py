"""Pydantic models and money helpers."""
from datetime import date as date_cls
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ledgify import config

TxType = Literal["expense", "income"]


def parse_amount(text, currency: str = "USD") -> int:
    """'12.50' -> 1250 (minor units). Uses Decimal, never float."""
    digits = config.CURRENCIES.get(currency, ("", 2))[1]
    try:
        value = Decimal(str(text).strip().replace(",", ""))
    except (InvalidOperation, AttributeError):
        raise ValueError("Please enter the amount as a number, like 12.50")
    if not value.is_finite():
        raise ValueError("Please enter the amount as a number, like 12.50")
    if value <= 0:
        raise ValueError("The amount must be more than zero")
    scaled = (value * (10 ** digits)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    if scaled <= 0:
        raise ValueError("The amount is too small")
    return int(scaled)


def format_money(cents: int, currency: str = "USD") -> str:
    symbol, digits = config.CURRENCIES.get(currency, ("", 2))
    value = Decimal(cents) / (10 ** digits)
    sign = "-" if cents < 0 else ""
    return f"{sign}{symbol}{abs(value):,.{digits}f}"


class TransactionIn(BaseModel):
    date: date_cls
    amount: int = Field(gt=0)
    type: TxType
    category_id: int
    note: str = ""
    payment_method: str = ""

    @field_validator("note", "payment_method")
    @classmethod
    def _strip(cls, v):
        return v.strip()


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    type: TxType
    colour: str = "#8c8c8c"

    @field_validator("name")
    @classmethod
    def _strip(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v
