#!/usr/bin/env python3
"""Validate provenance, completeness, and replay for the canonical correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.analyze_canonical_correction import read_jsonl, rescore_rows

MODEL = "meta-llama/Llama-3.2-3B-Instruct"
REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"
CONDITION = "xgrammar_json_canonical_integer_string_reasoning_first"
FROZEN_TREATMENT_SHA256 = (
    "298d1a38ad8d95d89ca97ab1f98d14bef4853342bf388d080f57f06de9c47342"
)


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


def git_blob(root: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--historical-control", type=Path, required=True)
    parser.add_argument("--frozen-treatment", type=Path, required=True)
    parser.add_argument("--frozen-treatment-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-analysis", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    source_path = args.run_dir / "source-manifest.json"
    source = read_json(source_path, failures)
    source_commit = str(source.get("git_commit", ""))
    for item in source.get("files", []):
        relative = str(item.get("path"))
        try:
            content = git_blob(args.source_root, source_commit, relative)
        except subprocess.CalledProcessError:
            failures.append(f"frozen git source missing: {relative}")
            continue
        if hashlib.sha256(content).hexdigest() != item.get("sha256"):
            failures.append(f"frozen git source hash mismatch: {relative}")

    dataset = read_jsonl(args.dataset)
    expected_ids = [str(row["id"]) for row in dataset]
    if len(expected_ids) != 150 or len(set(expected_ids)) != 150:
        failures.append("dataset must contain 150 unique IDs")
    result_path = args.run_dir / "results" / f"{CONDITION}.jsonl"
    manifest_path = args.run_dir / "manifests" / f"{CONDITION}.json"
    rows = read_jsonl(result_path) if result_path.is_file() else []
    manifest = read_json(manifest_path, failures)
    historical = read_jsonl(args.historical_control)
    treatment = read_jsonl(args.frozen_treatment)
    ids = [str(row.get("item_id")) for row in rows]
    if ids != expected_ids:
        failures.append("canonical control IDs or ordering differ from dataset")
    if len(rows) != 150:
        failures.append(f"expected 150 canonical rows, found {len(rows)}")
    if len(set(ids)) != len(ids):
        failures.append("canonical rows contain duplicate IDs")
    if [row.get("prompt") for row in rows] != [
        row.get("prompt") for row in historical
    ]:
        failures.append("canonical raw prompts differ from historical control")
    if any(row.get("condition") != CONDITION for row in rows):
        failures.append("canonical condition identity differs")
    if any(row.get("model_revision") != REVISION for row in rows):
        failures.append("canonical model revision differs")
    if any(row.get("tokenizer_revision") != REVISION for row in rows):
        failures.append("canonical tokenizer revision differs")
    if any(row.get("effective_chat_template_depth") != 1 for row in rows):
        failures.append("canonical chat-template depth differs")
    if any(row.get("dataset_sha256") != sha256(args.dataset) for row in rows):
        failures.append("canonical dataset hash differs")
    replayed, score_mismatches = rescore_rows(rows, treatment=False)
    if score_mismatches:
        failures.append(f"canonical stored score mismatches: {len(score_mismatches)}")
    config = manifest.get("run_config", {})
    required_config = {
        "model": MODEL,
        "revision": REVISION,
        "dataset_role": "fresh",
        "dataset_sha256": sha256(args.dataset),
        "condition": CONDITION,
        "backend": "xgrammar",
        "answer_representation": "canonical-signed-integer-string",
        "seed": 0,
        "do_sample": False,
        "max_new_tokens": 256,
        "dtype": "float32",
        "device_map_auto": True,
        "prompt_version": "contract-alignment-unified-v1",
        "xgrammar_any_whitespace": False,
        "xgrammar_separators": [",", ":"],
    }
    if any(config.get(key) != value for key, value in required_config.items()):
        failures.append("canonical run configuration differs from protocol")
    if manifest.get("source_manifest_sha256") != sha256(source_path):
        failures.append("canonical manifest is not bound to source manifest")
    treatment_manifest = read_json(args.frozen_treatment_manifest, failures)
    if manifest.get("packages") != treatment_manifest.get("packages"):
        failures.append("canonical and frozen treatment package environments differ")
    if manifest.get("gpus") != treatment_manifest.get("gpus"):
        failures.append("canonical and frozen treatment GPU environments differ")
    if sha256(args.frozen_treatment) != FROZEN_TREATMENT_SHA256:
        failures.append("frozen treatment hash differs")
    if len(treatment) != 150 or [str(row.get("item_id")) for row in treatment] != expected_ids:
        failures.append("frozen treatment IDs or row count differ")
    canary = read_json(args.run_dir / "canary-gate.json", failures)
    if canary.get("passed") is not True:
        failures.append("canonical operational canary did not pass")
    if canary.get("semantic_outcomes_inspected") is not False:
        failures.append("canonical canary inspected semantic outcomes")
    if args.require_analysis:
        summary = read_json(args.run_dir / "paired-summary.json", failures)
        if summary.get("analysis_version") != "canonical-schema-equivalence-correction-v1":
            failures.append("canonical analysis version differs")
        if summary.get("manual_audit_complete") is not True:
            failures.append("canonical manual audit is incomplete")
        attribution_path = args.run_dir / "failure-attribution.jsonl"
        attribution = read_jsonl(attribution_path) if attribution_path.is_file() else []
        if len(attribution) != summary.get("discordant_items"):
            failures.append("canonical attribution count differs")
        if summary.get("control_stored_score_mismatches"):
            failures.append("canonical analysis found stored score mismatches")
        if not (args.run_dir / "decision-report.md").is_file():
            failures.append("canonical decision report is missing")
    report = {
        "validation_version": "canonical-schema-correction-artifacts-v1",
        "valid": not failures,
        "model": MODEL,
        "model_revision": REVISION,
        "source_commit": source_commit,
        "source_manifest_sha256": sha256(source_path) if source_path.is_file() else None,
        "dataset_sha256": sha256(args.dataset),
        "expected_new_rows": 150,
        "validated_new_rows": len(rows),
        "canonical_result_sha256": sha256(result_path) if result_path.is_file() else None,
        "canonical_manifest_sha256": sha256(manifest_path) if manifest_path.is_file() else None,
        "frozen_treatment_sha256": sha256(args.frozen_treatment),
        "score_replay_mismatches": len(score_mismatches),
        "errors": sum(row.get("error") is not None for row in replayed),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in replayed),
        "internal_invalid": sum(row.get("internal_schema_valid") is not True for row in replayed),
        "external_invalid": sum(row.get("external_schema_valid") is not True for row in replayed),
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("canonical correction artifact validation failed")


if __name__ == "__main__":
    main()
