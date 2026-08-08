from __future__ import annotations

import os

import pytest

from project_a.runtime import (
    RuntimeRepresentation,
    format_chat_prompt,
    make_contract_prompt,
)

MODEL = "meta-llama/Llama-3.2-3B-Instruct"


def llama_tokenizer():
    if os.environ.get("RUN_LLAMA_PROMPT_PARITY") != "1":
        pytest.skip("set RUN_LLAMA_PROMPT_PARITY=1 in the pinned Modal image")
    from transformers import AutoTokenizer

    revision = os.environ["LLAMA_MODEL_REVISION"]
    return AutoTokenizer.from_pretrained(MODEL, revision=revision)


@pytest.mark.parametrize("representation", tuple(RuntimeRepresentation))
def test_llama_direct_xgrammar_and_outlines_effective_prompts_match(
    representation: RuntimeRepresentation,
) -> None:
    pytest.importorskip("outlines")
    from outlines.models.transformers import TransformersTypeAdapter

    tokenizer = llama_tokenizer()
    raw = make_contract_prompt("What is 2 + 2?", representation)
    direct_and_xgrammar = format_chat_prompt(tokenizer, raw)
    outlines = TransformersTypeAdapter(tokenizer, has_chat_template=True).format_input(raw)

    assert direct_and_xgrammar == outlines
    assert tokenizer(direct_and_xgrammar, add_special_tokens=False)["input_ids"] == tokenizer(
        outlines, add_special_tokens=False
    )["input_ids"]

    nested = TransformersTypeAdapter(tokenizer, has_chat_template=True).format_input(
        direct_and_xgrammar
    )
    assert tokenizer(nested, add_special_tokens=False)["input_ids"] != tokenizer(
        direct_and_xgrammar, add_special_tokens=False
    )["input_ids"]
