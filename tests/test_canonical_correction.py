import copy
import json
from pathlib import Path

from scripts.analyze_canonical_correction import rescore_rows

ROOT = Path(__file__).resolve().parents[1]


def read_first(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def test_historical_canonical_like_control_row_replays_under_corrected_schema() -> None:
    row = read_first(
        ROOT
        / "experiments/second-family-replication/results/fresh"
        / "xgrammar_json_reasoning_first.jsonl"
    )
    corrected = copy.deepcopy(row)
    corrected["condition"] = (
        "xgrammar_json_canonical_integer_string_reasoning_first"
    )
    replayed, mismatches = rescore_rows([corrected], treatment=False)
    assert mismatches == []
    assert replayed[0]["external_schema_valid"] is True


def test_frozen_integer_treatment_replays_against_canonical_external_schema() -> None:
    row = read_first(
        ROOT
        / "experiments/second-family-replication/results/fresh"
        / "xgrammar_json_integer_reasoning_first.jsonl"
    )
    replayed, mismatches = rescore_rows([row], treatment=True)
    assert mismatches == []
    assert replayed[0]["external_schema_valid"] == row["external_schema_valid"]
    assert replayed[0]["contract_valid_correct"] == row["contract_valid_correct"]
