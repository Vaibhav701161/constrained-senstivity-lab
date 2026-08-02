#!/usr/bin/env python3
"""Aggregate baseline JSONL files without dropping failed generations."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    return parser.parse_args()


def load_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON at {path}:{line_number}: {exc}"
                    ) from exc
                row["_source_file"] = str(path)
                rows.append(row)
    return rows


def rate(rows: list[dict[str, Any]], field: str) -> float | None:
    relevant = [row[field] for row in rows if row.get(field) is not None]
    if not relevant:
        return None
    return sum(bool(value) for value in relevant) / len(relevant)


def mean_numeric(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return statistics.fmean(values) if values else None


def median_numeric(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return statistics.median(values) if values else None


def summarize_group(
    model: str, condition: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "model": model,
        "condition": condition,
        "examples": len(rows),
        "correct_exact": sum(bool(row.get("correct_exact")) for row in rows),
        "accuracy": rate(rows, "correct_exact"),
        "whole_response_valid_json": rate(rows, "whole_response_valid_json"),
        "first_object_recoverable": rate(rows, "first_object_recoverable"),
        "schema_valid": rate(rows, "schema_valid"),
        "field_order_matches": rate(rows, "field_order_matches"),
        "final_answer_marker_at_end": rate(rows, "final_answer_marker_at_end"),
        "hit_max_new_tokens": rate(rows, "hit_max_new_tokens"),
        "avg_latency_ms": mean_numeric(rows, "latency_ms"),
        "median_latency_ms": median_numeric(rows, "latency_ms"),
        "avg_generated_tokens": mean_numeric(rows, "generated_tokens"),
        "errors": sum(row.get("error") is not None for row in rows),
        "source_files": sorted({row["_source_file"] for row in rows}),
    }


def paired_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model_condition: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(
        dict
    )
    for row in rows:
        key = (str(row["model"]), str(row["condition"]))
        by_model_condition[key][str(row["item_id"])] = row

    comparisons = (
        ("prompted_json_reasoning_first", "free", "json_prompt_cost"),
        (
            "prompted_json_answer_first",
            "prompted_json_reasoning_first",
            "prompted_field_order_effect",
        ),
        (
            "outlines_json_reasoning_first",
            "prompted_json_reasoning_first",
            "outlines_constraint_effect",
        ),
        (
            "outlines_json_answer_first",
            "outlines_json_reasoning_first",
            "outlines_field_order_effect",
        ),
    )
    models = sorted({model for model, _ in by_model_condition})
    results: list[dict[str, Any]] = []
    for model in models:
        for treatment, control, name in comparisons:
            treatment_rows = by_model_condition.get((model, treatment), {})
            control_rows = by_model_condition.get((model, control), {})
            shared_ids = sorted(set(treatment_rows) & set(control_rows))
            if not shared_ids:
                continue
            treatment_wins = 0
            control_wins = 0
            both_correct = 0
            both_wrong = 0
            for item_id in shared_ids:
                treatment_correct = bool(treatment_rows[item_id].get("correct_exact"))
                control_correct = bool(control_rows[item_id].get("correct_exact"))
                if treatment_correct and not control_correct:
                    treatment_wins += 1
                elif control_correct and not treatment_correct:
                    control_wins += 1
                elif treatment_correct:
                    both_correct += 1
                else:
                    both_wrong += 1
            results.append(
                {
                    "model": model,
                    "comparison": name,
                    "treatment": treatment,
                    "control": control,
                    "paired_examples": len(shared_ids),
                    "accuracy_delta": (treatment_wins - control_wins) / len(shared_ids),
                    "treatment_only_correct": treatment_wins,
                    "control_only_correct": control_wins,
                    "both_correct": both_correct,
                    "both_wrong": both_wrong,
                }
            )
    return results


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def number(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Day 2 baseline summary",
        "",
        "All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.",
        "",
        "| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for group in summary["groups"]:
        lines.append(
            "| {model} | {condition} | {examples} | {accuracy} | {whole} | "
            "{recoverable} | {schema} | {order} | {final_marker} | {hit_cap} | {avg_ms} | {median_ms} | "
            "{tokens} | {errors} |".format(
                model=group["model"],
                condition=group["condition"],
                examples=group["examples"],
                accuracy=percent(group["accuracy"]),
                whole=percent(group["whole_response_valid_json"]),
                recoverable=percent(group["first_object_recoverable"]),
                schema=percent(group["schema_valid"]),
                order=percent(group["field_order_matches"]),
                final_marker=percent(group["final_answer_marker_at_end"]),
                hit_cap=percent(group["hit_max_new_tokens"]),
                avg_ms=number(group["avg_latency_ms"]),
                median_ms=number(group["median_latency_ms"]),
                tokens=number(group["avg_generated_tokens"]),
                errors=group["errors"],
            )
        )

    lines.extend(
        [
            "",
            "## Paired comparisons",
            "",
            "Positive delta favors treatment; negative delta favors control.",
            "",
            "| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for comparison in summary["paired_comparisons"]:
        lines.append(
            "| {model} | {comparison} | {paired_examples} | {delta} | "
            "{treatment_only_correct} | {control_only_correct} | {both_correct} | {both_wrong} |".format(
                **comparison,
                delta=percent(comparison["accuracy_delta"]),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    rows = load_rows(args.inputs)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["model"]), str(row["condition"]))].append(row)

    summary = {
        "input_files": [str(path) for path in args.inputs],
        "total_rows": len(rows),
        "groups": [
            summarize_group(model, condition, group_rows)
            for (model, condition), group_rows in sorted(grouped.items())
        ],
        "paired_comparisons": paired_deltas(rows),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(summary), encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
