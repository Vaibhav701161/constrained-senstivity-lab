#!/usr/bin/env python3
"""Validate completeness and provenance of the corrected paired replication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CONDITIONS = (
    "outlines_json_reasoning_first",
    "xgrammar_json_reasoning_first",
    "outlines_json_integer_reasoning_first",
    "xgrammar_json_integer_reasoning_first",
)
EXPECTED_COMPARISONS = (
    "outlines_integer_vs_signed",
    "xgrammar_integer_vs_signed",
)
EXPECTED_TRACE_ITEMS = (
    "gsm8k_test_173",
    "gsm8k_test_1216",
    "gsm8k_test_12",
)
EXPECTED_EXCLUSION = "gsm8k_test_454"
EXPECTED_LIMIT = 50
EXPECTED_CLEAN_LIMIT = 49


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--kernel-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.is_file():
        failures.append(f"missing JSON file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"cannot read {path}: {error}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"{path}: expected a JSON object")
        return {}
    return value


def read_jsonl(path: Path, failures: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        failures.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                failures.append(f"{path}:{line_number}: invalid JSON: {error}")
                continue
            if not isinstance(value, dict):
                failures.append(f"{path}:{line_number}: expected a JSON object")
                continue
            rows.append(value)
    return rows


def schema_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("internal_schema_valid", row.get("schema_valid")))


def external_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("external_schema_valid", row.get("schema_valid")))


def canonical_signature(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def main() -> None:
    args = parse_args()
    failures: list[str] = []
    warnings: list[str] = []

    dataset_rows = read_jsonl(args.dataset, failures)
    expected_ids = [str(row.get("id")) for row in dataset_rows]
    if len(expected_ids) != EXPECTED_LIMIT:
        failures.append(
            f"dataset must contain {EXPECTED_LIMIT} rows, found {len(expected_ids)}"
        )
    if len(set(expected_ids)) != len(expected_ids):
        failures.append("dataset contains duplicate item IDs")
    dataset_hash = sha256(args.dataset) if args.dataset.is_file() else None

    source_manifest = read_json(args.source_root / "source-manifest.json", failures)
    source_files = source_manifest.get("files", {})
    if not isinstance(source_files, dict):
        failures.append("source manifest files must be an object")
        source_files = {}
    for name, expected_hash in source_files.items():
        path = args.source_root / str(name)
        if not path.is_file():
            failures.append(f"source manifest file is absent: {path}")
        elif sha256(path) != expected_hash:
            failures.append(f"source hash mismatch: {path}")

    kernel_manifest = read_json(args.run_dir / "kernel-manifest.json", failures)
    condition_specs = kernel_manifest.get("conditions", [])
    kernel_conditions = (
        [str(item.get("name")) for item in condition_specs]
        if isinstance(condition_specs, list)
        and all(isinstance(item, dict) for item in condition_specs)
        else []
    )
    if kernel_conditions != list(EXPECTED_CONDITIONS):
        failures.append("kernel manifest conditions differ from the protocol")
    if kernel_manifest.get("full_limit") != EXPECTED_LIMIT:
        failures.append("kernel manifest full limit differs from the protocol")
    if kernel_manifest.get("canary_limit") != 5:
        failures.append("kernel manifest canary limit differs from the protocol")
    if kernel_manifest.get("excluded_item_ids") != [EXPECTED_EXCLUSION]:
        failures.append("kernel manifest exclusion differs from the protocol")
    if kernel_manifest.get("dataset_sha256") != dataset_hash:
        failures.append("kernel manifest dataset hash differs from the local dataset")
    if args.kernel_source.is_file():
        if kernel_manifest.get("kernel_source_sha256") != sha256(args.kernel_source):
            failures.append("kernel source hash differs from the downloaded manifest")
    else:
        failures.append(f"missing kernel source: {args.kernel_source}")
    source_manifest_path = args.source_root / "source-manifest.json"
    if source_manifest_path.is_file() and kernel_manifest.get(
        "source_manifest_sha256"
    ) != sha256(source_manifest_path):
        failures.append("source manifest hash differs from the kernel manifest")

    canary_gate = read_json(args.run_dir / "canary-gate.json", failures)
    full_gate = read_json(args.run_dir / "full-gate.json", failures)
    for name, gate, limit in (
        ("canary", canary_gate, 5),
        ("full", full_gate, EXPECTED_LIMIT),
    ):
        if gate.get("passed") is not True:
            failures.append(f"{name} operational gate did not pass")
        if gate.get("expected_limit") != limit:
            failures.append(f"{name} operational gate has an unexpected limit")
        if gate.get("failures") != []:
            failures.append(f"{name} operational gate contains failures")

    runner_hashes = {
        "external": sha256(args.source_root / "run_evaluation.py")
        if (args.source_root / "run_evaluation.py").is_file()
        else None,
        "integer": sha256(args.source_root / "run_representation_alignment.py")
        if (args.source_root / "run_representation_alignment.py").is_file()
        else None,
    }
    result_reports: dict[str, Any] = {}
    rows_by_condition: dict[str, list[dict[str, Any]]] = {}
    prompt_hashes: dict[str, dict[str, str]] = {}

    for condition in EXPECTED_CONDITIONS:
        path = args.run_dir / f"{condition}.jsonl"
        rows = read_jsonl(path, failures)
        rows_by_condition[condition] = rows
        item_ids = [str(row.get("item_id")) for row in rows]
        if len(rows) != EXPECTED_LIMIT:
            failures.append(f"{condition}: expected {EXPECTED_LIMIT} rows, found {len(rows)}")
        if item_ids != expected_ids:
            failures.append(f"{condition}: item IDs or order differ from the dataset")
        if len(set(item_ids)) != len(item_ids):
            failures.append(f"{condition}: duplicate item IDs")

        signatures = {str(row.get("run_signature")) for row in rows}
        run_ids = {str(row.get("run_id")) for row in rows}
        row_dataset_hashes = {row.get("dataset_sha256") for row in rows}
        errors = sum(row.get("error") is not None for row in rows)
        cap_hits = sum(bool(row.get("hit_max_new_tokens")) for row in rows)
        blanks = sum(not str(row.get("raw_output", "")).strip() for row in rows)
        internal_invalid = sum(not schema_valid(row) for row in rows)
        external_invalid = sum(not external_valid(row) for row in rows)
        if len(signatures) != 1:
            failures.append(f"{condition}: expected one run signature")
        if len(run_ids) != 1:
            failures.append(f"{condition}: expected one run ID")
        if row_dataset_hashes != {dataset_hash}:
            failures.append(f"{condition}: row dataset hashes differ")
        if errors or cap_hits or blanks or internal_invalid or external_invalid:
            failures.append(
                f"{condition}: errors={errors}, caps={cap_hits}, blanks={blanks}, "
                f"internal_invalid={internal_invalid}, external_invalid={external_invalid}"
            )

        manifest = read_json(args.run_dir / "manifests" / f"{condition}.json", failures)
        run_config = manifest.get("run_config", {})
        if not isinstance(run_config, dict):
            failures.append(f"{condition}: run configuration is not an object")
            run_config = {}
        expected_signature = canonical_signature(run_config)
        if signatures and signatures != {expected_signature}:
            failures.append(f"{condition}: run signature does not match its manifest")
        runner_kind = "integer" if "_integer_" in condition else "external"
        recorded_runner_hash = (
            run_config.get("runner_sha256")
            if runner_kind == "integer"
            else manifest.get("runner_sha256")
        )
        if recorded_runner_hash != runner_hashes[runner_kind]:
            failures.append(f"{condition}: runner hash differs from frozen source")
        if run_config.get("dataset_sha256") != dataset_hash:
            failures.append(f"{condition}: manifest dataset hash differs")

        prompt_hashes[condition] = {
            str(row.get("item_id")): hashlib.sha256(
                str(row.get("formatted_prompt", "")).encode("utf-8")
            ).hexdigest()
            for row in rows
        }
        result_reports[condition] = {
            "path": str(path),
            "sha256": sha256(path) if path.is_file() else None,
            "rows": len(rows),
            "unique_item_ids": len(set(item_ids)),
            "run_signature": next(iter(signatures), None),
            "run_id": next(iter(run_ids), None),
            "errors": errors,
            "cap_hits": cap_hits,
            "blank_outputs": blanks,
            "internal_invalid": internal_invalid,
            "external_invalid": external_invalid,
        }

    equivalent_pairs = (
        ("outlines_json_reasoning_first", "xgrammar_json_reasoning_first"),
        (
            "outlines_json_integer_reasoning_first",
            "xgrammar_json_integer_reasoning_first",
        ),
    )
    for left, right in equivalent_pairs:
        if prompt_hashes.get(left) != prompt_hashes.get(right):
            failures.append(f"effective prompts differ between {left} and {right}")

    trace_path = args.run_dir / "traces" / "xgrammar-integer-answer-boundary.jsonl"
    traces = read_jsonl(trace_path, failures)
    traced_ids = {str(row.get("item_id")) for row in traces}
    if not set(EXPECTED_TRACE_ITEMS).issubset(traced_ids):
        failures.append(
            f"trace coverage missing expected items: {sorted(set(EXPECTED_TRACE_ITEMS) - traced_ids)}"
        )
    if any(row.get("condition") != "xgrammar_json_integer_reasoning_first" for row in traces):
        failures.append("trace file contains an unexpected condition")

    paired_summary = read_json(args.run_dir / "paired-summary.json", failures)
    if paired_summary.get("excluded_item_ids") != [EXPECTED_EXCLUSION]:
        failures.append("paired summary exclusion differs from the protocol")
    if paired_summary.get("total_rows") != EXPECTED_CLEAN_LIMIT * len(EXPECTED_CONDITIONS):
        failures.append("paired summary has an unexpected cleaned row count")
    comparisons = paired_summary.get("paired_comparisons", [])
    comparison_names = (
        [str(item.get("name")) for item in comparisons]
        if isinstance(comparisons, list)
        and all(isinstance(item, dict) for item in comparisons)
        else []
    )
    if comparison_names != list(EXPECTED_COMPARISONS):
        failures.append("paired summary comparisons differ from the protocol")
    for comparison in comparisons if isinstance(comparisons, list) else []:
        if comparison.get("paired_examples") != EXPECTED_CLEAN_LIMIT:
            failures.append(
                f"{comparison.get('name')}: unexpected paired example count"
            )

    report = {
        "validation_version": "corrected-replication-artifact-validation-v1",
        "valid": not failures,
        "run_dir": str(args.run_dir),
        "dataset_sha256": dataset_hash,
        "expected_conditions": list(EXPECTED_CONDITIONS),
        "expected_rows": EXPECTED_LIMIT * len(EXPECTED_CONDITIONS),
        "failures": failures,
        "warnings": warnings,
        "conditions": result_reports,
        "trace": {
            "path": str(trace_path),
            "sha256": sha256(trace_path) if trace_path.is_file() else None,
            "records": len(traces),
            "traced_item_ids": sorted(traced_ids),
        },
        "paired_summary_sha256": (
            sha256(args.run_dir / "paired-summary.json")
            if (args.run_dir / "paired-summary.json").is_file()
            else None
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
