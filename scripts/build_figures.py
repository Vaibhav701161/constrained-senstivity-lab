#!/usr/bin/env python3
"""Generate publication-style figures from accepted experiment artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "results/qwen2.5-7b/primary/combined/summary_clean.json"
DEFAULT_OUTPUT = ROOT / "assets/figures"

COLORS = {
    "recoverable": "#0072B2",
    "strict": "#009E73",
    "schema": "#D55E00",
    "negative": "#B2182B",
    "positive": "#2166AC",
    "neutral": "#4D4D4D",
    "grid": "#D9D9D9",
}

LABELS = {
    "free": "Free response",
    "prompted_json_reasoning_first": "Prompted JSON\nreasoning first",
    "outlines_json_reasoning_first": "Outlines\nreasoning first",
    "xgrammar_json_reasoning_first": "XGrammar\nreasoning first",
    "prompted_json_answer_first": "Prompted JSON\nanswer first",
    "outlines_json_answer_first": "Outlines\nanswer first",
}

ORDER = (
    "free",
    "prompted_json_reasoning_first",
    "outlines_json_reasoning_first",
    "xgrammar_json_reasoning_first",
    "prompted_json_answer_first",
    "outlines_json_answer_first",
)

EFFECT_LABELS = {
    "json_prompt_cost": "Prompted RF vs free",
    "outlines_constraint_effect": "Outlines RF vs prompted RF",
    "xgrammar_constraint_effect": "XGrammar RF vs prompted RF",
    "prompted_field_order_effect": "Prompted AF vs prompted RF",
    "outlines_field_order_effect": "Outlines AF vs Outlines RF",
}

EFFECT_ORDER = tuple(EFFECT_LABELS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 13,
            "svg.hashsalt": "constrained-decoding-lab",
        }
    )


def save_figure(figure: Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / f"{stem}.svg"
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Creator": "Matplotlib", "Date": None},
    )
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_lines) + "\n",
        encoding="utf-8",
    )
    figure.savefig(
        output_dir / f"{stem}.png",
        bbox_inches="tight",
        dpi=180,
        metadata={"Software": "Matplotlib"},
    )
    plt.close(figure)


def build_tradeoff(summary: dict[str, Any], output_dir: Path) -> None:
    groups = {group["condition"]: group for group in summary["groups"]}
    y = np.arange(len(ORDER))
    bar_height = 0.23
    metrics = (
        ("accuracy", "Recoverable accuracy", COLORS["recoverable"]),
        ("strict_accuracy", "Strict accuracy", COLORS["strict"]),
        ("schema_valid", "Schema compliance", COLORS["schema"]),
    )

    figure, axis = plt.subplots(figsize=(10, 5.8))
    for offset, (field, label, color) in zip((-1, 0, 1), metrics, strict=True):
        values = [groups[condition][field] for condition in ORDER]
        plotted = [np.nan if value is None else 100 * float(value) for value in values]
        bars = axis.barh(
            y + offset * bar_height,
            plotted,
            height=bar_height,
            label=label,
            color=color,
            alpha=0.9,
        )
        axis.bar_label(bars, fmt="%.1f", padding=3, fontsize=7)

    axis.set_yticks(y, [LABELS[condition] for condition in ORDER])
    axis.invert_yaxis()
    axis.set_xlim(0, 108)
    axis.set_xlabel("Rate (%)")
    axis.grid(axis="x", color=COLORS["grid"], linewidth=0.7)
    axis.set_axisbelow(True)
    figure.suptitle(
        "Qwen2.5-7B accuracy and contract compliance",
        x=0.19,
        y=0.97,
        ha="left",
    )
    axis.legend(frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, 1.08))
    figure.subplots_adjust(left=0.19, right=0.98, top=0.84, bottom=0.1)
    save_figure(figure, output_dir, "accuracy-compliance-tradeoff")


def build_effects(summary: dict[str, Any], output_dir: Path) -> None:
    comparisons = {row["comparison"]: row for row in summary["paired_comparisons"]}
    rows = [comparisons[name] for name in EFFECT_ORDER]
    estimates = np.array([100 * float(row["accuracy_delta"]) for row in rows])
    intervals = np.array(
        [[100 * float(value) for value in row["accuracy_delta_ci95"]] for row in rows]
    )
    errors = np.vstack((estimates - intervals[:, 0], intervals[:, 1] - estimates))
    y = np.arange(len(rows))

    figure, axis = plt.subplots(figsize=(9, 4.4), constrained_layout=True)
    for index, (estimate, p_value) in enumerate(
        zip(estimates, [row["mcnemar_p_exact"] for row in rows], strict=True)
    ):
        color = COLORS["negative"] if estimate < 0 else COLORS["positive"]
        axis.errorbar(
            estimate,
            index,
            xerr=errors[:, index : index + 1],
            fmt="o",
            color=color,
            capsize=4,
            linewidth=1.4,
            markersize=5,
        )
        axis.text(27, index, f"p = {p_value:.4g}", va="center", ha="right", fontsize=8)

    axis.axvline(0, color="black", linewidth=0.9)
    axis.set_yticks(y, [EFFECT_LABELS[name] for name in EFFECT_ORDER])
    axis.invert_yaxis()
    axis.set_xlim(-80, 30)
    axis.set_xlabel("Paired difference in recoverable accuracy (percentage points)")
    axis.set_title("Paired effects with bootstrap 95% confidence intervals", loc="left")
    axis.grid(axis="x", color=COLORS["grid"], linewidth=0.7)
    axis.set_axisbelow(True)
    save_figure(figure, output_dir, "paired-effects")


def build_transitions(summary: dict[str, Any], output_dir: Path) -> None:
    comparisons = {row["comparison"]: row for row in summary["paired_comparisons"]}
    panels = (
        (
            "outlines_constraint_effect",
            "Prompted RF vs Outlines RF",
            "Prompted RF",
            "Outlines RF",
        ),
        (
            "xgrammar_constraint_effect",
            "Prompted RF vs XGrammar RF",
            "Prompted RF",
            "XGrammar RF",
        ),
        (
            "xgrammar_vs_outlines",
            "Outlines RF vs XGrammar RF",
            "Outlines RF",
            "XGrammar RF",
        ),
    )
    figure, axes = plt.subplots(1, 3, figsize=(10.5, 3.7), constrained_layout=True)

    for axis, (name, title, control, treatment) in zip(axes, panels, strict=True):
        row = comparisons[name]
        matrix = np.array(
            [
                [row["both_correct"], row["control_only_correct"]],
                [row["treatment_only_correct"], row["both_wrong"]],
            ]
        )
        axis.imshow(matrix, cmap="Blues", vmin=0, vmax=49)
        for row_index in range(2):
            for column_index in range(2):
                value = int(matrix[row_index, column_index])
                color = "white" if value >= 25 else "black"
                axis.text(
                    column_index,
                    row_index,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=16,
                    color=color,
                )
        axis.set_xticks((0, 1), ("Correct", "Wrong"))
        axis.set_yticks((0, 1), ("Correct", "Wrong"))
        axis.set_xlabel(f"Treatment: {treatment}")
        axis.set_ylabel(f"Control: {control}")
        axis.set_title(title)
        delta = 100 * float(row["accuracy_delta"])
        axis.text(
            0.5,
            -0.34,
            f"Δ = {delta:+.1f} pp; exact p = {row['mcnemar_p_exact']:.4g}",
            transform=axis.transAxes,
            ha="center",
            fontsize=8,
        )
        for spine in axis.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)

    figure.suptitle("Paired correctness contingency tables", x=0.02, ha="left")
    save_figure(figure, output_dir, "paired-transitions")


def build_field_order(summary: dict[str, Any], output_dir: Path) -> None:
    groups = {group["condition"]: group for group in summary["groups"]}
    panel_specs = (
        (
            "Prompt-only JSON",
            groups["prompted_json_reasoning_first"],
            groups["prompted_json_answer_first"],
            (
                ("Recoverable", "accuracy", COLORS["recoverable"], "o", "-"),
                ("Strict", "strict_accuracy", COLORS["strict"], "s", "--"),
                ("Schema", "schema_valid", COLORS["schema"], "^", ":"),
            ),
        ),
        (
            "Outlines JSON",
            groups["outlines_json_reasoning_first"],
            groups["outlines_json_answer_first"],
            (
                (
                    "Recoverable = strict",
                    "accuracy",
                    COLORS["recoverable"],
                    "o",
                    "-",
                ),
                ("Schema", "schema_valid", COLORS["schema"], "^", ":"),
            ),
        ),
    )
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=True, constrained_layout=True)
    x = np.array((0, 1))

    for axis, (title, reasoning_first, answer_first, metrics) in zip(
        axes, panel_specs, strict=True
    ):
        for label, field, color, marker, linestyle in metrics:
            values = np.array(
                [100 * float(reasoning_first[field]), 100 * float(answer_first[field])]
            )
            axis.plot(
                x,
                values,
                label=label,
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=1.8,
                markersize=6,
            )
        axis.set_xticks(x, ("Reasoning first", "Answer first"))
        axis.set_xlim(-0.15, 1.15)
        axis.set_ylim(0, 105)
        axis.set_title(title)
        axis.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        axis.grid(axis="y", color=COLORS["grid"], linewidth=0.7)
        axis.set_axisbelow(True)
        axis.legend(frameon=False, loc="best")

    axes[0].set_ylabel("Rate")
    figure.suptitle("Sensitivity to JSON field order", x=0.02, ha="left")
    save_figure(figure, output_dir, "field-order-sensitivity")


def build_design(output_dir: Path) -> None:
    figure, axis = plt.subplots(figsize=(10.5, 2.5), constrained_layout=True)
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 3)
    axis.axis("off")

    stages = (
        (0.2, "Frozen data", "GSM8K test\nseed 0; n = 50"),
        (2.2, "Data audit", "49 retained\n1 excluded"),
        (4.2, "Matched generation", "Chat template\ngreedy; FP32"),
        (6.2, "Six conditions", "Free, prompted,\nOutlines, XGrammar"),
        (8.2, "Paired analysis", "Strict + recoverable\nCIs + McNemar"),
    )
    for index, (x_position, title, detail) in enumerate(stages):
        rectangle = plt.Rectangle(
            (x_position, 1.0),
            1.55,
            1.05,
            fill=False,
            linewidth=1.0,
            edgecolor="black",
        )
        axis.add_patch(rectangle)
        axis.text(x_position + 0.775, 1.72, title, ha="center", va="center", weight="bold")
        axis.text(x_position + 0.775, 1.33, detail, ha="center", va="center", fontsize=8)
        if index < len(stages) - 1:
            axis.annotate(
                "",
                xy=(x_position + 2.0, 1.52),
                xytext=(x_position + 1.57, 1.52),
                arrowprops={"arrowstyle": "->", "linewidth": 1.0, "color": "black"},
            )

    axis.set_title("Controlled evaluation and validation flow", loc="left")
    save_figure(figure, output_dir, "evaluation-design")


def main() -> None:
    args = parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    configure_plotting()
    build_tradeoff(summary, args.output_dir)
    build_effects(summary, args.output_dir)
    build_transitions(summary, args.output_dir)
    build_field_order(summary, args.output_dir)
    build_design(args.output_dir)
    for stem in (
        "accuracy-compliance-tradeoff",
        "paired-effects",
        "paired-transitions",
        "field-order-sensitivity",
        "evaluation-design",
    ):
        print(f"wrote assets/figures/{stem}.svg and .png")


if __name__ == "__main__":
    main()
