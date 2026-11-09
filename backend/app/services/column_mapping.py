"""Map the columns of an uploaded sales file to the roles the ETL needs.

The proposal only looks at header names: a header matches a role when its
comparison key equals the role name (``exacto``) or one of its synonyms
(``sinonimo``). The user reviews the proposal before loading, so there is no
fuzzy matching. Every function here is pure and never touches the database.
"""

import re
from typing import Any, Literal

from app.services.category_service import category_key
from app.services.errors import UserFacingError

Role = Literal["producto", "categoria", "monto", "precio_unitario", "cantidad", "fecha"]
Origin = Literal["exacto", "sinonimo"]

# Resolution order inside each matching level.
ROLES: tuple[Role, ...] = (
    "producto",
    "categoria",
    "monto",
    "precio_unitario",
    "cantidad",
    "fecha",
)

ROLE_LABELS: dict[str, str] = {
    "producto": "Producto",
    "categoria": "Categoría",
    "monto": "Monto",
    "precio_unitario": "Precio unitario",
    "cantidad": "Cantidad",
    "fecha": "Fecha",
}

# "dia", "linea", "subtotal" and "venta" are left out on purpose: they usually
# name a day of the month, an invoice line, a pre-tax amount, or a sale id.
SYNONYMS: dict[str, frozenset[str]] = {
    "producto": frozenset(
        {"producto", "product", "item", "articulo", "descripcion", "nombre_producto", "sku_descripcion"}
    ),
    "categoria": frozenset({"categoria", "category", "rubro", "familia", "tipo", "departamento"}),
    "monto": frozenset({"monto", "total", "importe", "ventas", "monto_total", "total_venta", "amount"}),
    "precio_unitario": frozenset(
        {"precio", "precio_unitario", "precio_unit", "pu", "valor_unitario", "unit_price", "price"}
    ),
    "cantidad": frozenset({"cantidad", "unidades", "qty", "quantity", "cant", "uds", "piezas"}),
    "fecha": frozenset({"fecha", "fecha_venta", "fecha_de_venta", "date", "fecha_emision"}),
}

NON_ALPHANUMERIC = re.compile(r"[^0-9a-z]+")


class MappingValidationError(UserFacingError):
    """The mapping sent by the client cannot be applied to the file."""


def header_key(header: str) -> str:
    """Return the comparison key: no accents, casefolded, ``_`` between words."""
    return NON_ALPHANUMERIC.sub("_", category_key(str(header))).strip("_")


def _matches(level: Origin, role: str, header: str) -> bool:
    key = header_key(header)
    if level == "exacto":
        return key == role
    return key in SYNONYMS[role]


def propose_mapping(columns: list[str]) -> dict[str, dict[str, Any]]:
    """Propose one header per role: every exact match first, then synonyms.

    A role matched by several free headers stays unassigned; those headers are
    listed as ``candidatos`` and are not offered to later roles.
    """
    proposal: dict[str, dict[str, Any]] = {
        role: {"columna": None, "origen": None, "candidatos": []} for role in ROLES
    }
    taken: set[str] = set()
    levels: tuple[Origin, ...] = ("exacto", "sinonimo")
    for level in levels:
        for role in ROLES:
            entry = proposal[role]
            if entry["columna"] is not None or entry["candidatos"]:
                continue
            matches = [
                header for header in columns if header not in taken and _matches(level, role, header)
            ]
            if len(matches) == 1:
                entry["columna"] = matches[0]
                entry["origen"] = level
            elif len(matches) > 1:
                entry["candidatos"] = matches
            taken.update(matches)
    return proposal


def missing_roles(assigned: dict[str, Any]) -> list[str]:
    """Return the required roles that have no column, in role order."""
    missing = []
    for role in ("producto", "monto", "fecha"):
        if role == "monto":
            if not assigned.get("monto") and not assigned.get("precio_unitario"):
                missing.append("monto")
        elif not assigned.get(role):
            missing.append(role)
    return missing


def validate_mapping(mapping: dict[str, Any], columns: list[str]) -> dict[str, str]:
    """Check a client mapping and return it without unassigned roles."""
    cleaned: dict[str, str] = {}
    used_by: dict[str, str] = {}
    for role, column in mapping.items():
        if role not in ROLES:
            raise MappingValidationError(f"El rol {role} no existe.")
        if column is None:
            continue
        if not isinstance(column, str) or column not in columns:
            raise MappingValidationError(f"La columna {column} no existe en el archivo.")
        if column in used_by:
            raise MappingValidationError(f"La columna {column} está asignada a dos roles.")
        used_by[column] = role
        cleaned[role] = column

    missing = missing_roles(cleaned)
    if missing:
        labels = [
            "Monto o Precio unitario" if role == "monto" else ROLE_LABELS[role] for role in missing
        ]
        raise MappingValidationError(f"Falta asignar: {', '.join(labels)}.")
    return cleaned


def apply_mapping(rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Build new rows holding only the mapped roles, so unmapped columns never leak."""
    return [{role: row.get(column) for role, column in mapping.items()} for row in rows]
