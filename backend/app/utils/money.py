"""Exact money arithmetic. Authoritative amounts are always `Decimal`, never float."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(unit_price: Decimal, quantity: int) -> Decimal:
    return to_money(unit_price * quantity)
