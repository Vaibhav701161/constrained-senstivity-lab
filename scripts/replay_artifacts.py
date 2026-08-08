#!/usr/bin/env python3
"""Recompute accepted artifact scores and paired summaries from raw outputs."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from project_a.metrics import score_alignment_output
from project_a.schema_variants import (
    AnswerRepresentation,
    ConditionSpec,
    external_schema,
    schema_for_spec,
)
from project_a.tool_runtime import score_tool_output
from scripts.analyze_second_family_replication import analyze_role
from scripts.analyze_tool_call_pilot import analyze_subset

SECOND_FAMILY_ROOT = ROOT / "experiments/second-family-replication"
TOOL_ROOT = ROOT / "experiments/tool-call-gate"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected only JSON objects")
    return rows


def compare_fields(
    *,
    scope: str,
    item_id: str,
    stored: dict[str, Any],
    replayed: dict[str, Any],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for field, replayed_value in replayed.items():
        if stored.get(field) != replayed_value:
            mismatches.append(
                {
                    "scope": scope,
                    "item_id": item_id,
                    "field": field,
                    "stored": stored.get(field),
                    "replayed": replayed_value,
                }
            )
    return mismatches


def replay_second_family() -> dict[str, Any]:
    result_root = SECOND_FAMILY_ROOT / "results"
    summary = read_json(SECOND_FAMILY_ROOT / "paired-summary.json")
    paths = {
        "fresh": {
            "control": result_root / "fresh/xgrammar_json_reasoning_first.jsonl",
            "treatment": result_root
            / "fresh/xgrammar_json_integer_reasoning_first.jsonl",
        },
        "bridge": {
            "control": result_root / "bridge/xgrammar_json_reasoning_first.jsonl",
            "treatment": result_root
            / "bridge/xgrammar_json_integer_reasoning_first.jsonl",
        },
    }
    specs = {
        "control": ConditionSpec(
            name="xgrammar_json_reasoning_first",
            backend="xgrammar",
            answer_representation=AnswerRepresentation.SIGNED_NUMERIC_STRING,
        ),
        "treatment": ConditionSpec(
            name="xgrammar_json_integer_reasoning_first",
            backend="xgrammar",
            answer_representation=AnswerRepresentation.INTEGER,
        ),
    }
    row_mismatches: list[dict[str, Any]] = []
    replayed_roles: dict[str, dict[str, list[dict[str, Any]]]] = {}
    replayed_rows = 0
    for role, role_paths in paths.items():
        replayed_roles[role] = {}
        for condition, path in role_paths.items():
            rows = read_jsonl(path)
            spec = specs[condition]
            replayed_condition: list[dict[str, Any]] = []
            for row in rows:
                score = score_alignment_output(
                    str(row["raw_output"]),
                    schema_for_spec(spec),
                    external_schema(spec.field_order),
                    spec.field_order,
                    str(row["gold_answer"]),
                    spec.answer_representation,
                )
                aliases = {
                    **score,
                    "correct_exact": score["semantic_correct"],
                    "correct_exact_strict": score["contract_valid_correct"],
                }
                row_mismatches.extend(
                    compare_fields(
                        scope=f"second_family:{role}:{condition}",
                        item_id=str(row["item_id"]),
                        stored=row,
                        replayed=aliases,
                    )
                )
                updated = copy.deepcopy(row)
                updated.update(aliases)
                replayed_condition.append(updated)
                replayed_rows += 1
            replayed_roles[role][condition] = replayed_condition

    summary_mismatches: list[dict[str, Any]] = []
    for role in ("fresh", "bridge"):
        replayed_summary, _ = analyze_role(
            role,
            replayed_roles[role]["control"],
            replayed_roles[role]["treatment"],
        )
        if replayed_summary != summary["datasets"][role]:
            summary_mismatches.append(
                {
                    "scope": f"second_family:{role}",
                    "stored": summary["datasets"][role],
                    "replayed": replayed_summary,
                }
            )
    return {
        "scope": "second_family",
        "replayed_rows": replayed_rows,
        "row_score_mismatches": row_mismatches,
        "paired_summary_mismatches": summary_mismatches,
        "valid": not row_mismatches and not summary_mismatches,
    }


def replay_tool_call() -> dict[str, Any]:
    dataset = {
        str(row["id"]): row
        for row in read_jsonl(ROOT / "data/bfcl_tool_pilot_seed20260817.jsonl")
    }
    summary = read_json(TOOL_ROOT / "paired-summary.json")
    paths = {
        "control": TOOL_ROOT
        / "results/xgrammar_tool_external_integer_strings.jsonl",
        "treatment": TOOL_ROOT / "results/xgrammar_tool_internal_integers.jsonl",
    }
    row_mismatches: list[dict[str, Any]] = []
    replayed_conditions: dict[str, list[dict[str, Any]]] = {}
    replayed_rows = 0
    for condition, path in paths.items():
        rows = read_jsonl(path)
        replayed_condition: list[dict[str, Any]] = []
        for row in rows:
            item = dataset[str(row["item_id"])]
            score = score_tool_output(
                str(row["raw_output"]),
                function_name=str(item["function_name"]),
                normalized_arguments_schema=item["normalized_arguments_schema"],
                acceptable_arguments=item["acceptable_arguments"],
                model_uses_integers=condition == "treatment",
            )
            row_mismatches.extend(
                compare_fields(
                    scope=f"tool_call:{condition}",
                    item_id=str(row["item_id"]),
                    stored=row,
                    replayed=score,
                )
            )
            updated = copy.deepcopy(row)
            updated.update(score)
            replayed_condition.append(updated)
            replayed_rows += 1
        replayed_conditions[condition] = replayed_condition

    summary_mismatches: list[dict[str, Any]] = []
    for subset in ("primary", "sign_stress"):
        replayed_summary, _ = analyze_subset(
            subset,
            replayed_conditions["control"],
            replayed_conditions["treatment"],
        )
        if replayed_summary != summary["subsets"][subset]:
            summary_mismatches.append(
                {
                    "scope": f"tool_call:{subset}",
                    "stored": summary["subsets"][subset],
                    "replayed": replayed_summary,
                }
            )
    return {
        "scope": "tool_call",
        "replayed_rows": replayed_rows,
        "row_score_mismatches": row_mismatches,
        "paired_summary_mismatches": summary_mismatches,
        "valid": not row_mismatches and not summary_mismatches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("all", "second-family", "tool-call"),
        default="all",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = []
    if args.scope in {"all", "second-family"}:
        results.append(replay_second_family())
    if args.scope in {"all", "tool-call"}:
        results.append(replay_tool_call())
    report = {
        "replay_version": "artifact-score-replay-v1",
        "scopes": results,
        "replayed_rows": sum(item["replayed_rows"] for item in results),
        "valid": all(item["valid"] for item in results),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit("artifact score replay failed")


if __name__ == "__main__":
    main()
