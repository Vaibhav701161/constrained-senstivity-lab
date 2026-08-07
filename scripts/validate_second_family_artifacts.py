#!/usr/bin/env python3
"""Validate completeness and provenance of the second-family XGrammar matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MODEL = "meta-llama/Llama-3.2-3B-Instruct"
ROLES = {
    "fresh": {
        "count": 150,
        "excluded": [],
    },
    "bridge": {
        "count": 49,
        "excluded": ["gsm8k_test_454"],
    },
}
CONDITIONS = {
    "xgrammar_json_reasoning_first": "signed-numeric-string",
    "xgrammar_json_integer_reasoning_first": "integer",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.is_file():
        failures.append(f"missing JSON: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"cannot read {path}: {error}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"{path}: expected object")
        return {}
    return value


def read_jsonl(path: Path, failures: list[str]) -> list[dict[str, Any]]:
    if not path.is_file():
        failures.append(f"missing JSONL: {path}")
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            failures.append(f"{path}:{number}: invalid JSON: {error}")
            continue
        if not isinstance(value, dict):
            failures.append(f"{path}:{number}: expected object")
            continue
        rows.append(value)
    return rows


def stable_signature(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def source_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    files = manifest.get("files", [])
    if not isinstance(files, list):
        return {}
    return {
        str(item["path"]): str(item["sha256"])
        for item in files
        if isinstance(item, dict) and "path" in item and "sha256" in item
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--fresh-dataset", type=Path, required=True)
    parser.add_argument("--bridge-dataset", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-analysis", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    source_manifest_path = (
        args.source_root
        / "experiments/second-family-replication/source-manifest.json"
    )
    source_manifest = read_json(source_manifest_path, failures)
    expected_revision = source_manifest.get("model_revision")
    frozen_files = source_hashes(source_manifest)
    if not frozen_files:
        failures.append("source manifest contains no frozen files")
    for relative, expected_hash in frozen_files.items():
        path = args.source_root / relative
        if not path.is_file():
            failures.append(f"frozen source missing: {relative}")
        elif sha256(path) != expected_hash:
            failures.append(f"frozen source hash mismatch: {relative}")
    source_manifest_hash = (
        sha256(source_manifest_path) if source_manifest_path.is_file() else None
    )

    datasets = {
        "fresh": read_jsonl(args.fresh_dataset, failures),
        "bridge": read_jsonl(args.bridge_dataset, failures),
    }
    dataset_paths = {
        "fresh": args.fresh_dataset,
        "bridge": args.bridge_dataset,
    }
    expected_ids: dict[str, list[str]] = {}
    for role, rows in datasets.items():
        excluded = set(ROLES[role]["excluded"])
        expected_ids[role] = [
            str(row["id"]) for row in rows if str(row["id"]) not in excluded
        ]
        if len(expected_ids[role]) != ROLES[role]["count"]:
            failures.append(
                f"{role}: expected {ROLES[role]['count']} assigned IDs, "
                f"found {len(expected_ids[role])}"
            )
        if len(expected_ids[role]) != len(set(expected_ids[role])):
            failures.append(f"{role}: dataset contains duplicate IDs")

    result_report: dict[str, Any] = {}
    environment_fingerprints: set[str] = set()
    paired_configs: dict[str, dict[str, Any]] = {}
    for role, role_spec in ROLES.items():
        paired_configs[role] = {}
        for condition, representation in CONDITIONS.items():
            result_path = args.run_dir / "results" / role / f"{condition}.jsonl"
            manifest_path = args.run_dir / "manifests" / role / f"{condition}.json"
            rows = read_jsonl(result_path, failures)
            manifest = read_json(manifest_path, failures)
            ids = [str(row.get("item_id")) for row in rows]
            prefix = f"{role}/{condition}"
            if ids != expected_ids[role]:
                failures.append(f"{prefix}: item IDs or ordering differ")
            if len(rows) != role_spec["count"]:
                failures.append(
                    f"{prefix}: expected {role_spec['count']} rows, found {len(rows)}"
                )
            if len(ids) != len(set(ids)):
                failures.append(f"{prefix}: duplicate item IDs")
            signatures = {str(row.get("run_signature")) for row in rows}
            run_ids = {str(row.get("run_id")) for row in rows}
            revisions = {row.get("model_revision") for row in rows}
            tokenizer_revisions = {row.get("tokenizer_revision") for row in rows}
            if len(signatures) != 1:
                failures.append(f"{prefix}: expected one run signature")
            if len(run_ids) != 1:
                failures.append(f"{prefix}: expected one run ID")
            if revisions != {expected_revision}:
                failures.append(f"{prefix}: model revision mismatch")
            if tokenizer_revisions != {expected_revision}:
                failures.append(f"{prefix}: tokenizer revision mismatch")
            if any(row.get("condition") != condition for row in rows):
                failures.append(f"{prefix}: row condition mismatch")
            if any(row.get("answer_representation") != representation for row in rows):
                failures.append(f"{prefix}: representation mismatch")
            if any(row.get("effective_chat_template_depth") != 1 for row in rows):
                failures.append(f"{prefix}: chat template depth mismatch")

            config = manifest.get("run_config", {})
            if not isinstance(config, dict):
                failures.append(f"{prefix}: run config is not an object")
                config = {}
            paired_configs[role][condition] = config
            if signatures and signatures != {stable_signature(config)}:
                failures.append(f"{prefix}: row signature differs from manifest")
            if config.get("model") != MODEL or config.get("revision") != expected_revision:
                failures.append(f"{prefix}: frozen model identity mismatch")
            if config.get("dataset_sha256") != sha256(dataset_paths[role]):
                failures.append(f"{prefix}: dataset hash mismatch")
            if config.get("excluded_item_ids") != role_spec["excluded"]:
                failures.append(f"{prefix}: post-launch exclusion mismatch")
            if config.get("seed") != 0 or config.get("do_sample") is not False:
                failures.append(f"{prefix}: decoding determinism mismatch")
            if config.get("dtype") != "float32" or config.get("max_new_tokens") != 256:
                failures.append(f"{prefix}: numeric runtime configuration mismatch")
            if config.get("backend") != "xgrammar":
                failures.append(f"{prefix}: primary backend mismatch")
            if manifest.get("source_manifest_sha256") != source_manifest_hash:
                failures.append(f"{prefix}: source manifest binding mismatch")
            if manifest.get("model_revision") != expected_revision:
                failures.append(f"{prefix}: manifest model revision mismatch")
            environment = json.dumps(
                {
                    "packages": manifest.get("packages"),
                    "torch": manifest.get("torch"),
                    "cuda_runtime": manifest.get("cuda_runtime"),
                    "gpus": manifest.get("gpus"),
                    "python": manifest.get("python"),
                },
                sort_keys=True,
            )
            environment_fingerprints.add(hashlib.sha256(environment.encode()).hexdigest())
            result_report[prefix] = {
                "rows": len(rows),
                "sha256": sha256(result_path) if result_path.is_file() else None,
                "manifest_sha256": sha256(manifest_path)
                if manifest_path.is_file()
                else None,
                "run_signature": next(iter(signatures), None),
                "run_id": next(iter(run_ids), None),
                "errors": sum(row.get("error") is not None for row in rows),
                "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
                "internal_invalid": sum(
                    not bool(row.get("internal_schema_valid")) for row in rows
                ),
                "external_invalid": sum(
                    not bool(row.get("external_schema_valid")) for row in rows
                ),
            }

        left = dict(paired_configs[role]["xgrammar_json_reasoning_first"])
        right = dict(
            paired_configs[role]["xgrammar_json_integer_reasoning_first"]
        )
        representation_keys = {
            "condition",
            "answer_representation",
            "internal_schema_sha256",
            "transducer_version",
            "plan_id",
        }
        for key in representation_keys:
            left.pop(key, None)
            right.pop(key, None)
        if left != right:
            failures.append(f"{role}: paired run configurations diverge")

    if len(environment_fingerprints) != 1:
        failures.append("the four primary conditions used different environments")

    canary = read_json(args.run_dir / "canary-gate.json", failures)
    if canary.get("passed") is not True:
        failures.append("operational canary did not pass")
    if canary.get("semantic_outcomes_inspected") is not False:
        failures.append("canary gate does not certify semantic blinding")

    if args.require_analysis:
        summary = read_json(args.run_dir / "paired-summary.json", failures)
        if summary.get("analysis_version") != "second-family-paired-analysis-v1":
            failures.append("paired analysis version mismatch")
        if summary.get("manual_audit_complete") is not True:
            failures.append("manual discordant audit is incomplete")
        attribution = read_jsonl(args.run_dir / "failure-attribution.jsonl", failures)
        if len(attribution) != summary.get("discordant_items"):
            failures.append("failure attribution row count differs from summary")

    report = {
        "validation_version": "second-family-artifact-validation-v1",
        "valid": not failures,
        "model": MODEL,
        "model_revision": expected_revision,
        "source_manifest_sha256": source_manifest_hash,
        "expected_primary_rows": 398,
        "validated_primary_rows": sum(item["rows"] for item in result_report.values()),
        "results": result_report,
        "failures": failures,
        "warnings": warnings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("second-family artifact validation failed")


if __name__ == "__main__":
    main()
