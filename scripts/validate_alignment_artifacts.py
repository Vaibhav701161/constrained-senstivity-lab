#!/usr/bin/env python3
"""Validate completeness and provenance of a representation-alignment run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: invalid JSON: {error}") from error
            if not isinstance(row, dict):
                raise TypeError(f"{path}:{number}: expected JSON object")
            rows.append(row)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--conditions", nargs="+", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--summarizer", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--trace-item-id", action="append", default=[])
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures: list[str] = []
    warnings: list[str] = []
    dataset_rows = read_jsonl(args.dataset)
    expected_ids = [str(row["id"]) for row in dataset_rows[: args.limit]]
    dataset_hash = sha256(args.dataset)
    kernel_manifest_path = args.run_dir / "kernel-manifest.json"
    if not kernel_manifest_path.exists():
        failures.append(f"missing kernel manifest: {kernel_manifest_path}")
        kernel_manifest: dict[str, Any] = {}
    else:
        kernel_manifest = json.loads(kernel_manifest_path.read_text(encoding="utf-8"))
    if kernel_manifest.get("conditions") != list(args.conditions):
        failures.append("kernel manifest conditions do not match expected conditions")
    if kernel_manifest.get("limit") != args.limit:
        failures.append("kernel manifest limit does not match expected limit")
    if kernel_manifest.get("dataset_sha256") != dataset_hash:
        failures.append("kernel manifest dataset hash does not match local dataset")
    if kernel_manifest.get("runner_sha256") != sha256(args.runner):
        failures.append("kernel manifest runner hash does not match immutable source")
    if kernel_manifest.get("summarizer_sha256") != sha256(args.summarizer):
        failures.append("kernel manifest summarizer hash does not match immutable source")
    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    expected_source_hashes = source_manifest.get("files", {})
    for path, name in ((args.runner, "run_representation_alignment.py"), (args.summarizer, "summarize_alignment_gate.py"), (args.dataset, args.dataset.name)):
        expected = expected_source_hashes.get(name)
        if expected is not None and expected != sha256(path):
            failures.append(f"source manifest hash mismatch for {name}")

    reports: dict[str, Any] = {}
    reference_ids: list[str] | None = None
    for condition in args.conditions:
        path = args.run_dir / f"{condition}.jsonl"
        if not path.exists():
            failures.append(f"missing result: {path}")
            continue
        rows = read_jsonl(path)
        ids = [str(row.get("item_id")) for row in rows]
        signatures = sorted({str(row.get("run_signature")) for row in rows})
        fields = {
            "condition": sorted({str(row.get("condition")) for row in rows}),
            "dataset_sha256": sorted({str(row.get("dataset_sha256")) for row in rows}),
            "seed": sorted({row.get("seed") for row in rows}),
            "do_sample": sorted({row.get("do_sample") for row in rows}),
            "max_new_tokens": sorted({row.get("max_new_tokens") for row in rows}),
            "dtype": sorted({str(row.get("dtype")) for row in rows}),
            "external_schema_valid": sorted({row.get("external_schema_valid") for row in rows}),
        }
        if len(rows) != args.limit:
            failures.append(f"{condition}: {len(rows)} rows != {args.limit}")
        if len(set(ids)) != len(ids):
            failures.append(f"{condition}: duplicate item IDs")
        if ids != expected_ids:
            failures.append(f"{condition}: item order does not match planned dataset")
        if fields["condition"] != [condition]:
            failures.append(f"{condition}: mixed or incorrect condition values")
        if fields["dataset_sha256"] != [dataset_hash]:
            failures.append(f"{condition}: incorrect dataset hash in rows")
        if fields["seed"] != [0] or fields["do_sample"] != [False]:
            failures.append(f"{condition}: stochastic or incorrect seed settings")
        if fields["max_new_tokens"] != [256] or fields["dtype"] != ["float32"]:
            failures.append(f"{condition}: incorrect decoding or precision settings")
        if len(signatures) != 1:
            failures.append(f"{condition}: expected one run signature")
        errors = sum(row.get("error") is not None for row in rows)
        caps = sum(bool(row.get("hit_max_new_tokens")) for row in rows)
        if errors:
            warnings.append(f"{condition}: {errors} generation errors")
        if caps:
            warnings.append(f"{condition}: {caps} token-cap hits")
        if reference_ids is None:
            reference_ids = ids
        elif ids != reference_ids:
            failures.append(f"{condition}: item order differs from another condition")
        reports[condition] = {
            "path": str(path),
            "sha256": sha256(path),
            "rows": len(rows),
            "unique_item_ids": len(set(ids)),
            "run_signature": signatures[0] if len(signatures) == 1 else None,
            "errors": errors,
            "hit_max_new_tokens": caps,
            "external_valid_rows": sum(bool(row.get("external_schema_valid")) for row in rows),
        }

    trace_report: dict[str, Any] | None = None
    if args.trace is not None:
        if not args.trace.exists():
            failures.append(f"missing trace: {args.trace}")
        else:
            traces = read_jsonl(args.trace)
            traced_ids = sorted({str(row.get("item_id")) for row in traces})
            required_ids = sorted({str(item_id) for item_id in args.trace_item_id})
            if not set(required_ids).issubset(traced_ids):
                failures.append("trace does not cover every requested item")
            if any(row.get("condition") != "xgrammar_json_integer_reasoning_first" for row in traces):
                failures.append("trace contains a non-XGrammar-integer condition")
            trace_report = {
                "path": str(args.trace),
                "sha256": sha256(args.trace),
                "records": len(traces),
                "traced_item_ids": traced_ids,
            }

    report = {
        "valid": not failures,
        "run_dir": str(args.run_dir),
        "dataset_sha256": dataset_hash,
        "expected_limit": args.limit,
        "expected_conditions": args.conditions,
        "failures": failures,
        "warnings": warnings,
        "conditions": reports,
        "trace": trace_report,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
