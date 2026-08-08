#!/usr/bin/env python3
"""Build the canonical correction figure directly from frozen evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


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


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def build(summary: dict[str, Any], audit: list[dict[str, Any]]) -> plt.Figure:
    if summary.get("manual_audit_complete") is not True:
        raise ValueError("manual audit must be complete")
    if len(audit) != summary.get("discordant_items"):
        raise ValueError("audit and paired summary disagree")

    control = summary["control"]
    treatment = summary["treatment"]
    effect = summary["primary_contract_valid_effect"]
    conditions = [control, treatment]
    rates = [group["contract_valid_correctness"]["rate"] for group in conditions]
    intervals = [group["contract_valid_correctness"]["wilson_ci95"] for group in conditions]
    errors = np.array(
        [
            [rate - interval[0] for rate, interval in zip(rates, intervals)],
            [interval[1] - rate for rate, interval in zip(rates, intervals)],
        ]
    )

    figure = plt.figure(figsize=(14.4, 5.6), layout="constrained")
    grid = figure.add_gridspec(1, 3, width_ratios=(1.0, 1.0, 1.35))
    colors = ["#315C8C", "#C45A35"]

    accuracy = figure.add_subplot(grid[0, 0])
    bars = accuracy.bar(
        [0, 1],
        rates,
        yerr=errors,
        capsize=5,
        color=colors,
        width=0.62,
        edgecolor="#1D2733",
        linewidth=0.8,
    )
    accuracy.set_ylim(0, 0.78)
    accuracy.set_xticks([0, 1], ["Canonical\nstring", "Integer +\ntransducer"])
    accuracy.set_ylabel("Contract-valid correctness")
    accuracy.set_title("A. Primary paired outcome", loc="left", fontweight="bold")
    accuracy.grid(axis="y", color="#D9DEE5", linewidth=0.8)
    accuracy.set_axisbelow(True)
    for bar, rate, group in zip(bars, rates, conditions):
        count = group["contract_valid_correctness"]["count"]
        accuracy.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 0.045,
            f"{count}/150\n{percent(rate)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    low, high = effect["exact_paired_bootstrap_ci95"]
    accuracy.text(
        0.5,
        0.03,
        f"Paired effect {100 * effect['paired_difference']:+.1f} pp\n"
        f"95% interval [{100 * low:.1f}, {100 * high:.1f}] pp",
        transform=accuracy.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#AAB3BF", "pad": 5},
    )

    transitions = np.array(
        [
            [effect["both_success"], effect["control_only"]],
            [effect["treatment_only"], effect["both_failure"]],
        ]
    )
    transition_axis = figure.add_subplot(grid[0, 1])
    transition_axis.imshow(transitions, cmap="Blues", vmin=0, vmax=transitions.max())
    transition_axis.set_xticks([0, 1], ["Treatment\ncorrect", "Treatment\nwrong"])
    transition_axis.set_yticks([0, 1], ["Control correct", "Control wrong"])
    transition_axis.set_title("B. Item transitions", loc="left", fontweight="bold")
    for row in range(2):
        for column in range(2):
            value = int(transitions[row, column])
            transition_axis.text(
                column,
                row,
                str(value),
                ha="center",
                va="center",
                color="white" if value > transitions.max() / 2 else "#17212B",
                fontsize=17,
                fontweight="bold",
            )
    transition_axis.text(
        0.5,
        -0.22,
        f"Wins {effect['treatment_only']} : losses {effect['control_only']}   |   "
        f"exact McNemar p = {effect['mcnemar_p_exact']:.4f}",
        transform=transition_axis.transAxes,
        ha="center",
        va="top",
        fontsize=9,
    )

    category_counts = Counter(str(row["manual_category"]) for row in audit)
    category_order = [
        "problem_interpretation_change",
        "reasoning_final_answer_inconsistency",
        "arithmetic_regression",
        "arithmetic_correction",
        "sign_or_lexical_boundary_change",
        "parser_or_validator_issue",
        "truncation",
        "other",
    ]
    labels = {
        "problem_interpretation_change": "Problem interpretation",
        "reasoning_final_answer_inconsistency": "Reasoning / final mismatch",
        "arithmetic_regression": "Arithmetic regression",
        "arithmetic_correction": "Arithmetic correction",
        "sign_or_lexical_boundary_change": "Sign / lexical boundary",
        "parser_or_validator_issue": "Parser / validator",
        "truncation": "Truncation",
        "other": "Other",
    }
    shown = [key for key in category_order if category_counts.get(key, 0)]
    values = [category_counts[key] for key in shown]
    audit_axis = figure.add_subplot(grid[0, 2])
    y_positions = np.arange(len(shown))
    audit_bars = audit_axis.barh(
        y_positions,
        values,
        color="#647C90",
        edgecolor="#263746",
        linewidth=0.8,
    )
    audit_axis.set_yticks(y_positions, [labels[key] for key in shown])
    audit_axis.invert_yaxis()
    audit_axis.set_xlim(0, max(values) + 2)
    audit_axis.set_xlabel("Discordant items")
    audit_axis.set_title("C. Complete mechanism audit", loc="left", fontweight="bold")
    audit_axis.grid(axis="x", color="#D9DEE5", linewidth=0.8)
    audit_axis.set_axisbelow(True)
    for bar, value in zip(audit_bars, values):
        audit_axis.text(
            value + 0.2,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontsize=10,
            fontweight="bold",
        )
    audit_axis.text(
        0,
        -0.22,
        "22/22 inspected; 0 sign, parser, validator, or truncation cases",
        transform=audit_axis.transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )

    figure.suptitle(
        "Canonical schema-equivalence correction on Llama 3.2 3B",
        fontsize=15,
        fontweight="bold",
    )
    figure.supxlabel(
        "Frozen unseen GSM8K holdout, n = 150 paired items, greedy FP32, XGrammar 0.2.3",
        fontsize=9,
    )
    return figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--svg", type=Path, required=True)
    args = parser.parse_args()
    figure = build(read_json(args.summary), read_jsonl(args.audit))
    args.png.parent.mkdir(parents=True, exist_ok=True)
    args.svg.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.png, dpi=180, bbox_inches="tight", facecolor="white")
    figure.savefig(args.svg, bbox_inches="tight", facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    main()
