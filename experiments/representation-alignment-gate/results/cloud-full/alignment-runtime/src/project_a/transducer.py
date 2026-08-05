"""Fail-closed conversion from an internal integer object to the external contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from jsonschema import ValidationError, validate

TRANSDUCER_VERSION = "integer-string-v1"


@dataclass(frozen=True)
class TransductionResult:
    """Typed result of deterministic external-contract reconstruction."""

    external_value: dict[str, Any] | None
    external_valid: bool
    error: str | None


def canonical_integer_string(value: object) -> str:
    """Return canonical base-10 text for a JSON integer, rejecting ambiguous inputs."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("internal answer must be a JSON integer and not a boolean")
    return str(value)


def transduce_integer_object(internal_value: Mapping[str, Any]) -> dict[str, Any]:
    """Map a reasoning-plus-integer internal object to the external string contract."""

    if set(internal_value) != {"reasoning", "answer"}:
        raise ValueError("internal object must contain exactly reasoning and answer")
    reasoning = internal_value.get("reasoning")
    if not isinstance(reasoning, str):
        raise TypeError("internal reasoning must be a string")
    return {
        "reasoning": reasoning,
        "answer": canonical_integer_string(internal_value.get("answer")),
    }


def transduce_and_validate(
    internal_value: Mapping[str, Any], external_schema: dict[str, Any]
) -> TransductionResult:
    """Transduce then validate, returning no object on any failure."""

    try:
        external_value = transduce_integer_object(internal_value)
        validate(instance=external_value, schema=external_schema)
    except (TypeError, ValueError, ValidationError) as error:
        return TransductionResult(
            external_value=None,
            external_valid=False,
            error=f"{type(error).__name__}: {error}",
        )
    return TransductionResult(external_value=external_value, external_valid=True, error=None)
