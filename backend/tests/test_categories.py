"""Tests for category normalization shared by ETL and analytics."""

from app.services.category_service import normalize_category


def test_normalize_category_accepts_case_spaces_and_accents():
    assert normalize_category("  CUIDADO   PERSONAL ") == "Cuidado Personal"
    assert normalize_category("lacteos") == "Lácteos"
    assert normalize_category("LÁCTEOS") == "Lácteos"


def test_normalize_category_preserves_unknown_category():
    assert normalize_category("  Electrónica  ") == "Electrónica"
    assert normalize_category("ropa infantil") == "Ropa Infantil"


def test_normalize_empty_category_uses_general():
    assert normalize_category(None) == "General"
    assert normalize_category("   ") == "General"
