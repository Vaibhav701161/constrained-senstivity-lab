from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_corrected_replication.py"
SPEC = importlib.util.spec_from_file_location("corrected_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def build_fixture(root: Path) -> tuple[Path, Path, Path]:
    run_dir = root / "run"
    source_root = root / "source"
    kernel_source = root / "run_kaggle.py"
    kernel_source.write_text("print('fixture')\n", encoding="utf-8")
    external_runner = source_root / "run_evaluation.py"
    integer_runner = source_root / "run_representation_alignment.py"
    external_runner.parent.mkdir(parents=True)
    external_runner.write_text("# external\n", encoding="utf-8")
    integer_runner.write_text("# integer\n", encoding="utf-8")
    source_manifest = {
        "files": {
            external_runner.name: digest(external_runner),
            integer_runner.name: digest(integer_runner),
        }
    }
    write_json(source_root / "source-manifest.json", source_manifest)

    dataset = root / "dataset.jsonl"
    dataset_rows = [
        {"id": "gsm8k_test_454" if index == 49 else f"item-{index}"}
        for index in range(50)
    ]
    write_jsonl(dataset, dataset_rows)
    dataset_hash = digest(dataset)

    conditions = [
        "outlines_json_reasoning_first",
        "xgrammar_json_reasoning_first",
        "outlines_json_integer_reasoning_first",
        "xgrammar_json_integer_reasoning_first",
    ]
    specs = []
    for condition in conditions:
        integer = "_integer_" in condition
        runner_hash = digest(integer_runner if integer else external_runner)
        run_config = {"condition": condition, "dataset_sha256": dataset_hash}
        if integer:
            run_config["runner_sha256"] = runner_hash
        signature = hashlib.sha256(
            json.dumps(run_config, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:12]
        manifest = {"run_config": run_config}
        if not integer:
            manifest["runner_sha256"] = runner_hash
        write_json(run_dir / "manifests" / f"{condition}.json", manifest)
        representation = "integer" if integer else "signed_numeric_string"
        backend = "outlines" if condition.startswith("outlines") else "xgrammar"
        specs.append(
            {
                "name": condition,
                "runner": "integer" if integer else "external",
                "backend": backend,
                "representation": representation,
            }
        )
        prompt_prefix = "integer" if integer else "signed"
        rows = [
            {
                "item_id": row["id"],
                "run_id": f"run-{condition}",
                "run_signature": signature,
                "dataset_sha256": dataset_hash,
                "raw_output": "{}",
                "formatted_prompt": f"{prompt_prefix}-{index}",
                "schema_valid": True,
                "internal_schema_valid": True,
                "external_schema_valid": True,
                "hit_max_new_tokens": False,
                "error": None,
            }
            for index, row in enumerate(dataset_rows)
        ]
        write_jsonl(run_dir / f"{condition}.jsonl", rows)

    source_manifest_path = source_root / "source-manifest.json"
    write_json(
        run_dir / "kernel-manifest.json",
        {
            "conditions": specs,
            "full_limit": 50,
            "canary_limit": 5,
            "excluded_item_ids": ["gsm8k_test_454"],
            "dataset_sha256": dataset_hash,
            "kernel_source_sha256": digest(kernel_source),
            "source_manifest_sha256": digest(source_manifest_path),
        },
    )
    for stage, limit in (("canary", 5), ("full", 50)):
        write_json(
            run_dir / f"{stage}-gate.json",
            {"passed": True, "expected_limit": limit, "failures": []},
        )
    write_jsonl(
        run_dir / "traces" / "xgrammar-integer-answer-boundary.jsonl",
        [
            {
                "item_id": item_id,
                "condition": "xgrammar_json_integer_reasoning_first",
            }
            for item_id in VALIDATOR.EXPECTED_TRACE_ITEMS
        ],
    )
    write_json(
        run_dir / "paired-summary.json",
        {
            "excluded_item_ids": ["gsm8k_test_454"],
            "total_rows": 196,
            "paired_comparisons": [
                {"name": name, "paired_examples": 49}
                for name in VALIDATOR.EXPECTED_COMPARISONS
            ],
        },
    )
    return run_dir, source_root, dataset


def invoke_validator(
    monkeypatch: pytest.MonkeyPatch,
    run_dir: Path,
    source_root: Path,
    dataset: Path,
    kernel_source: Path,
    output: Path,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(VALIDATOR_PATH),
            "--run-dir",
            str(run_dir),
            "--dataset",
            str(dataset),
            "--source-root",
            str(source_root),
            "--kernel-source",
            str(kernel_source),
            "--out",
            str(output),
        ],
    )
    VALIDATOR.main()


def test_validator_accepts_complete_consistent_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir, source_root, dataset = build_fixture(tmp_path)
    output = tmp_path / "validation.json"
    invoke_validator(
        monkeypatch,
        run_dir,
        source_root,
        dataset,
        tmp_path / "run_kaggle.py",
        output,
    )
    assert json.loads(output.read_text(encoding="utf-8"))["valid"] is True


def test_validator_rejects_cross_backend_prompt_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir, source_root, dataset = build_fixture(tmp_path)
    path = run_dir / "xgrammar_json_reasoning_first.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["formatted_prompt"] = "different-effective-prompt"
    write_jsonl(path, rows)
    output = tmp_path / "rejected-validation.json"

    with pytest.raises(SystemExit):
        invoke_validator(
            monkeypatch,
            run_dir,
            source_root,
            dataset,
            tmp_path / "run_kaggle.py",
            output,
        )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert any("effective prompts differ" in item for item in report["failures"])
