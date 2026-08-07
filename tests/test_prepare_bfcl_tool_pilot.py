from __future__ import annotations

from scripts.prepare_bfcl_tool_pilot import prepare


def question(item: int, value: int, *, parameter_type: str = "integer") -> dict:
    return {
        "id": f"simple_python_{item}",
        "question": [[{"role": "user", "content": f"Use {value}."}]],
        "function": [
            {
                "name": f"tool_{item}",
                "description": "A deterministic tool.",
                "parameters": {
                    "type": "dict",
                    "properties": {"value": {"type": parameter_type}},
                    "required": ["value"],
                },
            }
        ],
    }


def answer(item: int, value: object) -> dict:
    return {
        "id": f"simple_python_{item}",
        "ground_truth": [{f"tool_{item}": {"value": [value]}}],
    }


def test_selection_is_seeded_source_order_and_adds_negative_stress() -> None:
    questions = [question(index, index) for index in range(8)]
    answers = [answer(index, -3 if index == 7 else index) for index in range(8)]
    selected_a, manifest_a = prepare(
        questions, answers, seed=20260817, primary_count=3
    )
    selected_b, manifest_b = prepare(
        questions, answers, seed=20260817, primary_count=3
    )
    assert selected_a == selected_b
    assert manifest_a == manifest_b
    primary = [row for row in selected_a if row["subset"] == "primary"]
    stress = [row for row in selected_a if row["subset"] == "sign_stress"]
    assert len(primary) == 3
    assert [row["source_index"] for row in primary] == sorted(
        row["source_index"] for row in primary
    )
    if "simple_python_7" not in {row["id"] for row in primary}:
        assert [row["id"] for row in stress] == ["simple_python_7"]
    assert manifest_a["integrity"]["primary_stress_overlap"] == []


def test_non_integer_and_unsupported_cases_are_excluded() -> None:
    questions = [
        question(0, 1),
        question(1, 1, parameter_type="string"),
        question(2, 1, parameter_type="tuple"),
    ]
    answers = [answer(0, 1), answer(1, "one"), answer(2, [1])]
    selected, manifest = prepare(questions, answers, seed=1, primary_count=1)
    assert [row["id"] for row in selected] == ["simple_python_0"]
    reasons = manifest["eligibility"]["ineligible_reason_counts"]
    assert reasons["no_required_integer"] == 2
