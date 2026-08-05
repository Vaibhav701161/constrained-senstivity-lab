#!/usr/bin/env python3
"""Generate deterministic architecture and result figures for contract alignment."""

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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = (
    ROOT
    / "experiments/representation-alignment-gate/results/cloud-full/paired-summary.json"
)
DEFAULT_OUTPUT = ROOT / "assets/figures"

COLORS = {
    "navy": "#17324D",
    "blue": "#2474B5",
    "teal": "#198F8C",
    "orange": "#D8732F",
    "red": "#B64747",
    "green": "#2F855A",
    "light_blue": "#EAF3FA",
    "light_teal": "#E8F5F3",
    "light_orange": "#FFF1E6",
    "light_gray": "#F3F5F7",
    "grid": "#D8DEE4",
    "text": "#1F2933",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 12,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.titlesize": 14,
            "svg.hashsalt": "contract-alignment-figures-v1",
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
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n",
        encoding="utf-8",
    )
    figure.savefig(
        output_dir / f"{stem}.png",
        bbox_inches="tight",
        dpi=200,
        metadata={"Software": "Matplotlib"},
    )
    plt.close(figure)


def add_box(
    axis: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    detail: str,
    facecolor: str,
) -> None:
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=facecolor,
        edgecolor=COLORS["navy"],
        linewidth=1.1,
    )
    axis.add_patch(box)
    axis.text(
        x + width / 2,
        y + height * 0.67,
        title,
        ha="center",
        va="center",
        color=COLORS["navy"],
        fontsize=9,
        fontweight="bold",
    )
    axis.text(
        x + width / 2,
        y + height * 0.31,
        detail,
        ha="center",
        va="center",
        color=COLORS["text"],
        fontsize=7.6,
        linespacing=1.3,
    )


def add_arrow(
    axis: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.25,
        color=COLORS["blue"],
        connectionstyle="arc3,rad=0",
    )
    axis.add_patch(arrow)
    axis.text(
        (start[0] + end[0]) / 2,
        start[1] + 0.195,
        label,
        ha="center",
        va="bottom",
        fontsize=7.2,
        color=COLORS["blue"],
    )


def build_pipeline(output_dir: Path) -> None:
    figure, axis = plt.subplots(figsize=(13, 4.8))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    positions = (0.02, 0.215, 0.41, 0.605, 0.80)
    width = 0.165
    height = 0.32
    y = 0.43
    boxes = (
        (
            "External contract",
            "answer: string\noptional sign + digits",
            COLORS["light_orange"],
        ),
        (
            "Safe contract compiler",
            "applicability check\ninteger-string rewrite plan",
            COLORS["light_blue"],
        ),
        (
            "Model-facing schema",
            "answer: integer\nreasoning before answer",
            COLORS["light_teal"],
        ),
        (
            "Constrained generation",
            "Qwen2.5-7B\nOutlines or XGrammar",
            COLORS["light_blue"],
        ),
        (
            "Deterministic boundary",
            "parse integer, stringify\nvalidate original schema",
            COLORS["light_teal"],
        ),
    )
    for x, (title, detail, color) in zip(positions, boxes, strict=True):
        add_box(axis, (x, y), width, height, title, detail, color)

    labels = ("analyze", "compile", "generate once", "transduce")
    for index, label in enumerate(labels):
        add_arrow(
            axis,
            (positions[index] + width + 0.005, y + height / 2),
            (positions[index + 1] - 0.005, y + height / 2),
            label,
        )

    axis.text(
        0.5,
        0.92,
        "Contract-preserving, model-aligned structured generation",
        ha="center",
        color=COLORS["navy"],
        fontsize=14,
        fontweight="bold",
    )
    axis.text(
        0.5,
        0.855,
        "The caller's schema remains authoritative; only the model-facing representation changes.",
        ha="center",
        color=COLORS["text"],
        fontsize=9,
    )

    guarantees = (
        "ONE MODEL CALL",
        "NO HEURISTIC REPAIR",
        "CANONICAL BASE-10",
        "FAIL CLOSED",
        "FINAL SCHEMA VALIDATION",
    )
    guarantee_x = np.linspace(0.08, 0.92, len(guarantees))
    for x, label in zip(guarantee_x, guarantees, strict=True):
        axis.text(
            x,
            0.18,
            label,
            ha="center",
            va="center",
            fontsize=7.4,
            color=COLORS["green"],
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#EDF7F1",
                "edgecolor": "#A9D5BA",
                "linewidth": 0.7,
            },
        )
    axis.text(
        0.5,
        0.055,
        "Implemented path for the signed numeric-string to native-integer gate",
        ha="center",
        fontsize=7.5,
        color="#5B6570",
    )
    save_figure(figure, output_dir, "contract-alignment-pipeline")


def indexed(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows}


def build_recovery(summary: dict[str, Any], output_dir: Path) -> None:
    groups = indexed(summary["groups"], "condition")
    comparisons = indexed(summary["paired_comparisons"], "name")
    backends = ("Outlines", "XGrammar")
    signed_conditions = (
        "outlines_json_reasoning_first",
        "xgrammar_json_reasoning_first",
    )
    integer_conditions = (
        "outlines_json_integer_reasoning_first",
        "xgrammar_json_integer_reasoning_first",
    )
    comparison_names = ("outlines_integer_vs_signed", "xgrammar_integer_vs_signed")

    signed = np.array(
        [100 * groups[name]["contract_valid"]["rate"] for name in signed_conditions]
    )
    integer = np.array(
        [100 * groups[name]["contract_valid"]["rate"] for name in integer_conditions]
    )
    negatives_signed = np.array(
        [groups[name]["negative_answers"] for name in signed_conditions]
    )
    negatives_integer = np.array(
        [groups[name]["negative_answers"] for name in integer_conditions]
    )
    repairs = np.array(
        [comparisons[name]["semantic"]["treatment_only"] for name in comparison_names]
    )
    breaks = np.array(
        [comparisons[name]["semantic"]["control_only"] for name in comparison_names]
    )

    figure = plt.figure(figsize=(12, 5.8))
    grid = figure.add_gridspec(1, 2, width_ratios=(1.45, 1))
    left = figure.add_subplot(grid[0, 0])
    right = figure.add_subplot(grid[0, 1])

    y = np.arange(len(backends))
    for index, backend in enumerate(backends):
        left.plot(
            [signed[index], integer[index]],
            [index, index],
            color=COLORS["grid"],
            linewidth=4,
            solid_capstyle="round",
            zorder=1,
        )
        left.scatter(
            signed[index],
            index,
            s=95,
            color=COLORS["orange"],
            edgecolor="white",
            linewidth=1,
            zorder=3,
            label="Signed string" if index == 0 else None,
        )
        left.scatter(
            integer[index],
            index,
            s=95,
            color=COLORS["teal"],
            edgecolor="white",
            linewidth=1,
            zorder=3,
            label="Native integer + transducer" if index == 0 else None,
        )
        left.text(signed[index] - 0.8, index - 0.12, f"{signed[index]:.1f}%", ha="right")
        left.text(integer[index] + 0.8, index - 0.12, f"{integer[index]:.1f}%", ha="left")
        left.text(
            (signed[index] + integer[index]) / 2,
            index + 0.13,
            f"+{integer[index] - signed[index]:.1f} pp",
            ha="center",
            color=COLORS["green"],
            fontweight="bold",
        )

    left.set_yticks(y, backends)
    left.set_ylim(1.35, -0.35)
    left.set_xlim(55, 82)
    left.set_xlabel("Contract-valid correctness on 49 audited items")
    left.set_title("Representation alignment recovered constrained accuracy", loc="left")
    left.grid(axis="x", color=COLORS["grid"], linewidth=0.7)
    left.set_axisbelow(True)
    left.legend(frameon=False, loc="lower right")

    x = np.arange(len(backends))
    width = 0.25
    right.bar(
        x - width,
        repairs,
        width,
        label="Baseline errors repaired",
        color=COLORS["green"],
    )
    right.bar(
        x,
        breaks,
        width,
        label="New errors",
        color=COLORS["red"],
    )
    right.bar(
        x + width,
        negatives_signed - negatives_integer,
        width,
        label="Negative answers removed",
        color=COLORS["blue"],
    )
    for offset, values in ((-width, repairs), (0, breaks), (width, negatives_signed)):
        for index, value in enumerate(values):
            right.text(index + offset, value + 0.25, str(int(value)), ha="center", fontsize=8)
    right.set_xticks(x, backends)
    right.set_ylim(0, 16)
    right.set_ylabel("Paired item count")
    right.set_title("Repairs, regressions, and sign failures", loc="left")
    right.grid(axis="y", color=COLORS["grid"], linewidth=0.7)
    right.set_axisbelow(True)
    right.legend(frameon=False, fontsize=7.6, loc="upper right")

    figure.suptitle(
        "Qwen2.5-7B full confirmation: signed numeric string vs native integer",
        x=0.01,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )
    figure.text(
        0.01,
        0.005,
        "Source: accepted paired-summary.json. All integer outputs were externally valid after deterministic transduction; no errors or cap hits.",
        fontsize=7.4,
        color="#5B6570",
    )
    figure.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.16, wspace=0.24)
    save_figure(figure, output_dir, "representation-alignment-recovery")


def main() -> None:
    args = parse_args()
    configure_plotting()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    build_pipeline(args.output_dir)
    build_recovery(summary, args.output_dir)
    print(f"wrote alignment figures to {args.output_dir}")


if __name__ == "__main__":
    main()
