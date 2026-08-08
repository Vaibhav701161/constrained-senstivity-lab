#!/usr/bin/env python3
"""Freeze source and immutable input hashes for the canonical correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/canonical-schema-equivalence-correction/source-manifest.json"
)
MODEL_REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"
FROZEN_PATHS = (
    "requirements.txt",
    "src/project_a/contracts.py",
    "src/project_a/runtime.py",
    "src/project_a/metrics.py",
    "src/project_a/schema_variants.py",
    "src/project_a/transforms.py",
    "src/project_a/transducer.py",
    "src/project_a/tool_runtime.py",
    "scripts/run_contract_alignment.py",
    "scripts/analyze_canonical_correction.py",
    "scripts/validate_canonical_correction_canary.py",
    "scripts/validate_canonical_correction_artifacts.py",
    "scripts/replay_artifacts.py",
    "scripts/check_modal_budget.py",
    "scripts/package_canonical_correction_source.py",
    "deployment/modal/canonical-correction/modal_app.py",
    "tests/test_contract_runtime.py",
    "tests/test_contract_alignment.py",
    "tests/test_tool_runtime.py",
    "tests/test_transforms.py",
    "tests/test_artifact_replay.py",
    "tests/test_canonical_correction.py",
    "data/gsm8k_unseen_150_seed20260815.jsonl",
    "experiments/canonical-schema-equivalence-correction/HYPOTHESIS.md",
    "experiments/canonical-schema-equivalence-correction/protocol.md",
    "experiments/canonical-schema-equivalence-correction/mismatch-audit.json",
    "experiments/second-family-replication/results/fresh/xgrammar_json_integer_reasoning_first.jsonl",
    "experiments/second-family-replication/manifests/fresh/xgrammar_json_integer_reasoning_first.json",
    "experiments/second-family-replication/results/fresh/xgrammar_json_reasoning_first.jsonl",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if git_output("status", "--porcelain"):
        raise SystemExit("refusing to freeze a dirty source tree")
    missing = [path for path in FROZEN_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"missing frozen paths: {missing}")
    payload = {
        "manifest_version": "canonical-schema-correction-source-v1",
        "frozen_at": datetime.now(UTC).isoformat(),
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "model_revision": MODEL_REVISION,
        "git_commit": git_output("rev-parse", "HEAD"),
        "git_branch": git_output("branch", "--show-current"),
        "new_generation_arms": [
            "xgrammar_json_canonical_integer_string_reasoning_first"
        ],
        "frozen_treatment_regenerated": False,
        "files": [
            {
                "path": relative,
                "sha256": sha256(ROOT / relative),
                "bytes": (ROOT / relative).stat().st_size,
            }
            for relative in FROZEN_PATHS
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(sha256(args.out))


if __name__ == "__main__":
    main()
