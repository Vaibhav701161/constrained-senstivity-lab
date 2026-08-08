"""Modal execution surface for the preregistered second-family replication."""

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
GPU_TYPE = "L4"
MODEL_VOLUME_NAME = "contract-alignment-model-cache"
EVIDENCE_VOLUME_NAME = "contract-alignment-second-family-evidence"
HF_SECRET_NAME = "huggingface-secret"

app = modal.App("contract-alignment-second-family")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements(str(LOCAL_ROOT / "requirements.txt"))
    .pip_install("modal==1.5.3")
    .add_local_dir(LOCAL_ROOT / "src", str(REMOTE_ROOT / "src"), copy=True)
    .add_local_file(
        LOCAL_ROOT / "scripts/run_contract_alignment.py",
        str(REMOTE_ROOT / "scripts/run_contract_alignment.py"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "data/gsm8k_unseen_150_seed20260815.jsonl",
        str(REMOTE_ROOT / "data/gsm8k_unseen_150_seed20260815.jsonl"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "data/gsm8k_50_seed0.jsonl",
        str(REMOTE_ROOT / "data/gsm8k_50_seed0.jsonl"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "tests/test_llama_prompt_parity.py",
        str(REMOTE_ROOT / "tests/test_llama_prompt_parity.py"),
        copy=True,
    )
    .add_local_file(
        LOCAL_ROOT / "experiments/second-family-replication/source-manifest.json",
        str(
            REMOTE_ROOT
            / "experiments/second-family-replication/source-manifest.json"
        ),
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


@app.function(
    image=image,
    secrets=[huggingface_secret],
    volumes={"/model-cache": model_volume},
    env=COMMON_ENV,
    cpu=2,
    memory=8192,
    timeout=1800,
)
def probe_model_access() -> dict[str, Any]:
    """Resolve the immutable revision and prove Llama prompt parity without a GPU."""

    from huggingface_hub import model_info
    from outlines.models.transformers import TransformersTypeAdapter
    from project_a.runtime import (
        RuntimeRepresentation,
        format_chat_prompt,
        make_contract_prompt,
        package_versions,
    )
    from transformers import AutoTokenizer

    info = model_info(MODEL_ID, revision="main")
    revision = str(info.sha)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=revision)
    parity: dict[str, Any] = {}
    for representation in RuntimeRepresentation:
        raw = make_contract_prompt("What is 2 + 2?", representation)
        direct = format_chat_prompt(tokenizer, raw)
        outlines = TransformersTypeAdapter(
            tokenizer, has_chat_template=True
        ).format_input(raw)
        nested = TransformersTypeAdapter(
            tokenizer, has_chat_template=True
        ).format_input(direct)
        direct_ids = tokenizer(direct, add_special_tokens=False)["input_ids"]
        outlines_ids = tokenizer(outlines, add_special_tokens=False)["input_ids"]
        nested_ids = tokenizer(nested, add_special_tokens=False)["input_ids"]
        parity[representation.value] = {
            "effective_prompt_equal": direct == outlines,
            "effective_token_ids_equal": direct_ids == outlines_ids,
            "nested_token_ids_differ": nested_ids != direct_ids,
            "effective_prompt_tokens": len(direct_ids),
        }
    parity_checks = [
        checks[key]
        for checks in parity.values()
        for key in (
            "effective_prompt_equal",
            "effective_token_ids_equal",
            "nested_token_ids_differ",
        )
    ]
    if not all(parity_checks):
        raise RuntimeError(f"Llama prompt parity failed: {parity}")

    test_env = {
        **os.environ,
        "RUN_LLAMA_PROMPT_PARITY": "1",
        "LLAMA_MODEL_REVISION": revision,
    }
    tests = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(REMOTE_ROOT / "tests/test_llama_prompt_parity.py"),
        ],
        cwd=REMOTE_ROOT,
        env=test_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if tests.returncode != 0:
        raise RuntimeError(f"Llama prompt parity tests failed\n{tests.stdout}")
    model_volume.commit()
    return {
        "model": MODEL_ID,
        "revision": revision,
        "tokenizer_revision": tokenizer.init_kwargs.get("_commit_hash", revision),
        "parity": parity,
        "parity_test_output": tests.stdout.strip(),
        "packages": package_versions(),
        "python": sys.version,
    }


def condition_paths(dataset_role: str, representation: str) -> tuple[Path, Path, Path]:
    condition = (
        "xgrammar_json_integer_reasoning_first"
        if representation == "integer"
        else "xgrammar_json_reasoning_first"
    )
    root = Path("/evidence/second-family-replication")
    return (
        root / "results" / dataset_role / f"{condition}.jsonl",
        root / "manifests" / dataset_role / f"{condition}.json",
        root / "traces" / dataset_role / f"{condition}.jsonl",
    )


def parity_paths(representation: str) -> tuple[Path, Path]:
    condition = (
        "outlines_json_integer_reasoning_first"
        if representation == "integer"
        else "outlines_json_reasoning_first"
    )
    root = Path("/evidence/second-family-replication")
    return (
        root / "results" / "parity" / f"{condition}.jsonl",
        root / "manifests" / "parity" / f"{condition}.json",
    )


@app.function(
    image=image,
    secrets=[huggingface_secret],
    gpu=GPU_TYPE,
    volumes={
        "/model-cache": model_volume,
        "/evidence": evidence_volume,
    },
    env={**COMMON_ENV, "PROJECT_A_MODAL_EVIDENCE_VOLUME": EVIDENCE_VOLUME_NAME},
    cpu=4,
    memory=32768,
    timeout=14400,
    scaledown_window=300,
)
def run_condition(
    *,
    revision: str,
    dataset_role: str,
    representation: str,
    limit: int,
    resume: bool,
    trace_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run one registered condition and persist every completed row."""

    if dataset_role not in {"fresh", "bridge"}:
        raise ValueError(f"unsupported dataset role: {dataset_role}")
    if representation not in {"signed-numeric-string", "integer"}:
        raise ValueError(f"unsupported representation: {representation}")
    dataset = (
        REMOTE_ROOT / "data/gsm8k_unseen_150_seed20260815.jsonl"
        if dataset_role == "fresh"
        else REMOTE_ROOT / "data/gsm8k_50_seed0.jsonl"
    )
    output, manifest, trace = condition_paths(dataset_role, representation)
    command = [
        sys.executable,
        str(REMOTE_ROOT / "scripts/run_contract_alignment.py"),
        "--model",
        MODEL_ID,
        "--revision",
        revision,
        "--dataset",
        str(dataset),
        "--dataset-role",
        dataset_role,
        "--representation",
        representation,
        "--backend",
        "xgrammar",
        "--out",
        str(output),
        "--manifest-out",
        str(manifest),
        "--source-manifest",
        str(
            REMOTE_ROOT
            / "experiments/second-family-replication/source-manifest.json"
        ),
        "--limit",
        str(limit),
        "--seed",
        "0",
        "--max-new-tokens",
        "256",
        "--dtype",
        "float32",
        "--device-map-auto",
    ]
    if dataset_role == "bridge":
        command.extend(["--exclude-item-id", "gsm8k_test_454"])
    if resume:
        command.append("--resume")
    for item_id in trace_item_ids or []:
        command.extend(["--trace-item-id", item_id])
    if trace_item_ids:
        command.extend(["--trace-out", str(trace)])

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
        "dataset_role": dataset_role,
        "representation": representation,
        "requested_limit": limit,
        "rows": len(rows),
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "internal_invalid": sum(
            not bool(row.get("internal_schema_valid")) for row in rows
        ),
        "external_invalid": sum(
            not bool(row.get("external_schema_valid")) for row in rows
        ),
        "output": str(output),
        "manifest": str(manifest),
        "stdout_tail": completed.stdout[-4000:],
    }


@app.function(
    image=image,
    secrets=[huggingface_secret],
    gpu=GPU_TYPE,
    volumes={
        "/model-cache": model_volume,
        "/evidence": evidence_volume,
    },
    env={**COMMON_ENV, "PROJECT_A_MODAL_EVIDENCE_VOLUME": EVIDENCE_VOLUME_NAME},
    cpu=4,
    memory=32768,
    timeout=14400,
    scaledown_window=300,
)
def run_outlines_parity(
    *,
    revision: str,
    representation: str,
    item_ids: list[str],
    resume: bool,
) -> dict[str, Any]:
    """Run the post-result implementation-parity subset through Outlines."""

    if representation not in {"signed-numeric-string", "integer"}:
        raise ValueError(f"unsupported representation: {representation}")
    if not item_ids or len(item_ids) != len(set(item_ids)):
        raise ValueError("parity item IDs must be nonempty and unique")
    source_rows = [
        json.loads(line)
        for line in (
            REMOTE_ROOT / "data/gsm8k_unseen_150_seed20260815.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    wanted = set(item_ids)
    selected = [row for row in source_rows if str(row["id"]) in wanted]
    selected_ids = [str(row["id"]) for row in selected]
    if selected_ids != item_ids:
        raise ValueError("parity IDs are missing or not in frozen dataset order")
    dataset = Path("/evidence/second-family-replication/parity-dataset.jsonl")
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected)
    if dataset.exists() and dataset.read_text(encoding="utf-8") != payload:
        raise ValueError("refusing to replace a different frozen parity dataset")
    dataset.parent.mkdir(parents=True, exist_ok=True)
    if not dataset.exists():
        dataset.write_text(payload, encoding="utf-8")
        evidence_volume.commit()

    output, manifest = parity_paths(representation)
    command = [
        sys.executable,
        str(REMOTE_ROOT / "scripts/run_contract_alignment.py"),
        "--model",
        MODEL_ID,
        "--revision",
        revision,
        "--dataset",
        str(dataset),
        "--dataset-role",
        "parity",
        "--representation",
        representation,
        "--backend",
        "outlines",
        "--out",
        str(output),
        "--manifest-out",
        str(manifest),
        "--source-manifest",
        str(
            REMOTE_ROOT
            / "experiments/second-family-replication/source-manifest.json"
        ),
        "--limit",
        str(len(item_ids)),
        "--seed",
        "0",
        "--max-new-tokens",
        "256",
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
        "rows": len(rows),
        "selected_item_ids": item_ids,
        "errors": sum(row.get("error") is not None for row in rows),
        "cap_hits": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "output": str(output),
        "manifest": str(manifest),
        "stdout_tail": completed.stdout[-4000:],
    }


@app.local_entrypoint()
def probe() -> None:
    print(json.dumps(probe_model_access.remote(), indent=2))


@app.local_entrypoint()
def execute(
    revision: str,
    dataset_role: str,
    representation: str,
    limit: int,
    resume: bool = False,
) -> None:
    report = run_condition.remote(
        revision=revision,
        dataset_role=dataset_role,
        representation=representation,
        limit=limit,
        resume=resume,
        trace_item_ids=[],
    )
    print(json.dumps(report, indent=2))


@app.local_entrypoint()
def execute_parity(
    revision: str,
    representation: str,
    item_ids_json: str,
    resume: bool = False,
) -> None:
    item_ids = json.loads(item_ids_json)
    if not isinstance(item_ids, list) or not all(
        isinstance(item, str) for item in item_ids
    ):
        raise ValueError("item_ids_json must encode a list of strings")
    report = run_outlines_parity.remote(
        revision=revision,
        representation=representation,
        item_ids=item_ids,
        resume=resume,
    )
    print(json.dumps(report, indent=2))
