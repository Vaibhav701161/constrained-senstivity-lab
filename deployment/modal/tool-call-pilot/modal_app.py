"""Modal execution surface for the bounded executable tool-call pilot."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import modal

REMOTE_ROOT = Path("/workspace")
MODULE_PATH = Path(__file__).resolve()
LOCAL_ROOT = MODULE_PATH.parents[3] if len(MODULE_PATH.parents) > 3 else REMOTE_ROOT
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
MODEL_REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"
GPU_TYPE = "L4"
MODEL_VOLUME_NAME = "contract-alignment-model-cache"
EVIDENCE_VOLUME_NAME = "contract-alignment-tool-call-evidence"
HF_SECRET_NAME = "huggingface-secret"

app = modal.App("contract-alignment-tool-call-pilot")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements(str(LOCAL_ROOT / "requirements.txt"))
    .pip_install("modal==1.5.3")
    .add_local_dir(LOCAL_ROOT / "src", str(REMOTE_ROOT / "src"), copy=True)
    .add_local_file(
        LOCAL_ROOT / "scripts/run_tool_call_pilot.py",
        str(REMOTE_ROOT / "scripts/run_tool_call_pilot.py"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "data/bfcl_tool_pilot_seed20260817.jsonl",
        str(REMOTE_ROOT / "data/bfcl_tool_pilot_seed20260817.jsonl"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "experiments/tool-call-gate/source-manifest.json",
        str(REMOTE_ROOT / "experiments/tool-call-gate/source-manifest.json"),
        copy=True,
    )
)

model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)
evidence_volume = modal.Volume.from_name(EVIDENCE_VOLUME_NAME, create_if_missing=True)
huggingface_secret = modal.Secret.from_name(HF_SECRET_NAME)

COMMON_ENV = {
    "HF_HOME": "/model-cache/huggingface",
    "HF_HUB_DISABLE_XET": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "PYTHONUNBUFFERED": "1",
    "PYTHONPATH": "/workspace/src",
}


def paths(representation: str) -> tuple[Path, Path]:
    condition = (
        "xgrammar_tool_internal_integers"
        if representation == "internal-integers"
        else "xgrammar_tool_external_integer_strings"
    )
    root = Path("/evidence/tool-call-gate")
    return (
        root / "results" / f"{condition}.jsonl",
        root / "manifests" / f"{condition}.json",
    )


@app.function(
    image=image,
    secrets=[huggingface_secret],
    gpu=GPU_TYPE,
    volumes={"/model-cache": model_volume, "/evidence": evidence_volume},
    env={**COMMON_ENV, "PROJECT_A_MODAL_EVIDENCE_VOLUME": EVIDENCE_VOLUME_NAME},
    cpu=4,
    memory=32768,
    timeout=7200,
    scaledown_window=300,
)
def run_condition(
    *, representation: str, limit: int, resume: bool
) -> dict[str, Any]:
    if representation not in {"external-integer-strings", "internal-integers"}:
        raise ValueError(f"unsupported representation: {representation}")
    output, manifest = paths(representation)
    command = [
        sys.executable,
        str(REMOTE_ROOT / "scripts/run_tool_call_pilot.py"),
        "--model",
        MODEL_ID,
        "--revision",
        MODEL_REVISION,
        "--dataset",
        str(REMOTE_ROOT / "data/bfcl_tool_pilot_seed20260817.jsonl"),
        "--representation",
        representation,
        "--out",
        str(output),
        "--manifest-out",
        str(manifest),
        "--source-manifest",
        str(REMOTE_ROOT / "experiments/tool-call-gate/source-manifest.json"),
        "--limit",
        str(limit),
        "--seed",
        "0",
        "--max-new-tokens",
        "192",
        "--dtype",
        "float32",
        "--device-map-auto",
    ]
    if resume:
        command.append("--resume")
    completed = subprocess.run(
        command,
        cwd=REMOTE_ROOT,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    evidence_volume.commit()
    if completed.returncode != 0:
        raise RuntimeError(
            f"runner exited {completed.returncode}\n{completed.stdout[-12000:]}"
        )
    rows = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "gpu_type": GPU_TYPE,
        "representation": representation,
        "requested_limit": limit,
        "rows": len(rows),
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "internal_invalid": sum(row.get("internal_schema_valid") is not True for row in rows),
        "external_invalid": sum(row.get("external_schema_valid") is not True for row in rows),
        "execution_failures": sum(row.get("execution_success") is not True for row in rows),
        "output": str(output),
        "manifest": str(manifest),
        "stdout_tail": completed.stdout[-5000:],
    }


@app.local_entrypoint()
def execute(
    representation: str,
    limit: int,
    resume: bool = False,
) -> None:
    report = run_condition.remote(
        representation=representation,
        limit=limit,
        resume=resume,
    )
    print(json.dumps(report, indent=2))
