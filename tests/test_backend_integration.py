from __future__ import annotations

import json
import re

import pytest


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def model_components():
    from transformers import AutoConfig, AutoTokenizer

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        config = AutoConfig.from_pretrained(MODEL_NAME, local_files_only=True)
    except OSError as error:
        pytest.skip(f"local tokenizer fixture is unavailable: {error}")
    return tokenizer, config


def internal_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "answer": {"type": "integer"},
            "reasoning": {"type": "string"},
        },
        "required": ["answer", "reasoning"],
        "additionalProperties": False,
    }


def test_effective_prompt_tokens_match_between_direct_and_outlines_paths() -> None:
    pytest.importorskip("outlines")
    from outlines.models.transformers import TransformersTypeAdapter

    tokenizer, _ = model_components()
    raw = "Solve 2 + 2 and return one JSON object."
    direct = tokenizer.apply_chat_template(
        [{"role": "user", "content": raw}],
        tokenize=False,
        add_generation_prompt=True,
    )
    outlines = TransformersTypeAdapter(tokenizer, has_chat_template=True).format_input(raw)

    assert direct == outlines
    assert tokenizer(direct)["input_ids"] == tokenizer(outlines)["input_ids"]

    nested = TransformersTypeAdapter(tokenizer, has_chat_template=True).format_input(direct)
    assert tokenizer(nested)["input_ids"] != tokenizer(direct)["input_ids"]


def test_outlines_compiles_tokenizer_aware_canonical_schema() -> None:
    pytest.importorskip("outlines")
    from outlines.backends.outlines_core import OutlinesCoreBackend
    from outlines.models.transformers import TransformerTokenizer
    from outlines_core import Index
    from outlines_core.json_schema import build_regex_from_schema

    tokenizer, _ = model_components()
    wrapped = TransformerTokenizer(tokenizer)
    vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(
        wrapped.get_vocab(),
        wrapped.eos_token_id,
        wrapped.eos_token,
        wrapped.convert_token_to_string,
    )
    regex = build_regex_from_schema(json.dumps(internal_schema()), "")
    index = Index(regex, vocabulary)

    assert index is not None
    assert re.fullmatch(regex, '{"answer":1,"reasoning":"x"}')
    assert not re.fullmatch(regex, '{"answer":          1,"reasoning":"x"}')


def test_xgrammar_compiles_canonical_schema_and_rejects_whitespace_loop() -> None:
    pytest.importorskip("xgrammar")
    import xgrammar as xgr

    tokenizer, config = model_components()
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer, vocab_size=config.vocab_size
    )
    compiled = xgr.GrammarCompiler(tokenizer_info).compile_json_schema(
        internal_schema(),
        any_whitespace=False,
        separators=(",", ":"),
        strict_mode=True,
        any_order=False,
    )

    valid = xgr.GrammarMatcher(compiled)
    assert valid.accept_string('{"answer":1,"reasoning":"x"}')
    assert valid.is_completed()

    whitespace_loop = xgr.GrammarMatcher(compiled)
    assert not whitespace_loop.accept_string(
        '{"answer":          1,"reasoning":"x"}'
    )
    assert not whitespace_loop.is_completed()


def test_xgrammar_huggingface_processor_is_fresh_per_generation() -> None:
    pytest.importorskip("xgrammar")
    import xgrammar as xgr

    tokenizer, config = model_components()
    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer, vocab_size=config.vocab_size
    )
    compiled = xgr.GrammarCompiler(tokenizer_info).compile_json_schema(
        internal_schema(),
        any_whitespace=False,
        separators=(",", ":"),
        strict_mode=True,
        any_order=False,
    )
    first = xgr.contrib.hf.LogitsProcessor(compiled)
    second = xgr.contrib.hf.LogitsProcessor(compiled)

    assert first is not second
    assert first.matchers == []
    assert second.matchers == []
    assert not first.prefilled
    assert not second.prefilled
