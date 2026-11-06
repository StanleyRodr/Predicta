"""Tests for report number formats."""

from decimal import Decimal

import pytest
from matplotlib.figure import Figure

from app.api.analytics_routes import _use_money_axis
from app.services.formatting import format_axis_money, format_money


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "$0.00"),
        (1234.5, "$1,234.50"),
        (1234567.891, "$1,234,567.89"),
        (-1234.5, "-$1,234.50"),
        (-0.001, "$0.00"),
        (Decimal("45.95"), "$45.95"),
    ],
)
def test_format_money(value, expected):
    assert format_money(value) == expected


def test_format_axis_money_omits_decimals():
    assert format_axis_money(12000) == "$12,000"
    assert format_axis_money(-12000) == "-$12,000"


def test_report_chart_axis_uses_money_format():
    ax = Figure().subplots()

    _use_money_axis(ax)

    assert ax.yaxis.get_major_formatter()(12000, 0) == "$12,000"
