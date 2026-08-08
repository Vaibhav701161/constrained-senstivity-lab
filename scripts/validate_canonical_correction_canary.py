#!/usr/bin/env python3
"""Validate the operational-only canary for the canonical control correction."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--control-results", type=Path, required=True)
    parser.add_argument("--control-manifest", type=Path, required=True)
    parser.add_argument("--historical-control", type=Path, required=True)
    parser.add_argument("--frozen-treatment", type=Path, required=True)
    parser.add_argument("--frozen-treatment-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    dataset = read_jsonl(args.dataset)
    source = read_json(args.source_manifest)
    control = read_jsonl(args.control_results)
    historical = read_jsonl(args.historical_control)[:5]
    treatment = read_jsonl(args.frozen_treatment)[:5]
    control_manifest = read_json(args.control_manifest)
    treatment_manifest = read_json(args.frozen_treatment_manifest)
    expected_ids = [str(row["id"]) for row in dataset[:5]]
    intended_settings = {
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "revision": "0cb88a4f764b7a12671c53f0838cd831a0843b95",
        "dataset_role": "fresh",
        "dataset_sha256": sha256(args.dataset),
        "backend": "xgrammar",
        "seed": 0,
        "do_sample": False,
        "max_new_tokens": 256,
        "dtype": "float32",
        "device_map_auto": True,
        "prompt_version": "contract-alignment-unified-v1",
        "xgrammar_any_whitespace": False,
        "xgrammar_separators": [",", ":"],
    }
    config = control_manifest.get("run_config", {})
    treatment_config = treatment_manifest.get("run_config", {})
    checks = {
        "exactly_five_control_rows": len(control) == 5,
        "control_ids_match_frozen_order": [str(row.get("item_id")) for row in control]
        == expected_ids,
        "historical_ids_match_frozen_order": [
            str(row.get("item_id")) for row in historical
        ]
        == expected_ids,
        "treatment_ids_match_frozen_order": [
            str(row.get("item_id")) for row in treatment
        ]
        == expected_ids,
        "no_duplicates": len({row.get("item_id") for row in control}) == 5,
        "prompts_byte_identical_to_historical_control": [
            row.get("prompt") for row in control
        ]
        == [row.get("prompt") for row in historical],
        "one_chat_template_application": all(
            row.get("effective_chat_template_depth") == 1 for row in control
        ),
        "nonempty_outputs": all(
            bool(str(row.get("raw_output", "")).strip()) for row in control
        ),
        "no_generation_exceptions": all(row.get("error") is None for row in control),
        "no_token_cap_hits": all(
            row.get("hit_max_new_tokens") is False for row in control
        ),
        "all_internal_schema_valid": all(
            row.get("internal_schema_valid") is True for row in control
        ),
        "all_external_schema_valid": all(
            row.get("external_schema_valid") is True for row in control
        ),
        "one_run_signature": len({row.get("run_signature") for row in control}) == 1,
        "condition_is_canonical_control": {
            row.get("condition") for row in control
        }
        == {"xgrammar_json_canonical_integer_string_reasoning_first"},
        "model_revision_is_frozen": {
            row.get("model_revision") for row in control
        }
        == {source.get("model_revision")},
        "tokenizer_revision_is_frozen": {
            row.get("tokenizer_revision") for row in control
        }
        == {source.get("model_revision")},
        "dataset_hash_is_frozen": {
            row.get("dataset_sha256") for row in control
        }
        == {sha256(args.dataset)},
        "run_settings_are_frozen": all(
            config.get(key) == value for key, value in intended_settings.items()
        ),
        "paired_settings_match_frozen_treatment": all(
            config.get(key) == treatment_config.get(key)
            for key in intended_settings
            if key not in {"dataset_sha256"}
        ),
        "matching_package_environment": control_manifest.get("packages")
        == treatment_manifest.get("packages"),
        "matching_gpu_environment": control_manifest.get("gpus")
        == treatment_manifest.get("gpus"),
        "source_manifest_bound": control_manifest.get("source_manifest_sha256")
        == sha256(args.source_manifest),
    }
    report = {
        "gate_version": "canonical-schema-correction-canary-v1",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "scope": "operational_integrity_only",
        "semantic_outcomes_inspected": False,
        "passed": all(checks.values()),
        "checks": checks,
        "expected_item_ids": expected_ids,
        "control_run_signature": control[0].get("run_signature") if control else None,
        "dataset_sha256": sha256(args.dataset),
        "source_manifest_sha256": sha256(args.source_manifest),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit("canonical correction canary failed")


if __name__ == "__main__":
    main()
