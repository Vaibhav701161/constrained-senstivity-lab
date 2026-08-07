from __future__ import annotations

import hashlib
import json
import random

import pytest
from jsonschema import validate

from project_a.plan import AlignmentPlan, BackendRequirements, TransformStep
from project_a.transforms import (
    FieldOrderTransform,
    IntegerStringTransform,
    KeyAliasTransform,
    ScratchFieldTransform,
    TransformError,
    WhitespacePolicy,
    build_internal_schema,
    execute_transducer,
)

CANONICAL_PATTERN = r"^-?(?:0|[1-9][0-9]*)$"


def external_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "pattern": CANONICAL_PATTERN},
            "reasoning": {"type": "string"},
        },
        "required": ["answer", "reasoning"],
        "additionalProperties": False,
    }


def plan_for(steps: tuple[TransformStep, ...], internal_schema: dict) -> AlignmentPlan:
    external_hash = hashlib.sha256(
        json.dumps(external_schema(), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return AlignmentPlan.create(
        external_schema_hash=external_hash,
        internal_schema=internal_schema,
        transforms=steps,
        backend_requirements=BackendRequirements(
            backend="xgrammar",
            property_order="schema",
            whitespace_policy="canonical",
            requires_buffering=True,
            capabilities=("json_schema",),
        ),
        transducer_version="pipeline-v1",
        provenance={"test": True},
        explanation="Unit-test alignment plan.",
    )


def integer_step() -> TransformStep:
    return TransformStep.create("integer_string", path=("answer",))


def alias_step() -> TransformStep:
    return TransformStep.create(
        "key_alias",
        parameters={
            "external_to_internal": {"answer": "final_numeric_answer"},
            "reserved_keys": ["_scratch"],
        },
    )


def scratch_step() -> TransformStep:
    return TransformStep.create(
        "scratch_field",
        parameters={"key": "_scratch", "allowed": True, "max_length": 64},
    )


def order_step(*, composed: bool = False) -> TransformStep:
    parameters = {
        "internal_order": (
            ["reasoning", "final_numeric_answer", "_scratch"]
            if composed
            else ["reasoning", "answer"]
        ),
        "external_order": ["answer", "reasoning"],
        "buffer_output": True,
    }
    if composed:
        parameters.update(
            {
                "internal_to_external": {"final_numeric_answer": "answer"},
                "internal_only": ["_scratch"],
            }
        )
    return TransformStep.create("field_order", parameters=parameters)


def test_integer_string_safe_examples_round_trip_exactly() -> None:
    step = (integer_step(),)
    internal = build_internal_schema(external_schema(), step)
    plan = plan_for(step, internal)

    for value in (0, 26, -26, 10**1000, -(10**1000)):
        result = execute_transducer(
            plan,
            {"answer": value, "reasoning": "checked"},
            external_schema(),
        )
        assert result.valid
        assert result.external_value == {
            "answer": str(value),
            "reasoning": "checked",
        }


@pytest.mark.parametrize("unsafe", [True, False, 1.5, "12", None])
def test_integer_string_rejects_non_integer_internal_values(unsafe: object) -> None:
    transform = IntegerStringTransform(("answer",))
    value = {"answer": unsafe, "reasoning": "checked"}
    with pytest.raises(TransformError, match="not_integer"):
        transform.to_external(value)


@pytest.mark.parametrize(
    "pattern",
    [
        r"^[0-9]{6}$",
        r"^\+[0-9]+$",
        r"^-?[0-9]{1,3}(?:,[0-9]{3})*$",
        r"^-?[0-9]+\.[0-9]{2}$",
        r"^-?[0-9]+e[+-]?[0-9]+$",
        r"^-?[0-9]+ USD$",
    ],
)
def test_unsafe_lexical_contracts_are_refused_before_generation(pattern: str) -> None:
    schema = external_schema()
    schema["properties"]["answer"]["pattern"] = pattern
    with pytest.raises(TransformError, match="unsupported_numeric_lexical_contract"):
        IntegerStringTransform(("answer",)).rewrite_schema(schema)


def test_explicit_integer_domain_assertion_allows_deliberate_narrowing() -> None:
    schema = external_schema()
    schema["properties"]["answer"]["pattern"] = r"^-?[0-9]+(?:\.[0-9]+)?$"
    internal = IntegerStringTransform(
        ("answer",), allow_narrowing_with_integer_assertion=True
    ).rewrite_schema(schema)
    assert internal["properties"]["answer"]["type"] == "integer"


def test_alias_collision_and_reserved_key_protection() -> None:
    with pytest.raises(TransformError, match="alias_collision"):
        KeyAliasTransform((), (("answer", "value"), ("reasoning", "value")))
    with pytest.raises(TransformError, match="reserved_key_collision"):
        KeyAliasTransform((), (("answer", "_scratch"),), ("_scratch",))


def test_alias_cannot_overwrite_an_untouched_key() -> None:
    schema = external_schema()
    with pytest.raises(TransformError, match="alias_collision"):
        KeyAliasTransform((), (("answer", "reasoning"),)).rewrite_schema(schema)


def test_nested_alias_is_scoped_and_restores_exact_external_name() -> None:
    schema = {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "properties": {
                    "answer": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["answer"],
                "additionalProperties": False,
            }
        },
        "required": ["payload"],
        "additionalProperties": False,
    }
    transform = KeyAliasTransform(("payload",), (("answer", "final_answer"),))
    internal = transform.rewrite_schema(schema)
    assert list(internal["properties"]["payload"]["properties"]) == [
        "final_answer",
        "note",
    ]
    assert internal["properties"]["payload"]["required"] == ["final_answer"]

    value = {"payload": {"final_answer": 7, "note": "unchanged"}}
    transform.to_external(value)
    assert value == {"payload": {"answer": 7, "note": "unchanged"}}


def test_alias_preserves_required_and_optional_status() -> None:
    schema = external_schema()
    schema["required"] = ["answer"]
    internal = KeyAliasTransform(
        (), (("answer", "final_answer"), ("reasoning", "work"))
    ).rewrite_schema(schema)
    assert internal["required"] == ["final_answer"]


def test_field_order_restores_answer_first_without_changing_values() -> None:
    transform = FieldOrderTransform(
        (), ("reasoning", "answer"), ("answer", "reasoning"), buffer_output=True
    )
    internal = transform.rewrite_schema(external_schema())
    assert list(internal["properties"]) == ["reasoning", "answer"]

    value = {"reasoning": "2 + 2 = 4", "answer": "4"}
    transform.to_external(value)
    assert list(value) == ["answer", "reasoning"]
    assert value == {"answer": "4", "reasoning": "2 + 2 = 4"}


def test_field_order_requires_buffering_when_orders_differ() -> None:
    with pytest.raises(TransformError, match="streaming_requires_buffer"):
        FieldOrderTransform(
            (), ("reasoning", "answer"), ("answer", "reasoning"), buffer_output=False
        )


def test_nested_field_order_retains_nested_policy() -> None:
    schema = {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "properties": {"answer": {"type": "string"}, "reasoning": {"type": "string"}},
                "required": ["answer", "reasoning"],
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
    }
    transform = FieldOrderTransform(
        ("payload",),
        ("reasoning", "answer"),
        ("answer", "reasoning"),
    )
    internal = transform.rewrite_schema(schema)
    nested = internal["properties"]["payload"]
    assert list(nested["properties"]) == ["reasoning", "answer"]
    assert nested["additionalProperties"] is False


def test_scratch_field_collision_policy_and_removal() -> None:
    with pytest.raises(TransformError, match="scratch_prohibited"):
        ScratchFieldTransform((), "_scratch", allowed=False)
    with pytest.raises(TransformError, match="scratch_collision"):
        ScratchFieldTransform((), "answer", allowed=True).rewrite_schema(external_schema())

    transform = ScratchFieldTransform((), "_scratch", allowed=True, max_length=16)
    internal = transform.rewrite_schema(external_schema())
    assert "_scratch" in internal["properties"]
    value = {"answer": "4", "reasoning": "kept", "_scratch": "2+2"}
    transform.to_external(value)
    assert value == {"answer": "4", "reasoning": "kept"}


def test_canonical_whitespace_options_are_backend_explicit() -> None:
    xgrammar = WhitespacePolicy("xgrammar", "canonical").backend_options()
    outlines = WhitespacePolicy("outlines", "canonical").backend_options()
    assert xgrammar["any_whitespace"] is False
    assert xgrammar["separators"] == [",", ":"]
    assert outlines["whitespace_pattern"] == ""


@pytest.mark.parametrize(
    "steps,internal_value,expected",
    [
        (
            (integer_step(), order_step()),
            {"reasoning": "work", "answer": -9},
            {"answer": "-9", "reasoning": "work"},
        ),
        (
            (integer_step(), alias_step()),
            {"final_numeric_answer": 12, "reasoning": "work"},
            {"answer": "12", "reasoning": "work"},
        ),
        (
            (alias_step(), TransformStep.create(
                "field_order",
                parameters={
                    "internal_order": ["reasoning", "final_numeric_answer"],
                    "external_order": ["answer", "reasoning"],
                    "internal_to_external": {"final_numeric_answer": "answer"},
                    "buffer_output": True,
                },
            )),
            {"reasoning": "work", "final_numeric_answer": "15"},
            {"answer": "15", "reasoning": "work"},
        ),
    ],
)
def test_supported_transform_pairs_compose_deterministically(
    steps: tuple[TransformStep, ...], internal_value: dict, expected: dict
) -> None:
    internal_schema = build_internal_schema(external_schema(), steps)
    plan = plan_for(steps, internal_schema)
    result = execute_transducer(plan, internal_value, external_schema())

    assert result.valid, result.error
    assert result.external_value == expected
    assert list(result.external_value or {}) == ["answer", "reasoning"]


def test_full_integer_alias_scratch_order_composition() -> None:
    steps = (integer_step(), alias_step(), scratch_step(), order_step(composed=True))
    internal_schema = build_internal_schema(external_schema(), steps)
    assert list(internal_schema["properties"]) == [
        "reasoning",
        "final_numeric_answer",
        "_scratch",
    ]
    plan = plan_for(steps, internal_schema)
    internal_value = {
        "reasoning": "40 + 2 = 42",
        "final_numeric_answer": 42,
        "_scratch": "40+2",
    }

    first = execute_transducer(plan, internal_value, external_schema())
    second = execute_transducer(plan, internal_value, external_schema())
    assert first == second
    assert first.valid
    assert first.external_value == {
        "answer": "42",
        "reasoning": "40 + 2 = 42",
    }
    assert "_scratch" not in (first.external_value or {})


def test_property_sweep_every_accepted_integer_maps_to_external_validity() -> None:
    rng = random.Random(0)
    values = list(range(-500, 501))
    values.extend(rng.randint(-(10**300), 10**300) for _ in range(500))
    steps = (integer_step(),)
    internal_schema = build_internal_schema(external_schema(), steps)
    plan = plan_for(steps, internal_schema)

    for value in values:
        result = execute_transducer(
            plan, {"answer": value, "reasoning": "property"}, external_schema()
        )
        assert result.valid, (value, result.error)
        validate(instance=result.external_value, schema=external_schema())


@pytest.mark.parametrize(
    "internal_value",
    [
        {},
        {"answer": 2},
        {"answer": 2, "reasoning": "ok", "extra": 1},
        {"answer": True, "reasoning": "ok"},
        {"answer": 2.0, "reasoning": "ok"},
        "malformed internal JSON",
    ],
)
def test_invalid_internal_values_fail_closed(internal_value: object) -> None:
    steps = (integer_step(),)
    internal_schema = build_internal_schema(external_schema(), steps)
    result = execute_transducer(plan_for(steps, internal_schema), internal_value, external_schema())  # type: ignore[arg-type]
    assert not result.valid
    assert result.external_value is None
    assert result.error_code is not None


def test_external_validator_exception_fails_closed() -> None:
    steps = (integer_step(),)
    internal_schema = build_internal_schema(external_schema(), steps)
    invalid_external_schema = external_schema()
    invalid_external_schema["properties"]["answer"]["type"] = "not-a-json-type"
    result = execute_transducer(
        plan_for(steps, internal_schema),
        {"answer": 4, "reasoning": "ok"},
        invalid_external_schema,
    )
    assert not result.valid
    assert result.external_value is None
    assert result.error_code == "SchemaError"
