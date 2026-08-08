from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from project_a.runtime import (
    RuntimeBackend,
    RuntimeRepresentation,
    existing_state,
    load_jsonl,
    make_contract_prompt,
    representation_spec,
    score_output,
    select_examples,
)
from project_a.schema_variants import canonical_schema_pair

ROOT = Path(__file__).parents[1]
ACCEPTED = (
    ROOT
    / "experiments/corrected-replication/results/qwen2.5-7b-corrected/results/corrected-replication"
)
FIXTURE = ROOT / "tests/fixtures/corrected-qwen-first5-golden.json"
ARTIFACTS = {
    RuntimeRepresentation.SIGNED_NUMERIC_STRING: ACCEPTED
    / "xgrammar_json_reasoning_first.jsonl",
    RuntimeRepresentation.INTEGER: ACCEPTED
    / "xgrammar_json_integer_reasoning_first.jsonl",
}


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "representation",
    (
        RuntimeRepresentation.SIGNED_NUMERIC_STRING,
        RuntimeRepresentation.INTEGER,
    ),
)
def test_first_five_corrected_qwen_artifacts_are_golden_and_runtime_compatible(
    representation: RuntimeRepresentation,
) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["conditions"][representation.value]
    rows = load_jsonl(ARTIFACTS[representation])[:5]

    assert [row["item_id"] for row in rows] == [row["item_id"] for row in expected]
    for accepted, golden in zip(rows, expected, strict=True):
        prompt = make_contract_prompt(accepted["question"], representation)
        assert prompt == accepted["prompt"]
        assert digest_text(prompt) == golden["prompt_sha256"]
        assert digest_text(accepted["raw_output"]) == golden["raw_output_sha256"]

        scored = score_output(
            accepted["raw_output"],
            representation,
            RuntimeBackend.XGRAMMAR,
            accepted["gold_answer"],
        )
        expected_values = {
            "internal_schema_valid": accepted.get(
                "internal_schema_valid", accepted.get("schema_valid")
            ),
            "external_schema_valid": accepted.get(
                "external_schema_valid", accepted.get("schema_valid")
            ),
            "predicted_answer": accepted["predicted_answer"],
            "semantic_correct": accepted.get(
                "semantic_correct", accepted.get("correct_exact")
            ),
            "contract_valid_correct": accepted.get(
                "contract_valid_correct", accepted.get("correct_exact_strict")
            ),
        }
        for key, expected_value in expected_values.items():
            assert scored[key] == expected_value


def test_representation_is_the_only_prompt_difference() -> None:
    question = "What is 2 + 2?"
    signed = make_contract_prompt(
        question, RuntimeRepresentation.SIGNED_NUMERIC_STRING
    )
    integer = make_contract_prompt(question, RuntimeRepresentation.INTEGER)

    assert signed.replace('"<final numeric answer>"', "<integer>") == integer


def test_canonical_control_preserves_the_accepted_string_prompt_exactly() -> None:
    question = "What is 2 + 2?"
    broad = make_contract_prompt(
        question, RuntimeRepresentation.SIGNED_NUMERIC_STRING
    )
    canonical = make_contract_prompt(
        question, RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING
    )

    assert canonical == broad


def test_canonical_schema_pair_uses_the_compiler_rewrite_path() -> None:
    external, internal = canonical_schema_pair()
    assert external["properties"]["answer"] == {
        "type": "string",
        "pattern": r"^-?(?:0|[1-9][0-9]*)$",
    }
    assert internal["properties"]["answer"] == {"type": "integer"}


def test_condition_names_preserve_accepted_identifiers() -> None:
    assert representation_spec(
        RuntimeRepresentation.SIGNED_NUMERIC_STRING, RuntimeBackend.XGRAMMAR
    ).name == "xgrammar_json_reasoning_first"
    assert representation_spec(
        RuntimeRepresentation.INTEGER, RuntimeBackend.XGRAMMAR
    ).name == "xgrammar_json_integer_reasoning_first"
    assert representation_spec(
        RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING,
        RuntimeBackend.XGRAMMAR,
    ).name == "xgrammar_json_canonical_integer_string_reasoning_first"


def test_selection_applies_frozen_exclusion_before_slicing() -> None:
    rows = [{"id": f"item-{index}"} for index in range(6)]
    selected = select_examples(
        rows,
        start_index=1,
        limit=3,
        exclude_item_ids=["item-2"],
    )
    assert [row["id"] for row in selected] == ["item-1", "item-3", "item-4"]


def test_resume_rejects_duplicate_and_mismatched_rows(tmp_path: Path) -> None:
    output = tmp_path / "rows.jsonl"
    output.write_text(
        json.dumps(
            {"run_signature": "expected", "run_id": "run", "item_id": "a"}
        )
        + "\n",
        encoding="utf-8",
    )
    completed, run_id = existing_state(
        output, resume=True, expected_signature="expected"
    )
    assert completed == {"a"}
    assert run_id == "run"

    output.write_text(
        output.read_text(encoding="utf-8")
        + json.dumps(
            {"run_signature": "expected", "run_id": "run", "item_id": "a"}
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        existing_state(output, resume=True, expected_signature="expected")
