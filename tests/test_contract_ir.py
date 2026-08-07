from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_a.ir import ContractIR, ContractIRError, UnsupportedSchemaError

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_contract_ir_records_typed_properties_and_declared_order() -> None:
    ir = ContractIR.from_schema(load_fixture("canonical-answer.schema.json"))

    assert ir.supported
    assert ir.external_field_order == ("answer", "reasoning")
    assert ir.required_fields == ("answer", "reasoning")
    assert [item.name for item in ir.properties] == ["answer", "reasoning"]
    assert ir.properties[0].scalar_representation == "patterned_string"
    assert ir.properties[1].scalar_representation == "string"
    assert len(ir.stable_hash) == 64


def test_equivalent_keyword_and_required_order_normalize_identically() -> None:
    first = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
        "required": ["b", "a"],
        "additionalProperties": False,
    }
    second = {
        "required": ["a", "b"],
        "additionalProperties": False,
        "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
        "type": "object",
    }

    assert ContractIR.from_schema(first).canonical_json() == ContractIR.from_schema(
        second
    ).canonical_json()


def test_generation_property_order_changes_ir_hash() -> None:
    first = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
    }
    second = {
        "type": "object",
        "properties": {"b": {"type": "integer"}, "a": {"type": "string"}},
    }

    assert ContractIR.from_schema(first).stable_hash != ContractIR.from_schema(
        second
    ).stable_hash


def test_unsupported_keywords_are_recorded_and_refused() -> None:
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string", "oneOf": [{"const": "1"}]}},
    }
    ir = ContractIR.from_schema(schema)

    assert not ir.supported
    assert [(item.keyword, item.path) for item in ir.unsupported] == [
        ("oneOf", ("properties", "answer"))
    ]
    with pytest.raises(UnsupportedSchemaError, match="oneOf"):
        ir.require_supported()


def test_remote_reference_is_captured_and_refused() -> None:
    ir = ContractIR.from_schema(load_fixture("unsupported-reference.schema.json"))

    assert any(item.keyword == "$ref" for item in ir.unsupported)
    assert any("remote references" in item.reason for item in ir.unsupported)
    with pytest.raises(UnsupportedSchemaError):
        ir.require_supported()


def test_local_reference_is_refused_in_initial_subset() -> None:
    schema = {
        "type": "object",
        "properties": {"answer": {"$ref": "#/$defs/answer"}},
        "$defs": {"answer": {"type": "integer"}},
    }
    ir = ContractIR.from_schema(schema)

    assert any("local and recursive references" in item.reason for item in ir.unsupported)
    with pytest.raises(UnsupportedSchemaError):
        ir.require_supported()


def test_invalid_pattern_is_recorded_not_silently_accepted() -> None:
    ir = ContractIR.from_schema(
        {"type": "object", "properties": {"answer": {"type": "string", "pattern": "["}}}
    )
    assert any(item.keyword == "pattern" and "invalid" in item.reason for item in ir.unsupported)


def test_malformed_contracts_raise_explicit_errors() -> None:
    with pytest.raises(ContractIRError, match="top-level object"):
        ContractIR.from_schema({"type": "array"})
    with pytest.raises(ContractIRError, match="not declared"):
        ContractIR.from_schema(
            {"type": "object", "properties": {}, "required": ["missing"]}
        )
