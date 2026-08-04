#!/usr/bin/env python3
"""Run the controlled Qwen2.5-7B evaluation on Kaggle."""

from __future__ import annotations

import importlib.metadata
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
LIMIT = 50
MAX_NEW_TOKENS = 256
CONDITIONS = (
    "prompted_json_answer_first",
    "outlines_json_answer_first",
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


def file_sha256(path: Path) -> str:
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


def package_versions(names: tuple[str, ...]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
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
    output_root = Path("/kaggle/working/results/qwen2.5-7b-smoke")
    output_root.mkdir(parents=True, exist_ok=True)

    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        run([nvidia_smi])
    else:
        print("nvidia-smi is not installed; continuing to the PyTorch CUDA check")

    import torch

    print(
        json.dumps(
            {
                "preinstall_torch": torch.__version__,
                "preinstall_cuda_runtime": torch.version.cuda,
                "preinstall_cuda_available": torch.cuda.is_available(),
                "preinstall_packages": package_versions(
                    (
                        "transformers",
                        "accelerate",
                        "datasets",
                        "jsonschema",
                        "outlines",
                        "bitsandbytes",
                        "xgrammar",
                    )
                ),
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

    runner = one_match(input_root, "07_run_baseline.py")
    summarizer = one_match(input_root, "08_summarize_results.py")
    dataset = one_match(input_root, "gsm8k_50_seed0.jsonl")
    model_path = one_match(input_root, "config.json").parent

    probe_code = (
        "import json, torch; print(json.dumps({"
        "'torch': torch.__version__, 'cuda_runtime': torch.version.cuda, "
        "'cuda_available': torch.cuda.is_available(), "
        "'gpu_count': torch.cuda.device_count()}))"
    )
    runtime = json.loads(
        subprocess.check_output(
            [sys.executable, "-c", probe_code],
            text=True,
        )
    )
    if not runtime["cuda_available"]:
        raise RuntimeError(f"Pinned PyTorch cannot see CUDA: {runtime}")

    gpu = torch.cuda.get_device_properties(0)
    manifest = {
        "experiment": "v8-symbolic-template-answer-order-controls-fifty",
        "started_at": datetime.now(UTC).isoformat(),
        "model": MODEL_ID,
        "model_path": str(model_path),
        "limit": LIMIT,
        "conditions": list(CONDITIONS),
        "max_new_tokens": MAX_NEW_TOKENS,
        "seed": 0,
        "load_in_4bit": False,
        "device_map_auto": True,
        "dtype": "float32",
        "python": sys.version,
        "platform": platform.platform(),
        "torch": runtime["torch"],
        "cuda_runtime": runtime["cuda_runtime"],
        "gpu_count": runtime["gpu_count"],
        "gpu": gpu.name,
        "gpu_total_memory_bytes": gpu.total_memory,
        "packages": package_versions(
            (
                "transformers",
                "accelerate",
                "datasets",
                "jsonschema",
                "outlines",
                "bitsandbytes",
                "xgrammar",
            )
        ),
        "runner": str(runner),
        "runner_sha256": file_sha256(runner),
        "summarizer": str(summarizer),
        "summarizer_sha256": file_sha256(summarizer),
        "dataset": str(dataset),
        "dataset_sha256": file_sha256(dataset),
    }
    manifest_path = output_root / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)

    result_files: list[Path] = []
    for condition in CONDITIONS:
        result_path = output_root / f"{condition}.jsonl"
        run(
            [
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
                "--limit",
                str(LIMIT),
                "--seed",
                "0",
                "--max-new-tokens",
                str(MAX_NEW_TOKENS),
                "--device-map-auto",
                "--dtype",
                "float32",
            ]
        )
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
