#!/usr/bin/env python3
"""Validate completeness and provenance of the bounded BFCL tool-call pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MODEL = "meta-llama/Llama-3.2-3B-Instruct"
CONDITIONS = {
    "xgrammar_tool_external_integer_strings": "external-integer-strings",
    "xgrammar_tool_internal_integers": "internal-integers",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.is_file():
        failures.append(f"missing JSON: {path}")
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        failures.append(f"{path}: expected object")
        return {}
    return value


def read_jsonl(path: Path, failures: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        failures.append(f"missing JSONL: {path}")
        return []
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        failures.append(f"{path}: expected only objects")
        return []
    return rows


def stable_signature(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-analysis", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    source_path = args.run_dir / "source-manifest.json"
    source = read_json(source_path, failures)
    source_hash = sha256(source_path) if source_path.is_file() else None
    expected_revision = source.get("model_revision")
    frozen_files = source.get("files", [])
    if not isinstance(frozen_files, list) or not frozen_files:
        failures.append("source manifest contains no frozen files")
        frozen_files = []
    for item in frozen_files:
        path = args.source_root / str(item.get("path"))
        if not path.is_file():
            failures.append(f"frozen source missing: {item.get('path')}")
        elif sha256(path) != item.get("sha256"):
            failures.append(f"frozen source hash mismatch: {item.get('path')}")
    dataset = read_jsonl(args.dataset, failures)
    expected_ids = [str(row["id"]) for row in dataset]
    if len(expected_ids) != 33 or len(expected_ids) != len(set(expected_ids)):
        failures.append("dataset must contain 33 unique selected IDs")
    environments: set[str] = set()
    configs: dict[str, dict[str, Any]] = {}
    results: dict[str, Any] = {}
    for condition, representation in CONDITIONS.items():
        result_path = args.run_dir / "results" / f"{condition}.jsonl"
        manifest_path = args.run_dir / "manifests" / f"{condition}.json"
        rows = read_jsonl(result_path, failures)
        manifest = read_json(manifest_path, failures)
        ids = [str(row.get("item_id")) for row in rows]
        if ids != expected_ids:
            failures.append(f"{condition}: IDs or ordering differ")
        if len(rows) != 33:
            failures.append(f"{condition}: expected 33 rows, found {len(rows)}")
        if len(ids) != len(set(ids)):
            failures.append(f"{condition}: duplicate IDs")
        if {row.get("run_id") for row in rows} and len({row.get("run_id") for row in rows}) != 1:
            failures.append(f"{condition}: multiple run IDs")
        if any(row.get("condition") != condition for row in rows):
            failures.append(f"{condition}: row condition differs")
        if any(row.get("representation") != representation for row in rows):
            failures.append(f"{condition}: row representation differs")
        if any(row.get("effective_chat_template_depth") != 1 for row in rows):
            failures.append(f"{condition}: chat-template depth differs")
        if any(row.get("model_revision") != expected_revision for row in rows):
            failures.append(f"{condition}: model revision differs")
        if any(row.get("tokenizer_revision") != expected_revision for row in rows):
            failures.append(f"{condition}: tokenizer revision differs")
        config = manifest.get("run_config", {})
        configs[condition] = config
        signatures = {row.get("run_signature") for row in rows}
        if signatures != {stable_signature(config)}:
            failures.append(f"{condition}: signature differs from manifest")
        if config.get("model") != MODEL or config.get("revision") != expected_revision:
            failures.append(f"{condition}: model identity differs")
        if config.get("dataset_sha256") != sha256(args.dataset):
            failures.append(f"{condition}: dataset hash differs")
        if config.get("seed") != 0 or config.get("do_sample") is not False:
            failures.append(f"{condition}: decoding determinism differs")
        if config.get("dtype") != "float32" or config.get("max_new_tokens") != 192:
            failures.append(f"{condition}: numeric runtime differs")
        if manifest.get("source_manifest_sha256") != source_hash:
            failures.append(f"{condition}: source binding differs")
        environment = json.dumps(
            {key: manifest.get(key) for key in ("python", "torch", "cuda_runtime", "gpus", "packages")},
            sort_keys=True,
        )
        environments.add(hashlib.sha256(environment.encode()).hexdigest())
        results[condition] = {
            "rows": len(rows),
            "sha256": sha256(result_path) if result_path.is_file() else None,
            "manifest_sha256": sha256(manifest_path) if manifest_path.is_file() else None,
            "run_id": next(iter({row.get("run_id") for row in rows}), None),
            "run_signature": next(iter(signatures), None),
            "errors": sum(row.get("error") is not None for row in rows),
            "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
            "internal_invalid": sum(row.get("internal_schema_valid") is not True for row in rows),
            "external_invalid": sum(row.get("external_schema_valid") is not True for row in rows),
            "execution_failures": sum(row.get("execution_success") is not True for row in rows),
            "heuristic_repairs": sum(int(row.get("heuristic_repair_count", 0)) for row in rows),
        }
    left = dict(configs.get("xgrammar_tool_external_integer_strings", {}))
    right = dict(configs.get("xgrammar_tool_internal_integers", {}))
    for key in ("condition", "representation", "model_uses_integers", "transducer_version"):
        left.pop(key, None)
        right.pop(key, None)
    if left != right:
        failures.append("paired run configurations diverge")
    if len(environments) != 1:
        failures.append("paired environments differ")
    canary = read_json(args.run_dir / "canary-gate.json", failures)
    if canary.get("passed") is not True or canary.get("semantic_outcomes_inspected") is not False:
        failures.append("operational canary is missing or invalid")
    if args.require_analysis:
        summary = read_json(args.run_dir / "paired-summary.json", failures)
        if summary.get("analysis_version") != "bounded-bfcl-tool-paired-v1":
            failures.append("paired analysis version differs")
        if summary.get("manual_audit_complete") is not True:
            failures.append("manual discordant audit is incomplete")
        attribution = read_jsonl(args.run_dir / "failure-attribution.jsonl", failures)
        if len(attribution) != summary.get("discordant_items"):
            failures.append("failure attribution count differs")
    report = {
        "validation_version": "bounded-bfcl-tool-artifacts-v1",
        "valid": not failures,
        "model": MODEL,
        "model_revision": expected_revision,
        "source_manifest_sha256": source_hash,
        "expected_generation_rows": 66,
        "validated_generation_rows": sum(item["rows"] for item in results.values()),
        "results": results,
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("tool-call artifact validation failed")


if __name__ == "__main__":
    main()
