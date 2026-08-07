from __future__ import annotations

from scripts.analyze_tool_call_pilot import analyze_subset


def row(item: int, subset: str, success: bool, condition: str) -> dict:
    return {
        "item_id": f"item-{item}",
        "subset": subset,
        "condition": condition,
        "executable_contract_success": success,
        "tool_selection_correct": True,
        "whole_response_valid_json": True,
        "internal_schema_valid": True,
        "external_schema_valid": True,
        "argument_semantics_correct": success,
        "execution_success": True,
        "correct_post_execution_state": success,
        "error": None,
        "hit_max_new_tokens": False,
        "transduction_error": None,
        "heuristic_repair_count": 0,
        "generated_tokens": 10,
        "latency_ms": 1.0,
        "function_name": "tool",
        "required_integer_fields": ["value"],
        "negative_required_integer_references": [],
        "acceptable_arguments": {"value": [1]},
        "decoded_arguments": {"value": 1 if success else 2},
        "raw_output": "{}",
    }


def test_primary_paired_effect_and_discordants() -> None:
    control = [row(index, "primary", index < 20, "control") for index in range(30)]
    treatment = [row(index, "primary", index < 22, "treatment") for index in range(30)]
    result, discordants = analyze_subset("primary", control, treatment)
    effect = result["primary_executable_effect"]
    assert effect["paired_difference"] == 2 / 30
    assert effect["treatment_only"] == 2
    assert effect["control_only"] == 0
    assert len(discordants) == 2
