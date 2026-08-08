#!/usr/bin/env python3
"""Produce paired primary and sign-stress analysis for the bounded tool pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.summarize_alignment_gate import bootstrap_interval, exact_mcnemar, wilson_interval

EXPECTED_COUNTS = {"primary": 30, "sign_stress": 3}
CONTROL = "xgrammar_tool_external_integer_strings"
TREATMENT = "xgrammar_tool_internal_integers"
ATTRIBUTION_CATEGORIES = (
    "integer_lexical_boundary_change",
    "tool_selection_change",
    "argument_semantic_correction",
    "argument_semantic_regression",
    "transduction_or_validation_failure",
    "execution_or_state_failure",
    "truncation",
    "other",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def rate(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    count = sum(row.get(field) is True for row in rows)
    return {
        "count": count,
        "rate": count / len(rows),
        "wilson_ci95": wilson_interval(count, len(rows)),
    }


def summarize_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [int(row["generated_tokens"]) for row in rows]
    latencies = [float(row["latency_ms"]) for row in rows]
    fields = (
        "executable_contract_success",
        "tool_selection_correct",
        "whole_response_valid_json",
        "internal_schema_valid",
        "external_schema_valid",
        "argument_semantics_correct",
        "execution_success",
        "correct_post_execution_state",
    )
    return {
        "condition": rows[0]["condition"],
        "examples": len(rows),
        **{field: rate(rows, field) for field in fields},
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "transduction_failures": sum(row.get("transduction_error") is not None for row in rows),
        "heuristic_repairs": sum(int(row.get("heuristic_repair_count", 0)) for row in rows),
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
    }


def paired_effect(
    ids: list[str],
    control: dict[str, dict[str, Any]],
    treatment: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    values = [
        int(treatment[item].get("executable_contract_success") is True)
        - int(control[item].get("executable_contract_success") is True)
        for item in ids
    ]
    treatment_only = sum(value == 1 for value in values)
    control_only = sum(value == -1 for value in values)
    return {
        "paired_difference": sum(values) / len(values),
        "exact_paired_bootstrap_ci95": bootstrap_interval(values),
        "treatment_only": treatment_only,
        "control_only": control_only,
        "both_success": sum(
            control[item].get("executable_contract_success") is True
            and treatment[item].get("executable_contract_success") is True
            for item in ids
        ),
        "both_failure": sum(
            control[item].get("executable_contract_success") is not True
            and treatment[item].get("executable_contract_success") is not True
            for item in ids
        ),
        "mcnemar_p_exact": exact_mcnemar(treatment_only, control_only),
    }


def analyze_subset(
    subset: str,
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected = EXPECTED_COUNTS[subset]
    control_subset = [row for row in control_rows if row.get("subset") == subset]
    treatment_subset = [row for row in treatment_rows if row.get("subset") == subset]
    if len(control_subset) != expected or len(treatment_subset) != expected:
        raise ValueError(f"{subset}: expected {expected} rows per condition")
    control_ids = [str(row["item_id"]) for row in control_subset]
    treatment_ids = [str(row["item_id"]) for row in treatment_subset]
    if control_ids != treatment_ids or len(control_ids) != len(set(control_ids)):
        raise ValueError(f"{subset}: paired IDs differ or contain duplicates")
    control = {str(row["item_id"]): row for row in control_subset}
    treatment = {str(row["item_id"]): row for row in treatment_subset}
    repaired = [
        item
        for item in control_ids
        if treatment[item].get("executable_contract_success") is True
        and control[item].get("executable_contract_success") is not True
    ]
    broken = [
        item
        for item in control_ids
        if control[item].get("executable_contract_success") is True
        and treatment[item].get("executable_contract_success") is not True
    ]
    discordants = []
    for item in repaired + broken:
        left = control[item]
        right = treatment[item]
        discordants.append(
            {
                "subset": subset,
                "item_id": item,
                "direction": "treatment_only_win" if item in repaired else "control_only_win",
                "function_name": left.get("function_name"),
                "required_integer_fields": left.get("required_integer_fields"),
                "negative_required_integer_references": left.get("negative_required_integer_references"),
                "acceptable_arguments": left.get("acceptable_arguments"),
                "control_decoded_arguments": left.get("decoded_arguments"),
                "treatment_decoded_arguments": right.get("decoded_arguments"),
                "control_components": {
                    field: left.get(field)
                    for field in (
                        "tool_selection_correct",
                        "internal_schema_valid",
                        "external_schema_valid",
                        "argument_semantics_correct",
                        "execution_success",
                        "correct_post_execution_state",
                        "hit_max_new_tokens",
                        "error",
                    )
                },
                "treatment_components": {
                    field: right.get(field)
                    for field in (
                        "tool_selection_correct",
                        "internal_schema_valid",
                        "external_schema_valid",
                        "argument_semantics_correct",
                        "execution_success",
                        "correct_post_execution_state",
                        "hit_max_new_tokens",
                        "error",
                    )
                },
                "control_raw_output": left.get("raw_output"),
                "treatment_raw_output": right.get("raw_output"),
                "manual_category": None,
                "manual_notes": None,
            }
        )
    return (
        {
            "subset": subset,
            "paired_examples": expected,
            "control": summarize_condition(control_subset),
            "treatment": summarize_condition(treatment_subset),
            "primary_executable_effect": paired_effect(
                control_ids, control, treatment
            ),
            "repaired_item_ids": repaired,
            "newly_broken_item_ids": broken,
        },
        discordants,
    )


def merge_manual(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not path.is_file():
        return rows
    prior = {
        (str(row.get("subset")), str(row.get("item_id"))): row
        for row in read_jsonl(path)
    }
    for row in rows:
        old = prior.get((row["subset"], row["item_id"]), {})
        row["manual_category"] = old.get("manual_category")
        row["manual_notes"] = old.get("manual_notes")
    return rows


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Bounded executable tool-call pilot summary",
        "",
        "The random primary sample and negative sign-stress set are reported separately. Latency is descriptive only.",
        "",
    ]
    for subset in EXPECTED_COUNTS:
        result = summary["subsets"][subset]
        effect = result["primary_executable_effect"]
        lines.extend(
            [
                f"## {subset.replace('_', ' ').title()}",
                "",
                "| Condition | n | Executable success | External valid | Exact arguments | Execution success | State correct | Errors | Caps |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for condition in ("control", "treatment"):
            group = result[condition]
            lines.append(
                f"| {condition} | {group['examples']} | "
                f"{percent(group['executable_contract_success']['rate'])} | "
                f"{percent(group['external_schema_valid']['rate'])} | "
                f"{percent(group['argument_semantics_correct']['rate'])} | "
                f"{percent(group['execution_success']['rate'])} | "
                f"{percent(group['correct_post_execution_state']['rate'])} | "
                f"{group['errors']} | {group['cap_hits']} |"
            )
        interval = effect["exact_paired_bootstrap_ci95"]
        lines.extend(
            [
                "",
                f"Paired difference: {percent(effect['paired_difference'])}, interval [{percent(interval[0])}, {percent(interval[1])}].",
                f"Treatment-only wins: {effect['treatment_only']}. Control-only wins: {effect['control_only']}. Exact McNemar p: {effect['mcnemar_p_exact']:.6g}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Manual audit",
            "",
            f"Discordant rows: {summary['discordant_items']}.",
            f"Manual audit complete: {str(summary['manual_audit_complete']).lower()}.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--treatment", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--failure-attribution", type=Path, required=True)
    parser.add_argument("--require-attribution", action="store_true")
    args = parser.parse_args()
    control_rows = read_jsonl(args.control)
    treatment_rows = read_jsonl(args.treatment)
    if {row.get("condition") for row in control_rows} != {CONTROL}:
        raise ValueError("unexpected control condition")
    if {row.get("condition") for row in treatment_rows} != {TREATMENT}:
        raise ValueError("unexpected treatment condition")
    subsets: dict[str, Any] = {}
    discordants: list[dict[str, Any]] = []
    for subset in EXPECTED_COUNTS:
        result, rows = analyze_subset(subset, control_rows, treatment_rows)
        subsets[subset] = result
        discordants.extend(rows)
    discordants = merge_manual(args.failure_attribution, discordants)
    manual_complete = all(
        row.get("manual_category") in ATTRIBUTION_CATEGORIES
        and bool(str(row.get("manual_notes") or "").strip())
        for row in discordants
    )
    if args.require_attribution and not manual_complete:
        raise ValueError("manual discordant audit is incomplete")
    summary = {
        "analysis_version": "bounded-bfcl-tool-paired-v1",
        "primary_subset": "primary",
        "inputs": {
            "control": {"path": str(args.control), "sha256": sha256(args.control)},
            "treatment": {"path": str(args.treatment), "sha256": sha256(args.treatment)},
        },
        "subsets": subsets,
        "discordant_items": len(discordants),
        "manual_audit_complete": manual_complete,
        "attribution_categories": list(ATTRIBUTION_CATEGORIES),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(summary), encoding="utf-8")
    write_jsonl(args.failure_attribution, discordants)
    print(args.out_json)
    print(args.out_md)
    print(args.failure_attribution)


if __name__ == "__main__":
    main()
