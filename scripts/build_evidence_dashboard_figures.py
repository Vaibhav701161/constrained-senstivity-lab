#!/usr/bin/env python3
"""Build deterministic overview figures from frozen experiment artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets/figures"

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


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.titlesize": 14,
            "svg.hashsalt": "csl-evidence-dashboard-v1",
        }
    )


def save_figure(figure: Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / f"{stem}.svg"
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        facecolor="white",
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
        facecolor="white",
        metadata={"Software": "Matplotlib"},
    )
    plt.close(figure)


def load_evidence() -> dict[str, Any]:
    baseline = read_json(
        ROOT / "results/qwen2.5-7b/primary/combined/summary_clean.json"
    )
    qwen = read_json(
        ROOT
        / "experiments/corrected-replication/results/qwen2.5-7b-corrected/decision.json"
    )
    canonical = read_json(
        ROOT / "experiments/canonical-schema-equivalence-correction/paired-summary.json"
    )
    tool = read_json(ROOT / "experiments/tool-call-gate/paired-summary.json")
    replay = read_json(ROOT / "experiments/replay-validation.json")

    canonical_control = read_jsonl(
        ROOT
        / "experiments/canonical-schema-equivalence-correction/results/"
        "xgrammar_json_canonical_integer_string_reasoning_first.jsonl"
    )
    canonical_treatment = read_jsonl(
        ROOT
        / "experiments/second-family-replication/results/fresh/"
        "xgrammar_json_integer_reasoning_first.jsonl"
    )
    broad_control = read_jsonl(
        ROOT
        / "experiments/second-family-replication/results/fresh/"
        "xgrammar_json_reasoning_first.jsonl"
    )

    if qwen.get("clean_paired_examples") != 49:
        raise ValueError("unexpected corrected Qwen sample size")
    if canonical.get("control", {}).get("examples") != 150:
        raise ValueError("unexpected canonical-correction sample size")
    if tool.get("subsets", {}).get("primary", {}).get("paired_examples") != 30:
        raise ValueError("unexpected tool-call sample size")
    if replay.get("valid") is not True or replay.get("replayed_rows") != 464:
        raise ValueError("accepted artifact replay is not clean")
    if len(canonical_control) != 150 or len(canonical_treatment) != 150:
        raise ValueError("canonical item map requires 150 rows per condition")
    if [row["item_id"] for row in canonical_control] != [
        row["item_id"] for row in canonical_treatment
    ]:
        raise ValueError("canonical control and treatment item order differs")
    if [row["item_id"] for row in broad_control] != [
        row["item_id"] for row in canonical_control
    ]:
        raise ValueError("broad and canonical control item order differs")

    return {
        "baseline": baseline,
        "qwen": qwen,
        "canonical": canonical,
        "tool": tool,
        "canonical_control": canonical_control,
        "canonical_treatment": canonical_treatment,
        "broad_control": broad_control,
    }


def build_validity_semantics_figure(
    evidence: dict[str, Any], output_dir: Path
) -> None:
    baseline_groups = {
        group["condition"]: group for group in evidence["baseline"]["groups"]
    }
    baseline_points = [
        ("Prompted, reasoning first", "prompted_json_reasoning_first", COLORS["blue"], "o"),
        ("Outlines, reasoning first", "outlines_json_reasoning_first", COLORS["teal"], "o"),
        ("XGrammar, reasoning first", "xgrammar_json_reasoning_first", COLORS["green"], "s"),
        ("Prompted, answer first", "prompted_json_answer_first", COLORS["orange"], "o"),
        ("Outlines, answer first", "outlines_json_answer_first", COLORS["red"], "o"),
    ]

    figure, (baseline_axis, transform_axis) = plt.subplots(
        1,
        2,
        figsize=(13.4, 5.8),
        gridspec_kw={"width_ratios": [1.05, 1]},
    )
    figure.suptitle(
        "Structural validity and task correctness are separate outcomes",
        x=0.06,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )

    for label, condition, color, marker in baseline_points:
        group = baseline_groups[condition]
        x = 100 * float(group["schema_valid"])
        y = 100 * float(group["accuracy"])
        baseline_axis.scatter(
            x,
            y,
            s=78,
            color=color,
            marker=marker,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
            label=label,
        )

    for control, treatment in [
        ("prompted_json_reasoning_first", "outlines_json_reasoning_first"),
        ("prompted_json_answer_first", "outlines_json_answer_first"),
    ]:
        left = baseline_groups[control]
        right = baseline_groups[treatment]
        baseline_axis.annotate(
            "",
            xy=(100 * right["schema_valid"], 100 * right["accuracy"]),
            xytext=(100 * left["schema_valid"], 100 * left["accuracy"]),
            arrowprops={
                "arrowstyle": "->",
                "color": COLORS["gray"],
                "linewidth": 1.25,
            },
            zorder=2,
        )

    baseline_axis.set_title("A. Matched Qwen baseline conditions", loc="left")
    baseline_axis.set_xlabel("Whole-response schema validity (%)")
    baseline_axis.set_ylabel("Recoverable mathematical accuracy (%)")
    baseline_axis.set_xlim(-4, 105)
    baseline_axis.set_ylim(0, 90)
    baseline_axis.grid(color=COLORS["grid"], linewidth=0.8)
    baseline_axis.set_axisbelow(True)
    baseline_axis.legend(
        frameon=False,
        fontsize=7.6,
        loc="lower left",
        ncol=1,
    )

    qwen = evidence["qwen"]
    canonical = evidence["canonical"]
    tool = evidence["tool"]["subsets"]["primary"]
    pairs = [
        {
            "label": "Qwen GSM8K, n=49",
            "control": (
                100 * qwen["conditions"]["signed_string"]["external_valid"] / 49,
                100 * qwen["conditions"]["signed_string"]["accuracy"],
            ),
            "treatment": (
                100 * qwen["conditions"]["internal_integer"]["external_valid"] / 49,
                100 * qwen["conditions"]["internal_integer"]["accuracy"],
            ),
        },
        {
            "label": "Llama GSM8K, n=150",
            "control": (
                100 * canonical["control"]["final_external_validity"]["rate"],
                100 * canonical["control"]["contract_valid_correctness"]["rate"],
            ),
            "treatment": (
                100 * canonical["treatment"]["final_external_validity"]["rate"],
                100 * canonical["treatment"]["contract_valid_correctness"]["rate"],
            ),
        },
        {
            "label": "Llama tools, n=30",
            "control": (
                100 * tool["control"]["external_schema_valid"]["rate"],
                100 * tool["control"]["executable_contract_success"]["rate"],
            ),
            "treatment": (
                100 * tool["treatment"]["external_schema_valid"]["rate"],
                100 * tool["treatment"]["executable_contract_success"]["rate"],
            ),
        },
    ]
    y_offsets = [-1.2, 0.0, 1.2]
    for pair, offset in zip(pairs, y_offsets, strict=True):
        control_x, control_y = pair["control"]
        treatment_x, treatment_y = pair["treatment"]
        transform_axis.plot(
            [control_x, treatment_x],
            [control_y + offset, treatment_y + offset],
            color=COLORS["gray"],
            linewidth=1.3,
            zorder=1,
        )
        transform_axis.scatter(
            control_x,
            control_y + offset,
            s=78,
            color=COLORS["orange"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        transform_axis.scatter(
            treatment_x,
            treatment_y + offset,
            s=78,
            color=COLORS["teal"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        transform_axis.text(
            98.7,
            max(control_y, treatment_y) + offset + 3.0,
            pair["label"],
            ha="right",
            color=COLORS["text"],
            fontweight="bold",
            fontsize=8,
        )

    transform_axis.scatter([], [], color=COLORS["orange"], label="String control")
    transform_axis.scatter([], [], color=COLORS["teal"], label="Integer treatment")
    transform_axis.set_title("B. Contract-preserving representation pairs", loc="left")
    transform_axis.set_xlabel("Final external-schema validity (%)")
    transform_axis.set_ylabel("Contract-valid or executable correctness (%)")
    transform_axis.set_xlim(94, 100.5)
    transform_axis.set_ylim(25, 96)
    transform_axis.grid(color=COLORS["grid"], linewidth=0.8)
    transform_axis.set_axisbelow(True)
    transform_axis.legend(frameon=False, loc="lower left", ncol=2, fontsize=8)

    figure.text(
        0.06,
        0.015,
        "Arrows connect matched conditions. Task metrics are shown within each study and are not pooled across domains.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.16, wspace=0.25)
    save_figure(figure, output_dir, "validity-semantics-separation")


def build_paired_composition_figure(
    evidence: dict[str, Any], output_dir: Path
) -> None:
    qwen = evidence["qwen"]["paired_effect"]
    canonical = evidence["canonical"]["primary_contract_valid_effect"]
    tool = evidence["tool"]["subsets"]["primary"]["primary_executable_effect"]
    rows = [
        {
            "label": "Corrected Qwen\nGSM8K, n=49",
            "n": 49,
            "both": qwen["both_correct"],
            "win": qwen["treatment_only"],
            "loss": qwen["control_only"],
            "neither": qwen["both_wrong"],
        },
        {
            "label": "Canonical Llama\nGSM8K, n=150",
            "n": 150,
            "both": canonical["both_success"],
            "win": canonical["treatment_only"],
            "loss": canonical["control_only"],
            "neither": canonical["both_failure"],
        },
        {
            "label": "Llama executable\ntools, n=30",
            "n": 30,
            "both": tool["both_success"],
            "win": tool["treatment_only"],
            "loss": tool["control_only"],
            "neither": tool["both_failure"],
        },
    ]
    categories = [
        ("both", "Both correct", COLORS["blue"]),
        ("win", "Treatment only", COLORS["green"]),
        ("loss", "Control only", COLORS["red"]),
        ("neither", "Both incorrect", "#A5AFB8"),
    ]

    figure, axis = plt.subplots(figsize=(12.4, 5.5))
    figure.suptitle(
        "Paired outcome composition across decision gates",
        x=0.07,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )
    y = np.arange(len(rows))[::-1]
    left = np.zeros(len(rows))
    for key, label, color in categories:
        values = np.array([100 * row[key] / row["n"] for row in rows])
        bars = axis.barh(y, values, left=left, height=0.56, color=color, label=label)
        for bar, value, row in zip(bars, values, rows, strict=True):
            count = row[key]
            if value >= 7:
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    str(count),
                    ha="center",
                    va="center",
                    color="white" if key != "neither" else COLORS["navy"],
                    fontweight="bold",
                    fontsize=8.5,
                )
        left += values

    for row_y, row in zip(y, rows, strict=True):
        net = 100 * (row["win"] - row["loss"]) / row["n"]
        axis.text(
            102.0,
            row_y,
            f"wins {row['win']} : losses {row['loss']}   net {net:+.1f} pp",
            va="center",
            color=COLORS["text"],
            fontweight="bold",
            fontsize=8.5,
        )

    axis.set_yticks(y, [row["label"] for row in rows])
    axis.set_xlim(0, 139)
    axis.set_xlabel("Share of paired examples (%)")
    axis.set_title(
        "Each example is assigned to exactly one paired correctness state",
        loc="left",
        color=COLORS["gray"],
        fontsize=9,
    )
    axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    axis.set_axisbelow(True)
    axis.legend(
        frameon=False,
        ncol=4,
        loc="upper left",
        bbox_to_anchor=(0, 1.13),
        fontsize=8,
    )
    figure.text(
        0.07,
        0.02,
        "Counts are read directly from frozen paired summaries. Positive Qwen transitions did not persist in the two Llama gates.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.20, right=0.98, top=0.82, bottom=0.17)
    save_figure(figure, output_dir, "paired-outcome-composition")


def build_llama_item_map(evidence: dict[str, Any], output_dir: Path) -> None:
    control_rows = evidence["canonical_control"]
    treatment_rows = evidence["canonical_treatment"]
    status_codes: list[int] = []
    discordant_labels: list[tuple[int, str, int]] = []
    for index, (control, treatment) in enumerate(
        zip(control_rows, treatment_rows, strict=True)
    ):
        control_correct = bool(control["contract_valid_correct"])
        treatment_correct = bool(treatment["contract_valid_correct"])
        if control_correct and treatment_correct:
            code = 0
        elif not control_correct and treatment_correct:
            code = 1
            discordant_labels.append((index, str(control["source_index"]), code))
        elif control_correct and not treatment_correct:
            code = 2
            discordant_labels.append((index, str(control["source_index"]), code))
        else:
            code = 3
        status_codes.append(code)

    grid = np.array(status_codes).reshape(10, 15)
    cmap = ListedColormap(
        [COLORS["blue"], COLORS["green"], COLORS["red"], "#C6CDD4"]
    )
    figure, axis = plt.subplots(figsize=(13.5, 6.5))
    figure.suptitle(
        "Item-level paired transitions on the canonical Llama holdout",
        x=0.07,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )
    axis.imshow(grid, cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    axis.set_xticks(np.arange(15), [str(value) for value in range(1, 16)])
    axis.set_yticks(np.arange(10), [str(value) for value in range(1, 11)])
    axis.set_xlabel("Position within 15-item block")
    axis.set_ylabel("Block in frozen dataset order")
    axis.set_title(
        "All 150 items shown once; discordant cells display the original GSM8K source index",
        loc="left",
        fontsize=9,
        color=COLORS["gray"],
    )
    axis.set_xticks(np.arange(-0.5, 15, 1), minor=True)
    axis.set_yticks(np.arange(-0.5, 10, 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=1.2)
    axis.tick_params(which="minor", bottom=False, left=False)
    axis.tick_params(length=0)
    for flat_index, source_index, code in discordant_labels:
        row, column = divmod(flat_index, 15)
        axis.text(
            column,
            row,
            source_index,
            ha="center",
            va="center",
            color="white",
            fontsize=6.8,
            fontweight="bold",
        )

    labels = [
        (COLORS["blue"], "Both correct: 76"),
        (COLORS["green"], "Treatment only: 6"),
        (COLORS["red"], "Control only: 16"),
        ("#C6CDD4", "Both incorrect: 52"),
    ]
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="s",
            linestyle="",
            markerfacecolor=color,
            markeredgecolor="none",
            markersize=9,
            label=label,
        )
        for color, label in labels
    ]
    axis.legend(
        handles=handles,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0, 1.12),
        ncol=4,
        fontsize=8,
    )
    figure.text(
        0.07,
        0.02,
        "The 22 labeled discordances were all manually attributed. No post-launch item was excluded.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.14)
    save_figure(figure, output_dir, "llama-paired-item-map")


def build_canonical_correction_delta(
    evidence: dict[str, Any], output_dir: Path
) -> None:
    broad_rows = evidence["broad_control"]
    canonical_rows = evidence["canonical_control"]
    canonical_pattern = re.compile(r"^-?(?:0|[1-9][0-9]*)$")

    raw_identical = sum(
        left["raw_output"] == right["raw_output"]
        for left, right in zip(broad_rows, canonical_rows, strict=True)
    )
    answer_identical = sum(
        left.get("predicted_answer_normalized")
        == right.get("predicted_answer_normalized")
        for left, right in zip(broad_rows, canonical_rows, strict=True)
    )
    correctness_identical = sum(
        bool(left["contract_valid_correct"]) == bool(right["contract_valid_correct"])
        for left, right in zip(broad_rows, canonical_rows, strict=True)
    )
    broad_noncanonical = sum(
        not bool(
            canonical_pattern.fullmatch(
                str((row.get("external_value") or {}).get("answer", ""))
            )
        )
        for row in broad_rows
    )
    canonical_noncanonical = sum(
        not bool(
            canonical_pattern.fullmatch(
                str((row.get("external_value") or {}).get("answer", ""))
            )
        )
        for row in canonical_rows
    )
    broad_correct = sum(bool(row["contract_valid_correct"]) for row in broad_rows)
    canonical_correct = sum(
        bool(row["contract_valid_correct"]) for row in canonical_rows
    )
    repair = sum(
        not bool(left["contract_valid_correct"])
        and bool(right["contract_valid_correct"])
        for left, right in zip(broad_rows, canonical_rows, strict=True)
    )
    regression = sum(
        bool(left["contract_valid_correct"])
        and not bool(right["contract_valid_correct"])
        for left, right in zip(broad_rows, canonical_rows, strict=True)
    )
    observed = {
        "raw_identical": raw_identical,
        "answer_identical": answer_identical,
        "correctness_identical": correctness_identical,
        "broad_noncanonical": broad_noncanonical,
        "canonical_noncanonical": canonical_noncanonical,
        "broad_correct": broad_correct,
        "canonical_correct": canonical_correct,
        "repair": repair,
        "regression": regression,
    }
    expected = {
        "raw_identical": 134,
        "answer_identical": 140,
        "correctness_identical": 148,
        "broad_noncanonical": 6,
        "canonical_noncanonical": 0,
        "broad_correct": 92,
        "canonical_correct": 92,
        "repair": 1,
        "regression": 1,
    }
    if observed != expected:
        raise ValueError(f"unexpected canonical correction deltas: {observed}")

    figure, (stability_axis, outcome_axis) = plt.subplots(
        1,
        2,
        figsize=(12.8, 5.3),
        gridspec_kw={"width_ratios": [1.45, 1]},
    )
    figure.suptitle(
        "What exact canonical-string enforcement changed",
        x=0.07,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )

    labels = ["Raw output", "Normalized answer", "Correct / incorrect state"]
    identical = np.array([raw_identical, answer_identical, correctness_identical])
    changed = 150 - identical
    y = np.arange(3)[::-1]
    stability_axis.barh(
        y,
        identical,
        color=COLORS["blue"],
        height=0.56,
        label="Unchanged",
    )
    stability_axis.barh(
        y,
        changed,
        left=identical,
        color=COLORS["orange"],
        height=0.56,
        label="Changed",
    )
    for row_y, same, different in zip(y, identical, changed, strict=True):
        stability_axis.text(
            same / 2,
            row_y,
            str(int(same)),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )
        stability_axis.text(
            same + different / 2,
            row_y,
            str(int(different)),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )
    stability_axis.set_yticks(y, labels)
    stability_axis.set_xlim(0, 150)
    stability_axis.set_xlabel("Items in the frozen holdout")
    stability_axis.set_title("A. Broad control vs canonical control", loc="left")
    stability_axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    stability_axis.set_axisbelow(True)
    stability_axis.legend(frameon=False, ncol=2, loc="lower left")

    x = np.array([0, 1])
    width = 0.32
    outcome_axis.bar(
        x - width / 2,
        [broad_noncanonical, canonical_noncanonical],
        width,
        color=COLORS["red"],
        label="Noncanonical values",
    )
    outcome_axis.bar(
        x + width / 2,
        [broad_correct, canonical_correct],
        width,
        color=COLORS["teal"],
        label="Correct answers",
    )
    for index, values in enumerate(
        ([broad_noncanonical, canonical_noncanonical], [broad_correct, canonical_correct])
    ):
        offset = -width / 2 if index == 0 else width / 2
        for position, value in zip(x, values, strict=True):
            outcome_axis.text(
                position + offset,
                value + 2.2,
                str(value),
                ha="center",
                va="bottom",
                color=COLORS["text"],
                fontweight="bold",
            )
    outcome_axis.set_xticks(x, ["Broad string\ncontrol", "Canonical string\ncontrol"])
    outcome_axis.set_ylim(0, 116)
    outcome_axis.set_ylabel("Items")
    outcome_axis.set_title("B. Constraint and task outcome", loc="left")
    outcome_axis.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    outcome_axis.set_axisbelow(True)
    outcome_axis.legend(
        frameon=False,
        fontsize=8,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=2,
    )
    outcome_axis.text(
        0.5,
        0.15,
        "1 repair and 1 regression\nNet accuracy change: 0 items",
        transform=outcome_axis.transAxes,
        ha="center",
        va="center",
        color=COLORS["text"],
        fontweight="bold",
        bbox={"facecolor": "white", "edgecolor": COLORS["grid"], "pad": 5},
    )

    figure.text(
        0.07,
        0.018,
        "The correction removed all six noncanonical control values. It did not change aggregate control accuracy: 92/150 in both runs.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.16, right=0.98, top=0.84, bottom=0.18, wspace=0.28)
    save_figure(figure, output_dir, "canonical-correction-delta")


def build_system_architecture_figure(output_dir: Path) -> None:
    figure, axis = plt.subplots(figsize=(15.2, 5.8))
    axis.set_xlim(0, 15.2)
    axis.set_ylim(0, 5.8)
    axis.axis("off")
    figure.suptitle(
        "Contract-sensitivity evaluation pipeline",
        x=0.055,
        y=0.97,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
        fontsize=15,
    )
    axis.text(
        0.1,
        5.18,
        "The caller contract remains authoritative. Representation changes are paired, reversible, and evaluated rather than assumed beneficial.",
        color=COLORS["gray"],
        fontsize=9.5,
    )

    stages = [
        {
            "x": 0.1,
            "title": "Inputs",
            "body": "External JSON Schema\nFrozen dataset\nSemantic or execution oracle",
            "foot": "HASHED",
            "color": "#EAF2FF",
        },
        {
            "x": 2.55,
            "title": "Analyze",
            "body": "ContractIR\nEligibility proof\nTyped refusal",
            "foot": "FAIL CLOSED",
            "color": "#EDF6F7",
        },
        {
            "x": 5.0,
            "title": "Plan paired arms",
            "body": "Control schema\nTreatment schema\nInverse transducer",
            "foot": "ONE VARIABLE",
            "color": "#EAF2FF",
        },
        {
            "x": 7.45,
            "title": "Generate",
            "body": "Shared model and tokenizer\nOne chat template\nMatched decoding and backend",
            "foot": "RUNTIME PARITY",
            "color": "#EDF6F7",
        },
        {
            "x": 9.9,
            "title": "Reconstruct",
            "body": "Parse internal object\nDeterministic inverse\nOriginal-schema validation",
            "foot": "ZERO REPAIRS",
            "color": "#EAF2FF",
        },
        {
            "x": 12.35,
            "title": "Evaluate",
            "body": "Structural + semantic scores\nExecution outcome\nPaired CI and case audit",
            "foot": "DECISION GATE",
            "color": "#EDF6F7",
        },
    ]
    box_y = 1.55
    width = 2.15
    height = 2.75
    for index, stage in enumerate(stages):
        box = FancyBboxPatch(
            (stage["x"], box_y),
            width,
            height,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            linewidth=1.3,
            edgecolor=COLORS["navy"],
            facecolor=stage["color"],
        )
        axis.add_patch(box)
        axis.text(
            stage["x"] + 0.18,
            box_y + 2.22,
            stage["title"],
            color=COLORS["navy"],
            fontsize=10.5,
            fontweight="bold",
        )
        axis.text(
            stage["x"] + width / 2,
            box_y + 1.25,
            stage["body"],
            ha="center",
            va="center",
            color=COLORS["text"],
            fontsize=8.5,
            linespacing=1.55,
        )
        axis.text(
            stage["x"] + width / 2,
            0.95,
            stage["foot"],
            ha="center",
            va="center",
            color=COLORS["green"],
            fontsize=7.5,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "#EFFAF5",
                "edgecolor": "#A8D8C2",
            },
        )
        if index < len(stages) - 1:
            next_x = stages[index + 1]["x"]
            arrow = FancyArrowPatch(
                (stage["x"] + width + 0.03, box_y + height / 2),
                (next_x - 0.03, box_y + height / 2),
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=1.25,
                color=COLORS["blue"],
            )
            axis.add_patch(arrow)

    axis.text(
        7.6,
        0.18,
        "Failures, invalid objects, and cap hits remain in the denominator. Unsupported transforms stop before generation.",
        ha="center",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.02, right=0.99, top=0.90, bottom=0.05)
    save_figure(figure, output_dir, "research-system-architecture")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    configure_plotting()
    evidence = load_evidence()
    build_validity_semantics_figure(evidence, args.output_dir)
    build_paired_composition_figure(evidence, args.output_dir)
    build_llama_item_map(evidence, args.output_dir)
    build_canonical_correction_delta(evidence, args.output_dir)
    build_system_architecture_figure(args.output_dir)


if __name__ == "__main__":
    main()
