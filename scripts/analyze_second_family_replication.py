#!/usr/bin/env python3
"""Produce the preregistered paired analysis for the second-family replication."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from project_a.metrics import NUMBER_PATTERN, canonical_number

from scripts.summarize_alignment_gate import (
    bootstrap_interval,
    exact_mcnemar,
    wilson_interval,
)

EXPECTED_COUNTS = {"fresh": 150, "bridge": 49}
CONTROL = "xgrammar_json_reasoning_first"
TREATMENT = "xgrammar_json_integer_reasoning_first"
ATTRIBUTION_CATEGORIES = (
    "sign_or_lexical_boundary_change",
    "arithmetic_correction",
    "arithmetic_regression",
    "problem_interpretation_change",
    "reasoning_final_answer_inconsistency",
    "truncation",
    "parser_or_validator_issue",
    "other",
)


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: expected object")
        rows.append(value)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def reasoning_consistency(row: dict[str, Any]) -> str:
    """Compare the final numeric mention in reasoning with the answer field."""

    parsed = row.get("parsed_internal")
    if not isinstance(parsed, dict) or not isinstance(parsed.get("reasoning"), str):
        return "not_assessable"
    answer = canonical_number(row.get("predicted_answer"))
    matches = NUMBER_PATTERN.findall(parsed["reasoning"])
    reasoning_final = canonical_number(matches[-1]) if matches else None
    if answer is None or reasoning_final is None:
        return "not_assessable"
    return "consistent" if answer == reasoning_final else "inconsistent"


def metric(row: dict[str, Any], name: str) -> bool:
    return bool(row.get(name))


def rate(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    count = sum(metric(row, name) for row in rows)
    return {
        "count": count,
        "rate": count / len(rows),
        "wilson_ci95": wilson_interval(count, len(rows)),
    }


def summarize_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(row["latency_ms"]) for row in rows]
    tokens = [int(row["generated_tokens"]) for row in rows]
    consistency = [reasoning_consistency(row) for row in rows]
    assessed = sum(value != "not_assessable" for value in consistency)
    consistent = sum(value == "consistent" for value in consistency)
    predicted_negative = sum(
        str(row.get("predicted_answer_normalized", "")).startswith("-")
        for row in rows
    )
    gold_negative = sum(
        str(row.get("gold_answer_normalized", "")).startswith("-") for row in rows
    )
    return {
        "condition": str(rows[0]["condition"]),
        "examples": len(rows),
        "contract_valid_correctness": rate(rows, "contract_valid_correct"),
        "semantic_correctness": rate(rows, "semantic_correct"),
        "final_external_validity": rate(rows, "external_schema_valid"),
        "internal_schema_validity": rate(rows, "internal_schema_valid"),
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "generated_tokens": {
            "total": sum(tokens),
            "mean": statistics.fmean(tokens),
            "median": statistics.median(tokens),
        },
        "latency_ms_descriptive": {
            "total": sum(latencies),
            "mean": statistics.fmean(latencies),
            "median": statistics.median(latencies),
        },
        "negative_answers": {
            "gold": gold_negative,
            "predicted": predicted_negative,
        },
        "reasoning_final_answer_consistency": {
            "method": "last_numeric_mention_equals_final_answer",
            "assessed": assessed,
            "consistent": consistent,
            "inconsistent": sum(value == "inconsistent" for value in consistency),
            "not_assessable": sum(value == "not_assessable" for value in consistency),
            "consistent_rate_among_assessed": consistent / assessed if assessed else None,
        },
    }


def paired_metric(
    ids: list[str],
    control: dict[str, dict[str, Any]],
    treatment: dict[str, dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    values = [int(predicate(treatment[item])) - int(predicate(control[item])) for item in ids]
    treatment_only = sum(value == 1 for value in values)
    control_only = sum(value == -1 for value in values)
    return {
        "paired_difference": sum(values) / len(values),
        "exact_paired_bootstrap_ci95": bootstrap_interval(values),
        "treatment_only": treatment_only,
        "control_only": control_only,
        "both_success": sum(
            predicate(treatment[item]) and predicate(control[item]) for item in ids
        ),
        "both_failure": sum(
            not predicate(treatment[item]) and not predicate(control[item]) for item in ids
        ),
        "mcnemar_p_exact": exact_mcnemar(treatment_only, control_only),
    }


def validate_pair(
    role: str,
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    expected = EXPECTED_COUNTS[role]
    if len(control_rows) != expected or len(treatment_rows) != expected:
        raise ValueError(
            f"{role}: expected {expected} rows per condition, found "
            f"{len(control_rows)} and {len(treatment_rows)}"
        )
    control_ids = [str(row["item_id"]) for row in control_rows]
    treatment_ids = [str(row["item_id"]) for row in treatment_rows]
    if control_ids != treatment_ids:
        raise ValueError(f"{role}: paired item IDs or ordering differ")
    if len(set(control_ids)) != expected:
        raise ValueError(f"{role}: duplicate item IDs")
    if {row.get("condition") for row in control_rows} != {CONTROL}:
        raise ValueError(f"{role}: unexpected control condition")
    if {row.get("condition") for row in treatment_rows} != {TREATMENT}:
        raise ValueError(f"{role}: unexpected treatment condition")
    return (
        control_ids,
        {str(row["item_id"]): row for row in control_rows},
        {str(row["item_id"]): row for row in treatment_rows},
    )


def analyze_role(
    role: str,
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ids, control, treatment = validate_pair(role, control_rows, treatment_rows)
    contract = paired_metric(
        ids, control, treatment, lambda row: metric(row, "contract_valid_correct")
    )
    semantic = paired_metric(
        ids, control, treatment, lambda row: metric(row, "semantic_correct")
    )
    repaired = [
        item
        for item in ids
        if metric(treatment[item], "contract_valid_correct")
        and not metric(control[item], "contract_valid_correct")
    ]
    broken = [
        item
        for item in ids
        if metric(control[item], "contract_valid_correct")
        and not metric(treatment[item], "contract_valid_correct")
    ]
    discordants = []
    for item in repaired + broken:
        direction = "treatment_only_win" if item in repaired else "control_only_win"
        discordants.append(
            {
                "dataset_role": role,
                "item_id": item,
                "direction": direction,
                "gold_answer": control[item].get("gold_answer_normalized"),
                "control_answer": control[item].get("predicted_answer_normalized"),
                "treatment_answer": treatment[item].get("predicted_answer_normalized"),
                "control_reasoning_consistency": reasoning_consistency(control[item]),
                "treatment_reasoning_consistency": reasoning_consistency(treatment[item]),
                "control_raw_output": control[item].get("raw_output"),
                "treatment_raw_output": treatment[item].get("raw_output"),
                "control_error": control[item].get("error"),
                "treatment_error": treatment[item].get("error"),
                "control_cap_hit": bool(control[item].get("hit_max_new_tokens")),
                "treatment_cap_hit": bool(treatment[item].get("hit_max_new_tokens")),
                "manual_category": None,
                "manual_notes": None,
            }
        )
    return (
        {
            "dataset_role": role,
            "paired_examples": len(ids),
            "control": summarize_condition(control_rows),
            "treatment": summarize_condition(treatment_rows),
            "primary_contract_valid_effect": contract,
            "secondary_semantic_effect": semantic,
            "repaired_item_ids": repaired,
            "newly_broken_item_ids": broken,
        },
        discordants,
    )


def merge_manual_attribution(
    path: Path, generated: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not path.is_file():
        return generated
    prior = {
        (str(row.get("dataset_role")), str(row.get("item_id"))): row
        for row in read_jsonl(path)
    }
    for row in generated:
        previous = prior.get((row["dataset_role"], row["item_id"]), {})
        row["manual_category"] = previous.get("manual_category")
        row["manual_notes"] = previous.get("manual_notes")
    return generated


def validate_manual_attribution(rows: list[dict[str, Any]]) -> None:
    failures = []
    for row in rows:
        if row.get("manual_category") not in ATTRIBUTION_CATEGORIES:
            failures.append(f"{row['dataset_role']}:{row['item_id']}: missing category")
        if not str(row.get("manual_notes") or "").strip():
            failures.append(f"{row['dataset_role']}:{row['item_id']}: missing notes")
    if failures:
        raise ValueError("manual discordant audit incomplete: " + "; ".join(failures))


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Second-family paired summary",
        "",
        "Generation errors, token-cap hits, invalid objects, and transduction failures remain in every denominator.",
        "Latency is descriptive and is not an inferential endpoint.",
        "",
    ]
    for role in ("fresh", "bridge"):
        result = summary["datasets"][role]
        effect = result["primary_contract_valid_effect"]
        lines.extend(
            [
                f"## {role.capitalize()} set",
                "",
                "| Condition | n | Contract-valid correct | Semantic correct | External valid | Internal valid | Errors | Cap hits | Mean tokens | Mean latency ms |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for condition in ("control", "treatment"):
            group = result[condition]
            lines.append(
                f"| {condition} | {group['examples']} | "
                f"{percent(group['contract_valid_correctness']['rate'])} | "
                f"{percent(group['semantic_correctness']['rate'])} | "
                f"{percent(group['final_external_validity']['rate'])} | "
                f"{percent(group['internal_schema_validity']['rate'])} | "
                f"{group['errors']} | {group['cap_hits']} | "
                f"{group['generated_tokens']['mean']:.1f} | "
                f"{group['latency_ms_descriptive']['mean']:.1f} |"
            )
        interval = effect["exact_paired_bootstrap_ci95"]
        lines.extend(
            [
                "",
                f"Primary paired difference: {percent(effect['paired_difference'])} "
                f"with exact paired bootstrap 95% interval "
                f"[{percent(interval[0])}, {percent(interval[1])}].",
                f"Treatment-only wins: {effect['treatment_only']}. Control-only wins: "
                f"{effect['control_only']}. Exact McNemar p: {effect['mcnemar_p_exact']:.6g}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Discordant-item audit",
            "",
            f"Total discordant items requiring manual attribution: {summary['discordant_items']}.",
            f"Manual audit complete: {str(summary['manual_audit_complete']).lower()}.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for role in EXPECTED_COUNTS:
        parser.add_argument(f"--{role}-control", type=Path, required=True)
        parser.add_argument(f"--{role}-treatment", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--failure-attribution", type=Path, required=True)
    parser.add_argument("--require-attribution", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {
        "fresh": (args.fresh_control, args.fresh_treatment),
        "bridge": (args.bridge_control, args.bridge_treatment),
    }
    datasets: dict[str, Any] = {}
    discordants: list[dict[str, Any]] = []
    for role, (control_path, treatment_path) in paths.items():
        result, role_discordants = analyze_role(
            role, read_jsonl(control_path), read_jsonl(treatment_path)
        )
        datasets[role] = result
        discordants.extend(role_discordants)
    discordants = merge_manual_attribution(args.failure_attribution, discordants)
    manual_complete = all(
        row.get("manual_category") in ATTRIBUTION_CATEGORIES
        and bool(str(row.get("manual_notes") or "").strip())
        for row in discordants
    )
    if args.require_attribution:
        validate_manual_attribution(discordants)
    summary = {
        "analysis_version": "second-family-paired-analysis-v1",
        "primary_dataset": "fresh",
        "inputs": {
            role: {
                "control": {"path": str(pair[0]), "sha256": sha256(pair[0])},
                "treatment": {"path": str(pair[1]), "sha256": sha256(pair[1])},
            }
            for role, pair in paths.items()
        },
        "datasets": datasets,
        "discordant_items": len(discordants),
        "manual_audit_complete": manual_complete,
        "attribution_categories": list(ATTRIBUTION_CATEGORIES),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(summary), encoding="utf-8")
    write_jsonl(args.failure_attribution, discordants)
    print(args.out_json)
    print(args.out_md)
    print(args.failure_attribution)


if __name__ == "__main__":
    main()
