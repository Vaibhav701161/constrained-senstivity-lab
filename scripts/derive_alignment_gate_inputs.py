#!/usr/bin/env python3
"""Derive the representation-alignment failure catalogue and targeted suite."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

DEFAULT_EXCLUSION = "gsm8k_test_454"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
            if not isinstance(row, dict):
                raise TypeError(f"{path}:{number}: expected JSON object")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_rows(path: Path) -> dict[str, dict[str, Any]]:
    indexed = {str(row["item_id"]): row for row in read_jsonl(path)}
    if len(indexed) != 50:
        raise ValueError(f"{path}: expected 50 unique items, found {len(indexed)}")
    return indexed


def answer(row: dict[str, Any]) -> str | None:
    value = row.get("predicted_answer_normalized", row.get("predicted_answer"))
    return str(value) if value is not None else None


def sign_inverse(left: str | None, right: str | None) -> bool:
    return bool(left and right and right.startswith("-") and right[1:] == left)


def compact_reasoning(row: dict[str, Any]) -> str | None:
    parsed = row.get("parsed_json")
    if not isinstance(parsed, dict):
        return None
    reasoning = parsed.get("reasoning")
    if not isinstance(reasoning, str):
        return None
    return reasoning[-240:]


def add_loss_records(
    records: list[dict[str, Any]],
    control: dict[str, dict[str, Any]],
    constrained: dict[str, dict[str, Any]],
    backend: str,
    excluded: set[str],
) -> set[str]:
    losses: set[str] = set()
    for item_id in sorted(control, key=lambda value: control[value]["source_index"]):
        if item_id in excluded:
            continue
        prompt_row = control[item_id]
        constrained_row = constrained[item_id]
        if not prompt_row.get("correct_exact") or constrained_row.get("correct_exact"):
            continue
        losses.add(item_id)
        prompt_answer = answer(prompt_row)
        constrained_answer = answer(constrained_row)
        is_sign_inverse = sign_inverse(prompt_answer, constrained_answer)
        records.append(
            {
                "record_type": "paired_loss",
                "item_id": item_id,
                "source_index": constrained_row.get("source_index"),
                "comparison": f"{backend}_reasoning_first_vs_prompted_reasoning_first",
                "failure_class": (
                    "sign_inversion_at_answer_boundary"
                    if is_sign_inverse
                    else "constrained_semantic_regression"
                ),
                "candidate_mechanism": (
                    "signed_numeric_string_boundary"
                    if is_sign_inverse
                    else "requires_representation_or_boundary_trace"
                ),
                "evidence": {
                    "prompt_answer": prompt_answer,
                    "constrained_answer": constrained_answer,
                    "gold_answer": constrained_row.get("gold_answer_normalized"),
                    "reasoning_suffix": compact_reasoning(constrained_row),
                },
                "confidence": "high" if is_sign_inverse else "medium",
                "confirmatory": False,
            }
        )
    return losses


def add_negative_records(
    records: list[dict[str, Any]],
    rows: dict[str, dict[str, Any]],
    condition: str,
    excluded: set[str],
) -> None:
    for item_id in sorted(rows, key=lambda value: rows[value]["source_index"]):
        if item_id in excluded:
            continue
        row = rows[item_id]
        predicted = answer(row)
        if not predicted or not predicted.startswith("-"):
            continue
        records.append(
            {
                "record_type": "negative_answer",
                "item_id": item_id,
                "source_index": row.get("source_index"),
                "comparison": condition,
                "failure_class": "negative_answer_on_positive_gold_subset",
                "candidate_mechanism": "signed_numeric_string_boundary",
                "evidence": {
                    "predicted_answer": predicted,
                    "gold_answer": row.get("gold_answer_normalized"),
                    "reasoning_suffix": compact_reasoning(row),
                },
                "confidence": "high",
                "confirmatory": False,
            }
        )


def add_field_order_records(
    records: list[dict[str, Any]],
    reasoning_first: dict[str, dict[str, Any]],
    answer_first: dict[str, dict[str, Any]],
    system: str,
    excluded: set[str],
) -> None:
    for item_id in sorted(reasoning_first, key=lambda value: reasoning_first[value]["source_index"]):
        if item_id in excluded:
            continue
        first = reasoning_first[item_id]
        second = answer_first[item_id]
        if bool(first.get("correct_exact")) == bool(second.get("correct_exact")):
            continue
        records.append(
            {
                "record_type": "field_order_discordance",
                "item_id": item_id,
                "source_index": first.get("source_index"),
                "comparison": f"{system}_answer_first_vs_reasoning_first",
                "failure_class": (
                    "premature_answer_commitment"
                    if first.get("correct_exact") and not second.get("correct_exact")
                    else "answer_first_specific_recovery"
                ),
                "candidate_mechanism": "field_dependency_order",
                "evidence": {
                    "reasoning_first_answer": answer(first),
                    "answer_first_answer": answer(second),
                    "gold_answer": first.get("gold_answer_normalized"),
                },
                "confidence": "high",
                "confirmatory": False,
            }
        )


def add_completion_records(
    records: list[dict[str, Any]],
    diagnostics_root: Path,
) -> None:
    for path in sorted(diagnostics_root.rglob("*.jsonl")):
        for row in read_jsonl(path):
            if not row.get("hit_max_new_tokens") and row.get("error") is None:
                continue
            records.append(
                {
                    "record_type": "completion_diagnostic",
                    "item_id": str(row.get("item_id", "unknown")),
                    "source_index": row.get("source_index"),
                    "comparison": str(row.get("condition", "unknown")),
                    "failure_class": (
                        "token_cap_hit"
                        if row.get("hit_max_new_tokens")
                        else "generation_error"
                    ),
                    "candidate_mechanism": "completion_or_whitespace_policy",
                    "evidence": {
                        "source_path": str(path),
                        "error": row.get("error"),
                        "generated_tokens": row.get("generated_tokens"),
                        "max_new_tokens": row.get("max_new_tokens"),
                    },
                    "confidence": "high",
                    "confirmatory": False,
                }
            )


def build_targeted_suite(
    dataset: list[dict[str, Any]],
    prompt: dict[str, dict[str, Any]],
    outlines: dict[str, dict[str, Any]],
    xgrammar: dict[str, dict[str, Any]],
    losses: set[str],
    excluded: set[str],
) -> list[dict[str, Any]]:
    reasons: dict[str, list[str]] = defaultdict(list)
    for item_id in sorted(losses, key=lambda value: prompt[value]["source_index"]):
        reasons[item_id].append("constrained_semantic_loss")

    eligible = [row for row in dataset if str(row["id"]) not in excluded]
    matched_controls = [
        row
        for row in eligible
        if all(
            source[str(row["id"])].get("correct_exact")
            for source in (prompt, outlines, xgrammar)
        )
    ][:5]
    shared_wrong = [
        row
        for row in eligible
        if not any(
            source[str(row["id"])].get("correct_exact")
            for source in (prompt, outlines, xgrammar)
        )
    ][:3]
    for row in matched_controls:
        reasons[str(row["id"])].append("matched_all_correct_control")
    for row in shared_wrong:
        reasons[str(row["id"])].append("shared_wrong_diagnostic")

    selected = [row for row in eligible if str(row["id"]) in reasons]
    selected.sort(key=lambda row: int(row["source_index"]))
    return [{**row, "selection_reason": reasons[str(row["id"])]} for row in selected]


def parse_args() -> argparse.Namespace:
    root = Path("results/qwen2.5-7b/primary")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/gsm8k_50_seed0.jsonl"))
    parser.add_argument(
        "--prompted",
        type=Path,
        default=root / "reasoning-first/results/qwen2.5-7b-smoke/prompted_json_reasoning_first.jsonl",
    )
    parser.add_argument(
        "--outlines",
        type=Path,
        default=root / "reasoning-first/results/qwen2.5-7b-smoke/outlines_json_reasoning_first.jsonl",
    )
    parser.add_argument(
        "--xgrammar",
        type=Path,
        default=root / "reasoning-first/results/qwen2.5-7b-smoke/xgrammar_json_reasoning_first.jsonl",
    )
    parser.add_argument(
        "--prompted-answer-first",
        type=Path,
        default=root / "answer-first/results/qwen2.5-7b-smoke/prompted_json_answer_first.jsonl",
    )
    parser.add_argument(
        "--outlines-answer-first",
        type=Path,
        default=root / "answer-first/results/qwen2.5-7b-smoke/outlines_json_answer_first.jsonl",
    )
    parser.add_argument(
        "--diagnostics-root",
        type=Path,
        default=Path("results/qwen2.5-7b/diagnostics"),
    )
    parser.add_argument(
        "--exclude-item-id", action="append", default=[DEFAULT_EXCLUSION]
    )
    parser.add_argument(
        "--out-catalog",
        type=Path,
        default=Path("analysis/failure-catalog.jsonl"),
    )
    parser.add_argument(
        "--out-targeted",
        type=Path,
        default=Path("experiments/representation-alignment-gate/targeted-items.jsonl"),
    )
    parser.add_argument(
        "--out-manifest",
        type=Path,
        default=Path("experiments/representation-alignment-gate/targeted-suite-manifest.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    excluded = {str(item_id) for item_id in args.exclude_item_id}
    dataset = read_jsonl(args.dataset)
    prompt = index_rows(args.prompted)
    outlines = index_rows(args.outlines)
    xgrammar = index_rows(args.xgrammar)
    prompted_answer_first = index_rows(args.prompted_answer_first)
    outlines_answer_first = index_rows(args.outlines_answer_first)
    expected_ids = {str(row["id"]) for row in dataset}
    for name, rows in (("prompted", prompt), ("outlines", outlines), ("xgrammar", xgrammar)):
        if set(rows) != expected_ids:
            raise ValueError(f"{name}: result IDs do not match dataset IDs")

    records: list[dict[str, Any]] = []
    outlines_losses = add_loss_records(records, prompt, outlines, "outlines", excluded)
    xgrammar_losses = add_loss_records(records, prompt, xgrammar, "xgrammar", excluded)
    for name, rows in (("prompted_reasoning_first", prompt), ("outlines_reasoning_first", outlines), ("xgrammar_reasoning_first", xgrammar)):
        add_negative_records(records, rows, name, excluded)
    add_field_order_records(records, prompt, prompted_answer_first, "prompted", excluded)
    add_field_order_records(records, outlines, outlines_answer_first, "outlines", excluded)
    add_completion_records(records, args.diagnostics_root)
    records.sort(key=lambda row: (int(row.get("source_index") or -1), row["record_type"], row["comparison"]))
    write_jsonl(args.out_catalog, records)

    losses = outlines_losses | xgrammar_losses
    targeted = build_targeted_suite(dataset, prompt, outlines, xgrammar, losses, excluded)
    write_jsonl(args.out_targeted, targeted)
    manifest = {
        "selection_rule_version": "representation-alignment-targeted-v1",
        "dataset_sha256": sha256(args.dataset),
        "excluded_item_ids": sorted(excluded),
        "source_hashes": {
            "prompted": sha256(args.prompted),
            "outlines": sha256(args.outlines),
            "xgrammar": sha256(args.xgrammar),
            "prompted_answer_first": sha256(args.prompted_answer_first),
            "outlines_answer_first": sha256(args.outlines_answer_first),
        },
        "loss_counts": {
            "outlines": len(outlines_losses),
            "xgrammar": len(xgrammar_losses),
            "shared": len(outlines_losses & xgrammar_losses),
            "union": len(losses),
        },
        "targeted_examples": len(targeted),
        "targeted_item_ids": [str(row["id"]) for row in targeted],
        "catalog_records": len(records),
    }
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
