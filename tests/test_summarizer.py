from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SUMMARIZER_PATH = Path(__file__).parents[1] / "scripts" / "summarize_results.py"
SPEC = importlib.util.spec_from_file_location("summarize_results", SUMMARIZER_PATH)
assert SPEC is not None and SPEC.loader is not None
SUMMARIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARIZER)


class PairedComparisonTests(unittest.TestCase):
    def test_uncertainty_intervals(self) -> None:
        self.assertIsNone(SUMMARIZER.wilson_interval(0, 0))
        interval = SUMMARIZER.wilson_interval(5, 10)
        assert interval is not None
        self.assertAlmostEqual(interval[0], 0.236593090512564, places=12)
        self.assertAlmostEqual(interval[1], 0.7634069094874361, places=12)
        self.assertEqual(
            SUMMARIZER.paired_bootstrap_interval([0, 0, 0], "zeros"),
            [0.0, 0.0],
        )

    def test_exact_mcnemar_p(self) -> None:
        self.assertEqual(SUMMARIZER.exact_mcnemar_p(0, 0), 1.0)
        self.assertEqual(SUMMARIZER.exact_mcnemar_p(3, 4), 1.0)
        self.assertAlmostEqual(SUMMARIZER.exact_mcnemar_p(2, 11), 0.0224609375)
        self.assertEqual(SUMMARIZER.p_value(2.9103830456733704e-11), "2.91e-11")
        self.assertEqual(SUMMARIZER.p_value(0.00390625), "0.00391")

    def test_latency_per_token_uses_row_level_rates(self) -> None:
        rows = [
            {"latency_ms": 100.0, "generated_tokens": 10},
            {"latency_ms": 300.0, "generated_tokens": 20},
            {"latency_ms": 1.0, "generated_tokens": 0},
        ]
        self.assertEqual(SUMMARIZER.mean_latency_per_token_ms(rows), 12.5)

    def test_strict_pairs_do_not_count_lenient_json_extraction(self) -> None:
        rows = [
            {
                "model": "model",
                "condition": "prompted_json_reasoning_first",
                "item_id": "a",
                "correct_exact": True,
                "correct_exact_strict": False,
            },
            {
                "model": "model",
                "condition": "outlines_json_reasoning_first",
                "item_id": "a",
                "correct_exact": False,
                "correct_exact_strict": False,
            },
            {
                "model": "model",
                "condition": "prompted_json_reasoning_first",
                "item_id": "b",
                "correct_exact": False,
                "correct_exact_strict": False,
            },
            {
                "model": "model",
                "condition": "outlines_json_reasoning_first",
                "item_id": "b",
                "correct_exact": True,
                "correct_exact_strict": True,
            },
        ]

        comparisons = SUMMARIZER.paired_deltas(rows)
        comparison = next(
            row
            for row in comparisons
            if row["comparison"] == "outlines_constraint_effect"
        )

        self.assertEqual(comparison["accuracy_delta"], 0.0)
        self.assertEqual(comparison["strict_accuracy_delta"], 0.5)
        self.assertEqual(comparison["strict_treatment_only_correct"], 1)
        self.assertEqual(comparison["strict_control_only_correct"], 0)

    def test_free_condition_falls_back_to_legacy_correctness(self) -> None:
        rows = [
            {
                "model": "model",
                "condition": "free",
                "item_id": "a",
                "correct_exact": True,
                "correct_exact_strict": None,
            },
            {
                "model": "model",
                "condition": "prompted_json_reasoning_first",
                "item_id": "a",
                "correct_exact": False,
                "correct_exact_strict": False,
            },
        ]

        comparison = SUMMARIZER.paired_deltas(rows)[0]

        self.assertEqual(comparison["strict_accuracy_delta"], -1.0)
        self.assertEqual(comparison["strict_control_only_correct"], 1)

    def test_direct_backend_comparison_is_reported(self) -> None:
        rows = [
            {
                "model": "model",
                "condition": "outlines_json_reasoning_first",
                "item_id": "a",
                "correct_exact": True,
                "correct_exact_strict": True,
            },
            {
                "model": "model",
                "condition": "xgrammar_json_reasoning_first",
                "item_id": "a",
                "correct_exact": False,
                "correct_exact_strict": False,
            },
        ]
        comparisons = SUMMARIZER.paired_deltas(rows)
        comparison = next(
            row for row in comparisons if row["comparison"] == "xgrammar_vs_outlines"
        )
        self.assertEqual(comparison["accuracy_delta"], -1.0)
        self.assertEqual(comparison["mcnemar_p_exact"], 1.0)


if __name__ == "__main__":
    unittest.main()
