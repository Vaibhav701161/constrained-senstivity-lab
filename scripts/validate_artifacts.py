#!/usr/bin/env python3
"""Validate completeness and provenance of a baseline experiment directory."""

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
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error}"
                ) from error
            if not isinstance(row, dict):
                raise TypeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--conditions", nargs="+", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument(
        "--prompt-version",
        required=True,
        help="Expected prompt version for JSON conditions",
    )
    parser.add_argument(
        "--free-prompt-version",
        default="day2-v4-reasoning-before-answer",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--dtype", default="float32")
    parser.add_argument(
        "--xgrammar-any-whitespace",
        choices=("true", "false"),
        help="Expected XGrammar JSON whitespace policy, when XGrammar is present",
    )
    parser.add_argument("--runner", type=Path)
    parser.add_argument("--summarizer", type=Path)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures: list[str] = []
    warnings: list[str] = []
    run_dir = args.run_dir
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        failures.append(f"missing manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    expected_conditions = list(args.conditions)
    expected_xgrammar_whitespace = (
        args.xgrammar_any_whitespace == "true"
        if args.xgrammar_any_whitespace is not None
        else None
    )
    if manifest.get("conditions") != expected_conditions:
        failures.append(
            f"manifest conditions {manifest.get('conditions')!r} != {expected_conditions!r}"
        )
    if manifest.get("limit") != args.limit:
        failures.append(f"manifest limit {manifest.get('limit')!r} != {args.limit}")
    for key, expected in (
        ("seed", args.seed),
        ("max_new_tokens", args.max_new_tokens),
        ("dtype", args.dtype),
    ):
        if manifest.get(key) != expected:
            failures.append(f"manifest {key} {manifest.get(key)!r} != {expected!r}")
    if (
        expected_xgrammar_whitespace is not None
        and manifest.get("xgrammar_any_whitespace") is not expected_xgrammar_whitespace
    ):
        failures.append(
            "manifest xgrammar_any_whitespace "
            f"{manifest.get('xgrammar_any_whitespace')!r} != "
            f"{expected_xgrammar_whitespace!r}"
        )

    dataset_hash = sha256(args.dataset)
    dataset_rows = read_jsonl(args.dataset)
    expected_ids = [
        str(row.get("item_id", row.get("id"))) for row in dataset_rows[: args.limit]
    ]
    if len(expected_ids) != args.limit:
        failures.append(
            f"dataset has only {len(dataset_rows)} rows, fewer than limit {args.limit}"
        )
    if manifest.get("dataset_sha256") != dataset_hash:
        failures.append(
            f"manifest dataset hash {manifest.get('dataset_sha256')!r} != {dataset_hash}"
        )
    for label, local_path, manifest_key in (
        ("runner", args.runner, "runner_sha256"),
        ("summarizer", args.summarizer, "summarizer_sha256"),
    ):
        if local_path is None:
            continue
        local_hash = sha256(local_path)
        if manifest.get(manifest_key) != local_hash:
            failures.append(
                f"manifest {label} hash {manifest.get(manifest_key)!r} != {local_hash}"
            )

    condition_reports: dict[str, Any] = {}
    reference_ids: list[str] | None = None
    for condition in expected_conditions:
        path = run_dir / f"{condition}.jsonl"
        if not path.exists():
            failures.append(f"missing result: {path}")
            continue
        rows = read_jsonl(path)
        ids = [str(row.get("item_id")) for row in rows]
        unique_ids = set(ids)
        errors = sum(row.get("error") is not None for row in rows)
        caps = sum(bool(row.get("hit_max_new_tokens")) for row in rows)
        prompt_versions = sorted({str(row.get("prompt_version")) for row in rows})
        row_conditions = sorted({str(row.get("condition")) for row in rows})
        dataset_hashes = sorted({str(row.get("dataset_sha256")) for row in rows})
        invariant_values = {
            "seed": sorted({row.get("seed") for row in rows}),
            "do_sample": sorted({row.get("do_sample") for row in rows}),
            "max_new_tokens": sorted({row.get("max_new_tokens") for row in rows}),
            "dtype": sorted({str(row.get("dtype")) for row in rows}),
            "load_in_4bit": sorted({row.get("load_in_4bit") for row in rows}),
            "xgrammar_any_whitespace": sorted(
                {row.get("xgrammar_any_whitespace") for row in rows},
                key=lambda value: str(value),
            ),
        }

        if len(rows) != args.limit:
            failures.append(f"{condition}: {len(rows)} rows != {args.limit}")
        if len(unique_ids) != len(ids):
            failures.append(f"{condition}: duplicate item IDs")
        expected_prompt_version = (
            args.free_prompt_version if condition == "free" else args.prompt_version
        )
        if prompt_versions != [expected_prompt_version]:
            failures.append(
                f"{condition}: prompt versions {prompt_versions!r} "
                f"!= {[expected_prompt_version]!r}"
            )
        if row_conditions != [condition]:
            failures.append(f"{condition}: row conditions {row_conditions!r}")
        if dataset_hashes != [dataset_hash]:
            failures.append(f"{condition}: dataset hashes {dataset_hashes!r}")
        expected_invariants = {
            "seed": [args.seed],
            "do_sample": [False],
            "max_new_tokens": [args.max_new_tokens],
            "dtype": [args.dtype],
            "load_in_4bit": [False],
        }
        for key, expected in expected_invariants.items():
            if invariant_values[key] != expected:
                failures.append(
                    f"{condition}: {key} values {invariant_values[key]!r} != {expected!r}"
                )
        if (
            condition.startswith("xgrammar_")
            and expected_xgrammar_whitespace is not None
        ):
            expected = [expected_xgrammar_whitespace]
            if invariant_values["xgrammar_any_whitespace"] != expected:
                failures.append(
                    f"{condition}: xgrammar_any_whitespace values "
                    f"{invariant_values['xgrammar_any_whitespace']!r} != {expected!r}"
                )
        if reference_ids is None:
            reference_ids = ids
        elif ids != reference_ids:
            failures.append(
                f"{condition}: ordered item IDs do not match first condition"
            )
        if ids != expected_ids:
            failures.append(
                f"{condition}: item IDs do not match the planned dataset prefix"
            )
        if errors:
            warnings.append(f"{condition}: {errors} generation errors")
        if caps:
            warnings.append(f"{condition}: {caps} token-cap hits")

        condition_reports[condition] = {
            "path": str(path),
            "sha256": sha256(path),
            "rows": len(rows),
            "unique_item_ids": len(unique_ids),
            "errors": errors,
            "hit_max_new_tokens": caps,
            "prompt_versions": prompt_versions,
        }

    report = {
        "valid": not failures,
        "run_dir": str(run_dir),
        "dataset": str(args.dataset),
        "dataset_sha256": dataset_hash,
        "expected_limit": args.limit,
        "expected_conditions": expected_conditions,
        "expected_prompt_versions": {
            condition: (
                args.free_prompt_version if condition == "free" else args.prompt_version
            )
            for condition in expected_conditions
        },
        "expected_xgrammar_any_whitespace": expected_xgrammar_whitespace,
        "failures": failures,
        "warnings": warnings,
        "conditions": condition_reports,
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
