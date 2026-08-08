#!/usr/bin/env python3
"""Analyze the canonical string control against the frozen integer treatment."""

from __future__ import annotations

import argparse
import copy
import hashlib
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
    canonical_schema_pair,
)
from scripts.analyze_second_family_replication import (
    paired_metric,
    reasoning_consistency,
    summarize_condition,
)

CONTROL = "xgrammar_json_canonical_integer_string_reasoning_first"
TREATMENT = "xgrammar_json_integer_reasoning_first"
EXPECTED_ROWS = 150
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected only JSON objects")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def rescore_rows(
    rows: list[dict[str, Any]], *, treatment: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    external, internal_integer = canonical_schema_pair()
    control_spec = ConditionSpec(
        name=CONTROL,
        backend="xgrammar",
        answer_representation=AnswerRepresentation.CANONICAL_SIGNED_INTEGER_STRING,
    )
    internal = internal_integer if treatment else external
    representation = (
        AnswerRepresentation.INTEGER
        if treatment
        else AnswerRepresentation.CANONICAL_SIGNED_INTEGER_STRING
    )
    expected_condition = TREATMENT if treatment else CONTROL
    replayed: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for row in rows:
        if row.get("condition") != expected_condition:
            raise ValueError(f"unexpected condition: {row.get('condition')!r}")
        score = score_alignment_output(
            str(row["raw_output"]),
            internal,
            external,
            control_spec.field_order,
            str(row["gold_answer"]),
            representation,
        )
        updated = copy.deepcopy(row)
        updated.update(score)
        updated["correct_exact"] = score["semantic_correct"]
        updated["correct_exact_strict"] = score["contract_valid_correct"]
        if not treatment:
            for key, value in score.items():
                if row.get(key) != value:
                    mismatches.append(
                        {
                            "item_id": row["item_id"],
                            "field": key,
                            "stored": row.get(key),
                            "replayed": value,
                        }
                    )
        replayed.append(updated)
    return replayed, mismatches


def merge_manual(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not path.is_file():
        return rows
    prior = {str(row["item_id"]): row for row in read_jsonl(path)}
    for row in rows:
        old = prior.get(str(row["item_id"]), {})
        row["manual_category"] = old.get("manual_category")
        row["manual_notes"] = old.get("manual_notes")
    return rows


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def markdown(summary: dict[str, Any]) -> str:
    effect = summary["primary_contract_valid_effect"]
    interval = effect["exact_paired_bootstrap_ci95"]
    lines = [
        "# Canonical schema-equivalence correction summary",
        "",
        "The integer treatment is the immutable accepted Llama treatment arm. Both arms are rescored from raw output against the exact canonical external schema.",
        "",
        "| Condition | n | Contract-valid correct | Semantic correct | External valid | Internal valid | Errors | Caps | Mean tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("control", "treatment"):
        group = summary[name]
        lines.append(
            f"| {name} | {group['examples']} | "
            f"{percent(group['contract_valid_correctness']['rate'])} | "
            f"{percent(group['semantic_correctness']['rate'])} | "
            f"{percent(group['final_external_validity']['rate'])} | "
            f"{percent(group['internal_schema_validity']['rate'])} | "
            f"{group['errors']} | {group['cap_hits']} | "
            f"{group['generated_tokens']['mean']:.1f} |"
        )
    lines.extend(
        [
            "",
            f"Treatment-minus-control difference: {percent(effect['paired_difference'])} with exact paired bootstrap 95% interval [{percent(interval[0])}, {percent(interval[1])}].",
            f"Treatment-only wins: {effect['treatment_only']}. Control-only wins: {effect['control_only']}. Exact McNemar p: {effect['mcnemar_p_exact']:.6g}.",
            "",
            f"Discordant items: {summary['discordant_items']}.",
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
    control_source = read_jsonl(args.control)
    treatment_source = read_jsonl(args.treatment)
    if len(control_source) != EXPECTED_ROWS or len(treatment_source) != EXPECTED_ROWS:
        raise ValueError("correction requires exactly 150 rows per arm")
    control_ids = [str(row["item_id"]) for row in control_source]
    treatment_ids = [str(row["item_id"]) for row in treatment_source]
    if control_ids != treatment_ids or len(set(control_ids)) != EXPECTED_ROWS:
        raise ValueError("paired item IDs differ or contain duplicates")
    control, control_score_mismatches = rescore_rows(control_source, treatment=False)
    treatment, _ = rescore_rows(treatment_source, treatment=True)
    left = {str(row["item_id"]): row for row in control}
    right = {str(row["item_id"]): row for row in treatment}
    effect = paired_metric(
        control_ids,
        left,
        right,
        lambda row: bool(row.get("contract_valid_correct")),
    )
    repaired = [
        item
        for item in control_ids
        if right[item]["contract_valid_correct"]
        and not left[item]["contract_valid_correct"]
    ]
    broken = [
        item
        for item in control_ids
        if left[item]["contract_valid_correct"]
        and not right[item]["contract_valid_correct"]
    ]
    discordants = []
    for item in repaired + broken:
        discordants.append(
            {
                "item_id": item,
                "direction": (
                    "treatment_only_win" if item in repaired else "control_only_win"
                ),
                "gold_answer": left[item].get("gold_answer_normalized"),
                "control_answer": left[item].get("predicted_answer_normalized"),
                "treatment_answer": right[item].get("predicted_answer_normalized"),
                "control_reasoning_consistency": reasoning_consistency(left[item]),
                "treatment_reasoning_consistency": reasoning_consistency(right[item]),
                "control_raw_output": left[item].get("raw_output"),
                "treatment_raw_output": right[item].get("raw_output"),
                "control_error": left[item].get("error"),
                "treatment_error": right[item].get("error"),
                "control_cap_hit": bool(left[item].get("hit_max_new_tokens")),
                "treatment_cap_hit": bool(right[item].get("hit_max_new_tokens")),
                "manual_category": None,
                "manual_notes": None,
            }
        )
    discordants = merge_manual(args.failure_attribution, discordants)
    manual_complete = all(
        row.get("manual_category") in ATTRIBUTION_CATEGORIES
        and bool(str(row.get("manual_notes") or "").strip())
        for row in discordants
    )
    if args.require_attribution and not manual_complete:
        raise ValueError("manual discordant audit is incomplete")
    summary = {
        "analysis_version": "canonical-schema-equivalence-correction-v1",
        "primary_dataset": "fresh_unseen_150",
        "inputs": {
            "control": {"path": str(args.control), "sha256": sha256(args.control)},
            "frozen_treatment": {
                "path": str(args.treatment),
                "sha256": sha256(args.treatment),
            },
        },
        "external_pattern": r"^-?(?:0|[1-9][0-9]*)$",
        "control": summarize_condition(control),
        "treatment": summarize_condition(treatment),
        "primary_contract_valid_effect": effect,
        "secondary_semantic_effect": paired_metric(
            control_ids,
            left,
            right,
            lambda row: bool(row.get("semantic_correct")),
        ),
        "repaired_item_ids": repaired,
        "newly_broken_item_ids": broken,
        "discordant_items": len(discordants),
        "manual_audit_complete": manual_complete,
        "attribution_categories": list(ATTRIBUTION_CATEGORIES),
        "control_stored_score_mismatches": control_score_mismatches,
        "frozen_treatment_regenerated": False,
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
