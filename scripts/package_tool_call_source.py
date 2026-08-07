#!/usr/bin/env python3
"""Freeze exact source and input hashes for the bounded tool-call pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "experiments/tool-call-gate/source-manifest.json"
FROZEN_PATHS = (
    "requirements.txt",
    "src/project_a/runtime.py",
    "src/project_a/tool_runtime.py",
    "scripts/run_tool_call_pilot.py",
    "scripts/fetch_bfcl_foundation.py",
    "scripts/prepare_bfcl_tool_pilot.py",
    "scripts/analyze_tool_call_pilot.py",
    "scripts/validate_tool_call_canary.py",
    "scripts/validate_tool_call_artifacts.py",
    "scripts/package_tool_call_source.py",
    "scripts/check_modal_budget.py",
    "deployment/modal/tool-call-pilot/modal_app.py",
    "tests/test_tool_runtime.py",
    "tests/test_bfcl_foundation.py",
    "tests/test_tool_runner.py",
    "tests/test_prepare_bfcl_tool_pilot.py",
    "tests/test_tool_call_analysis.py",
    "tests/test_validate_tool_call_canary.py",
    "data/bfcl_tool_pilot_seed20260817.jsonl",
    "experiments/tool-call-gate/HYPOTHESIS.md",
    "experiments/tool-call-gate/protocol.md",
    "experiments/tool-call-gate/FOUNDATION.md",
    "experiments/tool-call-gate/upstream-manifest.json",
    "experiments/tool-call-gate/dataset-manifest.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    missing = [relative for relative in FROZEN_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit(f"missing frozen sources: {missing}")
    payload = {
        "manifest_version": "bounded-bfcl-tool-source-v1",
        "frozen_at": datetime.now(UTC).isoformat(),
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "model_revision": "0cb88a4f764b7a12671c53f0838cd831a0843b95",
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
