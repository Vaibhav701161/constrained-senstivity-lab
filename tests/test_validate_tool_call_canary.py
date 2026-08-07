from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_tool_call_canary.py"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_canary_does_not_gate_on_argument_correctness(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    write_jsonl(dataset, [{"id": f"item-{index}"} for index in range(3)])
    dataset_hash = hashlib.sha256(dataset.read_bytes()).hexdigest()
    dataset_manifest = tmp_path / "dataset-manifest.json"
    write_json(dataset_manifest, {"artifact": {"sha256": dataset_hash}})
    source = tmp_path / "source.json"
    write_json(source, {"model_revision": "revision"})
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    paths = {}
    base = {
        "model": "model",
        "revision": "revision",
        "dataset_sha256": dataset_hash,
        "seed": 0,
    }
    for role, representation in (("control", "external-integer-strings"), ("treatment", "internal-integers")):
        results = tmp_path / f"{role}.jsonl"
        rows = [
            {
                "item_id": f"item-{index}",
                "run_signature": role,
                "dataset_sha256": dataset_hash,
                "effective_chat_template_depth": 1,
                "raw_output": "{}",
                "error": None,
                "hit_max_new_tokens": False,
                "internal_schema_valid": True,
                "external_schema_valid": True,
                "execution_success": True,
                "heuristic_repair_count": 0,
                "argument_semantics_correct": False,
                "model_revision": "revision",
                "tokenizer_revision": "revision",
            }
            for index in range(3)
        ]
        write_jsonl(results, rows)
        manifest = tmp_path / f"{role}.json"
        config = {
            **base,
            "condition": role,
            "representation": representation,
            "model_uses_integers": role == "treatment",
            "transducer_version": "v1" if role == "treatment" else None,
        }
        write_json(
            manifest,
            {
                "run_config": config,
                "python": "3.12",
                "torch": "2.6",
                "cuda_runtime": "12.4",
                "gpus": [{"name": "L4"}],
                "packages": {},
                "source_manifest_sha256": source_hash,
            },
        )
        paths[f"{role}_results"] = results
        paths[f"{role}_manifest"] = manifest
    out = tmp_path / "gate.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dataset",
            str(dataset),
            "--dataset-manifest",
            str(dataset_manifest),
            "--source-manifest",
            str(source),
            "--control-results",
            str(paths["control_results"]),
            "--control-manifest",
            str(paths["control_manifest"]),
            "--treatment-results",
            str(paths["treatment_results"]),
            "--treatment-manifest",
            str(paths["treatment_manifest"]),
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["semantic_outcomes_inspected"] is False
