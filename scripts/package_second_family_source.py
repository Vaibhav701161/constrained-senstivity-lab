#!/usr/bin/env python3
"""Freeze the exact source and input hashes for the second-family replication."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "experiments/second-family-replication/source-manifest.json"
FROZEN_PATHS = (
    "requirements.txt",
    "src/project_a/runtime.py",
    "src/project_a/metrics.py",
    "src/project_a/schema_variants.py",
    "src/project_a/transducer.py",
    "scripts/run_contract_alignment.py",
    "scripts/prepare_unseen_gsm8k.py",
    "scripts/package_second_family_source.py",
    "scripts/check_modal_budget.py",
    "scripts/validate_second_family_canary.py",
    "deployment/modal/second-family/modal_app.py",
    "tests/test_contract_runtime.py",
    "tests/test_llama_prompt_parity.py",
    "tests/test_modal_budget.py",
    "tests/test_prepare_unseen_gsm8k.py",
    "tests/test_validate_second_family_canary.py",
    "tests/fixtures/corrected-qwen-first5-golden.json",
    "data/gsm8k_unseen_150_seed20260815.jsonl",
    "data/gsm8k_unseen_150_seed20260815.manifest.json",
    "data/gsm8k_50_seed0.jsonl",
    "experiments/second-family-replication/HYPOTHESIS.md",
    "experiments/second-family-replication/protocol.md",
    "experiments/second-family-replication/dataset-manifest.json",
    "docs/architecture.md",
    "docs/supported-contracts.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    parser.add_argument("--model-revision", required=True)
    args = parser.parse_args()

    missing = [relative for relative in FROZEN_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit(f"missing frozen sources: {missing}")
    payload = {
        "manifest_version": "second-family-source-v1",
        "frozen_at": datetime.now(UTC).isoformat(),
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "model_revision": args.model_revision,
        "git_commit": git_output("rev-parse", "HEAD"),
        "git_branch": git_output("branch", "--show-current"),
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
