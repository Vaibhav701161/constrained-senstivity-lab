#!/usr/bin/env python3
"""Prepare the preregistered random BFCL pilot and negative sign-stress set."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_a.tool_runtime import (  # noqa: E402
    UnsupportedToolSchema,
    call_schema,
    external_call_schema,
    normalize_bfcl_schema,
)

DEFAULT_SOURCE_ROOT = (
    ROOT / ".cache/bfcl/berkeley-function-call-leaderboard/bfcl_eval/data"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected only JSON objects")
    return rows


def compatible_options(options: Any, schema: Mapping[str, Any]) -> list[Any]:
    if not isinstance(options, list):
        return []
    validator = Draft202012Validator(schema)
    return [option for option in options if validator.is_valid(option)]


def prepare_candidate(
    question: dict[str, Any],
    answer: dict[str, Any],
    source_index: int,
) -> tuple[dict[str, Any] | None, str | None]:
    conversations = question.get("question")
    if (
        not isinstance(conversations, list)
        or len(conversations) != 1
        or not isinstance(conversations[0], list)
        or len(conversations[0]) != 1
        or conversations[0][0].get("role") != "user"
        or not isinstance(conversations[0][0].get("content"), str)
    ):
        return None, "not_single_turn_user_request"
    functions = question.get("function")
    if not isinstance(functions, list) or len(functions) != 1:
        return None, "not_single_function"
    function = functions[0]
    if not isinstance(function, dict) or not isinstance(function.get("name"), str):
        return None, "invalid_function_definition"
    parameters = function.get("parameters")
    if not isinstance(parameters, Mapping) or parameters.get("type") != "dict":
        return None, "parameters_not_object_like"
    properties = parameters.get("properties")
    required = parameters.get("required", [])
    if not isinstance(properties, Mapping) or not isinstance(required, list):
        return None, "invalid_parameter_schema"
    required_integers = [
        name
        for name in required
        if isinstance(properties.get(name), Mapping)
        and properties[name].get("type") == "integer"
    ]
    if not required_integers:
        return None, "no_required_integer"
    try:
        normalized = normalize_bfcl_schema(parameters)
    except UnsupportedToolSchema:
        return None, "unsupported_schema"
    normalized_properties = normalized["properties"]
    for schema in normalized_properties.values():
        if schema.get("type") == "integer" and any(
            key in schema for key in ("minimum", "maximum")
        ):
            return None, "bounded_integer_not_supported"
    ground_truth = answer.get("ground_truth")
    name = function["name"]
    if (
        not isinstance(ground_truth, list)
        or len(ground_truth) != 1
        or not isinstance(ground_truth[0], dict)
        or list(ground_truth[0]) != [name]
        or not isinstance(ground_truth[0][name], dict)
    ):
        return None, "ambiguous_ground_truth_call"
    acceptable = ground_truth[0][name]
    if any(key not in normalized_properties for key in acceptable):
        return None, "ground_truth_has_unknown_argument"
    for key in required:
        if key not in acceptable or not compatible_options(
            acceptable[key], normalized_properties[key]
        ):
            return None, "required_argument_has_no_typed_reference"
    if any(
        not isinstance(options, list) for options in acceptable.values()
    ):
        return None, "ground_truth_options_not_lists"
    if any(
        not compatible_options(acceptable[key], normalized_properties[key])
        for key in acceptable
        if key in required
    ):
        return None, "required_reference_type_mismatch"
    negative_references = [
        {"field": key, "value": value}
        for key in required_integers
        for value in acceptable[key]
        if type(value) is int and value < 0
    ]
    return (
        {
            "id": str(question["id"]),
            "bfcl_id": str(question["id"]),
            "source_index": source_index,
            "subset": None,
            "user_request": conversations[0][0]["content"],
            "function_name": name,
            "function_description": str(function.get("description", "")),
            "bfcl_parameters": parameters,
            "normalized_arguments_schema": normalized,
            "external_call_schema": external_call_schema(name, normalized),
            "integer_call_schema": call_schema(
                name, normalized, model_uses_integers=True
            ),
            "required_integer_fields": required_integers,
            "negative_required_integer_references": negative_references,
            "acceptable_arguments": acceptable,
            "pinned_ground_truth": ground_truth,
        },
        None,
    )


def prepare(
    question_rows: list[dict[str, Any]],
    answer_rows: list[dict[str, Any]],
    *,
    seed: int,
    primary_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    answer_by_id = {str(row.get("id")): row for row in answer_rows}
    if len(answer_by_id) != len(answer_rows):
        raise ValueError("ground-truth source contains duplicate IDs")
    ineligible = Counter()
    eligible: list[dict[str, Any]] = []
    for source_index, question in enumerate(question_rows):
        item_id = str(question.get("id"))
        answer = answer_by_id.get(item_id)
        if answer is None:
            ineligible["missing_ground_truth"] += 1
            continue
        candidate, reason = prepare_candidate(question, answer, source_index)
        if candidate is None:
            ineligible[str(reason)] += 1
        else:
            eligible.append(candidate)
    if len(eligible) < primary_count:
        raise ValueError(
            f"eligible pool has {len(eligible)} cases, fewer than {primary_count}"
        )
    draw_order = random.Random(seed).sample(
        [str(row["id"]) for row in eligible], primary_count
    )
    primary_set = set(draw_order)
    primary = []
    stress = []
    for row in eligible:
        item = dict(row)
        if str(item["id"]) in primary_set:
            item["subset"] = "primary"
            primary.append(item)
        elif item["negative_required_integer_references"]:
            item["subset"] = "sign_stress"
            stress.append(item)
    selected = primary + stress
    selected_ids = [str(row["id"]) for row in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("selected dataset contains duplicate IDs")
    manifest = {
        "manifest_version": "bfcl-bounded-pilot-selection-v1",
        "selection": {
            "seed": seed,
            "algorithm": "python-random-mt19937-sample-v1",
            "primary_count": len(primary),
            "sign_stress_count": len(stress),
            "selected_count": len(selected),
            "primary_draw_order": draw_order,
            "primary_ids_source_order": [str(row["id"]) for row in primary],
            "sign_stress_ids_source_order": [str(row["id"]) for row in stress],
            "selected_ids": selected_ids,
        },
        "eligibility": {
            "source_questions": len(question_rows),
            "source_ground_truths": len(answer_rows),
            "eligible_count": len(eligible),
            "eligible_ids_source_order": [str(row["id"]) for row in eligible],
            "ineligible_count": sum(ineligible.values()),
            "ineligible_reason_counts": dict(sorted(ineligible.items())),
            "eligible_negative_ids": [
                str(row["id"])
                for row in eligible
                if row["negative_required_integer_references"]
            ],
        },
        "integrity": {
            "selected_ids_unique": len(selected_ids) == len(set(selected_ids)),
            "primary_stress_overlap": sorted(
                set(row["id"] for row in primary)
                & set(row["id"] for row in stress)
            ),
            "post_launch_exclusions": [],
        },
    }
    return selected, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_SOURCE_ROOT / "BFCL_v4_simple_python.json",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_SOURCE_ROOT / "possible_answer/BFCL_v4_simple_python.json",
    )
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--primary-count", type=int, default=30)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    args = parser.parse_args()
    selected, manifest = prepare(
        read_jsonl(args.questions),
        read_jsonl(args.ground_truth),
        seed=args.seed,
        primary_count=args.primary_count,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected),
        encoding="utf-8",
    )
    manifest["sources"] = {
        "questions": {
            "path": portable_path(args.questions),
            "sha256": sha256(args.questions),
        },
        "ground_truth": {
            "path": portable_path(args.ground_truth),
            "sha256": sha256(args.ground_truth),
        },
    }
    manifest["artifact"] = {
        "path": str(args.out),
        "sha256": sha256(args.out),
        "bytes": args.out.stat().st_size,
    }
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(args.out)
    print(args.manifest_out)


if __name__ == "__main__":
    main()
