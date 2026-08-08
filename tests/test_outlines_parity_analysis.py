from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_outlines_parity.py"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def run_fixture(tmp_path: Path, *, mutate_output: bool = False) -> dict[str, object]:
    selection = tmp_path / "selection.json"
    selected_ids = ["item-1", "item-2"]
    write_json(
        selection,
        {
            "selected_count": 2,
            "selected_item_ids": selected_ids,
            "selected_dataset_sha256": "selected-hash",
        },
    )
    source = tmp_path / "source.json"
    write_json(source, {"source": "frozen"})
    import hashlib

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    xresults = tmp_path / "xresults"
    xmanifests = tmp_path / "xmanifests"
    oresults = tmp_path / "oresults"
    omanifests = tmp_path / "omanifests"
    common_environment = {
        "python": "3.12",
        "torch": "2.6.0",
        "cuda_runtime": "12.4",
        "gpus": [{"name": "L4"}],
        "model_revision": "revision",
        "tokenizer_revision": "revision",
        "packages": {"xgrammar": "0.2.3"},
        "source_manifest_sha256": source_hash,
    }
    for representation, (xname, oname) in {
        "signed-numeric-string": ("xgrammar_json_reasoning_first", "outlines_json_reasoning_first"),
        "integer": ("xgrammar_json_integer_reasoning_first", "outlines_json_integer_reasoning_first"),
    }.items():
        config = {
            "model": "model",
            "revision": "revision",
            "answer_representation": representation,
            "field_order": ["reasoning", "answer"],
            "prompt_version": "prompt",
            "seed": 0,
            "do_sample": False,
            "max_new_tokens": 256,
            "dtype": "float32",
            "device_map_auto": True,
            "internal_schema_sha256": representation,
            "external_schema_sha256": "external",
            "transducer_version": "v1" if representation == "integer" else None,
            "plan_id": representation,
            "runner_sha256": "runner",
            "runtime_sha256": "runtime",
        }
        rows = [
            {
                "item_id": item,
                "formatted_prompt": f"prompt-{item}",
                "raw_output": f"output-{item}",
                "predicted_answer_normalized": "1",
                "semantic_correct": True,
                "contract_valid_correct": True,
                "internal_schema_valid": True,
                "external_schema_valid": True,
                "hit_max_new_tokens": False,
                "error": None,
            }
            for item in selected_ids
        ]
        outlines_rows = [dict(row) for row in rows]
        if mutate_output and representation == "integer":
            outlines_rows[1]["raw_output"] = "different"
        write_jsonl(xresults / f"{xname}.jsonl", rows)
        write_jsonl(oresults / f"{oname}.jsonl", outlines_rows)
        write_json(xmanifests / f"{xname}.json", {**common_environment, "run_config": config})
        write_json(
            omanifests / f"{oname}.json",
            {
                **common_environment,
                "run_config": {**config, "dataset_sha256": "selected-hash"},
            },
        )
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--selection",
            str(selection),
            "--source-manifest",
            str(source),
            "--xgrammar-fresh-dir",
            str(xresults),
            "--xgrammar-manifest-dir",
            str(xmanifests),
            "--outlines-dir",
            str(oresults),
            "--outlines-manifest-dir",
            str(omanifests),
            "--out-json",
            str(output),
            "--out-md",
            str(tmp_path / "report.md"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_exact_backend_parity_passes(tmp_path: Path) -> None:
    report = run_fixture(tmp_path)
    assert report["structurally_valid"] is True
    assert report["implementation_parity_passed"] is True


def test_output_difference_is_reported_without_corrupting_structure(tmp_path: Path) -> None:
    report = run_fixture(tmp_path, mutate_output=True)
    assert report["structurally_valid"] is True
    assert report["implementation_parity_passed"] is False
    mismatch = report["representations"]["integer"]["mismatched_item_ids"]
    assert mismatch["raw_output"] == ["item-2"]
