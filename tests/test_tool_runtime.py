from __future__ import annotations

import pytest

from project_a.tool_runtime import (
    CANONICAL_INTEGER_PATTERN,
    UnsupportedToolSchema,
    call_schema,
    external_call_schema,
    make_tool_prompt,
    normalize_bfcl_schema,
    score_tool_output,
    transduce_call,
)


BFCL_ARGUMENTS = {
    "type": "dict",
    "properties": {
        "sku": {"type": "string"},
        "quantity_delta": {"type": "integer"},
        "bins": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["sku", "quantity_delta", "bins"],
}


def test_normalization_and_recursive_integer_mapping() -> None:
    normalized = normalize_bfcl_schema(BFCL_ARGUMENTS)
    external = external_call_schema("adjust_inventory", normalized)
    arguments = external["properties"]["arguments"]
    assert arguments["type"] == "object"
    assert arguments["additionalProperties"] is False
    assert arguments["properties"]["quantity_delta"] == {
        "type": "string",
        "pattern": CANONICAL_INTEGER_PATTERN,
    }
    assert arguments["properties"]["bins"]["items"]["type"] == "string"
    internal = call_schema("adjust_inventory", normalized, model_uses_integers=True)
    assert internal["properties"]["arguments"]["properties"]["quantity_delta"]["type"] == "integer"


def test_unsupported_schema_fails_closed() -> None:
    with pytest.raises(UnsupportedToolSchema):
        normalize_bfcl_schema({"type": "tuple"})


def test_transducer_canonicalizes_registered_integer_leaves_only() -> None:
    normalized = normalize_bfcl_schema(BFCL_ARGUMENTS)
    value = transduce_call(
        {
            "name": "adjust_inventory",
            "arguments": {"sku": "ABC-14", "quantity_delta": -12, "bins": [0, 3]},
        },
        normalized,
    )
    assert value == {
        "name": "adjust_inventory",
        "arguments": {"sku": "ABC-14", "quantity_delta": "-12", "bins": ["0", "3"]},
    }


@pytest.mark.parametrize("model_uses_integers", [False, True])
def test_correct_call_executes_to_reference_state(model_uses_integers: bool) -> None:
    normalized = normalize_bfcl_schema(BFCL_ARGUMENTS)
    raw = (
        '{"name":"adjust_inventory","arguments":{"sku":"ABC-14",'
        '"quantity_delta":-12,"bins":[0,3]}}'
        if model_uses_integers
        else '{"name":"adjust_inventory","arguments":{"sku":"ABC-14",'
        '"quantity_delta":"-12","bins":["0","3"]}}'
    )
    score = score_tool_output(
        raw,
        function_name="adjust_inventory",
        normalized_arguments_schema=normalized,
        acceptable_arguments={
            "sku": ["ABC-14"],
            "quantity_delta": [-12],
            "bins": [[0, 3]],
        },
        model_uses_integers=model_uses_integers,
    )
    assert score["internal_schema_valid"] is True
    assert score["external_schema_valid"] is True
    assert score["argument_semantics_correct"] is True
    assert score["execution_success"] is True
    assert score["correct_post_execution_state"] is True
    assert score["executable_contract_success"] is True
    assert score["heuristic_repair_count"] == 0


def test_wrong_argument_can_execute_but_is_not_successful() -> None:
    normalized = normalize_bfcl_schema(BFCL_ARGUMENTS)
    score = score_tool_output(
        '{"name":"adjust_inventory","arguments":{"sku":"ABC-14",'
        '"quantity_delta":9,"bins":[0,3]}}',
        function_name="adjust_inventory",
        normalized_arguments_schema=normalized,
        acceptable_arguments={
            "sku": ["ABC-14"],
            "quantity_delta": [-12],
            "bins": [[0, 3]],
        },
        model_uses_integers=True,
    )
    assert score["external_schema_valid"] is True
    assert score["execution_success"] is True
    assert score["argument_semantics_correct"] is False
    assert score["correct_post_execution_state"] is False
    assert score["executable_contract_success"] is False


def test_prompt_difference_is_confined_to_rendered_schema() -> None:
    normalized = normalize_bfcl_schema(BFCL_ARGUMENTS)
    control_schema = call_schema(
        "adjust_inventory", normalized, model_uses_integers=False
    )
    treatment_schema = call_schema(
        "adjust_inventory", normalized, model_uses_integers=True
    )
    control = make_tool_prompt("Adjust ABC-14 by -12", "adjust_inventory", "Adjust stock.", control_schema)
    treatment = make_tool_prompt("Adjust ABC-14 by -12", "adjust_inventory", "Adjust stock.", treatment_schema)
    assert control.split("Call schema:\n", 1)[0] == treatment.split("Call schema:\n", 1)[0]
    assert control != treatment
