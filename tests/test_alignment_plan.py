from __future__ import annotations

import hashlib

import pytest

from project_a.plan import (
    AlignmentPlan,
    BackendRequirements,
    PlanError,
    RefusalReason,
    TransformStep,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def requirements(whitespace: str = "canonical") -> BackendRequirements:
    return BackendRequirements(
        backend="xgrammar",
        property_order="schema",
        whitespace_policy=whitespace,
        requires_buffering=True,
        capabilities=("json_schema", "strict_properties"),
    )


def make_plan(schema_hash: str | None = None, whitespace: str = "canonical") -> AlignmentPlan:
    steps = (
        TransformStep.create("integer_string", path=("answer",)),
        TransformStep.create(
            "canonical_whitespace",
            parameters={"backend": "xgrammar", "mode": whitespace},
        ),
    )
    return AlignmentPlan.create(
        external_schema_hash=schema_hash or digest("external"),
        internal_schema={
            "type": "object",
            "properties": {"answer": {"type": "integer"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
        transforms=steps,
        backend_requirements=requirements(whitespace),
        transducer_version="test-v1",
        provenance={"model": "unit-test", "backend_version": "0.2.3"},
        explanation="Use a native integer and restore its canonical string.",
    )


def test_identical_inputs_produce_identical_plan_hashes() -> None:
    assert make_plan().stable_hash == make_plan().stable_hash


def test_changed_external_contract_changes_plan_hash() -> None:
    assert make_plan(digest("first")).stable_hash != make_plan(digest("second")).stable_hash


def test_plan_round_trip_preserves_all_information() -> None:
    original = make_plan()
    replayed = AlignmentPlan.from_json(original.canonical_json())

    assert replayed == original
    assert replayed.stable_hash == original.stable_hash
    assert replayed.internal_schema == original.internal_schema
    assert replayed.provenance == original.provenance


def test_invalid_transform_order_is_refused() -> None:
    with pytest.raises(PlanError, match="invalid transform ordering"):
        AlignmentPlan.create(
            external_schema_hash=digest("external"),
            internal_schema={"type": "object"},
            transforms=(
                TransformStep.create("field_order"),
                TransformStep.create("integer_string", path=("answer",)),
            ),
            backend_requirements=requirements(),
            transducer_version="v1",
            provenance={},
            explanation="invalid",
        )


def test_unsupported_backend_capability_is_an_explicit_refusal() -> None:
    refused = AlignmentPlan.create(
        external_schema_hash=digest("external"),
        internal_schema={"type": "object"},
        transforms=(),
        backend_requirements=requirements(),
        transducer_version="v1",
        provenance={},
        explanation="Backend does not support a required feature.",
        refusal_reasons=(
            RefusalReason(
                "backend_capability_missing",
                "selected backend does not implement dependentRequired",
            ),
        ),
    )

    assert not refused.executable
    with pytest.raises(PlanError, match="backend_capability_missing"):
        refused.require_executable()


def test_whitespace_policy_changes_plan_signature() -> None:
    assert make_plan(whitespace="canonical").stable_hash != make_plan(
        whitespace="any"
    ).stable_hash


def test_duplicate_transform_path_is_refused() -> None:
    duplicate = TransformStep.create("integer_string", path=("answer",))
    with pytest.raises(PlanError, match="duplicate"):
        AlignmentPlan.create(
            external_schema_hash=digest("external"),
            internal_schema={"type": "object"},
            transforms=(duplicate, duplicate),
            backend_requirements=requirements(),
            transducer_version="v1",
            provenance={},
            explanation="invalid",
        )
