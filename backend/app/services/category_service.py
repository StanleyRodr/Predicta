"""Canonical category names shared by ingestion and analytics."""

import unicodedata

CANONICAL_CATEGORIES = (
    "Abarrotes",
    "Limpieza",
    "Lácteos",
    "Bebidas",
    "Cuidado Personal",
)


def _category_key(value: str) -> str:
    """Build a comparison key without accents or case differences."""
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


CATEGORY_LOOKUP = {_category_key(category): category for category in CANONICAL_CATEGORIES}


def normalize_category(value: object) -> str:
    """Return a canonical known category or a stable display name for new ones."""
    if value is None:
        return "General"

    cleaned = " ".join(str(value).strip().split())
    if not cleaned:
        return "General"

    known_category = CATEGORY_LOOKUP.get(_category_key(cleaned))
    if known_category is not None:
        return known_category

    # Keep user-defined categories instead of silently mapping them to General.
    return cleaned.title()
