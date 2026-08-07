#!/usr/bin/env python3
"""Fetch and verify the two pinned BFCL foundation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "experiments/tool-call-gate/upstream-manifest.json"


def verify_bytes(payload: bytes, expected_sha256: str) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"BFCL source hash mismatch: expected {expected_sha256}, got {actual}")


def raw_url(repository: str, commit: str, path: str) -> str:
    prefix = repository.removesuffix(".git").replace(
        "https://github.com/", "https://raw.githubusercontent.com/"
    )
    return f"{prefix}/{commit}/{path}"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "project-a-research"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("BFCL source manifest must be an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=ROOT / ".cache/bfcl")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    for item in manifest["files"]:
        relative = str(item["path"])
        url = raw_url(manifest["repository"], manifest["commit"], relative)
        payload = fetch(url)
        verify_bytes(payload, str(item["sha256"]))
        destination = args.out_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        print(destination)


if __name__ == "__main__":
    main()
