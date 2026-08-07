from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_unseen_gsm8k.py"
SPEC = importlib.util.spec_from_file_location("prepare_unseen_gsm8k", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def test_collect_seen_indices_reads_all_supported_identity_fields(tmp_path: Path) -> None:
    write_jsonl(
        tmp_path / "results" / "a.jsonl",
        [
            {"item_id": "gsm8k_test_7"},
            {"id": "gsm8k_test_11"},
            {"source_index": 19},
            {"item_id": "another_dataset_3", "source_index": None},
        ],
    )
    write_jsonl(
        tmp_path / "experiments" / "b.jsonl",
        [{"item_id": "gsm8k_test_7", "source_index": 23}],
    )

    seen, files = MODULE.collect_seen_indices(
        [tmp_path / "results", tmp_path / "experiments"]
    )

    assert seen == {7, 11, 19, 23}
    assert len(files) == 2
    assert [entry["rows"] for entry in files] == [1, 4]
    assert all(len(entry["sha256"]) == 64 for entry in files)


def test_selection_is_deterministic_and_excludes_seen_indices() -> None:
    first = MODULE.select_unseen_indices(20, {0, 2, 4, 6}, 8, 20260815)
    second = MODULE.select_unseen_indices(20, {0, 2, 4, 6}, 8, 20260815)

    assert first == second
    assert len(first) == 8
    assert len(set(first)) == 8
    assert not set(first) & {0, 2, 4, 6}


def test_selection_refuses_an_oversized_holdout() -> None:
    with pytest.raises(ValueError, match="only 2 are eligible"):
        MODULE.select_unseen_indices(4, {0, 1}, 3, 20260815)


def test_extract_gold_validates_marker_and_numeric_answer() -> None:
    assert MODULE.extract_gold("work\n#### 1,234") == "1,234"
    with pytest.raises(ValueError, match="missing"):
        MODULE.extract_gold("work without marker")
    with pytest.raises(ValueError, match="not numeric"):
        MODULE.extract_gold("work\n#### unknown")


def test_invalid_jsonl_is_not_silently_skipped(tmp_path: Path) -> None:
    path = tmp_path / "results" / "broken.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"item_id":"gsm8k_test_1"}\nnot-json\n', encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        MODULE.collect_seen_indices([tmp_path / "results"])


def test_jsonl_serialization_is_stable() -> None:
    rows = [{"id": "gsm8k_test_1", "question": "2 + 2?"}]
    assert MODULE.jsonl_bytes(rows) == (
        b'{"id":"gsm8k_test_1","question":"2 + 2?"}\n'
    )
