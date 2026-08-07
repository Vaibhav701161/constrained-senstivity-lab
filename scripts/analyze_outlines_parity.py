#!/usr/bin/env python3
"""Validate and summarize XGrammar versus Outlines implementation parity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPRESENTATIONS = {
    "signed-numeric-string": (
        "xgrammar_json_reasoning_first",
        "outlines_json_reasoning_first",
    ),
    "integer": (
        "xgrammar_json_integer_reasoning_first",
        "outlines_json_integer_reasoning_first",
    ),
}
COMPARISON_FIELDS = (
    "formatted_prompt",
    "raw_output",
    "predicted_answer_normalized",
    "semantic_correct",
    "contract_valid_correct",
    "internal_schema_valid",
    "external_schema_valid",
    "hit_max_new_tokens",
    "error",
)
CONFIG_PARITY_FIELDS = (
    "model",
    "revision",
    "answer_representation",
    "field_order",
    "prompt_version",
    "seed",
    "do_sample",
    "max_new_tokens",
    "dtype",
    "device_map_auto",
    "internal_schema_sha256",
    "external_schema_sha256",
    "transducer_version",
    "plan_id",
    "runner_sha256",
    "runtime_sha256",
)
ENVIRONMENT_FIELDS = (
    "python",
    "torch",
    "cuda_runtime",
    "gpus",
    "model_revision",
    "tokenizer_revision",
    "packages",
    "source_manifest_sha256",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected only objects")
    return rows


def indexed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {str(row["item_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("result rows contain duplicate item IDs")
    return result


def environment(manifest: dict[str, Any]) -> dict[str, Any]:
    return {field: manifest.get(field) for field in ENVIRONMENT_FIELDS}


def config_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    config = manifest.get("run_config", {})
    return {field: config.get(field) for field in CONFIG_PARITY_FIELDS}


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Outlines implementation-parity report",
        "",
        "This post-result subset is an implementation check, not a second statistical result.",
        "",
        f"Structural validation passed: {str(report['structurally_valid']).lower()}.",
        f"Exact output parity passed: {str(report['implementation_parity_passed']).lower()}.",
        "",
        "| Representation | Rows | Byte-identical raw outputs | Score-identical rows | Prompt-identical rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in REPRESENTATIONS:
        result = report["representations"][name]
        lines.append(
            f"| {name} | {result['rows']} | "
            f"{result['agreements']['raw_output']}/{result['rows']} | "
            f"{result['score_identical_rows']}/{result['rows']} | "
            f"{result['agreements']['formatted_prompt']}/{result['rows']} |"
        )
    lines.extend(
        [
            "",
            "Latency is omitted from parity because backend implementations have different execution overhead. The primary XGrammar estimate remains unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--xgrammar-fresh-dir", type=Path, required=True)
    parser.add_argument("--xgrammar-manifest-dir", type=Path, required=True)
    parser.add_argument("--outlines-dir", type=Path, required=True)
    parser.add_argument("--outlines-manifest-dir", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selection = read_json(args.selection)
    selected_ids = [str(item) for item in selection["selected_item_ids"]]
    source_hash = sha256(args.source_manifest)
    failures: list[str] = []
    results: dict[str, Any] = {}

    if len(selected_ids) != selection.get("selected_count"):
        failures.append("selection count differs from selected item IDs")
    if len(selected_ids) != len(set(selected_ids)):
        failures.append("selection contains duplicate item IDs")

    all_manifests: list[dict[str, Any]] = []
    for representation, (xgrammar_name, outlines_name) in REPRESENTATIONS.items():
        xgrammar_path = args.xgrammar_fresh_dir / f"{xgrammar_name}.jsonl"
        outlines_path = args.outlines_dir / f"{outlines_name}.jsonl"
        xgrammar_manifest_path = args.xgrammar_manifest_dir / f"{xgrammar_name}.json"
        outlines_manifest_path = args.outlines_manifest_dir / f"{outlines_name}.json"
        xgrammar_rows = indexed(read_jsonl(xgrammar_path))
        outlines_rows = read_jsonl(outlines_path)
        outlines_ids = [str(row["item_id"]) for row in outlines_rows]
        xgrammar_manifest = read_json(xgrammar_manifest_path)
        outlines_manifest = read_json(outlines_manifest_path)
        all_manifests.extend([xgrammar_manifest, outlines_manifest])

        if outlines_ids != selected_ids:
            failures.append(f"{representation}: Outlines IDs or ordering differ")
        if any(item not in xgrammar_rows for item in selected_ids):
            failures.append(f"{representation}: selected ID missing from XGrammar")
        xgrammar_selected = [xgrammar_rows[item] for item in selected_ids if item in xgrammar_rows]
        if len(xgrammar_selected) != len(outlines_rows):
            failures.append(f"{representation}: paired row counts differ")

        config_left = config_projection(xgrammar_manifest)
        config_right = config_projection(outlines_manifest)
        if config_left != config_right:
            failures.append(f"{representation}: model-facing run configuration differs")
        if outlines_manifest.get("run_config", {}).get("dataset_sha256") != selection.get(
            "selected_dataset_sha256"
        ):
            failures.append(f"{representation}: Outlines dataset hash differs")
        if outlines_manifest.get("source_manifest_sha256") != source_hash:
            failures.append(f"{representation}: source-manifest binding differs")

        agreements = {
            field: sum(
                left.get(field) == right.get(field)
                for left, right in zip(xgrammar_selected, outlines_rows, strict=True)
            )
            for field in COMPARISON_FIELDS
        }
        mismatches = {
            field: [
                str(right["item_id"])
                for left, right in zip(xgrammar_selected, outlines_rows, strict=True)
                if left.get(field) != right.get(field)
            ]
            for field in COMPARISON_FIELDS
        }
        score_fields = (
            "predicted_answer_normalized",
            "semantic_correct",
            "contract_valid_correct",
            "internal_schema_valid",
            "external_schema_valid",
            "hit_max_new_tokens",
            "error",
        )
        score_identical = sum(
            all(left.get(field) == right.get(field) for field in score_fields)
            for left, right in zip(xgrammar_selected, outlines_rows, strict=True)
        )
        results[representation] = {
            "rows": len(outlines_rows),
            "xgrammar_sha256": sha256(xgrammar_path),
            "outlines_sha256": sha256(outlines_path),
            "xgrammar_manifest_sha256": sha256(xgrammar_manifest_path),
            "outlines_manifest_sha256": sha256(outlines_manifest_path),
            "agreements": agreements,
            "mismatched_item_ids": mismatches,
            "score_identical_rows": score_identical,
            "xgrammar_cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in xgrammar_selected),
            "outlines_cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in outlines_rows),
        }

    reference_environment = environment(all_manifests[0])
    if any(environment(manifest) != reference_environment for manifest in all_manifests[1:]):
        failures.append("XGrammar and Outlines environment manifests differ")
    parity_passed = not failures and all(
        result["agreements"]["raw_output"] == result["rows"]
        and result["score_identical_rows"] == result["rows"]
        and result["agreements"]["formatted_prompt"] == result["rows"]
        for result in results.values()
    )
    report = {
        "report_version": "outlines-implementation-parity-v1",
        "scope": "post_result_implementation_parity_only",
        "changes_primary_estimate": False,
        "selection_sha256": sha256(args.selection),
        "source_manifest_sha256": source_hash,
        "selected_rows": len(selected_ids),
        "structurally_valid": not failures,
        "implementation_parity_passed": parity_passed,
        "representations": results,
        "failures": failures,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("Outlines parity structure is invalid")


if __name__ == "__main__":
    main()
