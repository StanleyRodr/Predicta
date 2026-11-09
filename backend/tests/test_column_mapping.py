"""Tests for the column mapping rules used by the sales upload."""

import importlib.util
from pathlib import Path

import pytest

from app.services import column_mapping
from app.services.column_mapping import (
    MappingValidationError,
    apply_mapping,
    header_key,
    missing_roles,
    propose_mapping,
    validate_mapping,
)

DATASET_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_dataset.py"


def _assigned(proposal):
    return {role: entry["columna"] for role, entry in proposal.items() if entry["columna"]}


def test_header_key_drops_accents_case_and_punctuation():
    assert header_key("Fecha de Venta") == "fecha_de_venta"
    assert header_key("precio_unit.") == "precio_unit"
    assert header_key("  Categoría ") == "categoria"


def test_synonyms_are_proposed_with_their_origin():
    proposal = propose_mapping(["item", "rubro", "total", "unidades", "fecha_de_venta"])

    assert _assigned(proposal) == {
        "producto": "item",
        "categoria": "rubro",
        "monto": "total",
        "cantidad": "unidades",
        "fecha": "fecha_de_venta",
    }
    assert {entry["origen"] for entry in proposal.values() if entry["columna"]} == {"sinonimo"}


def test_accented_headers_are_recognized():
    proposal = propose_mapping(["descripción", "categoría", "monto", "fecha"])

    assert proposal["producto"] == {"columna": "descripción", "origen": "sinonimo", "candidatos": []}
    assert proposal["categoria"]["origen"] == "exacto"


def test_proposal_always_has_every_role():
    proposal = propose_mapping([])

    assert set(proposal) == set(column_mapping.ROLES)
    assert all(entry == {"columna": None, "origen": None, "candidatos": []} for entry in proposal.values())


def test_tied_headers_leave_the_role_unassigned():
    proposal = propose_mapping(["producto", "total", "importe", "fecha"])

    assert proposal["monto"] == {"columna": None, "origen": None, "candidatos": ["total", "importe"]}


def test_exact_match_beats_a_synonym_of_the_same_role():
    proposal = propose_mapping(["precio", "precio_unitario"])

    assert proposal["precio_unitario"] == {
        "columna": "precio_unitario",
        "origen": "exacto",
        "candidatos": [],
    }


def test_a_header_is_never_assigned_to_two_roles():
    proposal = propose_mapping(["producto", "producto"])

    assert proposal["producto"]["columna"] is None
    assert proposal["producto"]["candidatos"] == ["producto", "producto"]
    assert _assigned(proposal) == {}


@pytest.mark.parametrize("header", ["dia", "linea", "subtotal", "venta"])
def test_ambiguous_headers_are_not_proposed(header):
    assert _assigned(propose_mapping([header])) == {}


def test_missing_roles_accept_price_instead_of_amount():
    assert missing_roles({"producto": "a", "precio_unitario": "b", "fecha": "c"}) == []
    assert missing_roles({}) == ["producto", "monto", "fecha"]


def test_validate_mapping_drops_unassigned_roles():
    columns = ["item", "total", "fecha"]

    assert validate_mapping({"producto": "item", "monto": "total", "fecha": "fecha", "categoria": None}, columns) == {
        "producto": "item",
        "monto": "total",
        "fecha": "fecha",
    }


@pytest.mark.parametrize(
    ("mapping", "message"),
    [
        ({"producto": "item", "monto": "total", "fecha": "fecha", "color": "item"}, "El rol color no existe."),
        ({"producto": "nombre", "monto": "total", "fecha": "fecha"}, "La columna nombre no existe en el archivo."),
        ({"producto": "item", "monto": "item", "fecha": "fecha"}, "La columna item está asignada a dos roles."),
        ({"monto": "total", "fecha": "fecha"}, "Falta asignar: Producto."),
        ({"producto": "item", "monto": "total"}, "Falta asignar: Fecha."),
        ({"producto": "item", "fecha": "fecha"}, "Falta asignar: Monto o Precio unitario."),
    ],
)
def test_validate_mapping_errors(mapping, message):
    with pytest.raises(MappingValidationError) as error:
        validate_mapping(mapping, ["item", "total", "fecha"])

    assert error.value.detail == message


def test_apply_mapping_keeps_only_mapped_roles():
    rows = [{"item": "Pan", "categoria": "Abarrotes", "total": "10", "fecha": "2026-01-01"}]

    mapped = apply_mapping(rows, {"producto": "item", "monto": "total", "fecha": "fecha"})

    assert mapped == [{"producto": "Pan", "monto": "10", "fecha": "2026-01-01"}]


def test_generated_dataset_is_proposed_as_exact():
    spec = importlib.util.spec_from_file_location("generate_dataset", DATASET_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    proposal = propose_mapping(list(module.generate_dataset(days=3).columns))

    assert {role: entry["origen"] for role, entry in proposal.items()} == {
        "producto": "exacto",
        "categoria": "exacto",
        "monto": "exacto",
        "precio_unitario": None,
        "cantidad": "exacto",
        "fecha": "exacto",
    }
