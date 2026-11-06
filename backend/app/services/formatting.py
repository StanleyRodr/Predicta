"""Number formats shared by generated reports."""

from decimal import Decimal

EXCEL_MONEY_FORMAT = "#,##0.00"


def _with_sign(value: float, amount: str) -> str:
    is_zero = not amount.strip("0.,")
    return f"{'-' if value < 0 and not is_zero else ''}${amount}"


def format_money(value: float | Decimal) -> str:
    """Format an amount with comma thousands and two point decimals."""
    return _with_sign(float(value), f"{abs(float(value)):,.2f}")


def format_axis_money(value: float) -> str:
    """Format a chart axis amount with comma thousands and no decimals."""
    return _with_sign(float(value), f"{abs(float(value)):,.0f}")
