#!/usr/bin/env python3
"""Apply the operational-only canary gate for the bounded BFCL pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPRESENTATION_KEYS = {
    "condition",
    "representation",
    "model_uses_integers",
    "transducer_version",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalized_config(manifest: dict[str, Any]) -> dict[str, Any]:
    config = dict(manifest["run_config"])
    for key in REPRESENTATION_KEYS:
        config.pop(key, None)
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--control-results", type=Path, required=True)
    parser.add_argument("--control-manifest", type=Path, required=True)
    parser.add_argument("--treatment-results", type=Path, required=True)
    parser.add_argument("--treatment-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    dataset = read_jsonl(args.dataset)
    dataset_manifest = read_json(args.dataset_manifest)
    source_manifest = read_json(args.source_manifest)
    control = read_jsonl(args.control_results)
    treatment = read_jsonl(args.treatment_results)
    control_manifest = read_json(args.control_manifest)
    treatment_manifest = read_json(args.treatment_manifest)
    expected_ids = [str(row["id"]) for row in dataset[:3]]
    source_hash = sha256(args.source_manifest)
    combined = control + treatment
    checks = {
        "exactly_three_control_rows": len(control) == 3,
        "exactly_three_treatment_rows": len(treatment) == 3,
        "control_ids_match_frozen_order": [str(row.get("item_id")) for row in control] == expected_ids,
        "treatment_ids_match_frozen_order": [str(row.get("item_id")) for row in treatment] == expected_ids,
        "no_duplicates": len({row.get("item_id") for row in control}) == 3
        and len({row.get("item_id") for row in treatment}) == 3,
        "one_chat_template_application": all(row.get("effective_chat_template_depth") == 1 for row in combined),
        "nonempty_outputs": all(bool(str(row.get("raw_output", "")).strip()) for row in combined),
        "no_generation_exceptions": all(row.get("error") is None for row in combined),
        "no_token_cap_hits": all(row.get("hit_max_new_tokens") is False for row in combined),
        "all_internal_schema_valid": all(row.get("internal_schema_valid") is True for row in combined),
        "all_external_schema_valid": all(row.get("external_schema_valid") is True for row in combined),
        "all_execution_paths_operational": all(row.get("execution_success") is True for row in combined),
        "zero_heuristic_repairs": all(row.get("heuristic_repair_count") == 0 for row in combined),
        "paired_config_parity": normalized_config(control_manifest) == normalized_config(treatment_manifest),
        "matching_dataset_hashes": {row.get("dataset_sha256") for row in combined} == {sha256(args.dataset)},
        "dataset_hash_is_frozen": dataset_manifest.get("artifact", {}).get("sha256") == sha256(args.dataset),
        "one_model_revision": {row.get("model_revision") for row in combined} == {source_manifest.get("model_revision")},
        "one_tokenizer_revision": {row.get("tokenizer_revision") for row in combined} == {source_manifest.get("model_revision")},
        "matching_environment": all(
            control_manifest.get(key) == treatment_manifest.get(key)
            for key in ("python", "torch", "cuda_runtime", "gpus", "packages")
        ),
        "source_manifest_bound": control_manifest.get("source_manifest_sha256")
        == treatment_manifest.get("source_manifest_sha256")
        == source_hash,
    }
    report = {
        "gate_version": "bounded-bfcl-tool-canary-v1",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "scope": "operational_integrity_only",
        "semantic_outcomes_inspected": False,
        "passed": all(checks.values()),
        "checks": checks,
        "expected_item_ids": expected_ids,
        "control_run_signature": control[0].get("run_signature") if control else None,
        "treatment_run_signature": treatment[0].get("run_signature") if treatment else None,
        "dataset_sha256": sha256(args.dataset),
        "source_manifest_sha256": source_hash,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit("tool-call canary gate failed")


if __name__ == "__main__":
    main()
