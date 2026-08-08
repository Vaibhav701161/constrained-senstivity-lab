from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")

RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "run_evaluation.py"
SPEC = importlib.util.spec_from_file_location("run_baseline", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class BaselineScoringTests(unittest.TestCase):
    def test_json_prompt_has_no_example_answer(self) -> None:
        prompt = RUNNER.make_prompt(
            "A question with no digits.", "prompted_json_reasoning_first"
        )
        self.assertNotIn("42", prompt)
        self.assertIn('field order: "reasoning", then "answer"', prompt)
        self.assertIn('"answer": "<final numeric answer>"', prompt)

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

    def test_numeric_answer_field_is_strict(self) -> None:
        clean = RUNNER.score_json(
            '{"reasoning": "20 minus 17", "answer": "3"}',
            "prompted_json_reasoning_first",
        )
        embedded = RUNNER.score_json(
            '{"reasoning": "20 minus 17", "answer": "go3"}',
            "prompted_json_reasoning_first",
        )
        self.assertTrue(clean["schema_valid"])
        self.assertTrue(clean["answer_field_strict_numeric"])
        self.assertEqual(clean["predicted_answer_strict"], "3")
        self.assertFalse(embedded["schema_valid"])
        self.assertFalse(embedded["answer_field_strict_numeric"])
        self.assertEqual(embedded["predicted_answer"], "3")
        self.assertIsNone(embedded["predicted_answer_strict"])

    def test_number_normalization(self) -> None:
        self.assertEqual(RUNNER.canonical_number("$1,200.00"), "1200")
        self.assertEqual(RUNNER.canonical_number("2/4"), "1/2")

    def test_outlines_receives_raw_prompt_and_templates_it_once(self) -> None:
        class FakeTokenizer:
            def __init__(self) -> None:
                self.template_inputs: list[str] = []

            def apply_chat_template(self, messages, **_kwargs):
                content = messages[0]["content"]
                self.template_inputs.append(content)
                return f"<chat>{content}</chat>"

            def __call__(self, text, **_kwargs):
                return {"input_ids": list(range(len(text)))}

        tokenizer = FakeTokenizer()
        generated_prompt: list[str] = []

        def generator(raw_prompt: str, **_kwargs) -> str:
            generated_prompt.append(tokenizer.apply_chat_template(
                [{"role": "user", "content": raw_prompt}],
                tokenize=False,
                add_generation_prompt=True,
            ))
            return '{"answer": "4"}'

        raw_prompt = "What is 2 + 2?"
        args = SimpleNamespace(max_new_tokens=32, do_sample=False)
        RUNNER.timed_outlines_generate(
            generator, tokenizer, raw_prompt, args, use_cuda=False
        )

        self.assertEqual(tokenizer.template_inputs, [raw_prompt, raw_prompt])
        self.assertEqual(generated_prompt, [f"<chat>{raw_prompt}</chat>"])
        self.assertNotIn("<chat><chat>", generated_prompt[0])

    def test_generated_token_count_excludes_backend_only_stop_tokens(self) -> None:
        class FakeTokenizer:
            def __call__(self, text, **kwargs):
                self.last_kwargs = kwargs
                return {"input_ids": text.split()}

        tokenizer = FakeTokenizer()
        self.assertEqual(
            RUNNER.count_generated_content_tokens(tokenizer, "one two three"), 3
        )
        self.assertEqual(tokenizer.last_kwargs, {"add_special_tokens": False})

    def test_manifest_is_replayable_and_refuses_changed_configuration(self) -> None:
        model = SimpleNamespace(config=SimpleNamespace(_commit_hash="model-revision"))
        config = {"condition": "outlines_json_reasoning_first", "seed": 0}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            RUNNER.write_or_verify_manifest(path, config, model)
            first = json.loads(path.read_text(encoding="utf-8"))

            RUNNER.write_or_verify_manifest(path, config, model)
            second = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(first, second)
            self.assertEqual(first["model_revision"], "model-revision")
            self.assertEqual(len(first["runner_sha256"]), 64)

            with self.assertRaisesRegex(ValueError, "run configuration"):
                RUNNER.write_or_verify_manifest(
                    path,
                    {"condition": "outlines_json_reasoning_first", "seed": 1},
                    model,
                )


if __name__ == "__main__":
    unittest.main()
