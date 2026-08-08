#!/usr/bin/env python3
"""Build deterministic figures for the cross-family and executable gates."""

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
            "svg.hashsalt": "replication-gate-figures-v1",
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


def load_evidence() -> dict[str, Any]:
    qwen = read_json(
        ROOT
        / "experiments/corrected-replication/results/qwen2.5-7b-corrected/decision.json"
    )
    llama = read_json(
        ROOT / "experiments/canonical-schema-equivalence-correction/paired-summary.json"
    )
    tool = read_json(ROOT / "experiments/tool-call-gate/paired-summary.json")
    tool_validation = read_json(
        ROOT / "experiments/tool-call-gate/artifact-validation.json"
    )
    if qwen.get("clean_paired_examples") != 49:
        raise ValueError("unexpected corrected Qwen sample size")
    if llama.get("control", {}).get("examples") != 150:
        raise ValueError("unexpected canonical Llama sample size")
    if tool.get("subsets", {}).get("primary", {}).get("paired_examples") != 30:
        raise ValueError("unexpected tool-call primary sample size")
    if tool.get("manual_audit_complete") is not True:
        raise ValueError("tool-call discordance audit is incomplete")
    if tool_validation.get("valid") is not True or tool_validation.get("failures"):
        raise ValueError("tool-call artifacts are not valid")
    return {"qwen": qwen, "llama": llama, "tool": tool}


def build_cross_family_figure(evidence: dict[str, Any], output_dir: Path) -> None:
    qwen = evidence["qwen"]
    llama = evidence["llama"]
    tool = evidence["tool"]["subsets"]["primary"]
    effects = [
        {
            "label": "Qwen2.5-7B\nGSM8K corrected, n=49",
            "estimate": qwen["paired_effect"]["accuracy_delta"],
            "interval": qwen["paired_effect"]["exact_bootstrap_ci95"],
            "wins": qwen["paired_effect"]["treatment_only"],
            "losses": qwen["paired_effect"]["control_only"],
            "color": COLORS["teal"],
        },
        {
            "label": "Llama 3.2 3B\nCanonical GSM8K, n=150",
            "estimate": llama["primary_contract_valid_effect"]["paired_difference"],
            "interval": llama["primary_contract_valid_effect"][
                "exact_paired_bootstrap_ci95"
            ],
            "wins": llama["primary_contract_valid_effect"]["treatment_only"],
            "losses": llama["primary_contract_valid_effect"]["control_only"],
            "color": COLORS["red"],
        },
        {
            "label": "Llama 3.2 3B\nExecutable pilot, n=30",
            "estimate": tool["primary_executable_effect"]["paired_difference"],
            "interval": tool["primary_executable_effect"][
                "exact_paired_bootstrap_ci95"
            ],
            "wins": tool["primary_executable_effect"]["treatment_only"],
            "losses": tool["primary_executable_effect"]["control_only"],
            "color": COLORS["red"],
        },
    ]
    figure, axis = plt.subplots(figsize=(11.8, 5.4))
    figure.suptitle(
        "Contract-alignment effect across confirmatory gates",
        x=0.08,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )
    y = np.arange(len(effects))[::-1]
    for row_y, item in zip(y, effects, strict=True):
        estimate = 100 * item["estimate"]
        low, high = (100 * value for value in item["interval"])
        axis.errorbar(
            estimate,
            row_y,
            xerr=[[estimate - low], [high - estimate]],
            fmt="o",
            markersize=9,
            capsize=4,
            linewidth=2,
            color=item["color"],
        )
        axis.text(
            28.5,
            row_y,
            f"{estimate:+.1f} pp   wins {item['wins']} : losses {item['losses']}",
            ha="right",
            va="center",
            color=COLORS["text"],
            fontweight="bold",
        )
    axis.axvline(0, color=COLORS["navy"], linewidth=1.2)
    axis.axvspan(-25, 0, color=COLORS["red"], alpha=0.055)
    axis.axvspan(0, 30, color=COLORS["green"], alpha=0.055)
    axis.set_yticks(y, [item["label"] for item in effects])
    axis.set_xlim(-25, 30)
    axis.set_ylim(-0.7, len(effects) - 0.3)
    axis.set_xlabel("Paired treatment effect with exact bootstrap 95% interval")
    axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    axis.set_axisbelow(True)
    axis.text(-23.5, -0.52, "Control favored", color=COLORS["red"], fontsize=8)
    axis.text(28.5, -0.52, "Integer treatment favored", color=COLORS["green"], fontsize=8, ha="right")
    figure.text(
        0.08,
        0.02,
        "The Qwen point estimate did not reproduce on unseen Llama items or the bounded executable primary sample.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.28, right=0.97, top=0.86, bottom=0.19)
    save_figure(figure, output_dir, "cross-family-evidence")


def build_tool_pilot_figure(evidence: dict[str, Any], output_dir: Path) -> None:
    primary = evidence["tool"]["subsets"]["primary"]
    control = primary["control"]
    treatment = primary["treatment"]
    effect = primary["primary_executable_effect"]
    metrics = [
        ("Internal schema", "internal_schema_valid"),
        ("External schema", "external_schema_valid"),
        ("Dispatch / execution", "execution_success"),
        ("Exact arguments", "argument_semantics_correct"),
        ("Executable contract", "executable_contract_success"),
    ]
    figure, (metric_axis, transition_axis) = plt.subplots(
        1,
        2,
        figsize=(12.2, 5.4),
        gridspec_kw={"width_ratios": [1.65, 1]},
    )
    figure.suptitle(
        "Bounded executable tool-call pilot",
        x=0.06,
        ha="left",
        color=COLORS["navy"],
        fontweight="bold",
    )

    y = np.arange(len(metrics))[::-1]
    height = 0.34
    control_rates = [100 * control[key]["rate"] for _, key in metrics]
    treatment_rates = [100 * treatment[key]["rate"] for _, key in metrics]
    metric_axis.barh(
        y + height / 2,
        control_rates,
        height,
        label="String control",
        color=COLORS["orange"],
    )
    metric_axis.barh(
        y - height / 2,
        treatment_rates,
        height,
        label="Integer treatment",
        color=COLORS["teal"],
    )
    for row_y, left, right in zip(y, control_rates, treatment_rates, strict=True):
        metric_axis.text(left - 1, row_y + height / 2, f"{left:.1f}%", ha="right", va="center", color="white", fontweight="bold", fontsize=8)
        metric_axis.text(right - 1, row_y - height / 2, f"{right:.1f}%", ha="right", va="center", color="white", fontweight="bold", fontsize=8)
    metric_axis.set_yticks(y, [label for label, _ in metrics])
    metric_axis.set_xlim(0, 105)
    metric_axis.set_xlabel("Primary sample success rate")
    metric_axis.set_title("Component outcomes", loc="left")
    metric_axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    metric_axis.set_axisbelow(True)
    metric_axis.legend(
        frameon=False,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.13),
        ncol=2,
    )

    matrix = np.array(
        [
            [effect["both_success"], effect["control_only"]],
            [effect["treatment_only"], effect["both_failure"]],
        ]
    )
    transition_axis.imshow(matrix, cmap="Blues", vmin=0, vmax=max(matrix.flat))
    for row in range(2):
        for column in range(2):
            value = int(matrix[row, column])
            transition_axis.text(
                column,
                row,
                str(value),
                ha="center",
                va="center",
                color="white" if value > max(matrix.flat) / 2 else COLORS["navy"],
                fontsize=18,
                fontweight="bold",
            )
    transition_axis.set_xticks([0, 1], ["Treatment\ncorrect", "Treatment\nincorrect"])
    transition_axis.set_yticks([0, 1], ["Control\ncorrect", "Control\nincorrect"])
    transition_axis.set_title("Paired transition matrix", loc="left")
    transition_axis.tick_params(length=0)
    transition_axis.text(
        0.5,
        -0.30,
        "1 treatment-only win, 3 control-only wins",
        ha="center",
        transform=transition_axis.transAxes,
        color=COLORS["text"],
        fontweight="bold",
    )
    transition_axis.text(
        0.5,
        -0.41,
        "Paired effect -6.7 pp, interval [-20.0, 6.7] pp",
        ha="center",
        transform=transition_axis.transAxes,
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.text(
        0.06,
        0.015,
        "All 60 primary calls were schema-valid and executable. The observed difference came from argument semantics and resulting state.",
        color=COLORS["gray"],
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.18, right=0.97, top=0.84, bottom=0.21, wspace=0.35)
    save_figure(figure, output_dir, "tool-call-pilot-result")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    configure_plotting()
    evidence = load_evidence()
    build_cross_family_figure(evidence, args.output_dir)
    build_tool_pilot_figure(evidence, args.output_dir)
    print(args.output_dir / "cross-family-evidence.svg")
    print(args.output_dir / "tool-call-pilot-result.svg")


if __name__ == "__main__":
    main()
