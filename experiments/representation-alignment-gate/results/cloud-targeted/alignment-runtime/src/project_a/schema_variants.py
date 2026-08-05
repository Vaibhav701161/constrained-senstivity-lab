"""Schemas and prompts for the representation-alignment experiment."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

SIGNED_NUMERIC_STRING_PATTERN = re.compile(
    r"^-?(?:(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?|"
    r"(?:\d+|\d{1,3}(?:,\d{3})+)/(?:\d+|\d{1,3}(?:,\d{3})+))$"
)
UNSIGNED_NUMERIC_STRING_PATTERN = re.compile(
    r"^(?:(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?|"
    r"(?:\d+|\d{1,3}(?:,\d{3})+)/(?:\d+|\d{1,3}(?:,\d{3})+))$"
)
PROMPT_TEMPLATE_VERSION = "representation-alignment-v1"


class AnswerRepresentation(StrEnum):
    """Model-facing answer forms supported by the gate."""

    SIGNED_NUMERIC_STRING = "signed_numeric_string"
    UNSIGNED_NUMERIC_STRING_DIAGNOSTIC = "unsigned_numeric_string_diagnostic"
    INTEGER = "integer"


@dataclass(frozen=True)
class ConditionSpec:
    """Fully explicit description of one generation condition."""

    name: str
    backend: str
    answer_representation: AnswerRepresentation
    field_order: tuple[str, str] = ("reasoning", "answer")
    diagnostic_only: bool = False


_SPECS = {
    "prompted_json_integer_reasoning_first": ConditionSpec(
        name="prompted_json_integer_reasoning_first",
        backend="prompted",
        answer_representation=AnswerRepresentation.INTEGER,
    ),
    "outlines_json_integer_reasoning_first": ConditionSpec(
        name="outlines_json_integer_reasoning_first",
        backend="outlines",
        answer_representation=AnswerRepresentation.INTEGER,
    ),
    "xgrammar_json_integer_reasoning_first": ConditionSpec(
        name="xgrammar_json_integer_reasoning_first",
        backend="xgrammar",
        answer_representation=AnswerRepresentation.INTEGER,
    ),
    "outlines_json_unsigned_numeric_string_reasoning_first": ConditionSpec(
        name="outlines_json_unsigned_numeric_string_reasoning_first",
        backend="outlines",
        answer_representation=AnswerRepresentation.UNSIGNED_NUMERIC_STRING_DIAGNOSTIC,
        diagnostic_only=True,
    ),
    "xgrammar_json_unsigned_numeric_string_reasoning_first": ConditionSpec(
        name="xgrammar_json_unsigned_numeric_string_reasoning_first",
        backend="xgrammar",
        answer_representation=AnswerRepresentation.UNSIGNED_NUMERIC_STRING_DIAGNOSTIC,
        diagnostic_only=True,
    ),
}
CONDITIONS = tuple(_SPECS)


def spec_for_condition(name: str) -> ConditionSpec:
    """Return the immutable condition specification or fail explicitly."""

    try:
        return _SPECS[name]
    except KeyError as error:
        raise ValueError(f"Unsupported representation-alignment condition: {name}") from error


def numeric_string_pattern(representation: AnswerRepresentation) -> str:
    """Return the accepted lexical language for a numeric-string representation."""

    if representation is AnswerRepresentation.SIGNED_NUMERIC_STRING:
        return SIGNED_NUMERIC_STRING_PATTERN.pattern
    if representation is AnswerRepresentation.UNSIGNED_NUMERIC_STRING_DIAGNOSTIC:
        return UNSIGNED_NUMERIC_STRING_PATTERN.pattern
    raise ValueError(f"{representation} is not a numeric-string representation")


def answer_schema(representation: AnswerRepresentation) -> dict[str, Any]:
    """Return a schema for one model-facing answer representation."""

    if representation is AnswerRepresentation.INTEGER:
        return {"type": "integer"}
    return {"type": "string", "pattern": numeric_string_pattern(representation)}


def schema_for_spec(spec: ConditionSpec) -> dict[str, Any]:
    """Build the internal schema while preserving declared property order."""

    if set(spec.field_order) != {"reasoning", "answer"}:
        raise ValueError(f"Unsupported field order: {spec.field_order!r}")
    properties: dict[str, Any] = {}
    for field in spec.field_order:
        properties[field] = (
            {"type": "string"} if field == "reasoning" else answer_schema(spec.answer_representation)
        )
    return {
        "type": "object",
        "properties": properties,
        "required": list(spec.field_order),
        "additionalProperties": False,
    }


def external_schema(field_order: tuple[str, str] = ("reasoning", "answer")) -> dict[str, Any]:
    """Return the caller's frozen signed-numeric-string contract."""

    return schema_for_spec(
        ConditionSpec(
            name="external_signed_numeric_string",
            backend="external",
            answer_representation=AnswerRepresentation.SIGNED_NUMERIC_STRING,
            field_order=field_order,
        )
    )


def symbolic_template(spec: ConditionSpec) -> str:
    """Render a symbolic JSON-shaped template without a concrete answer example."""

    values = {
        "reasoning": json.dumps("<calculation sentences>", ensure_ascii=False),
        "answer": (
            "<integer>"
            if spec.answer_representation is AnswerRepresentation.INTEGER
            else json.dumps("<numeric string>", ensure_ascii=False)
        ),
    }
    fields = [f'{json.dumps(field)}: {values[field]}' for field in spec.field_order]
    return "{" + ", ".join(fields) + "}"


def make_prompt(question: str, spec: ConditionSpec) -> str:
    """Build the frozen symbolic prompt for a model-facing schema variant."""

    ordered_keys = ", then ".join(f'"{key}"' for key in spec.field_order)
    return (
        "Solve this grade-school math problem. The reasoning value must contain only 1-3 "
        "short calculation sentences, without lists or headings. "
        "The answer value must contain only the final numeric answer, "
        "with no units, currency symbol, or reasoning. "
        "Return only one valid JSON object, with no markdown or extra text. "
        f"Use exactly two keys in this field order: {ordered_keys}. "
        "Replace both angle-bracket placeholders in this template and do not output "
        "the angle brackets themselves:\n"
        f"{symbolic_template(spec)}\n\n"
        f"Question:\n{question}"
    )


def schema_sha256(schema: dict[str, Any]) -> str:
    """Hash a schema canonically for manifests and run signatures."""

    encoded = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
