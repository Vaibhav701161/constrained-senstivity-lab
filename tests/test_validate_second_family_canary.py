from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_second_family_canary.py"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def build_fixture(root: Path) -> list[str]:
    dataset = root / "dataset.jsonl"
    dataset_rows = [{"id": f"item-{index}"} for index in range(5)]
    write_jsonl(dataset, dataset_rows)
    dataset_hash = hashlib.sha256(dataset.read_bytes()).hexdigest()
    dataset_manifest = root / "dataset-manifest.json"
    write_json(dataset_manifest, {"selected_dataset": {"sha256": dataset_hash}})
    source_manifest = root / "source-manifest.json"
    write_json(source_manifest, {"model_revision": "frozen-revision"})
    source_hash = hashlib.sha256(source_manifest.read_bytes()).hexdigest()

    base_config = {
        "model": "model",
        "revision": "frozen-revision",
        "dataset_sha256": dataset_hash,
        "condition": "condition",
        "answer_representation": "representation",
        "internal_schema_sha256": "internal",
        "transducer_version": None,
        "plan_id": "plan",
    }
    paths: dict[str, Path] = {}
    for name, representation in (
        ("control", "signed-numeric-string"),
        ("treatment", "integer"),
    ):
        paths[f"{name}_results"] = root / f"{name}.jsonl"
        rows = [
            {
                "item_id": row["id"],
                "run_signature": f"{name}-signature",
                "dataset_sha256": dataset_hash,
                "effective_chat_template_depth": 1,
                "raw_output": "{}",
                "error": None,
                "hit_max_new_tokens": False,
                "internal_schema_valid": True,
                "external_schema_valid": True,
                "model_revision": "frozen-revision",
                "tokenizer_revision": "frozen-revision",
                "semantic_correct": False,
                "contract_valid_correct": False,
            }
            for row in dataset_rows
        ]
        write_jsonl(paths[f"{name}_results"], rows)
        paths[f"{name}_manifest"] = root / f"{name}-manifest.json"
        config = {
            **base_config,
            "condition": f"{name}-condition",
            "answer_representation": representation,
            "internal_schema_sha256": f"{name}-internal",
            "transducer_version": "v1" if name == "treatment" else None,
            "plan_id": f"{name}-plan",
        }
        write_json(
            paths[f"{name}_manifest"],
            {
                "run_config": config,
                "packages": {"torch": "2.6.0"},
                "gpus": [{"name": "L4"}],
                "source_manifest_sha256": source_hash,
            },
        )
    output = root / "gate.json"
    return [
        "--dataset",
        str(dataset),
        "--dataset-manifest",
        str(dataset_manifest),
        "--source-manifest",
        str(source_manifest),
        "--control-results",
        str(paths["control_results"]),
        "--control-manifest",
        str(paths["control_manifest"]),
        "--treatment-results",
        str(paths["treatment_results"]),
        "--treatment-manifest",
        str(paths["treatment_manifest"]),
        "--out",
        str(output),
    ]


def test_operational_canary_does_not_gate_on_semantic_success(tmp_path: Path) -> None:
    command = [sys.executable, str(SCRIPT), *build_fixture(tmp_path)]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((tmp_path / "gate.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["semantic_outcomes_inspected"] is False


def test_operational_canary_fails_on_empty_generation(tmp_path: Path) -> None:
    arguments = build_fixture(tmp_path)
    rows = [
        json.loads(line)
        for line in (tmp_path / "treatment.jsonl").read_text().splitlines()
    ]
    rows[2]["raw_output"] = ""
    write_jsonl(tmp_path / "treatment.jsonl", rows)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    report = json.loads((tmp_path / "gate.json").read_text(encoding="utf-8"))
    assert report["checks"]["nonempty_outputs"] is False
