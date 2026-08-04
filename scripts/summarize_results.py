#!/usr/bin/env python3
"""Aggregate baseline JSONL files without dropping failed generations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
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
    parser.add_argument(
        "--exclude-item-id",
        action="append",
        default=[],
        help="Exclude an audited item ID; repeat for multiple IDs",
    )
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


def wilson_interval(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
        / denominator
    )
    return [max(0.0, center - margin), min(1.0, center + margin)]


def field_interval(rows: list[dict[str, Any]], field: str) -> list[float] | None:
    relevant = [bool(row[field]) for row in rows if row.get(field) is not None]
    return wilson_interval(sum(relevant), len(relevant))


def paired_bootstrap_interval(
    differences: list[int], seed_text: str, replicates: int = 20_000
) -> list[float]:
    if not differences:
        raise ValueError("Paired bootstrap requires at least one difference")
    seed = int.from_bytes(hashlib.sha256(seed_text.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    total = len(differences)
    estimates = sorted(
        sum(differences[rng.randrange(total)] for _ in range(total)) / total
        for _ in range(replicates)
    )
    return [
        estimates[int(0.025 * (replicates - 1))],
        estimates[int(0.975 * (replicates - 1))],
    ]


def mean_numeric(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return statistics.fmean(values) if values else None


def median_numeric(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return statistics.median(values) if values else None


def mean_latency_per_token_ms(rows: list[dict[str, Any]]) -> float | None:
    values = [
        float(row["latency_ms"]) / int(row["generated_tokens"])
        for row in rows
        if row.get("latency_ms") is not None
        and row.get("generated_tokens") is not None
        and int(row["generated_tokens"]) > 0
    ]
    return statistics.fmean(values) if values else None


def exact_mcnemar_p(treatment_only: int, control_only: int) -> float:
    """Two-sided exact McNemar p-value over discordant pairs."""
    discordant = treatment_only + control_only
    if discordant == 0:
        return 1.0
    tail = sum(
        math.comb(discordant, successes)
        for successes in range(min(treatment_only, control_only) + 1)
    ) / (2**discordant)
    return min(1.0, 2 * tail)


def summarize_group(
    model: str, condition: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "model": model,
        "condition": condition,
        "examples": len(rows),
        "correct_exact": sum(bool(row.get("correct_exact")) for row in rows),
        "accuracy": rate(rows, "correct_exact"),
        "accuracy_ci95": field_interval(rows, "correct_exact"),
        "strict_accuracy": rate(rows, "correct_exact_strict"),
        "strict_accuracy_ci95": field_interval(rows, "correct_exact_strict"),
        "answer_field_strict_numeric": rate(rows, "answer_field_strict_numeric"),
        "whole_response_valid_json": rate(rows, "whole_response_valid_json"),
        "first_object_recoverable": rate(rows, "first_object_recoverable"),
        "schema_valid": rate(rows, "schema_valid"),
        "field_order_matches": rate(rows, "field_order_matches"),
        "final_answer_marker_at_end": rate(rows, "final_answer_marker_at_end"),
        "hit_max_new_tokens": rate(rows, "hit_max_new_tokens"),
        "avg_latency_ms": mean_numeric(rows, "latency_ms"),
        "median_latency_ms": median_numeric(rows, "latency_ms"),
        "avg_generated_tokens": mean_numeric(rows, "generated_tokens"),
        "avg_latency_per_token_ms": mean_latency_per_token_ms(rows),
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
        (
            "xgrammar_json_reasoning_first",
            "prompted_json_reasoning_first",
            "xgrammar_constraint_effect",
        ),
        (
            "xgrammar_json_reasoning_first",
            "outlines_json_reasoning_first",
            "xgrammar_vs_outlines",
        ),
    )
    models = sorted({model for model, _ in by_model_condition})
    results: list[dict[str, Any]] = []

    def strict_or_legacy(row: dict[str, Any]) -> bool:
        strict = row.get("correct_exact_strict")
        return bool(row.get("correct_exact")) if strict is None else bool(strict)

    def paired_counts(
        treatment_rows: dict[str, dict[str, Any]],
        control_rows: dict[str, dict[str, Any]],
        shared_ids: list[str],
        correctness,
    ) -> tuple[int, int, int, int]:
        treatment_wins = 0
        control_wins = 0
        both_correct = 0
        both_wrong = 0
        for item_id in shared_ids:
            treatment_correct = correctness(treatment_rows[item_id])
            control_correct = correctness(control_rows[item_id])
            if treatment_correct and not control_correct:
                treatment_wins += 1
            elif control_correct and not treatment_correct:
                control_wins += 1
            elif treatment_correct:
                both_correct += 1
            else:
                both_wrong += 1
        return treatment_wins, control_wins, both_correct, both_wrong

    for model in models:
        for treatment, control, name in comparisons:
            treatment_rows = by_model_condition.get((model, treatment), {})
            control_rows = by_model_condition.get((model, control), {})
            shared_ids = sorted(set(treatment_rows) & set(control_rows))
            if not shared_ids:
                continue
            treatment_wins, control_wins, both_correct, both_wrong = paired_counts(
                treatment_rows,
                control_rows,
                shared_ids,
                lambda row: bool(row.get("correct_exact")),
            )
            (
                strict_treatment_wins,
                strict_control_wins,
                strict_both_correct,
                strict_both_wrong,
            ) = paired_counts(
                treatment_rows,
                control_rows,
                shared_ids,
                strict_or_legacy,
            )
            results.append(
                {
                    "model": model,
                    "comparison": name,
                    "treatment": treatment,
                    "control": control,
                    "paired_examples": len(shared_ids),
                    "accuracy_delta": (treatment_wins - control_wins) / len(shared_ids),
                    "accuracy_delta_ci95": paired_bootstrap_interval(
                        [
                            int(bool(treatment_rows[item_id].get("correct_exact")))
                            - int(bool(control_rows[item_id].get("correct_exact")))
                            for item_id in shared_ids
                        ],
                        f"{model}:{name}:legacy",
                    ),
                    "treatment_only_correct": treatment_wins,
                    "control_only_correct": control_wins,
                    "both_correct": both_correct,
                    "both_wrong": both_wrong,
                    "mcnemar_p_exact": exact_mcnemar_p(treatment_wins, control_wins),
                    "strict_accuracy_delta": (
                        strict_treatment_wins - strict_control_wins
                    )
                    / len(shared_ids),
                    "strict_accuracy_delta_ci95": paired_bootstrap_interval(
                        [
                            int(strict_or_legacy(treatment_rows[item_id]))
                            - int(strict_or_legacy(control_rows[item_id]))
                            for item_id in shared_ids
                        ],
                        f"{model}:{name}:strict",
                    ),
                    "strict_treatment_only_correct": strict_treatment_wins,
                    "strict_control_only_correct": strict_control_wins,
                    "strict_both_correct": strict_both_correct,
                    "strict_both_wrong": strict_both_wrong,
                    "strict_mcnemar_p_exact": exact_mcnemar_p(
                        strict_treatment_wins, strict_control_wins
                    ),
                }
            )
    return results


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def number(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def p_value(value: float | None) -> str:
    """Format p-values without rounding small, nonzero values to zero."""
    return "n/a" if value is None else f"{value:.3g}"


def interval(value: list[float] | None) -> str:
    if value is None:
        return "n/a"
    return f"[{percent(value[0])}, {percent(value[1])}]"


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Baseline summary",
        "",
        "All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.",
        "",
        "| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for group in summary["groups"]:
        lines.append(
            "| {model} | {condition} | {examples} | {accuracy} | {accuracy_ci} | {strict_accuracy} | {strict_accuracy_ci} | {numeric_answer} | {whole} | "
            "{recoverable} | {schema} | {order} | {final_marker} | {hit_cap} | {avg_ms} | {median_ms} | "
            "{tokens} | {ms_per_token} | {errors} |".format(
                model=group["model"],
                condition=group["condition"],
                examples=group["examples"],
                accuracy=percent(group["accuracy"]),
                accuracy_ci=interval(group["accuracy_ci95"]),
                strict_accuracy=percent(group["strict_accuracy"]),
                strict_accuracy_ci=interval(group["strict_accuracy_ci95"]),
                numeric_answer=percent(group["answer_field_strict_numeric"]),
                whole=percent(group["whole_response_valid_json"]),
                recoverable=percent(group["first_object_recoverable"]),
                schema=percent(group["schema_valid"]),
                order=percent(group["field_order_matches"]),
                final_marker=percent(group["final_answer_marker_at_end"]),
                hit_cap=percent(group["hit_max_new_tokens"]),
                avg_ms=number(group["avg_latency_ms"]),
                median_ms=number(group["median_latency_ms"]),
                tokens=number(group["avg_generated_tokens"]),
                ms_per_token=number(group["avg_latency_per_token_ms"]),
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
            "| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for comparison in summary["paired_comparisons"]:
        lines.append(
            "| {model} | {comparison} | {paired_examples} | {delta} | {delta_ci} | {strict_delta} | {strict_delta_ci} | "
            "{exact_p} | {strict_exact_p} | "
            "{treatment_only_correct} | {control_only_correct} | "
            "{strict_treatment_only_correct} | {strict_control_only_correct} | "
            "{both_correct} | {both_wrong} |".format(
                **comparison,
                delta=percent(comparison["accuracy_delta"]),
                delta_ci=interval(comparison["accuracy_delta_ci95"]),
                strict_delta=percent(comparison["strict_accuracy_delta"]),
                strict_delta_ci=interval(comparison["strict_accuracy_delta_ci95"]),
                exact_p=p_value(comparison["mcnemar_p_exact"]),
                strict_exact_p=p_value(comparison["strict_mcnemar_p_exact"]),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    loaded_rows = load_rows(args.inputs)
    excluded_item_ids = set(args.exclude_item_id)
    rows = [
        row for row in loaded_rows if str(row.get("item_id")) not in excluded_item_ids
    ]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["model"]), str(row["condition"]))].append(row)

    summary = {
        "input_files": [str(path) for path in args.inputs],
        "excluded_item_ids": sorted(excluded_item_ids),
        "excluded_rows": len(loaded_rows) - len(rows),
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
