#!/usr/bin/env python3
"""Build deterministic technical figures for the corrected 7B replication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT_ROOT = (
    ROOT
    / "experiments/corrected-replication/results/qwen2.5-7b-corrected"
)
DEFAULT_OUTPUT = ROOT / "assets/figures"
EXCLUDED_ITEM_IDS = {"gsm8k_test_454"}

COLORS = {
    "navy": "#17324D",
    "blue": "#2474B5",
    "teal": "#198F8C",
    "orange": "#D8732F",
    "red": "#B64747",
    "green": "#2F855A",
    "gray": "#66737F",
    "light_gray": "#EFF2F5",
    "grid": "#D8DEE4",
    "text": "#1F2933",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-root", type=Path, default=DEFAULT_RESULT_ROOT)
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
            "svg.hashsalt": "corrected-replication-figures-v1",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def item_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["item_id"]): row for row in rows}


def semantic_correct(row: dict[str, Any], *, integer: bool) -> bool:
    key = "semantic_correct" if integer else "correct_exact"
    return bool(row[key])


def load_evidence(result_root: Path) -> dict[str, Any]:
    run_dir = result_root / "results/corrected-replication"
    decision = json.loads((result_root / "decision.json").read_text(encoding="utf-8"))
    summary = json.loads(
        (result_root / "paired-summary-exact.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (result_root / "artifact-validation.json").read_text(encoding="utf-8")
    )

    conditions = {
        name: read_jsonl(run_dir / f"{name}.jsonl")
        for name in (
            "outlines_json_reasoning_first",
            "xgrammar_json_reasoning_first",
            "outlines_json_integer_reasoning_first",
            "xgrammar_json_integer_reasoning_first",
        )
    }
    for name, rows in conditions.items():
        if len(rows) != 50:
            raise ValueError(f"{name} has {len(rows)} rows, expected 50")

    for representation in ("reasoning_first", "integer_reasoning_first"):
        outlines = item_map(conditions[f"outlines_json_{representation}"])
        xgrammar = item_map(conditions[f"xgrammar_json_{representation}"])
        if outlines.keys() != xgrammar.keys():
            raise ValueError(f"backend item sets differ for {representation}")
        mismatches = [
            item_id
            for item_id in outlines
            if outlines[item_id]["raw_output"] != xgrammar[item_id]["raw_output"]
        ]
        if mismatches:
            raise ValueError(f"backend outputs differ for {representation}: {mismatches}")

    if not validation["valid"] or validation["failures"] or validation["warnings"]:
        raise ValueError("artifact validation is not clean")
    if decision["clean_paired_examples"] != 49:
        raise ValueError("unexpected clean paired sample size")

    signed_rows = conditions["outlines_json_reasoning_first"]
    integer_rows = conditions["outlines_json_integer_reasoning_first"]
    signed_by_id = item_map(signed_rows)
    integer_by_id = item_map(integer_rows)
    item_ids = [
        str(row["item_id"])
        for row in sorted(signed_rows, key=lambda row: int(row["source_index"]))
        if str(row["item_id"]) not in EXCLUDED_ITEM_IDS
    ]
    pairs = [
        {
            "item_id": item_id,
            "source_index": int(signed_by_id[item_id]["source_index"]),
            "signed": semantic_correct(signed_by_id[item_id], integer=False),
            "integer": semantic_correct(integer_by_id[item_id], integer=True),
        }
        for item_id in item_ids
    ]

    observed = {
        "both_wrong": sum(not row["signed"] and not row["integer"] for row in pairs),
        "treatment_only": sum(not row["signed"] and row["integer"] for row in pairs),
        "control_only": sum(row["signed"] and not row["integer"] for row in pairs),
        "both_correct": sum(row["signed"] and row["integer"] for row in pairs),
    }
    expected = decision["paired_effect"]
    for key, value in observed.items():
        if value != expected[key]:
            raise ValueError(f"paired count mismatch for {key}: {value} != {expected[key]}")

    return {
        "decision": decision,
        "summary": summary,
        "validation": validation,
        "pairs": pairs,
    }


def build_effect_figure(evidence: dict[str, Any], output_dir: Path) -> None:
    decision = evidence["decision"]
    conditions = decision["conditions"]
    effect = decision["paired_effect"]

    signed = conditions["signed_string"]
    integer = conditions["internal_integer"]
    signed_rate = 100 * signed["accuracy"]
    integer_rate = 100 * integer["accuracy"]
    summary_groups = {
        group["condition"]: group for group in evidence["summary"]["groups"]
    }
    signed_ci = [
        100 * value
        for value in summary_groups["outlines_json_reasoning_first"]["contract_valid"][
            "ci95"
        ]
    ]
    integer_ci = [
        100 * value
        for value in summary_groups[
            "outlines_json_integer_reasoning_first"
        ]["contract_valid"]["ci95"]
    ]

    figure, (accuracy_axis, validity_axis) = plt.subplots(
        1,
        2,
        figsize=(12.5, 4.8),
        gridspec_kw={"width_ratios": [1.65, 1]},
    )
    figure.suptitle(
        "Corrected Qwen2.5-7B paired replication",
        x=0.06,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )

    labels = ["Signed numeric string", "Internal integer + transducer"]
    rates = [signed_rate, integer_rate]
    cis = [signed_ci, integer_ci]
    colors = [COLORS["orange"], COLORS["teal"]]
    y = np.array([1, 0])
    counts = [signed["correct"], integer["correct"]]
    for index, (rate, ci, color, count) in enumerate(
        zip(rates, cis, colors, counts, strict=True)
    ):
        accuracy_axis.errorbar(
            rate,
            y[index],
            xerr=[[rate - ci[0]], [ci[1] - rate]],
            fmt="o",
            markersize=9,
            capsize=4,
            color=color,
            ecolor=color,
            linewidth=2,
        )
        accuracy_axis.text(
            rate + 1.1,
            y[index],
            f"{count}/49  ({rate:.1f}%)",
            va="center",
            color=COLORS["text"],
            fontweight="bold",
        )
    accuracy_axis.set_yticks(y, labels)
    accuracy_axis.set_xlim(15, 70)
    accuracy_axis.set_ylim(-0.65, 1.65)
    accuracy_axis.set_xlabel("Contract-valid accuracy, with Wilson 95% intervals")
    accuracy_axis.set_title("Primary outcome", loc="left")
    accuracy_axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    accuracy_axis.set_axisbelow(True)
    accuracy_axis.text(
        16,
        -0.43,
        (
            f"Paired delta +{100 * effect['accuracy_delta']:.1f} pp; "
            f"exact bootstrap 95% CI "
            f"[{100 * effect['exact_bootstrap_ci95'][0]:.1f}, "
            f"{100 * effect['exact_bootstrap_ci95'][1]:.1f}] pp; "
            f"McNemar p = {effect['mcnemar_p_exact']:.3f}"
        ),
        fontsize=8.2,
        color=COLORS["gray"],
    )

    metrics = [
        ("Final external validity", 49, 49, COLORS["teal"]),
        ("Internal/schema validity", 49, 49, COLORS["blue"]),
        ("Nonblank outputs", 50, 50, COLORS["green"]),
        ("Rows checked by artifact validator", 200, 200, COLORS["navy"]),
    ]
    for index, (label, value, total, color) in enumerate(metrics[::-1]):
        validity_axis.barh(index, 100 * value / total, color=color, height=0.52)
        validity_axis.text(
            98.5,
            index,
            f"{value}/{total}",
            ha="right",
            va="center",
            color="white",
            fontweight="bold",
        )
    validity_axis.set_yticks(range(len(metrics)), [row[0] for row in metrics[::-1]])
    validity_axis.set_xlim(0, 100)
    validity_axis.set_xlabel("Observed completion rate (%)")
    validity_axis.set_title("Evidence integrity", loc="left")
    validity_axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    validity_axis.set_axisbelow(True)
    validity_axis.text(
        0,
        -0.85,
        "0 generation errors, 0 cap hits, 0 validation failures, 0 warnings",
        fontsize=8.2,
        color=COLORS["gray"],
    )

    figure.text(
        0.06,
        0.01,
        "One effective paired semantic experiment: Outlines and XGrammar outputs were byte-identical for all 50 signed and all 50 integer items.",
        fontsize=8,
        color=COLORS["gray"],
    )
    figure.subplots_adjust(top=0.8, bottom=0.2, left=0.19, right=0.98, wspace=0.5)
    save_figure(figure, output_dir, "corrected-replication-effect")


def build_transition_figure(evidence: dict[str, Any], output_dir: Path) -> None:
    effect = evidence["decision"]["paired_effect"]
    matrix = np.array(
        [
            [effect["both_wrong"], effect["treatment_only"]],
            [effect["control_only"], effect["both_correct"]],
        ]
    )

    figure, axis = plt.subplots(figsize=(7.2, 5.8))
    image = axis.imshow(matrix, cmap="Blues", vmin=0, vmax=int(matrix.max()))
    axis.set_xticks([0, 1], ["Incorrect", "Correct"])
    axis.set_yticks([0, 1], ["Incorrect", "Correct"])
    axis.set_xlabel("Internal integer + transducer")
    axis.set_ylabel("Signed numeric string")
    axis.set_title(
        "Paired correctness transitions on 49 audited items",
        loc="left",
        color=COLORS["navy"],
        fontweight="bold",
        pad=18,
    )

    cell_labels = np.array(
        [
            ["Both wrong", "Repaired"],
            ["Regressed", "Both correct"],
        ]
    )
    for row in range(2):
        for column in range(2):
            value = int(matrix[row, column])
            text_color = "white" if value >= 12 else COLORS["navy"]
            axis.text(
                column,
                row - 0.06,
                str(value),
                ha="center",
                va="center",
                fontsize=24,
                fontweight="bold",
                color=text_color,
            )
            axis.text(
                column,
                row + 0.18,
                cell_labels[row, column],
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
            )

    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.05)
    colorbar.set_label("Item count")
    figure.text(
        0.12,
        0.02,
        "Discordant pairs: 9 repairs and 3 regressions. Exact two-sided McNemar p = 0.146.",
        fontsize=8.5,
        color=COLORS["gray"],
    )
    figure.subplots_adjust(bottom=0.16, left=0.19, right=0.9, top=0.84)
    save_figure(figure, output_dir, "corrected-replication-transitions")


def build_item_map_figure(evidence: dict[str, Any], output_dir: Path) -> None:
    pairs = evidence["pairs"]
    values = np.array(
        [
            [int(row["signed"]) for row in pairs],
            [int(row["integer"]) for row in pairs],
        ]
    )
    item_labels = [row["item_id"].replace("gsm8k_test_", "") for row in pairs]
    states = [
        (
            "repaired"
            if not row["signed"] and row["integer"]
            else "regressed"
            if row["signed"] and not row["integer"]
            else "unchanged"
        )
        for row in pairs
    ]

    figure, axis = plt.subplots(figsize=(15.5, 4.7))
    cmap = ListedColormap([COLORS["light_gray"], COLORS["teal"]])
    axis.imshow(values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    axis.set_yticks([0, 1], ["Signed string", "Internal integer"])
    axis.set_xticks(np.arange(len(item_labels)), item_labels, rotation=90, fontsize=6.4)
    axis.set_xlabel("GSM8K test source index, sorted in frozen dataset order")
    figure.suptitle(
        "Item-level correctness map",
        x=0.11,
        y=0.96,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )

    axis.set_xticks(np.arange(-0.5, len(item_labels), 1), minor=True)
    axis.set_yticks(np.arange(-0.5, 2, 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=0.65)
    axis.tick_params(which="minor", bottom=False, left=False)

    for index, state in enumerate(states):
        if state == "repaired":
            axis.scatter(
                index,
                1.42,
                marker="^",
                s=24,
                color=COLORS["green"],
                clip_on=False,
            )
        elif state == "regressed":
            axis.scatter(
                index,
                1.42,
                marker="v",
                s=24,
                color=COLORS["red"],
                clip_on=False,
            )

    axis.set_ylim(1.62, -0.55)
    figure.text(
        0.11,
        0.83,
        "Cell: teal = correct, gray = incorrect    Marker: green triangle = repaired, red triangle = regressed",
        fontsize=8.3,
        color=COLORS["gray"],
    )
    figure.text(
        0.075,
        0.015,
        "All 49 preregistered clean-analysis items are shown. The contradictory reference gsm8k_test_454 is excluded by the frozen audit policy.",
        fontsize=8,
        color=COLORS["gray"],
    )
    figure.subplots_adjust(bottom=0.29, left=0.11, right=0.99, top=0.78)
    save_figure(figure, output_dir, "corrected-replication-item-map")


def main() -> None:
    args = parse_args()
    configure_plotting()
    evidence = load_evidence(args.result_root)
    build_effect_figure(evidence, args.output_dir)
    build_transition_figure(evidence, args.output_dir)
    build_item_map_figure(evidence, args.output_dir)


if __name__ == "__main__":
    main()
