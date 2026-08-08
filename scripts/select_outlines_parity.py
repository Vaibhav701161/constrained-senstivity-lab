#!/usr/bin/env python3
"""Select all fresh discordants and a frozen random concordant parity sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--paired-summary", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--concordant-count", type=int, default=20)
    parser.add_argument("--out-dataset", type=Path, required=True)
    parser.add_argument("--out-manifest", type=Path, required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.dataset)
    ids = [str(row["id"]) for row in rows]
    summary = json.loads(args.paired_summary.read_text(encoding="utf-8"))
    fresh = summary["datasets"]["fresh"]
    discordant = set(fresh["repaired_item_ids"]) | set(
        fresh["newly_broken_item_ids"]
    )
    unknown = discordant - set(ids)
    if unknown:
        raise ValueError(f"summary contains IDs outside the frozen dataset: {unknown}")
    concordant = [item for item in ids if item not in discordant]
    if len(concordant) < args.concordant_count:
        raise ValueError("not enough concordant items for the requested parity sample")
    sampled = set(random.Random(args.seed).sample(concordant, args.concordant_count))
    selected_ids = [item for item in ids if item in discordant or item in sampled]
    selected_rows = [row for row in rows if str(row["id"]) in set(selected_ids)]

    args.out_dataset.parent.mkdir(parents=True, exist_ok=True)
    args.out_dataset.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected_rows),
        encoding="utf-8",
    )
    manifest = {
        "manifest_version": "outlines-parity-selection-v1",
        "source_dataset": str(args.dataset),
        "source_dataset_sha256": sha256(args.dataset),
        "paired_summary": str(args.paired_summary),
        "paired_summary_sha256": sha256(args.paired_summary),
        "seed": args.seed,
        "discordant_count": len(discordant),
        "random_concordant_count": args.concordant_count,
        "selected_count": len(selected_rows),
        "discordant_item_ids": [item for item in ids if item in discordant],
        "random_concordant_item_ids": [item for item in ids if item in sampled],
        "selected_item_ids": selected_ids,
        "selected_dataset_sha256": sha256(args.out_dataset),
    }
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(args.out_dataset)
    print(args.out_manifest)


if __name__ == "__main__":
    main()
