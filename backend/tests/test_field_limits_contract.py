"""The frontend repeats the backend field limits; this test keeps them equal."""

import re
from pathlib import Path

import pytest

from app.schemas import schemas

FIELD_LIMITS_TS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "fieldLimits.ts"
CONSTANT = re.compile(r"^export const (\w+) = (\d+);$", re.MULTILINE)

SHARED_LIMITS = [
    "MIN_USERNAME_LENGTH",
    "MAX_USERNAME_LENGTH",
    "MAX_EMAIL_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "MAX_PASSWORD_BYTES",
    "MAX_CATEGORY_LENGTH",
    "MAX_PRODUCT_LENGTH",
]


def _frontend_limits() -> dict[str, int]:
    if not FIELD_LIMITS_TS.exists():
        pytest.skip("frontend/ is not checked out next to backend/")
    text = FIELD_LIMITS_TS.read_text(encoding="utf-8")
    return {name: int(value) for name, value in CONSTANT.findall(text)}


@pytest.mark.parametrize("name", SHARED_LIMITS)
def test_frontend_limit_matches_backend(name):
    assert _frontend_limits().get(name) == getattr(schemas, name)


def test_frontend_declares_no_unknown_limit():
    assert set(_frontend_limits()) == set(SHARED_LIMITS)
