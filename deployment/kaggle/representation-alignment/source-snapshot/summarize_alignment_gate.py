#!/usr/bin/env python3
"""Summarize contract-valid results and paired effects for an alignment gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
            if not isinstance(value, dict):
                raise TypeError(f"{path}:{number}: expected JSON object")
            rows.append(value)
    return rows


def wilson_interval(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    radius = z * math.sqrt(
        proportion * (1 - proportion) / total + z**2 / (4 * total**2)
    ) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def bootstrap_interval(values: list[int], seed_material: str) -> list[float] | None:
    if not values:
        return None
    seed = int(hashlib.sha256(seed_material.encode()).hexdigest()[:16], 16)
    generator = random.Random(seed)
    count = len(values)
    means = sorted(
        sum(values[generator.randrange(count)] for _ in range(count)) / count
        for _ in range(10_000)
    )
    return [means[249], means[9749]]


def exact_mcnemar(treatment_only: int, control_only: int) -> float:
    discordant = treatment_only + control_only
    if discordant == 0:
        return 1.0
    lower_tail = sum(math.comb(discordant, index) for index in range(min(treatment_only, control_only) + 1))
    return min(1.0, 2 * lower_tail / 2**discordant)


def semantic(row: dict[str, Any]) -> bool:
    return bool(row.get("semantic_correct", row.get("correct_exact")))


def external_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("external_schema_valid", row.get("schema_valid")))


def contract_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("contract_valid_correct", row.get("correct_exact_strict")))


def rate(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    successes = sum(predicate(row) for row in rows)
    return {"count": successes, "rate": successes / len(rows) if rows else None, "ci95": wilson_interval(successes, len(rows))}


def summarize_group(condition: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicted = [str(row.get("predicted_answer_normalized", "")) for row in rows]
    negative = sum(answer.startswith("-") for answer in predicted)
    latency = [float(row["latency_ms"]) for row in rows if row.get("latency_ms") is not None]
    tokens = [int(row["generated_tokens"]) for row in rows if row.get("generated_tokens") is not None]
    return {
        "condition": condition,
        "examples": len(rows),
        "semantic": rate(rows, semantic),
        "external_valid": rate(rows, external_valid),
        "contract_valid": rate(rows, contract_valid),
        "internal_valid": rate(rows, lambda row: bool(row.get("internal_schema_valid", row.get("schema_valid")))),
        "negative_answers": negative,
        "negative_answer_rate": negative / len(rows) if rows else None,
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "average_latency_ms": statistics.fmean(latency) if latency else None,
        "median_latency_ms": statistics.median(latency) if latency else None,
        "average_generated_tokens": statistics.fmean(tokens) if tokens else None,
    }


def paired_comparison(
    name: str,
    treatment_name: str,
    control_name: str,
    rows_by_condition: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    treatment = rows_by_condition[treatment_name]
    control = rows_by_condition[control_name]
    shared = sorted(set(treatment) & set(control))
    if not shared:
        raise ValueError(f"{name}: no shared item IDs")

    def paired_metric(metric: Callable[[dict[str, Any]], bool], label: str) -> dict[str, Any]:
        treatment_only = sum(metric(treatment[item]) and not metric(control[item]) for item in shared)
        control_only = sum(metric(control[item]) and not metric(treatment[item]) for item in shared)
        both_correct = sum(metric(treatment[item]) and metric(control[item]) for item in shared)
        both_wrong = len(shared) - treatment_only - control_only - both_correct
        values = [int(metric(treatment[item])) - int(metric(control[item])) for item in shared]
        return {
            "delta": (treatment_only - control_only) / len(shared),
            "delta_ci95": bootstrap_interval(values, f"{name}:{label}"),
            "treatment_only": treatment_only,
            "control_only": control_only,
            "both_correct": both_correct,
            "both_wrong": both_wrong,
            "mcnemar_p_exact": exact_mcnemar(treatment_only, control_only),
        }

    return {
        "name": name,
        "treatment": treatment_name,
        "control": control_name,
        "paired_examples": len(shared),
        "semantic": paired_metric(semantic, "semantic"),
        "contract_valid": paired_metric(contract_valid, "contract_valid"),
        "repaired_item_ids": [
            item for item in shared if semantic(treatment[item]) and not semantic(control[item])
        ],
        "newly_broken_item_ids": [
            item for item in shared if semantic(control[item]) and not semantic(treatment[item])
        ],
    }


def format_percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def format_interval(value: list[float] | None) -> str:
    return "n/a" if value is None else f"[{format_percent(value[0])}, {format_percent(value[1])}]"


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Representation-alignment gate summary",
        "",
        "All denominators retain generation errors and token-cap failures.",
        "",
        "| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for group in summary["groups"]:
        lines.append(
            "| {condition} | {examples} | {semantic_count}/{examples} ({semantic_rate}) | "
            "{external_count}/{examples} ({external_rate}) | {contract_count}/{examples} ({contract_rate}) | "
            "{internal_count}/{examples} ({internal_rate}) | {negative_answers}/{examples} ({negative_rate}) | "
            "{errors} | {cap_hits} | {latency} | {tokens} |".format(
                condition=group["condition"],
                examples=group["examples"],
                semantic_count=group["semantic"]["count"],
                semantic_rate=format_percent(group["semantic"]["rate"]),
                external_count=group["external_valid"]["count"],
                external_rate=format_percent(group["external_valid"]["rate"]),
                contract_count=group["contract_valid"]["count"],
                contract_rate=format_percent(group["contract_valid"]["rate"]),
                internal_count=group["internal_valid"]["count"],
                internal_rate=format_percent(group["internal_valid"]["rate"]),
                negative_answers=group["negative_answers"],
                negative_rate=format_percent(group["negative_answer_rate"]),
                errors=group["errors"],
                cap_hits=group["cap_hits"],
                latency="n/a" if group["average_latency_ms"] is None else f"{group['average_latency_ms']:.1f}",
                tokens="n/a" if group["average_generated_tokens"] is None else f"{group['average_generated_tokens']:.1f}",
            )
        )
    lines.extend(
        [
            "",
            "## Paired comparisons",
            "",
            "Positive deltas favor the treatment. The contract-valid metric is the primary product metric.",
            "",
            "| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for comparison in summary["paired_comparisons"]:
        semantic_result = comparison["semantic"]
        contract_result = comparison["contract_valid"]
        lines.append(
            "| {name} | {n} | {semantic_delta} ({semantic_ci}) | {semantic_wins}/{semantic_losses} | {semantic_p:.6g} | "
            "{contract_delta} ({contract_ci}) | {contract_wins}/{contract_losses} | {contract_p:.6g} |".format(
                name=comparison["name"],
                n=comparison["paired_examples"],
                semantic_delta=format_percent(semantic_result["delta"]),
                semantic_ci=format_interval(semantic_result["delta_ci95"]),
                semantic_wins=semantic_result["treatment_only"],
                semantic_losses=semantic_result["control_only"],
                semantic_p=semantic_result["mcnemar_p_exact"],
                contract_delta=format_percent(contract_result["delta"]),
                contract_ci=format_interval(contract_result["delta_ci95"]),
                contract_wins=contract_result["treatment_only"],
                contract_losses=contract_result["control_only"],
                contract_p=contract_result["mcnemar_p_exact"],
            )
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--exclude-item-id", action="append", default=[])
    parser.add_argument(
        "--comparison",
        action="append",
        nargs=3,
        metavar=("NAME", "TREATMENT", "CONTROL"),
        default=[],
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    excluded = {str(item_id) for item_id in args.exclude_item_id}
    rows = [
        row
        for path in args.inputs
        for row in read_jsonl(path)
        if str(row.get("item_id")) not in excluded
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["condition"])].append(row)
    rows_by_condition: dict[str, dict[str, dict[str, Any]]] = {}
    for condition, condition_rows in grouped.items():
        indexed = {str(row["item_id"]): row for row in condition_rows}
        if len(indexed) != len(condition_rows):
            raise ValueError(f"{condition}: duplicate item IDs")
        rows_by_condition[condition] = indexed
    comparisons = [
        paired_comparison(name, treatment, control, rows_by_condition)
        for name, treatment, control in args.comparison
    ]
    summary = {
        "input_files": [str(path) for path in args.inputs],
        "excluded_item_ids": sorted(excluded),
        "total_rows": len(rows),
        "groups": [summarize_group(condition, group) for condition, group in sorted(grouped.items())],
        "paired_comparisons": comparisons,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(summary), encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
