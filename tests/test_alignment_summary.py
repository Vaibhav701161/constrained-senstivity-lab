from __future__ import annotations

import importlib.util
from pathlib import Path

SUMMARY_PATH = Path(__file__).parents[1] / "scripts" / "summarize_alignment_gate.py"
SPEC = importlib.util.spec_from_file_location("alignment_summary", SUMMARY_PATH)
assert SPEC is not None and SPEC.loader is not None
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)


def test_exact_bootstrap_interval_is_deterministic_for_identical_vectors() -> None:
    values = [1] * 9 + [-1] * 3 + [0] * 37
    first = SUMMARY.bootstrap_interval(values)
    second = SUMMARY.bootstrap_interval(list(reversed(values)))

    assert first == second
    assert first == [0.0, 13 / 49]


def test_exact_bootstrap_interval_handles_constant_and_empty_inputs() -> None:
    assert SUMMARY.bootstrap_interval([]) is None
    assert SUMMARY.bootstrap_interval([0] * 49) == [0.0, 0.0]
    assert SUMMARY.bootstrap_interval([1] * 5) == [1.0, 1.0]
