#!/usr/bin/env python3
"""Build deterministic README figures from accepted experiment summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "results/qwen2.5-7b/primary/combined/summary_clean.json"
DEFAULT_OUTPUT = ROOT / "assets/figures"

COLORS = {
    "ink": "#172033",
    "muted": "#5E6B82",
    "grid": "#D9DFE8",
    "panel": "#F7F9FC",
    "recoverable": "#2563EB",
    "strict": "#0F766E",
    "schema": "#D97706",
    "negative": "#B42318",
    "positive": "#2563EB",
}

LABELS = {
    "free": "Free response",
    "prompted_json_reasoning_first": "Prompted JSON: reasoning first",
    "outlines_json_reasoning_first": "Outlines: reasoning first",
    "xgrammar_json_reasoning_first": "XGrammar: reasoning first",
    "prompted_json_answer_first": "Prompted JSON: answer first",
    "outlines_json_answer_first": "Outlines: answer first",
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
    "json_prompt_cost": "Prompted RF − Free",
    "outlines_constraint_effect": "Outlines RF − Prompted RF",
    "xgrammar_constraint_effect": "XGrammar RF − Prompted RF",
    "prompted_field_order_effect": "Prompted AF − Prompted RF",
    "outlines_field_order_effect": "Outlines AF − Outlines RF",
}

EFFECT_ORDER = tuple(EFFECT_LABELS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 16,
    weight: int = 400,
    fill: str | None = None,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, ui-sans-serif, '
        f'Segoe UI, sans-serif" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill or COLORS["ink"]}" text-anchor="{anchor}">'
        f"{escape(value)}</text>"
    )


def svg_document(width: int, height: int, body: list[str], title: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
                f'aria-labelledby="title desc">'
            ),
            f'<title id="title">{escape(title)}</title>',
            (
                '<desc id="desc">Generated directly from checked-in experiment '
                "summary data.</desc>"
            ),
            f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>',
            *body,
            "</svg>",
            "",
        ]
    )


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def build_tradeoff(summary: dict[str, Any]) -> str:
    width, height = 1200, 700
    left, right, top = 340, 1140, 175
    chart_width = right - left
    row_height = 76
    body = [
        text(60, 54, "Accuracy and contract compliance", size=28, weight=700),
        text(
            60,
            84,
            "Qwen2.5-7B · audited GSM8K subset · n = 49 per condition",
            size=15,
            fill=COLORS["muted"],
        ),
    ]

    legend = (
        ("Recoverable math accuracy", COLORS["recoverable"]),
        ("Strict correct + compliant", COLORS["strict"]),
        ("Schema compliance", COLORS["schema"]),
    )
    legend_x = 60
    for label, color in legend:
        body.append(
            f'<rect x="{legend_x}" y="108" width="14" height="14" rx="2" fill="{color}"/>'
        )
        body.append(text(legend_x + 22, 120, label, size=14))
        legend_x += 245

    for tick in range(0, 101, 25):
        x = left + chart_width * tick / 100
        body.append(
            f'<line x1="{x:.1f}" y1="{top - 14}" x2="{x:.1f}" '
            f'y2="{top + row_height * len(ORDER) - 15}" '
            f'stroke="{COLORS["grid"]}" stroke-width="1"/>'
        )
        body.append(
            text(x, top - 24, str(tick), size=13, fill=COLORS["muted"], anchor="middle")
        )

    groups = {group["condition"]: group for group in summary["groups"]}
    metrics = (
        ("accuracy", COLORS["recoverable"]),
        ("strict_accuracy", COLORS["strict"]),
        ("schema_valid", COLORS["schema"]),
    )
    for row, condition in enumerate(ORDER):
        group = groups[condition]
        y = top + row * row_height
        body.append(
            text(
                left - 18, y + 29, LABELS[condition], size=15, weight=550, anchor="end"
            )
        )
        if row % 2 == 1:
            body.append(
                f'<rect x="{left}" y="{y - 4}" width="{chart_width}" height="62" '
                f'fill="{COLORS["panel"]}"/>'
            )
        for offset, (field, color) in enumerate(metrics):
            value = group[field]
            bar_y = y + offset * 18
            if value is None:
                body.append(
                    text(left + 6, bar_y + 11, "n/a", size=11, fill=COLORS["muted"])
                )
                continue
            bar_width = chart_width * float(value)
            body.append(
                f'<rect x="{left}" y="{bar_y}" width="{max(bar_width, 2):.1f}" '
                f'height="11" rx="2" fill="{color}"/>'
            )
            label_x = min(left + bar_width + 8, right - 2)
            anchor = "start"
            if bar_width > chart_width - 55:
                label_x = left + bar_width - 6
                anchor = "end"
            body.append(
                text(
                    label_x,
                    bar_y + 10,
                    percent(value),
                    size=11,
                    weight=650,
                    anchor=anchor,
                )
            )

    body.extend(
        [
            text(
                left, height - 38, "Percentage of evaluated items", size=14, weight=600
            ),
            text(
                right,
                height - 38,
                "One contradictory benchmark row excluded by the predeclared audit rule.",
                size=12,
                fill=COLORS["muted"],
                anchor="end",
            ),
        ]
    )
    return svg_document(width, height, body, "Accuracy and schema-compliance trade-off")


def build_effects(summary: dict[str, Any]) -> str:
    width, height = 1200, 590
    left, right, top = 360, 1030, 145
    domain_min, domain_max = -80.0, 30.0
    chart_width = right - left
    row_height = 72
    body = [
        text(
            60, 54, "Paired effects on recoverable math accuracy", size=28, weight=700
        ),
        text(
            60,
            84,
            "Percentage-point differences with paired-bootstrap 95% intervals",
            size=15,
            fill=COLORS["muted"],
        ),
    ]

    def scale(value: float) -> float:
        return left + (value - domain_min) / (domain_max - domain_min) * chart_width

    for tick in (-80, -60, -40, -20, 0, 20):
        x = scale(float(tick))
        body.append(
            f'<line x1="{x:.1f}" y1="{top - 28}" x2="{x:.1f}" '
            f'y2="{top + row_height * len(EFFECT_ORDER) - 18}" '
            f'stroke="{COLORS["ink"] if tick == 0 else COLORS["grid"]}" '
            f'stroke-width="{2 if tick == 0 else 1}"/>'
        )
        body.append(
            text(
                x,
                top - 38,
                f"{tick:+d}",
                size=13,
                fill=COLORS["muted"],
                anchor="middle",
            )
        )

    comparisons = {row["comparison"]: row for row in summary["paired_comparisons"]}
    for index, name in enumerate(EFFECT_ORDER):
        row = comparisons[name]
        estimate = 100 * float(row["accuracy_delta"])
        low, high = (100 * float(value) for value in row["accuracy_delta_ci95"])
        y = top + index * row_height
        color = COLORS["negative"] if estimate < 0 else COLORS["positive"]
        body.append(
            text(
                left - 22, y + 6, EFFECT_LABELS[name], size=15, weight=550, anchor="end"
            )
        )
        body.append(
            f'<line x1="{scale(low):.1f}" y1="{y:.1f}" x2="{scale(high):.1f}" '
            f'y2="{y:.1f}" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
        for bound in (low, high):
            body.append(
                f'<line x1="{scale(bound):.1f}" y1="{y - 8:.1f}" '
                f'x2="{scale(bound):.1f}" y2="{y + 8:.1f}" '
                f'stroke="{color}" stroke-width="2"/>'
            )
        body.append(
            f'<circle cx="{scale(estimate):.1f}" cy="{y:.1f}" r="7" fill="{color}"/>'
        )
        body.append(text(right + 10, y + 5, f"{estimate:+.1f} pp", size=14, weight=600))
        body.append(
            text(
                width - 15,
                y + 5,
                f"p={row['mcnemar_p_exact']:.4g}",
                size=13,
                weight=600,
                anchor="end",
            )
        )

    body.extend(
        [
            text(left, height - 40, "Favors control", size=13, fill=COLORS["muted"]),
            text(
                right,
                height - 40,
                "Favors treatment",
                size=13,
                fill=COLORS["muted"],
                anchor="end",
            ),
            text(
                1140,
                84,
                "Two-sided exact McNemar p-values",
                size=12,
                fill=COLORS["muted"],
                anchor="end",
            ),
        ]
    )
    return svg_document(
        width, height, body, "Paired effects on recoverable math accuracy"
    )


def build_design() -> str:
    width, height = 1200, 420
    body = [
        text(60, 48, "Controlled evaluation design", size=28, weight=700),
        text(
            60,
            76,
            "Matched items, prompts, precision and decoding settings across conditions",
            size=15,
            fill=COLORS["muted"],
        ),
    ]

    def box(x: int, y: int, w: int, h: int, title: str, subtitle: str) -> None:
        body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
            f'fill="#FFFFFF" stroke="{COLORS["grid"]}" stroke-width="2"/>'
        )
        body.append(text(x + 18, y + 31, title, size=16, weight=650))
        body.append(text(x + 18, y + 55, subtitle, size=12, fill=COLORS["muted"]))

    def arrow(x1: int, y1: int, x2: int, y2: int) -> None:
        body.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{COLORS["muted"]}" stroke-width="2" marker-end="url(#arrow)"/>'
        )

    body.append(
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" '
        'refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" '
        f'fill="{COLORS["muted"]}"/></marker></defs>'
    )
    box(50, 150, 190, 80, "Deterministic subset", "GSM8K test · seed 0 · n=50")
    box(285, 150, 180, 80, "Audit rule", "49 retained · 1 defect excluded")
    box(510, 150, 180, 80, "Matched prompting", "Chat template · greedy · FP32")
    box(735, 105, 190, 68, "Free response", "Final-answer extraction")
    box(735, 183, 190, 68, "Prompt-only JSON", "No token constraints")
    box(735, 261, 190, 68, "Grammar JSON", "Outlines / XGrammar")
    box(970, 150, 180, 80, "Two-axis scoring", "Recoverable + strict")
    arrow(240, 190, 285, 190)
    arrow(465, 190, 510, 190)
    arrow(690, 190, 730, 139)
    arrow(690, 190, 730, 217)
    arrow(690, 190, 730, 295)
    arrow(925, 139, 970, 175)
    arrow(925, 217, 970, 190)
    arrow(925, 295, 970, 205)
    body.append(
        f'<rect x="285" y="285" width="405" height="62" rx="8" '
        f'fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>'
    )
    body.append(text(305, 311, "Models", size=13, weight=650))
    body.append(
        text(
            305, 334, "Qwen2.5-0.5B locally · Qwen2.5-7B on two Tesla T4 GPUs", size=13
        )
    )
    body.append(text(970, 286, "Paired analysis", size=13, weight=650))
    body.append(
        text(
            970, 310, "Wilson CIs · paired bootstrap CIs", size=12, fill=COLORS["muted"]
        )
    )
    body.append(
        text(970, 331, "two-sided exact McNemar tests", size=12, fill=COLORS["muted"])
    )
    return svg_document(
        width, height, body, "Controlled constrained-decoding evaluation design"
    )


def main() -> None:
    args = parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "accuracy-compliance-tradeoff.svg": build_tradeoff(summary),
        "paired-effects.svg": build_effects(summary),
        "evaluation-design.svg": build_design(),
    }
    for name, content in figures.items():
        path = args.output_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
