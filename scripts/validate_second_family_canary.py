#!/usr/bin/env python3
"""Apply the preregistered operational-only canary gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPRESENTATION_KEYS = {
    "condition",
    "answer_representation",
    "internal_schema_sha256",
    "transducer_version",
    "plan_id",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: expected only objects")
    return rows


def all_true(rows: list[dict[str, Any]], key: str) -> bool:
    return all(row.get(key) is True for row in rows)


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

    dataset = load_jsonl(args.dataset)
    dataset_manifest = load_json(args.dataset_manifest)
    source_manifest = load_json(args.source_manifest)
    control = load_jsonl(args.control_results)
    treatment = load_jsonl(args.treatment_results)
    control_manifest = load_json(args.control_manifest)
    treatment_manifest = load_json(args.treatment_manifest)
    expected_ids = [str(row["id"]) for row in dataset[:5]]
    source_hash = sha256(args.source_manifest)

    checks = {
        "exactly_five_control_rows": len(control) == 5,
        "exactly_five_treatment_rows": len(treatment) == 5,
        "control_ids_match_frozen_order": [str(row.get("item_id")) for row in control]
        == expected_ids,
        "treatment_ids_match_frozen_order": [
            str(row.get("item_id")) for row in treatment
        ]
        == expected_ids,
        "no_control_duplicates": len({row.get("item_id") for row in control})
        == len(control),
        "no_treatment_duplicates": len({row.get("item_id") for row in treatment})
        == len(treatment),
        "one_chat_template_application": all(
            row.get("effective_chat_template_depth") == 1
            for row in control + treatment
        ),
        "nonempty_outputs": all(bool(str(row.get("raw_output", "")).strip()) for row in control + treatment),
        "no_generation_exceptions": all(row.get("error") is None for row in control + treatment),
        "no_token_cap_hits": all(row.get("hit_max_new_tokens") is False for row in control + treatment),
        "all_internal_schema_valid": all_true(control + treatment, "internal_schema_valid"),
        "all_treatment_external_valid": all_true(treatment, "external_schema_valid"),
        "one_control_signature": len({row.get("run_signature") for row in control}) == 1,
        "one_treatment_signature": len({row.get("run_signature") for row in treatment}) == 1,
        "paired_config_parity": normalized_config(control_manifest)
        == normalized_config(treatment_manifest),
        "matching_dataset_hashes": len(
            {row.get("dataset_sha256") for row in control + treatment}
        )
        == 1,
        "dataset_hash_is_frozen": sha256(args.dataset)
        == dataset_manifest.get("artifact", {}).get("sha256"),
        "one_model_revision": len(
            {row.get("model_revision") for row in control + treatment}
        )
        == 1,
        "model_revision_is_preregistered": {
            row.get("model_revision") for row in control + treatment
        }
        == {source_manifest.get("model_revision")},
        "one_tokenizer_revision": len(
            {row.get("tokenizer_revision") for row in control + treatment}
        )
        == 1,
        "matching_package_environment": control_manifest.get("packages")
        == treatment_manifest.get("packages"),
        "matching_gpu_environment": control_manifest.get("gpus")
        == treatment_manifest.get("gpus"),
        "source_manifest_bound": control_manifest.get("source_manifest_sha256")
        == treatment_manifest.get("source_manifest_sha256")
        == source_hash,
    }
    passed = all(checks.values())
    report = {
        "gate_version": "second-family-canary-v1",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "scope": "operational_integrity_only",
        "semantic_outcomes_inspected": False,
        "passed": passed,
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
    if not passed:
        raise SystemExit("canary gate failed")


if __name__ == "__main__":
    main()
