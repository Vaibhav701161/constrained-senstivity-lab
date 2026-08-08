from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_a.metrics import score_alignment_output
from project_a.schema_variants import (
    AnswerRepresentation,
    canonical_schema_pair,
    external_schema,
    make_prompt,
    schema_for_spec,
    spec_for_condition,
    symbolic_template,
)
from project_a.transducer import canonical_integer_string, transduce_and_validate


class SchemaVariantTests(unittest.TestCase):
    def test_canonical_schema_pair_has_one_exact_language(self) -> None:
        external, internal = canonical_schema_pair()
        self.assertEqual(
            external["properties"]["answer"],
            {
                "type": "string",
                "pattern": r"^-?(?:0|[1-9][0-9]*)$",
            },
        )
        self.assertEqual(internal["properties"]["answer"], {"type": "integer"})

    def test_integer_schema_and_template_are_unquoted(self) -> None:
        spec = spec_for_condition("outlines_json_integer_reasoning_first")
        schema = schema_for_spec(spec)
        self.assertEqual(schema["properties"]["answer"], {"type": "integer"})
        self.assertIn('"answer": <integer>', symbolic_template(spec))

    def test_string_diagnostic_is_explicitly_not_the_integer_schema(self) -> None:
        spec = spec_for_condition(
            "xgrammar_json_unsigned_numeric_string_reasoning_first"
        )
        schema = schema_for_spec(spec)
        self.assertTrue(spec.diagnostic_only)
        self.assertEqual(
            spec.answer_representation,
            AnswerRepresentation.UNSIGNED_NUMERIC_STRING_DIAGNOSTIC,
        )
        self.assertEqual(schema["properties"]["answer"]["type"], "string")
        self.assertNotIn("-?", schema["properties"]["answer"]["pattern"])

    def test_prompt_has_no_concrete_example_answer(self) -> None:
        spec = spec_for_condition("prompted_json_integer_reasoning_first")
        prompt = make_prompt("What is 2 + 2?", spec)
        self.assertIn('"answer": <integer>', prompt)
        self.assertNotIn('"answer": "42"', prompt)
        self.assertIn("Return only one valid JSON object", prompt)

    def test_integer_prompt_changes_only_the_symbolic_answer_representation(self) -> None:
        baseline_path = (
            ROOT
            / "results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke"
            / "prompted_json_reasoning_first.jsonl"
        )
        baseline = json.loads(baseline_path.read_text(encoding="utf-8").splitlines()[0])
        spec = spec_for_condition("prompted_json_integer_reasoning_first")
        expected = baseline["prompt"].replace(
            '"answer": "<final numeric answer>"', '"answer": <integer>'
        )
        self.assertEqual(make_prompt(baseline["question"], spec), expected)


class IntegerStringTransducerTests(unittest.TestCase):
    def test_integer_stringification_is_canonical(self) -> None:
        self.assertEqual(canonical_integer_string(0), "0")
        self.assertEqual(canonical_integer_string(-17), "-17")
        self.assertEqual(canonical_integer_string(10**120), str(10**120))

    def test_non_integers_and_booleans_are_rejected(self) -> None:
        for value in (True, False, "12", 12.0, None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    canonical_integer_string(value)

    def test_valid_internal_values_always_validate_externally(self) -> None:
        schema = external_schema()
        for value in range(-100, 101):
            result = transduce_and_validate(
                {"reasoning": "calculation", "answer": value}, schema
            )
            with self.subTest(value=value):
                self.assertTrue(result.external_valid)
                self.assertEqual(result.external_value["answer"], str(value))

    def test_invalid_internal_value_fails_closed(self) -> None:
        result = transduce_and_validate(
            {"reasoning": "calculation", "answer": "00012"}, external_schema()
        )
        self.assertFalse(result.external_valid)
        self.assertIsNone(result.external_value)

    def test_transducer_never_repairs_or_infers_a_sign(self) -> None:
        result = transduce_and_validate(
            {"reasoning": "The magnitude is positive 26.", "answer": -26},
            external_schema(),
        )
        self.assertTrue(result.external_valid)
        self.assertEqual(result.external_value["answer"], "-26")

    def test_lexical_strings_are_not_heuristically_coerced(self) -> None:
        for value in ("-26", "+26", "00026", "26.0", "2.6e1"):
            with self.subTest(value=value):
                result = transduce_and_validate(
                    {"reasoning": "calculation", "answer": value}, external_schema()
                )
                self.assertFalse(result.external_valid)
                self.assertIsNone(result.external_value)


class ContractValidScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = spec_for_condition("prompted_json_integer_reasoning_first")
        self.internal = schema_for_spec(self.spec)
        self.external = external_schema()

    def test_integer_output_is_semantically_and_contract_valid(self) -> None:
        result = score_alignment_output(
            json.dumps({"reasoning": "2 + 2 = 4", "answer": 4}),
            self.internal,
            self.external,
            self.spec.field_order,
            "4",
        )
        self.assertTrue(result["semantic_correct"])
        self.assertTrue(result["internal_schema_valid"])
        self.assertTrue(result["external_schema_valid"])
        self.assertTrue(result["contract_valid_correct"])
        self.assertEqual(result["external_value"]["answer"], "4")

    def test_string_answer_is_not_coerced_to_an_integer(self) -> None:
        result = score_alignment_output(
            json.dumps({"reasoning": "2 + 2 = 4", "answer": "4"}),
            self.internal,
            self.external,
            self.spec.field_order,
            "4",
        )
        self.assertTrue(result["semantic_correct"])
        self.assertFalse(result["internal_schema_valid"])
        self.assertFalse(result["external_schema_valid"])
        self.assertFalse(result["contract_valid_correct"])

    def test_unsigned_diagnostic_string_uses_identity_transduction(self) -> None:
        spec = spec_for_condition(
            "outlines_json_unsigned_numeric_string_reasoning_first"
        )
        result = score_alignment_output(
            json.dumps({"reasoning": "2 + 2 = 4", "answer": "4"}),
            schema_for_spec(spec),
            self.external,
            spec.field_order,
            "4",
            spec.answer_representation,
        )
        self.assertTrue(result["internal_schema_valid"])
        self.assertTrue(result["external_schema_valid"])
        self.assertTrue(result["contract_valid_correct"])

    def test_extra_prose_cannot_be_contract_valid(self) -> None:
        result = score_alignment_output(
            'Answer: {"reasoning": "2 + 2 = 4", "answer": 4}',
            self.internal,
            self.external,
            self.spec.field_order,
            "4",
        )
        self.assertTrue(result["semantic_correct"])
        self.assertFalse(result["whole_response_valid_json"])
        self.assertFalse(result["contract_valid_correct"])


if __name__ == "__main__":
    unittest.main()
