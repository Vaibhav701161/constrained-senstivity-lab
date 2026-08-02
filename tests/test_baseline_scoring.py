from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "07_run_baseline.py"
SPEC = importlib.util.spec_from_file_location("run_baseline", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class BaselineScoringTests(unittest.TestCase):
    def test_free_prefers_final_answer_marker(self) -> None:
        scored = RUNNER.score_free("Final answer: 12. Later text contains 13")
        self.assertEqual(scored["predicted_answer"], "12")
        self.assertEqual(scored["answer_extraction_method"], "final_answer_marker")
        self.assertFalse(scored["final_answer_marker_at_end"])

    def test_free_records_final_marker_protocol(self) -> None:
        scored = RUNNER.score_free("Six times seven is 42.\nFinal answer: 42")
        self.assertTrue(scored["final_answer_marker_present"])
        self.assertTrue(scored["final_answer_marker_at_end"])

    def test_json_distinguishes_whole_validity_from_recovery(self) -> None:
        output = 'Here is the result: {"reasoning": "6 times 7", "answer": "42"}'
        scored = RUNNER.score_json(output, "prompted_json_reasoning_first")
        self.assertFalse(scored["whole_response_valid_json"])
        self.assertTrue(scored["first_object_recoverable"])
        self.assertTrue(scored["schema_valid"])
        self.assertEqual(scored["predicted_answer"], "42")

    def test_field_order_is_measured(self) -> None:
        output = '{"answer": "42", "reasoning": "6 times 7"}'
        scored = RUNNER.score_json(output, "prompted_json_reasoning_first")
        self.assertTrue(scored["schema_valid"])
        self.assertFalse(scored["field_order_matches"])

    def test_number_normalization(self) -> None:
        self.assertEqual(RUNNER.canonical_number("$1,200.00"), "1200")
        self.assertEqual(RUNNER.canonical_number("2/4"), "1/2")


if __name__ == "__main__":
    unittest.main()
