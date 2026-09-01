from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.01")
ZERO_MONEY = Decimal("0.00")


def as_money(value: Decimal) -> Decimal:
    """Normalize a monetary value to the database's NUMERIC(12, 2) precision."""
    return Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
