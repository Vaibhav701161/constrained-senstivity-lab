#!/usr/bin/env python3
"""Synchronize public technical figures into the MkDocs asset tree."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/figures"
TARGET = ROOT / "docs/assets/figures"

PUBLIC_STEMS = (
    "accuracy-compliance-tradeoff",
    "canonical-correction-delta",
    "canonical-schema-correction",
    "contract-alignment-pipeline",
    "corrected-replication-effect",
    "corrected-replication-item-map",
    "corrected-replication-transitions",
    "cross-family-evidence",
    "evaluation-design",
    "field-order-sensitivity",
    "llama-paired-item-map",
    "paired-effects",
    "paired-outcome-composition",
    "paired-transitions",
    "representation-alignment-recovery",
    "research-system-architecture",
    "tool-call-pilot-result",
    "validity-semantics-separation",
)


def expected_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for stem in PUBLIC_STEMS:
        for suffix in (".png", ".svg"):
            pairs.append((SOURCE / f"{stem}{suffix}", TARGET / f"{stem}{suffix}"))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if documentation copies differ instead of updating them.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    for source, target in expected_pairs():
        if not source.is_file():
            failures.append(f"missing source figure: {source.relative_to(ROOT)}")
            continue
        if args.check:
            if not target.is_file():
                failures.append(f"missing docs figure: {target.relative_to(ROOT)}")
            elif source.read_bytes() != target.read_bytes():
                failures.append(f"stale docs figure: {target.relative_to(ROOT)}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    if failures:
        raise SystemExit("\n".join(failures))
    action = "verified" if args.check else "synchronized"
    print(f"{action} {len(expected_pairs())} figure files")


if __name__ == "__main__":
    main()
