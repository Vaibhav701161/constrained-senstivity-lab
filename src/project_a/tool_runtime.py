"""Pure contract, transduction, execution, and scoring logic for tool-call pilots."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Mapping

from jsonschema import Draft202012Validator

CANONICAL_INTEGER_PATTERN = r"^-?(0|[1-9][0-9]*)$"
CANONICAL_INTEGER_RE = re.compile(CANONICAL_INTEGER_PATTERN)
SUPPORTED_BFCL_TYPES = {"string", "integer", "float", "boolean", "array", "dict"}


class UnsupportedToolSchema(ValueError):
    """Raised when a BFCL schema cannot be normalized without guessing."""


def normalize_bfcl_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the supported BFCL schema subset to strict JSON Schema."""

    bfcl_type = schema.get("type")
    if bfcl_type not in SUPPORTED_BFCL_TYPES:
        raise UnsupportedToolSchema(f"unsupported BFCL type: {bfcl_type!r}")
    json_type = {"dict": "object", "float": "number"}.get(bfcl_type, bfcl_type)
    result: dict[str, Any] = {"type": json_type}
    for key in ("description", "enum", "minimum", "maximum"):
        if key in schema:
            result[key] = deepcopy(schema[key])
    if bfcl_type == "array":
        items = schema.get("items")
        if not isinstance(items, Mapping):
            raise UnsupportedToolSchema("array schema is missing object-valued items")
        result["items"] = normalize_bfcl_schema(items)
    if bfcl_type == "dict":
        properties = schema.get("properties")
        if not isinstance(properties, Mapping):
            raise UnsupportedToolSchema("dict schema is missing object-valued properties")
        result["properties"] = {
            str(name): normalize_bfcl_schema(value)
            for name, value in properties.items()
            if isinstance(value, Mapping)
        }
        if len(result["properties"]) != len(properties):
            raise UnsupportedToolSchema("dict property schema is not an object")
        required = schema.get("required", [])
        if not isinstance(required, list) or not all(
            isinstance(name, str) and name in properties for name in required
        ):
            raise UnsupportedToolSchema("dict required list is invalid")
        result["required"] = list(required)
        result["additionalProperties"] = False
    return result


def map_integers_to_strings(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Return the unchanged external contract with integer leaves canonicalized."""

    schema_type = schema.get("type")
    if schema_type == "integer":
        result = {
            "type": "string",
            "pattern": CANONICAL_INTEGER_PATTERN,
        }
        if "description" in schema:
            result["description"] = schema["description"]
        return result
    result = deepcopy(dict(schema))
    if schema_type == "array":
        result["items"] = map_integers_to_strings(schema["items"])
    elif schema_type == "object":
        result["properties"] = {
            name: map_integers_to_strings(value)
            for name, value in schema.get("properties", {}).items()
        }
    return result


def call_schema(
    function_name: str,
    normalized_arguments_schema: Mapping[str, Any],
    *,
    model_uses_integers: bool,
) -> dict[str, Any]:
    arguments = (
        deepcopy(dict(normalized_arguments_schema))
        if model_uses_integers
        else map_integers_to_strings(normalized_arguments_schema)
    )
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "const": function_name},
            "arguments": arguments,
        },
        "required": ["name", "arguments"],
        "additionalProperties": False,
    }


def external_call_schema(
    function_name: str, normalized_arguments_schema: Mapping[str, Any]
) -> dict[str, Any]:
    return call_schema(
        function_name, normalized_arguments_schema, model_uses_integers=False
    )


def canonical_integer(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("registered integer value must be a JSON integer")
    return str(value)


def transduce_value(value: Any, normalized_schema: Mapping[str, Any]) -> Any:
    schema_type = normalized_schema.get("type")
    if schema_type == "integer":
        return canonical_integer(value)
    if schema_type == "array":
        if not isinstance(value, list):
            raise ValueError("registered array value is not a JSON array")
        return [transduce_value(item, normalized_schema["items"]) for item in value]
    if schema_type == "object":
        if not isinstance(value, Mapping):
            raise ValueError("registered object value is not a JSON object")
        properties = normalized_schema.get("properties", {})
        return {
            str(key): transduce_value(item, properties[str(key)])
            for key, item in value.items()
            if str(key) in properties
        }
    return deepcopy(value)


def transduce_call(
    internal_call: Mapping[str, Any], normalized_arguments_schema: Mapping[str, Any]
) -> dict[str, Any]:
    if set(internal_call) != {"name", "arguments"}:
        raise ValueError("internal call must contain exactly name and arguments")
    return {
        "name": internal_call["name"],
        "arguments": transduce_value(
            internal_call["arguments"], normalized_arguments_schema
        ),
    }


def decode_external_value(value: Any, normalized_schema: Mapping[str, Any]) -> Any:
    schema_type = normalized_schema.get("type")
    if schema_type == "integer":
        if not isinstance(value, str) or CANONICAL_INTEGER_RE.fullmatch(value) is None:
            raise ValueError("external integer string is not canonical")
        return int(value)
    if schema_type == "array":
        return [
            decode_external_value(item, normalized_schema["items"]) for item in value
        ]
    if schema_type == "object":
        properties = normalized_schema.get("properties", {})
        return {
            str(key): decode_external_value(item, properties[str(key)])
            for key, item in value.items()
        }
    return deepcopy(value)


def parse_whole_call(raw_output: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw_output)
    except json.JSONDecodeError as error:
        return None, f"invalid_json:{error.msg}"
    if not isinstance(value, dict):
        return None, "top_level_not_object"
    return value, None


def validation_error(value: Any, schema: Mapping[str, Any]) -> str | None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    return None if not errors else errors[0].message


def semantically_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left) == float(right)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            semantically_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            semantically_equal(left[key], right[key]) for key in left
        )
    return type(left) is type(right) and left == right


def exact_argument_semantics(
    decoded_arguments: Mapping[str, Any],
    acceptable_arguments: Mapping[str, Any],
    normalized_arguments_schema: Mapping[str, Any],
) -> bool:
    required = set(normalized_arguments_schema.get("required", []))
    if not required.issubset(decoded_arguments):
        return False
    if any(key not in acceptable_arguments for key in decoded_arguments):
        return False
    for key, predicted in decoded_arguments.items():
        options = acceptable_arguments.get(key)
        if not isinstance(options, list) or not any(
            semantically_equal(predicted, option) for option in options
        ):
            return False
    return True


def stable_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def execute_deterministic(
    external_call: Mapping[str, Any],
    normalized_arguments_schema: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    normalized_call = {
        "name": external_call["name"],
        "arguments": decode_external_value(
            external_call["arguments"], normalized_arguments_schema
        ),
    }
    state = {"call_count": 1, "last_call": normalized_call}
    return state, stable_digest(state)


def score_tool_output(
    raw_output: str,
    *,
    function_name: str,
    normalized_arguments_schema: Mapping[str, Any],
    acceptable_arguments: Mapping[str, Any],
    model_uses_integers: bool,
) -> dict[str, Any]:
    internal_schema = call_schema(
        function_name,
        normalized_arguments_schema,
        model_uses_integers=model_uses_integers,
    )
    external_schema = external_call_schema(function_name, normalized_arguments_schema)
    parsed, parse_error = parse_whole_call(raw_output)
    internal_error = validation_error(parsed, internal_schema) if parsed is not None else parse_error
    internal_valid = parsed is not None and internal_error is None
    tool_selection_correct = parsed is not None and parsed.get("name") == function_name
    external_value: dict[str, Any] | None = None
    transduction_error: str | None = None
    if internal_valid and parsed is not None:
        try:
            external_value = (
                transduce_call(parsed, normalized_arguments_schema)
                if model_uses_integers
                else deepcopy(parsed)
            )
        except (KeyError, TypeError, ValueError) as error:
            transduction_error = str(error)
    external_error = (
        validation_error(external_value, external_schema)
        if external_value is not None
        else transduction_error or internal_error
    )
    external_valid = external_value is not None and external_error is None
    decoded_arguments: dict[str, Any] | None = None
    argument_semantics_correct = False
    execution_success = False
    correct_post_execution_state = False
    execution_state: dict[str, Any] | None = None
    execution_receipt: str | None = None
    execution_error: str | None = None
    if external_valid and external_value is not None:
        try:
            decoded = decode_external_value(
                external_value["arguments"], normalized_arguments_schema
            )
            if not isinstance(decoded, dict):
                raise ValueError("decoded arguments are not an object")
            decoded_arguments = decoded
            argument_semantics_correct = exact_argument_semantics(
                decoded,
                acceptable_arguments,
                normalized_arguments_schema,
            )
            execution_state, execution_receipt = execute_deterministic(
                external_value, normalized_arguments_schema
            )
            execution_success = True
            correct_post_execution_state = (
                argument_semantics_correct
                and execution_state.get("last_call")
                == {"name": function_name, "arguments": decoded}
                and execution_receipt == stable_digest(execution_state)
            )
        except (KeyError, TypeError, ValueError) as error:
            execution_error = str(error)
    executable_success = all(
        (
            tool_selection_correct,
            internal_valid,
            transduction_error is None,
            external_valid,
            argument_semantics_correct,
            execution_success,
            correct_post_execution_state,
        )
    )
    return {
        "parsed_internal": parsed,
        "whole_response_valid_json": parsed is not None,
        "parse_error": parse_error,
        "internal_schema_valid": internal_valid,
        "internal_validation_error": internal_error,
        "tool_selection_correct": tool_selection_correct,
        "external_value": external_value,
        "transduction_error": transduction_error,
        "external_schema_valid": external_valid,
        "external_validation_error": external_error,
        "decoded_arguments": decoded_arguments,
        "argument_semantics_correct": argument_semantics_correct,
        "execution_success": execution_success,
        "execution_error": execution_error,
        "execution_state": execution_state,
        "execution_receipt": execution_receipt,
        "correct_post_execution_state": correct_post_execution_state,
        "heuristic_repair_count": 0,
        "executable_contract_success": executable_success,
    }


def make_tool_prompt(
    user_request: str,
    function_name: str,
    function_description: str,
    model_facing_schema: Mapping[str, Any],
) -> str:
    schema_text = json.dumps(
        model_facing_schema, ensure_ascii=False, separators=(",", ":")
    )
    return (
        "Call the single available function for the user request. "
        "Return only one JSON object that follows the call schema exactly, with no "
        "markdown or extra text. Do not add, remove, rename, or reorder fields.\n\n"
        f"User request:\n{user_request}\n\n"
        f"Function name:\n{function_name}\n\n"
        f"Function description:\n{function_description}\n\n"
        f"Call schema:\n{schema_text}"
    )
