#!/usr/bin/env python3
"""Print a machine-readable probe of the local evaluation environment."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
import sys
from typing import Any

PACKAGES = (
    "torch",
    "transformers",
    "accelerate",
    "datasets",
    "jsonschema",
    "outlines",
)


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def nvidia_smi() -> dict[str, str] | None:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.free",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None

    first_line = completed.stdout.strip().splitlines()[0]
    name, driver, total_mib, free_mib = [part.strip() for part in first_line.split(",")]
    return {
        "name": name,
        "driver_version": driver,
        "total_vram_mib": total_mib,
        "free_vram_mib": free_mib,
    }


def torch_probe() -> dict[str, Any]:
    try:
        import torch
    except ImportError as exc:
        return {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}

    result: dict[str, Any] = {
        "import_ok": True,
        "version": torch.__version__,
        "cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
    }
    if not torch.cuda.is_available():
        return result

    try:
        device = torch.device("cuda:0")
        left = torch.arange(16, dtype=torch.float32, device=device).reshape(4, 4)
        right = torch.eye(4, dtype=torch.float32, device=device)
        product = left @ right
        torch.cuda.synchronize(device)
        free_bytes, total_bytes = torch.cuda.mem_get_info(device)
        properties = torch.cuda.get_device_properties(device)
        result.update(
            {
                "device_name": torch.cuda.get_device_name(device),
                "compute_capability": f"{properties.major}.{properties.minor}",
                "total_vram_gib": round(total_bytes / 1024**3, 3),
                "free_vram_gib": round(free_bytes / 1024**3, 3),
                "cuda_tensor_test": bool(torch.equal(product.cpu(), left.cpu())),
            }
        )
    except Exception as exc:  # noqa: BLE001 - a probe must report arbitrary CUDA failures.
        result["cuda_tensor_test"] = False
        result["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    result = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "packages": {name: package_version(name) for name in PACKAGES},
        "nvidia_smi": nvidia_smi(),
        "torch": torch_probe(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
