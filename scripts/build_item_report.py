#!/usr/bin/env python3
"""Build an auditable per-item Markdown matrix from baseline JSONL files."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

CONDITION_LABELS = {
    "free": "Free",
    "prompted_json_reasoning_first": "Prompt RF",
    "outlines_json_reasoning_first": "Outlines RF",
    "prompted_json_answer_first": "Prompt AF",
    "outlines_json_answer_first": "Outlines AF",
    "xgrammar_json_reasoning_first": "XGrammar RF",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--exclude-item-id", action="append", default=[])
    return parser.parse_args()


def load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON at {path}:{line_number}: {exc}"
                    ) from exc
    return rows


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def primary_correct(row: dict[str, Any]) -> bool:
    strict = row.get("correct_exact_strict")
    return bool(row.get("correct_exact")) if strict is None else bool(strict)


def prediction_cell(row: dict[str, Any] | None) -> str:
    if row is None:
        return "missing row"
    strict_applicable = row.get("correct_exact_strict") is not None
    strict_prediction = row.get("predicted_answer_strict")
    legacy_prediction = row.get("predicted_answer")
    prediction = strict_prediction if strict_applicable else legacy_prediction
    suffix = ""
    if strict_applicable and prediction is None and legacy_prediction is not None:
        prediction = legacy_prediction
        suffix = " (non-strict)"
    if prediction is None:
        prediction = "∅"
    mark = "✓" if primary_correct(row) else "✗"
    flags: list[str] = []
    if row.get("error") is not None:
        flags.append("error")
    if row.get("hit_max_new_tokens"):
        flags.append("cap")
    flag_text = f"; {','.join(flags)}" if flags else ""
    return f"{escape(prediction)}{suffix} {mark}{flag_text}"


def markdown(rows: list[dict[str, Any]], excluded_ids: set[str]) -> str:
    models = sorted({str(row["model"]) for row in rows})
    if len(models) != 1:
        raise ValueError(f"Expected one model, found {models}")
    by_condition_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    ordered_ids: list[str] = []
    seen_ids: set[str] = set()
    for row in rows:
        condition = str(row["condition"])
        item_id = str(row["item_id"])
        if item_id in by_condition_item[condition]:
            raise ValueError(f"Duplicate row for {condition}/{item_id}")
        by_condition_item[condition][item_id] = row
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            ordered_ids.append(item_id)

    conditions = [
        condition for condition in CONDITION_LABELS if condition in by_condition_item
    ]
    lines = [
        "# Per-item baseline evidence",
        "",
        f"Model: `{models[0]}`",
        "",
        "A check mark uses the primary metric: free-response exact correctness for Free and strict whole-field numeric correctness for JSON conditions. `non-strict` means legacy extraction found a value but the full answer field failed the strict numeric rule.",
        "",
        "| Item | Audit | Gold | Question | "
        + " | ".join(CONDITION_LABELS[condition] for condition in conditions)
        + " |",
        "|---|---|---:|---|" + "---|" * len(conditions),
    ]
    for item_id in ordered_ids:
        available = next(
            rows_by_item[item_id]
            for rows_by_item in by_condition_item.values()
            if item_id in rows_by_item
        )
        audit = "excluded" if item_id in excluded_ids else "included"
        cells = [
            prediction_cell(by_condition_item[condition].get(item_id))
            for condition in conditions
        ]
        lines.append(
            f"| `{escape(item_id)}` | {audit} | {escape(available['gold_answer'])} | "
            f"{escape(available['question'])} | " + " | ".join(cells) + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    rows = load_rows(args.inputs)
    report = markdown(rows, set(args.exclude_item_id))
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(report, encoding="utf-8")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
