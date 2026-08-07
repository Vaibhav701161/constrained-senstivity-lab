#!/usr/bin/env python3
"""Run the preregistered corrected 7B representation-alignment replication."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_SOURCE = "qwen-lm/qwen2.5/transformers/7b-instruct/1"
EXPERIMENT_ID = "contract-alignment-corrected-replication-v1"
CANARY_LIMIT = 5
FULL_LIMIT = 50
MAX_NEW_TOKENS = 256
EXCLUDED_ITEM_IDS = ("gsm8k_test_454",)
TRACE_ITEM_IDS = ("gsm8k_test_173", "gsm8k_test_1216", "gsm8k_test_12")
CONDITIONS = (
    {
        "name": "outlines_json_reasoning_first",
        "runner": "external",
        "backend": "outlines",
        "representation": "signed_numeric_string",
    },
    {
        "name": "xgrammar_json_reasoning_first",
        "runner": "external",
        "backend": "xgrammar",
        "representation": "signed_numeric_string",
    },
    {
        "name": "outlines_json_integer_reasoning_first",
        "runner": "integer",
        "backend": "outlines",
        "representation": "integer",
    },
    {
        "name": "xgrammar_json_integer_reasoning_first",
        "runner": "integer",
        "backend": "xgrammar",
        "representation": "integer",
    },
)
PACKAGES = (
    "transformers==4.51.3",
    "accelerate==1.6.0",
    "datasets==3.6.0",
    "jsonschema==4.23.0",
    "outlines==1.3.2",
    "bitsandbytes==0.45.5",
    "xgrammar==0.2.3",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> None:
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, check=True, env=os.environ.copy())


def one_match(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {name} under {root}, found {matches}")
    return matches[0]


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in (
        "transformers",
        "accelerate",
        "datasets",
        "jsonschema",
        "outlines",
        "bitsandbytes",
        "xgrammar",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"{path}:{line_number}: expected an object")
            rows.append(value)
    return rows


def schema_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("internal_schema_valid", row.get("schema_valid")))


def external_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("external_schema_valid", row.get("schema_valid")))


def validate_stage(
    output_root: Path,
    dataset: Path,
    expected_limit: int,
    stage: str,
) -> dict[str, Any]:
    expected_items = [
        str(row["id"]) for row in read_jsonl(dataset)[:expected_limit]
    ]
    failures: list[str] = []
    condition_reports: dict[str, Any] = {}
    prompt_hashes: dict[str, dict[str, str]] = {}

    for spec in CONDITIONS:
        name = str(spec["name"])
        path = output_root / f"{name}.jsonl"
        rows = read_jsonl(path)
        item_ids = [str(row.get("item_id")) for row in rows]
        if len(rows) != expected_limit:
            failures.append(f"{name}: expected {expected_limit} rows, found {len(rows)}")
        if item_ids != expected_items:
            failures.append(f"{name}: item IDs or order differ from the frozen dataset")
        if len(set(item_ids)) != len(item_ids):
            failures.append(f"{name}: duplicate item IDs")
        signatures = {str(row.get("run_signature")) for row in rows}
        run_ids = {str(row.get("run_id")) for row in rows}
        errors = sum(row.get("error") is not None for row in rows)
        cap_hits = sum(bool(row.get("hit_max_new_tokens")) for row in rows)
        blank_outputs = sum(not str(row.get("raw_output", "")).strip() for row in rows)
        internal_invalid = sum(not schema_valid(row) for row in rows)
        external_invalid = sum(not external_valid(row) for row in rows)
        if len(signatures) != 1:
            failures.append(f"{name}: expected one run signature, found {sorted(signatures)}")
        if len(run_ids) != 1:
            failures.append(f"{name}: expected one run ID, found {sorted(run_ids)}")
        if errors:
            failures.append(f"{name}: {errors} generation errors")
        if cap_hits:
            failures.append(f"{name}: {cap_hits} token-cap hits")
        if blank_outputs:
            failures.append(f"{name}: {blank_outputs} blank outputs")
        if internal_invalid:
            failures.append(f"{name}: {internal_invalid} model-facing schema failures")
        if external_invalid:
            failures.append(f"{name}: {external_invalid} final external-schema failures")

        prompt_hashes[name] = {
            str(row["item_id"]): hashlib.sha256(
                str(row["formatted_prompt"]).encode("utf-8")
            ).hexdigest()
            for row in rows
        }
        condition_reports[name] = {
            "rows": len(rows),
            "unique_item_ids": len(set(item_ids)),
            "run_signature": next(iter(signatures), None),
            "run_id": next(iter(run_ids), None),
            "errors": errors,
            "cap_hits": cap_hits,
            "blank_outputs": blank_outputs,
            "internal_invalid": internal_invalid,
            "external_invalid": external_invalid,
            "sha256": sha256(path),
        }

    equivalent_pairs = (
        ("outlines_json_reasoning_first", "xgrammar_json_reasoning_first"),
        (
            "outlines_json_integer_reasoning_first",
            "xgrammar_json_integer_reasoning_first",
        ),
    )
    for left, right in equivalent_pairs:
        if prompt_hashes.get(left) != prompt_hashes.get(right):
            failures.append(f"effective prompts differ between {left} and {right}")

    report = {
        "gate_version": "corrected-replication-operational-gate-v1",
        "stage": stage,
        "checked_at": datetime.now(UTC).isoformat(),
        "expected_limit": expected_limit,
        "passed": not failures,
        "failures": failures,
        "conditions": condition_reports,
        "prompt_equivalence_pairs": [list(pair) for pair in equivalent_pairs],
    }
    report_path = output_root / f"{stage}-gate.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    if failures:
        raise RuntimeError(f"{stage} gate failed: {failures}")
    return report


def runner_command(
    spec: dict[str, str],
    runners: dict[str, Path],
    model_path: Path,
    dataset: Path,
    output_root: Path,
    limit: int,
    resume: bool,
) -> list[str]:
    name = spec["name"]
    command = [
        sys.executable,
        str(runners[spec["runner"]]),
        "--model",
        str(model_path),
        "--dataset",
        str(dataset),
        "--condition",
        name,
        "--out",
        str(output_root / f"{name}.jsonl"),
        "--limit",
        str(limit),
        "--seed",
        "0",
        "--max-new-tokens",
        str(MAX_NEW_TOKENS),
        "--device-map-auto",
        "--dtype",
        "float32",
        "--manifest-out",
        str(output_root / "manifests" / f"{name}.json"),
    ]
    if spec["runner"] == "integer":
        command.extend(
            [
                "--plan-id",
                "integer-string-representation-v1",
            ]
        )
    if name == "xgrammar_json_integer_reasoning_first":
        command.extend(
            [
                "--trace-out",
                str(output_root / "traces" / "xgrammar-integer-answer-boundary.jsonl"),
            ]
        )
        for item_id in TRACE_ITEM_IDS:
            command.extend(["--trace-item-id", item_id])
    if resume:
        command.append("--resume")
    return command


def main() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    input_root = Path("/kaggle/input")
    output_root = Path("/kaggle/working/results/corrected-replication")
    output_root.mkdir(parents=True, exist_ok=True)

    if shutil.which("nvidia-smi"):
        run(["nvidia-smi"])
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle did not attach a CUDA GPU")
    print(
        json.dumps(
            {
                "preinstall_torch": torch.__version__,
                "preinstall_cuda_runtime": torch.version.cuda,
                "preinstall_packages": package_versions(),
            },
            indent=2,
        ),
        flush=True,
    )

    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--force-reinstall",
            "torch==2.6.0",
            "--index-url",
            "https://download.pytorch.org/whl/cu124",
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "--yes",
            "torchvision",
            "torchaudio",
            "torchcodec",
        ]
    )
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            *PACKAGES,
        ]
    )

    source_external = one_match(input_root, "run_evaluation.py")
    source_integer = one_match(input_root, "run_representation_alignment.py")
    source_summarizer = one_match(input_root, "summarize_alignment_gate.py")
    source_manifest = one_match(input_root, "source-manifest.json")
    dataset = one_match(input_root, "gsm8k_50_seed0.jsonl")
    model_path = one_match(input_root, "config.json").parent
    runtime_package_root = one_match(input_root, "schema_variants.py").parents[2]
    runtime_root = Path("/kaggle/working/corrected-runtime")
    runtime_root.mkdir(parents=True, exist_ok=True)
    for source in (source_external, source_integer, source_summarizer):
        shutil.copy2(source, runtime_root / source.name)
    shutil.copytree(runtime_package_root / "src", runtime_root / "src")
    runners = {
        "external": runtime_root / "run_evaluation.py",
        "integer": runtime_root / "run_representation_alignment.py",
    }
    summarizer = runtime_root / "summarize_alignment_gate.py"

    expected_source = json.loads(source_manifest.read_text(encoding="utf-8"))
    actual_source = {
        "run_evaluation.py": sha256(source_external),
        "run_representation_alignment.py": sha256(source_integer),
        "summarize_alignment_gate.py": sha256(source_summarizer),
        "gsm8k_50_seed0.jsonl": sha256(dataset),
    }
    for name, digest in actual_source.items():
        if expected_source["files"].get(name) != digest:
            raise RuntimeError(f"source hash mismatch for {name}")

    runtime = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                "-c",
                "import json, torch; print(json.dumps({'torch': torch.__version__, 'cuda_runtime': torch.version.cuda, 'cuda_available': torch.cuda.is_available(), 'gpu_count': torch.cuda.device_count()}))",
            ],
            text=True,
        )
    )
    if not runtime["cuda_available"]:
        raise RuntimeError(f"Pinned PyTorch cannot see CUDA: {runtime}")

    gpu = torch.cuda.get_device_properties(0)
    kernel_manifest = {
        "experiment": EXPERIMENT_ID,
        "started_at": datetime.now(UTC).isoformat(),
        "question": "Does internal integer generation improve contract-valid correctness over corrected signed-string generation?",
        "model": MODEL_ID,
        "model_source": MODEL_SOURCE,
        "model_path": str(model_path),
        "canary_limit": CANARY_LIMIT,
        "full_limit": FULL_LIMIT,
        "excluded_item_ids": list(EXCLUDED_ITEM_IDS),
        "conditions": CONDITIONS,
        "max_new_tokens": MAX_NEW_TOKENS,
        "seed": 0,
        "dtype": "float32",
        "device_map_auto": True,
        "python": sys.version,
        "platform": platform.platform(),
        "torch": runtime["torch"],
        "cuda_runtime": runtime["cuda_runtime"],
        "gpu_count": runtime["gpu_count"],
        "gpu": gpu.name,
        "gpu_total_memory_bytes": gpu.total_memory,
        "packages": package_versions(),
        "kernel_source_sha256": sha256(Path(__file__)),
        "source_manifest_sha256": sha256(source_manifest),
        "source_hashes": actual_source,
        "dataset_sha256": sha256(dataset),
    }
    (output_root / "kernel-manifest.json").write_text(
        json.dumps(kernel_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(kernel_manifest, indent=2), flush=True)

    for spec in CONDITIONS:
        run(
            runner_command(
                spec,
                runners,
                model_path,
                dataset,
                output_root,
                CANARY_LIMIT,
                resume=False,
            )
        )
    validate_stage(output_root, dataset, CANARY_LIMIT, "canary")

    for spec in CONDITIONS:
        run(
            runner_command(
                spec,
                runners,
                model_path,
                dataset,
                output_root,
                FULL_LIMIT,
                resume=True,
            )
        )
    validate_stage(output_root, dataset, FULL_LIMIT, "full")

    result_paths = [output_root / f"{spec['name']}.jsonl" for spec in CONDITIONS]
    run(
        [
            sys.executable,
            str(summarizer),
            *(str(path) for path in result_paths),
            "--exclude-item-id",
            EXCLUDED_ITEM_IDS[0],
            "--comparison",
            "outlines_integer_vs_signed",
            "outlines_json_integer_reasoning_first",
            "outlines_json_reasoning_first",
            "--comparison",
            "xgrammar_integer_vs_signed",
            "xgrammar_json_integer_reasoning_first",
            "xgrammar_json_reasoning_first",
            "--out-json",
            str(output_root / "paired-summary.json"),
            "--out-md",
            str(output_root / "paired-summary.md"),
        ]
    )
    print((output_root / "paired-summary.md").read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
