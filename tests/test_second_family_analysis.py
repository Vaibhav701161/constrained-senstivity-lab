from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "second_family_analysis", ROOT / "scripts/analyze_second_family_replication.py"
)
assert SPEC and SPEC.loader
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


def row(
    index: int,
    *,
    condition: str,
    correct: bool,
    answer: str = "4",
    reasoning: str = "Two plus two equals 4.",
) -> dict[str, object]:
    return {
        "condition": condition,
        "item_id": f"item-{index}",
        "contract_valid_correct": correct,
        "semantic_correct": correct,
        "external_schema_valid": True,
        "internal_schema_valid": True,
        "error": None,
        "hit_max_new_tokens": False,
        "generated_tokens": 20,
        "latency_ms": 10.0,
        "predicted_answer": answer,
        "predicted_answer_normalized": answer,
        "gold_answer_normalized": "4",
        "parsed_internal": {"reasoning": reasoning, "answer": answer},
        "raw_output": "{}",
    }


def test_fresh_analysis_preserves_pairing_and_exact_effect() -> None:
    control = [
        row(index, condition=ANALYSIS.CONTROL, correct=index >= 10)
        for index in range(150)
    ]
    treatment = [
        row(index, condition=ANALYSIS.TREATMENT, correct=True)
        for index in range(150)
    ]
    result, discordants = ANALYSIS.analyze_role("fresh", control, treatment)
    effect = result["primary_contract_valid_effect"]
    assert effect["treatment_only"] == 10
    assert effect["control_only"] == 0
    assert effect["paired_difference"] == pytest.approx(10 / 150)
    assert result["repaired_item_ids"] == [f"item-{index}" for index in range(10)]
    assert len(discordants) == 10


def test_reasoning_consistency_is_reported_separately_from_correctness() -> None:
    consistent = row(0, condition=ANALYSIS.CONTROL, correct=False)
    inconsistent = row(
        1,
        condition=ANALYSIS.CONTROL,
        correct=True,
        reasoning="Two plus two equals 5.",
    )
    assert ANALYSIS.reasoning_consistency(consistent) == "consistent"
    assert ANALYSIS.reasoning_consistency(inconsistent) == "inconsistent"


def test_pair_validation_rejects_an_incomplete_confirmatory_set() -> None:
    control = [row(0, condition=ANALYSIS.CONTROL, correct=False)]
    treatment = [row(0, condition=ANALYSIS.TREATMENT, correct=True)]
    with pytest.raises(ValueError, match="expected 150 rows"):
        ANALYSIS.analyze_role("fresh", control, treatment)


def test_manual_attribution_is_mandatory_when_requested() -> None:
    discordant = {
        "dataset_role": "fresh",
        "item_id": "item-0",
        "manual_category": None,
        "manual_notes": None,
    }
    with pytest.raises(ValueError, match="manual discordant audit incomplete"):
        ANALYSIS.validate_manual_attribution([discordant])
    discordant["manual_category"] = "arithmetic_correction"
    discordant["manual_notes"] = "The treatment corrected the multiplication."
    ANALYSIS.validate_manual_attribution([discordant])
