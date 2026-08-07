"""Layered scoring for internal generation and final external contract validity."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from jsonschema import ValidationError, validate

from .schema_variants import AnswerRepresentation
from .transducer import TRANSDUCER_VERSION, transduce_and_validate

NUMBER_PATTERN = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?(?:/\d[\d,]*)?")


def canonical_number(value: str | int | None) -> str | None:
    """Normalize equivalent numeric forms for representation-independent scoring."""

    if value is None:
        return None
    cleaned = str(value).strip().replace(",", "").replace("$", "").rstrip(". ")
    if not cleaned:
        return None
    try:
        if "/" in cleaned and re.fullmatch(r"-?\d+/\d+", cleaned):
            return str(Fraction(cleaned))
        number = Decimal(cleaned)
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return cleaned.casefold()
    if number == number.to_integral():
        return str(number.quantize(Decimal(1)))
    return format(number.normalize(), "f")


def parse_whole_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse exactly one JSON object, without accepting surrounding prose."""

    try:
        value = json.loads(text.strip())
    except json.JSONDecodeError as error:
        return None, f"{type(error).__name__}: {error}"
    if not isinstance(value, dict):
        return None, f"expected object, got {type(value).__name__}"
    return value, None


def recover_first_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Recover the first object only for diagnostic semantic scoring."""

    decoder = json.JSONDecoder()
    errors: list[str] = []
    for position, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError as error:
            errors.append(f"offset {position}: {error.msg}")
            continue
        if isinstance(value, dict):
            return value, None
    return None, "; ".join(errors[:3]) if errors else "no JSON object start found"


def answer_from_object(value: dict[str, Any] | None) -> str | None:
    """Extract a numeric answer for recoverable semantic scoring."""

    if not isinstance(value, dict):
        return None
    answer = value.get("answer")
    if isinstance(answer, bool) or answer is None:
        return None
    if isinstance(answer, int):
        return str(answer)
    if isinstance(answer, str):
        matches = NUMBER_PATTERN.findall(answer)
        return matches[-1] if matches else None
    return None


def score_alignment_output(
    text: str,
    internal_schema: dict[str, Any],
    external_schema: dict[str, Any],
    expected_order: tuple[str, str],
    gold_answer: str,
    answer_representation: AnswerRepresentation = AnswerRepresentation.INTEGER,
) -> dict[str, Any]:
    """Score semantic recovery, internal validity, and final contract-valid correctness."""

    whole, whole_error = parse_whole_object(text)
    recovered, recovery_error = recover_first_object(text)
    internal_valid = False
    internal_error = whole_error
    if whole is not None:
        try:
            validate(instance=whole, schema=internal_schema)
            internal_valid = True
            internal_error = None
        except ValidationError as error:
            internal_error = f"ValidationError: {error.message}"

    diagnostic_object = whole if whole is not None else recovered
    predicted = answer_from_object(diagnostic_object)
    predicted_normalized = canonical_number(predicted)
    gold_normalized = canonical_number(gold_answer)
    semantic_correct = bool(
        predicted_normalized is not None
        and gold_normalized is not None
        and predicted_normalized == gold_normalized
    )
    transduction_error: str | None = None
    external_value: dict[str, Any] | None = None
    external_valid = False
    if internal_valid and whole is not None:
        if answer_representation is AnswerRepresentation.INTEGER:
            transformed = transduce_and_validate(whole, external_schema)
            external_value = transformed.external_value
            external_valid = transformed.external_valid
            transduction_error = transformed.error
        else:
            try:
                validate(instance=whole, schema=external_schema)
            except ValidationError as error:
                transduction_error = f"ValidationError: {error.message}"
            else:
                external_value = whole
                external_valid = True
                transduction_error = None
    else:
        transduction_error = "internal output did not satisfy the model-facing schema"

    return {
        "parsed_internal": diagnostic_object,
        "whole_response_valid_json": whole is not None,
        "first_object_recoverable": recovered is not None,
        "internal_schema_valid": internal_valid,
        "internal_validation_error": internal_error,
        "internal_key_order": list(whole) if whole is not None else None,
        "internal_field_order_matches": list(whole) == list(expected_order)
        if whole is not None
        else False,
        "predicted_answer": predicted,
        "predicted_answer_normalized": predicted_normalized,
        "gold_answer_normalized": gold_normalized,
        "semantic_correct": semantic_correct,
        "external_value": external_value,
        "external_schema_valid": external_valid,
        "transduction_error": transduction_error,
        "transducer_version": TRANSDUCER_VERSION,
        "contract_valid_correct": semantic_correct and external_valid,
        "recovery_error": recovery_error,
    }
