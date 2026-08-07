#!/usr/bin/env python3
"""Create a deterministic GSM8K holdout that excludes every repository-seen item."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_a.metrics import canonical_number  # noqa: E402

DEFAULT_OUTPUT = ROOT / "data/gsm8k_unseen_150_seed20260815.jsonl"
DEFAULT_MANIFEST = ROOT / "data/gsm8k_unseen_150_seed20260815.manifest.json"
DEFAULT_EXPERIMENT_MANIFEST = (
    ROOT / "experiments/second-family-replication/dataset-manifest.json"
)
DEFAULT_SCAN_ROOTS = (
    ROOT / "results",
    ROOT / "experiments",
    ROOT / "deployment",
)
DATASET_ID = "openai/gsm8k"
DATASET_CONFIG = "main"
DATASET_SPLIT = "test"
ITEM_PREFIX = "gsm8k_test_"
SELECTION_ALGORITHM = "python-random-mt19937-shuffle-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--experiment-manifest",
        type=Path,
        default=DEFAULT_EXPERIMENT_MANIFEST,
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        type=Path,
        dest="scan_roots",
        help="JSONL artifact root; repeat to replace the three default roots",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def parse_gsm8k_index(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.startswith(ITEM_PREFIX):
        suffix = value.removeprefix(ITEM_PREFIX)
        return int(suffix) if suffix.isdigit() else None
    return None


def indices_from_row(row: dict[str, Any]) -> set[int]:
    indices: set[int] = set()
    for key in ("item_id", "id", "source_index"):
        parsed = parse_gsm8k_index(row.get(key))
        if parsed is not None:
            indices.add(parsed)
    return indices


def relative_display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return str(resolved)


def collect_seen_indices(
    scan_roots: Iterable[Path],
) -> tuple[set[int], list[dict[str, Any]]]:
    seen: set[int] = set()
    files: list[dict[str, Any]] = []
    jsonl_paths = sorted(
        {
            path.resolve()
            for root in scan_roots
            if root.exists()
            for path in root.rglob("*.jsonl")
            if path.is_file()
        },
        key=str,
    )
    for path in jsonl_paths:
        rows = 0
        file_indices: set[int] = set()
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                rows += 1
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected a JSON object")
                file_indices.update(indices_from_row(value))
        seen.update(file_indices)
        files.append(
            {
                "path": relative_display(path),
                "sha256": sha256_file(path),
                "rows": rows,
                "unique_gsm8k_indices": len(file_indices),
            }
        )
    return seen, files


def select_unseen_indices(
    total: int,
    seen_indices: set[int],
    count: int,
    seed: int,
) -> list[int]:
    if count <= 0:
        raise ValueError("count must be positive")
    eligible = [index for index in range(total) if index not in seen_indices]
    if count > len(eligible):
        raise ValueError(
            f"requested {count} unseen rows, but only {len(eligible)} are eligible"
        )
    generator = random.Random(seed)
    generator.shuffle(eligible)
    return eligible[:count]


def extract_gold(reference_solution: str) -> str:
    marker = "####"
    if marker not in reference_solution:
        raise ValueError("GSM8K answer is missing the #### final-answer marker")
    gold = reference_solution.rsplit(marker, maxsplit=1)[1].strip()
    if not gold:
        raise ValueError("GSM8K final answer is empty")
    normalized = canonical_number(gold)
    if normalized is None or normalized.casefold() == gold.casefold() and not any(
        character.isdigit() for character in gold
    ):
        raise ValueError(f"GSM8K final answer is not numeric: {gold!r}")
    return gold


def build_rows(dataset: Any, indices: list[int], seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in indices:
        source = dataset[index]
        question = source.get("question")
        reference = source.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"GSM8K index {index} has an empty question")
        if not isinstance(reference, str):
            raise ValueError(f"GSM8K index {index} has a non-string answer")
        rows.append(
            {
                "id": f"{ITEM_PREFIX}{index}",
                "source": DATASET_ID,
                "split": DATASET_SPLIT,
                "subset_seed": seed,
                "source_index": index,
                "question": question,
                "gold_answer": extract_gold(reference),
                "reference_solution": reference,
            }
        )
    return rows


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        for row in rows
    )


def refuse_overwrite(paths: Iterable[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"refusing to overwrite {rendered}; pass --force")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def main() -> None:
    args = parse_args()
    scan_roots = tuple(args.scan_roots or DEFAULT_SCAN_ROOTS)
    output_paths = (args.out, args.manifest, args.experiment_manifest)
    try:
        refuse_overwrite(output_paths, args.force)
        seen, scanned_files = collect_seen_indices(scan_roots)
        dataset = load_dataset(DATASET_ID, DATASET_CONFIG, split=DATASET_SPLIT)
        selected_indices = select_unseen_indices(
            len(dataset), seen, args.count, args.seed
        )
        rows = build_rows(dataset, selected_indices, args.seed)
    except (FileExistsError, ValueError) as error:
        raise SystemExit(str(error)) from error

    selected_ids = [row["id"] for row in rows]
    excluded_indices = sorted(index for index in seen if 0 <= index < len(dataset))
    excluded_ids = [f"{ITEM_PREFIX}{index}" for index in excluded_indices]
    overlap = sorted(set(selected_indices) & set(excluded_indices))
    if overlap:
        raise SystemExit(f"unseen selection overlaps excluded indices: {overlap}")
    if len(selected_ids) != len(set(selected_ids)):
        raise SystemExit("selected dataset contains duplicate IDs")

    dataset_payload = jsonl_bytes(rows)
    manifest: dict[str, Any] = {
        "manifest_version": "unseen-gsm8k-manifest-v1",
        "dataset": {
            "source": DATASET_ID,
            "configuration": DATASET_CONFIG,
            "split": DATASET_SPLIT,
            "dataset_version": str(dataset.info.version),
            "dataset_fingerprint": str(dataset._fingerprint),
            "total_split_rows": len(dataset),
        },
        "selection": {
            "seed": args.seed,
            "algorithm": SELECTION_ALGORITHM,
            "requested_count": args.count,
            "selected_count": len(rows),
            "selected_ids": selected_ids,
            "selected_source_indices": selected_indices,
        },
        "exclusion": {
            "scan_roots": [relative_display(path) for path in scan_roots],
            "scanned_jsonl_files": scanned_files,
            "scanned_jsonl_file_count": len(scanned_files),
            "excluded_ids": excluded_ids,
            "excluded_source_indices": excluded_indices,
            "excluded_count": len(excluded_indices),
            "excluded_set_sha256": sha256_bytes(canonical_json_bytes(excluded_ids)),
        },
        "artifact": {
            "path": relative_display(args.out),
            "sha256": sha256_bytes(dataset_payload),
            "bytes": len(dataset_payload),
        },
        "integrity": {
            "selected_ids_unique": len(selected_ids) == len(set(selected_ids)),
            "selected_excluded_overlap": overlap,
            "all_questions_nonempty": all(bool(row["question"].strip()) for row in rows),
            "all_gold_answers_numeric": all(
                canonical_number(row["gold_answer"]) is not None for row in rows
            ),
            "post_launch_exclusions": [],
        },
    }
    manifest_payload = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    write_bytes(args.out, dataset_payload)
    write_bytes(args.manifest, manifest_payload)
    write_bytes(args.experiment_manifest, manifest_payload)
    print(f"wrote {len(rows)} unseen rows to {args.out}")
    print(f"excluded {len(excluded_indices)} previously seen GSM8K items")
    print(f"dataset sha256 {manifest['artifact']['sha256']}")
    print(f"excluded-set sha256 {manifest['exclusion']['excluded_set_sha256']}")


if __name__ == "__main__":
    main()
