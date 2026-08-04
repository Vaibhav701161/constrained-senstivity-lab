#!/usr/bin/env python3
"""Run the FP32 Qwen2.5-7B representation-alignment targeted gate on Kaggle."""

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

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
RUN_SCOPE = "targeted"
MAX_NEW_TOKENS = 256
CONDITIONS = (
    "prompted_json_integer_reasoning_first",
    "outlines_json_integer_reasoning_first",
    "xgrammar_json_integer_reasoning_first",
    "xgrammar_json_unsigned_numeric_string_reasoning_first",
)
TRACE_ITEM_IDS = ("gsm8k_test_173", "gsm8k_test_1216", "gsm8k_test_12")
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
    for name in ("transformers", "accelerate", "datasets", "jsonschema", "outlines", "bitsandbytes", "xgrammar"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def main() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    input_root = Path("/kaggle/input")
    output_root = Path("/kaggle/working/results/representation-alignment-targeted")
    output_root.mkdir(parents=True, exist_ok=True)

    if shutil.which("nvidia-smi"):
        run(["nvidia-smi"])
    import torch

    print(
        json.dumps(
            {
                "preinstall_torch": torch.__version__,
                "preinstall_cuda_runtime": torch.version.cuda,
                "preinstall_cuda_available": torch.cuda.is_available(),
                "preinstall_packages": package_versions(),
            },
            indent=2,
        ),
        flush=True,
    )
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle did not attach a CUDA GPU to this run")

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

    source_runner = one_match(input_root, "run_representation_alignment.py")
    source_root = source_runner.parent
    runtime_root = Path("/kaggle/working/alignment-runtime")
    runtime_root.mkdir(parents=True, exist_ok=True)
    for name in (
        "run_evaluation.py",
        "run_representation_alignment.py",
        "summarize_alignment_gate.py",
    ):
        shutil.copy2(source_root / name, runtime_root / name)
    runtime_package_root = one_match(input_root, "schema_variants.py").parents[2]
    shutil.copytree(runtime_package_root / "src", runtime_root / "src")
    runner = runtime_root / "run_representation_alignment.py"
    summarizer = runtime_root / "summarize_alignment_gate.py"
    dataset = one_match(input_root, "targeted-items.jsonl")
    model_path = one_match(input_root, "config.json").parent
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
    manifest = {
        "experiment": "representation-alignment-targeted-v1",
        "scope": RUN_SCOPE,
        "started_at": datetime.now(UTC).isoformat(),
        "model": MODEL_ID,
        "model_path": str(model_path),
        "limit": 18,
        "conditions": list(CONDITIONS),
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
        "runner": str(runner),
        "runner_sha256": sha256(source_runner),
        "summarizer": str(summarizer),
        "summarizer_sha256": sha256(source_root / "summarize_alignment_gate.py"),
        "runtime_package": str(runtime_package_root),
        "runtime_schema_variants_sha256": sha256(
            runtime_package_root / "src/project_a/schema_variants.py"
        ),
        "dataset": str(dataset),
        "dataset_sha256": sha256(dataset),
    }
    (output_root / "kernel-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2), flush=True)

    result_files: list[Path] = []
    for condition in CONDITIONS:
        result_path = output_root / f"{condition}.jsonl"
        command = [
            sys.executable,
            str(runner),
            "--model",
            str(model_path),
            "--dataset",
            str(dataset),
            "--condition",
            condition,
            "--out",
            str(result_path),
            "--manifest-out",
            str(output_root / "manifests" / f"{condition}.json"),
            "--limit",
            "18",
            "--seed",
            "0",
            "--max-new-tokens",
            str(MAX_NEW_TOKENS),
            "--device-map-auto",
            "--dtype",
            "float32",
        ]
        if condition == "xgrammar_json_integer_reasoning_first":
            command.extend(
                [
                    "--trace-out",
                    str(output_root / "traces" / "xgrammar-integer-answer-boundary.jsonl"),
                ]
            )
            for item_id in TRACE_ITEM_IDS:
                command.extend(["--trace-item-id", item_id])
        run(command)
        result_files.append(result_path)

    run(
        [
            sys.executable,
            str(summarizer),
            *(str(path) for path in result_files),
            "--out-json",
            str(output_root / "summary.json"),
            "--out-md",
            str(output_root / "summary.md"),
        ]
    )
    print((output_root / "summary.md").read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
