#!/usr/bin/env python3
"""Build an evidence-linked report for the representation-alignment gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_index(path: Path) -> dict[str, dict[str, Any]]:
    rows = read_jsonl(path)
    indexed = {str(row["item_id"]): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"{path}: duplicate item IDs")
    return indexed


def semantic(row: dict[str, Any]) -> bool:
    return bool(row.get("semantic_correct", row.get("correct_exact")))


def external_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("external_schema_valid", row.get("schema_valid")))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("targeted", "full"), required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--targeted-manifest", type=Path, required=True)
    parser.add_argument("--baseline-prompted", type=Path, required=True)
    parser.add_argument("--baseline-outlines", type=Path, required=True)
    parser.add_argument("--baseline-xgrammar", type=Path, required=True)
    parser.add_argument("--integer-outlines", type=Path, required=True)
    parser.add_argument("--integer-xgrammar", type=Path, required=True)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    validation = json.loads(args.validation.read_text(encoding="utf-8"))
    targeted_manifest = json.loads(args.targeted_manifest.read_text(encoding="utf-8"))
    prompt = read_index(args.baseline_prompted)
    signed_outlines = read_index(args.baseline_outlines)
    signed_xgrammar = read_index(args.baseline_xgrammar)
    integer_outlines = read_index(args.integer_outlines)
    integer_xgrammar = read_index(args.integer_xgrammar)
    excluded = {"gsm8k_test_454"}
    shared_losses = sorted(
        item_id
        for item_id in set(prompt) & set(signed_outlines) & set(signed_xgrammar)
        if item_id not in excluded
        and semantic(prompt[item_id])
        and not semantic(signed_outlines[item_id])
        and not semantic(signed_xgrammar[item_id])
    )

    def repair_summary(integer: dict[str, dict[str, Any]]) -> dict[str, Any]:
        available = [item_id for item_id in shared_losses if item_id in integer]
        repaired = [item_id for item_id in available if semantic(integer[item_id])]
        invalid = [item_id for item_id, row in integer.items() if not external_valid(row)]
        return {
            "available": available,
            "repaired": repaired,
            "invalid": invalid,
            "all_rows_externally_valid": not invalid,
        }

    outlines = repair_summary(integer_outlines)
    xgrammar = repair_summary(integer_xgrammar)
    trace_rows = read_jsonl(args.trace) if args.trace and args.trace.exists() else []
    trace_by_item: dict[str, list[dict[str, Any]]] = {}
    for row in trace_rows:
        trace_by_item.setdefault(str(row["item_id"]), []).append(row)
    tracer_lines: list[str] = []
    for item_id in sorted(trace_by_item):
        selected = [str(row.get("selected_text")) for row in trace_by_item[item_id]]
        tracer_lines.append(f"- `{item_id}`: selected boundary tokens {selected}.")
    if not tracer_lines:
        tracer_lines.append("- No trace records were available.")

    targeted_pass = any(
        len(result["repaired"]) >= 5 and result["all_rows_externally_valid"]
        for result in (outlines, xgrammar)
    ) and validation.get("valid", False)
    if args.stage == "targeted":
        decision = (
            "Advance to the frozen full confirmation."
            if targeted_pass
            else "Do not launch the full confirmation. Preserve this failed mechanism test and record the next narrow hypothesis."
        )
    else:
        decision = "Use the paired full-set comparisons in the summary to apply the preregistered green, yellow, or red rule."

    group_lines = []
    for group in summary["groups"]:
        semantic_result = group["semantic"]
        contract_result = group["contract_valid"]
        group_lines.append(
            f"| {group['condition']} | {semantic_result['count']}/{group['examples']} ({semantic_result['rate'] * 100:.1f}%) | "
            f"{contract_result['count']}/{group['examples']} ({contract_result['rate'] * 100:.1f}%) | "
            f"{group['external_valid']['count']}/{group['examples']} ({group['external_valid']['rate'] * 100:.1f}%) |"
        )
    text = "\n".join(
        [
            "# Representation-Alignment Gate Report",
            "",
            "## Scope",
            "",
            f"This is the `{args.stage}` stage of the preregistered representation-alignment gate. "
            "It tests a native internal integer followed by deterministic stringification against the frozen signed-numeric-string baseline.",
            "",
            "## Artifact acceptance",
            "",
            f"- Independent artifact validation: `{validation.get('valid')}`.",
            f"- Validation warnings: {validation.get('warnings', []) or 'none'}.",
            f"- Targeted suite: {targeted_manifest.get('targeted_examples')} items, mechanically derived from frozen rows.",
            f"- Baseline shared losses: {len(shared_losses)} items: {', '.join(f'`{item}`' for item in shared_losses)}.",
            "",
            "## Result table",
            "",
            "| Condition | Semantic correctness | Contract-valid correctness | Final external validity |",
            "|---|---:|---:|---:|",
            *group_lines,
            "",
            "## Shared-loss repair check",
            "",
            f"- Outlines integer repaired {len(outlines['repaired'])}/{len(outlines['available'])} available shared losses: {outlines['repaired'] or 'none'}.",
            f"- Outlines integer external-invalid rows: {outlines['invalid'] or 'none'}.",
            f"- XGrammar integer repaired {len(xgrammar['repaired'])}/{len(xgrammar['available'])} available shared losses: {xgrammar['repaired'] or 'none'}.",
            f"- XGrammar integer external-invalid rows: {xgrammar['invalid'] or 'none'}.",
            "",
            "## Boundary traces",
            "",
            *tracer_lines,
            "",
            "## Preregistered decision",
            "",
            decision,
            "",
            "The report does not generalize beyond the declared model, prompt, schema, greedy decoding, precision, backend versions, and evaluated items.",
        ]
    ) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
