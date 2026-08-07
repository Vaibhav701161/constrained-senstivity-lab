from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_second_family_artifacts.py"
REVISION = "frozen-revision"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(config: dict[str, object]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def build_fixture(root: Path) -> list[str]:
    source_root = root / "source"
    frozen = source_root / "frozen.py"
    frozen.parent.mkdir(parents=True)
    frozen.write_text("VALUE = 1\n", encoding="utf-8")
    source_manifest = (
        source_root / "experiments/second-family-replication/source-manifest.json"
    )
    write_json(
        source_manifest,
        {
            "model_revision": REVISION,
            "files": [
                {"path": "frozen.py", "sha256": digest(frozen), "bytes": frozen.stat().st_size}
            ],
        },
    )
    source_hash = digest(source_manifest)

    fresh_dataset = root / "fresh.jsonl"
    bridge_dataset = root / "bridge.jsonl"
    write_jsonl(fresh_dataset, [{"id": f"fresh-{i}"} for i in range(150)])
    write_jsonl(
        bridge_dataset,
        [{"id": f"bridge-{i}"} for i in range(49)]
        + [{"id": "gsm8k_test_454"}],
    )
    run_dir = root / "run"
    conditions = {
        "xgrammar_json_reasoning_first": "signed-numeric-string",
        "xgrammar_json_integer_reasoning_first": "integer",
    }
    for role, dataset, excluded in (
        ("fresh", fresh_dataset, []),
        ("bridge", bridge_dataset, ["gsm8k_test_454"]),
    ):
        ids = [
            row["id"]
            for row in [json.loads(line) for line in dataset.read_text().splitlines()]
            if row["id"] not in excluded
        ]
        for condition, representation in conditions.items():
            config = {
                "model": "meta-llama/Llama-3.2-3B-Instruct",
                "revision": REVISION,
                "dataset_sha256": digest(dataset),
                "excluded_item_ids": excluded,
                "condition": condition,
                "answer_representation": representation,
                "internal_schema_sha256": f"internal-{representation}",
                "transducer_version": "v1" if representation == "integer" else None,
                "plan_id": f"plan-{representation}",
                "seed": 0,
                "do_sample": False,
                "dtype": "float32",
                "max_new_tokens": 256,
                "backend": "xgrammar",
            }
            run_signature = signature(config)
            rows = [
                {
                    "item_id": item_id,
                    "run_signature": run_signature,
                    "run_id": f"run-{role}-{representation}",
                    "model_revision": REVISION,
                    "tokenizer_revision": REVISION,
                    "condition": condition,
                    "answer_representation": representation,
                    "effective_chat_template_depth": 1,
                    "error": None,
                    "hit_max_new_tokens": False,
                    "internal_schema_valid": True,
                    "external_schema_valid": True,
                }
                for item_id in ids
            ]
            write_jsonl(run_dir / "results" / role / f"{condition}.jsonl", rows)
            write_json(
                run_dir / "manifests" / role / f"{condition}.json",
                {
                    "run_config": config,
                    "source_manifest_sha256": source_hash,
                    "model_revision": REVISION,
                    "packages": {"torch": "2.6.0"},
                    "torch": "2.6.0",
                    "cuda_runtime": "12.4",
                    "gpus": [{"name": "L4"}],
                    "python": "3.12",
                },
            )
    write_json(
        run_dir / "canary-gate.json",
        {"passed": True, "semantic_outcomes_inspected": False},
    )
    output = run_dir / "artifact-validation.json"
    return [
        "--run-dir",
        str(run_dir),
        "--fresh-dataset",
        str(fresh_dataset),
        "--bridge-dataset",
        str(bridge_dataset),
        "--source-root",
        str(source_root),
        "--out",
        str(output),
    ]


def test_validator_accepts_complete_pinned_matrix(tmp_path: Path) -> None:
    command = [sys.executable, str(SCRIPT), *build_fixture(tmp_path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(
        (tmp_path / "run/artifact-validation.json").read_text(encoding="utf-8")
    )
    assert report["valid"] is True
    assert report["validated_primary_rows"] == 398


def test_validator_rejects_a_missing_assigned_row(tmp_path: Path) -> None:
    arguments = build_fixture(tmp_path)
    path = (
        tmp_path
        / "run/results/fresh/xgrammar_json_integer_reasoning_first.jsonl"
    )
    path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    report = json.loads(
        (tmp_path / "run/artifact-validation.json").read_text(encoding="utf-8")
    )
    assert report["valid"] is False
    assert any("expected 150 rows" in failure for failure in report["failures"])
