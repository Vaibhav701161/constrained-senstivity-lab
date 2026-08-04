#!/usr/bin/env python3
"""Create a deterministic, inspectable GSM8K evaluation subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import load_dataset

DEFAULT_OUTPUT = Path("data/gsm8k_50_seed0.jsonl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing subset file.",
    )
    return parser.parse_args()


def extract_gold(answer: str) -> str:
    marker = "####"
    if marker not in answer:
        raise ValueError("GSM8K answer is missing the #### final-answer marker")
    return answer.rsplit(marker, maxsplit=1)[1].strip()


def main() -> None:
    args = parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be positive")
    if args.out.exists() and not args.force:
        raise SystemExit(
            f"Refusing to overwrite {args.out}; pass --force to replace it"
        )

    dataset = load_dataset("openai/gsm8k", "main", split="test")
    if args.count > len(dataset):
        raise SystemExit(
            f"Requested {args.count} rows, but the test split has {len(dataset)}"
        )

    indexed = dataset.add_column("source_index", list(range(len(dataset))))
    subset = indexed.shuffle(seed=args.seed).select(range(args.count))
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("x" if not args.force else "w", encoding="utf-8") as output_file:
        for row in subset:
            output = {
                "id": f"gsm8k_test_{row['source_index']}",
                "source": "openai/gsm8k",
                "split": "test",
                "subset_seed": args.seed,
                "source_index": row["source_index"],
                "question": row["question"],
                "gold_answer": extract_gold(row["answer"]),
                "reference_solution": row["answer"],
            }
            output_file.write(json.dumps(output, ensure_ascii=False) + "\n")
            output_file.flush()

    print(f"wrote {len(subset)} rows to {args.out}")


if __name__ == "__main__":
    main()
