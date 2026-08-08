"""Shared structured-generation runtime for contract-alignment experiments."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, LogitsProcessor

from .metrics import score_alignment_output
from .schema_variants import (
    AnswerRepresentation,
    ConditionSpec,
    canonical_external_schema,
    external_schema,
    schema_for_spec,
    schema_sha256,
)
from .transducer import TRANSDUCER_VERSION

RUNTIME_VERSION = "contract-generation-runtime-v1"
PROMPT_VERSION = "contract-alignment-unified-v1"
TRACE_VERSION = "answer-boundary-v2"
XGRAMMAR_ANY_WHITESPACE = False
XGRAMMAR_SEPARATORS = (",", ":")
OUTLINES_WHITESPACE_PATTERN = ""
PACKAGE_NAMES = (
    "torch",
    "transformers",
    "accelerate",
    "datasets",
    "jsonschema",
    "outlines",
    "xgrammar",
)


class RuntimeRepresentation(StrEnum):
    """The only experimental switch in the unified runtime."""

    SIGNED_NUMERIC_STRING = "signed-numeric-string"
    CANONICAL_SIGNED_INTEGER_STRING = "canonical-signed-integer-string"
    INTEGER = "integer"


class RuntimeBackend(StrEnum):
    """Grammar backend used by one runtime invocation."""

    XGRAMMAR = "xgrammar"
    OUTLINES = "outlines"


@dataclass(frozen=True)
class LoadedModel:
    tokenizer: Any
    model: Any
    use_cuda: bool
    model_revision: str
    tokenizer_revision: str


@dataclass(frozen=True)
class GenerationMeasurement:
    raw_output: str
    latency_ms: float
    prompt_tokens: int
    generated_content_tokens: int
    generated_token_ids: int
    output_ids: torch.Tensor | None = None


def representation_spec(
    representation: RuntimeRepresentation,
    backend: RuntimeBackend,
) -> ConditionSpec:
    if representation is RuntimeRepresentation.INTEGER:
        answer_representation = AnswerRepresentation.INTEGER
        suffix = "integer_reasoning_first"
    elif representation is RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING:
        answer_representation = AnswerRepresentation.CANONICAL_SIGNED_INTEGER_STRING
        suffix = "canonical_integer_string_reasoning_first"
    else:
        answer_representation = AnswerRepresentation.SIGNED_NUMERIC_STRING
        suffix = "reasoning_first"
    return ConditionSpec(
        name=f"{backend.value}_json_{suffix}",
        backend=backend.value,
        answer_representation=answer_representation,
    )


def symbolic_template(representation: RuntimeRepresentation) -> str:
    answer = (
        "<integer>"
        if representation is RuntimeRepresentation.INTEGER
        else json.dumps("<final numeric answer>")
    )
    return '{"reasoning": "<calculation sentences>", "answer": ' + answer + "}"


def make_contract_prompt(question: str, representation: RuntimeRepresentation) -> str:
    """Build the accepted prompt with only the answer representation changed."""

    return (
        "Solve this grade-school math problem. The reasoning value must contain only 1-3 "
        "short calculation sentences, without lists or headings. "
        "The answer value must contain only the final numeric answer, "
        "with no units, currency symbol, or reasoning. "
        "Return only one valid JSON object, with no markdown or extra text. "
        'Use exactly two keys in this field order: "reasoning", then "answer". '
        "Replace both angle-bracket placeholders in this template and do not output "
        "the angle brackets themselves:\n"
        f"{symbolic_template(representation)}\n\n"
        f"Question:\n{question}"
    )


def format_chat_prompt(tokenizer: Any, raw_prompt: str) -> str:
    """Apply a model chat template exactly once to a raw project prompt."""

    return tokenizer.apply_chat_template(
        [{"role": "user", "content": raw_prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )


def count_generated_content_tokens(tokenizer: Any, raw_output: str) -> int:
    return len(tokenizer(raw_output, add_special_tokens=False)["input_ids"])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_signature(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def select_examples(
    rows: list[dict[str, Any]],
    *,
    start_index: int = 0,
    end_index: int | None = None,
    limit: int | None = None,
    exclude_item_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    excluded = set(exclude_item_ids)
    filtered = [row for row in rows if str(row.get("id")) not in excluded]
    end = end_index if end_index is not None else len(filtered)
    selected = filtered[start_index:end]
    if limit is not None:
        selected = selected[:limit]
    ids = [str(row["id"]) for row in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("selected dataset rows contain duplicate IDs")
    return selected


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in PACKAGE_NAMES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def resolved_tokenizer_revision(tokenizer: Any, requested_revision: str) -> str:
    commit = getattr(tokenizer, "init_kwargs", {}).get("_commit_hash")
    return str(commit or requested_revision)


def load_model(
    model_name: str,
    *,
    revision: str,
    force_cpu: bool,
    device_map_auto: bool,
    dtype: str,
) -> LoadedModel:
    use_cuda = torch.cuda.is_available() and not force_cpu
    if device_map_auto and not use_cuda:
        raise RuntimeError("device_map=auto requires an available CUDA GPU")
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    config = AutoConfig.from_pretrained(model_name, revision=revision)
    if not getattr(config, "use_sliding_window", False):
        config.sliding_window = None
    torch_dtype: str | torch.dtype
    if dtype == "auto":
        torch_dtype = "auto"
    elif dtype == "float32":
        torch_dtype = torch.float32
    else:
        torch_dtype = torch.float16 if use_cuda else torch.float32
    load_kwargs: dict[str, Any] = {
        "config": config,
        "revision": revision,
        "torch_dtype": torch_dtype,
        "low_cpu_mem_usage": True,
        "attn_implementation": "eager",
    }
    if use_cuda:
        if device_map_auto:
            load_kwargs["device_map"] = "auto"
            load_kwargs["max_memory"] = {
                index: (
                    f"{max(1, int(torch.cuda.get_device_properties(index).total_memory / 2**30) - 2)}GiB"
                )
                for index in range(torch.cuda.device_count())
            }
        else:
            load_kwargs["device_map"] = {"": "cuda:0"}
    model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
    model.eval()
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    model_revision = str(getattr(model.config, "_commit_hash", None) or revision)
    return LoadedModel(
        tokenizer=tokenizer,
        model=model,
        use_cuda=use_cuda,
        model_revision=model_revision,
        tokenizer_revision=resolved_tokenizer_revision(tokenizer, revision),
    )


def build_xgrammar_grammar(model: Any, tokenizer: Any, schema: dict[str, Any]):
    import xgrammar as xgr

    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer, vocab_size=model.config.vocab_size
    )
    return xgr.GrammarCompiler(tokenizer_info).compile_json_schema(
        schema,
        any_whitespace=XGRAMMAR_ANY_WHITESPACE,
        separators=XGRAMMAR_SEPARATORS,
        strict_mode=True,
        any_order=False,
    )


def new_xgrammar_processor(compiled_grammar: Any):
    import xgrammar as xgr

    return xgr.contrib.hf.LogitsProcessor(compiled_grammar)


def build_outlines_generator(model: Any, tokenizer: Any, schema: dict[str, Any]):
    from outlines import Generator, from_transformers
    from outlines.types import JsonSchema

    return Generator(
        from_transformers(model, tokenizer),
        JsonSchema(schema, whitespace_pattern=OUTLINES_WHITESPACE_PATTERN),
    )


def token_entry(tokenizer: Any, token_id: int, score: float) -> dict[str, Any]:
    return {
        "token_id": int(token_id),
        "text": tokenizer.decode([int(token_id)], skip_special_tokens=False),
        "score": round(float(score), 6),
    }


class AnswerBoundaryTraceProcessor(LogitsProcessor):
    """Record compact pre-mask and post-mask evidence at the answer boundary."""

    def __init__(self, inner: Any, tokenizer: Any, prompt_tokens: int) -> None:
        self.inner = inner
        self.tokenizer = tokenizer
        self.prompt_tokens = prompt_tokens
        self.records: list[dict[str, Any]] = []

    def _known_scores(self, scores: torch.Tensor) -> dict[str, Any]:
        known: dict[str, Any] = {}
        for text in ("-", "0", "1", "18", '"', " "):
            token_ids = self.tokenizer.encode(text, add_special_tokens=False)
            if len(token_ids) == 1:
                known[text] = {
                    "token_id": token_ids[0],
                    "score": round(float(scores[0, token_ids[0]].item()), 6),
                }
        return known

    def __call__(self, input_ids: torch.Tensor, scores: torch.Tensor) -> torch.Tensor:
        generated = input_ids[0, self.prompt_tokens :]
        decoded = self.tokenizer.decode(generated, skip_special_tokens=False)
        pre_scores = scores.detach().clone()
        post_scores = self.inner(input_ids, scores)
        if re.search(r'"answer"\s*:\s*$', decoded):
            pre_values, pre_ids = torch.topk(pre_scores[0], k=8)
            post_values, post_ids = torch.topk(post_scores[0], k=8)
            self.records.append(
                {
                    "trace_version": TRACE_VERSION,
                    "generation_step": int(generated.shape[0]),
                    "decoded_suffix": decoded[-240:],
                    "parser_state": "not_exposed_by_xgrammar_hf_processor",
                    "masked_count": int(torch.isneginf(post_scores[0]).sum().item()),
                    "top_pre_mask": [
                        token_entry(self.tokenizer, token_id, value)
                        for token_id, value in zip(
                            pre_ids.tolist(), pre_values.tolist(), strict=True
                        )
                    ],
                    "top_post_mask": [
                        token_entry(self.tokenizer, token_id, value)
                        for token_id, value in zip(
                            post_ids.tolist(), post_values.tolist(), strict=True
                        )
                    ],
                    "known_pre_mask_scores": self._known_scores(pre_scores),
                    "known_post_mask_scores": self._known_scores(post_scores),
                }
            )
        return post_scores

    def finalize(self, output_ids: torch.Tensor) -> list[dict[str, Any]]:
        for record in self.records:
            selected_index = self.prompt_tokens + record["generation_step"]
            if selected_index < output_ids.shape[1]:
                token_id = int(output_ids[0, selected_index].item())
                record["selected_token_id"] = token_id
                record["selected_text"] = self.tokenizer.decode(
                    [token_id], skip_special_tokens=False
                )
            else:
                record["selected_token_id"] = None
                record["selected_text"] = None
        return self.records


def generate_transformers(
    model: Any,
    tokenizer: Any,
    formatted_prompt: str,
    max_new_tokens: int,
    logits_processor: Any,
) -> GenerationMeasurement:
    device = next(model.parameters()).device
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            logits_processor=[logits_processor],
        )
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    prompt_tokens = int(inputs["input_ids"].shape[1])
    generated = output_ids[0, prompt_tokens:]
    raw_output = tokenizer.decode(generated, skip_special_tokens=True)
    return GenerationMeasurement(
        raw_output=raw_output,
        latency_ms=(time.perf_counter() - started) * 1000,
        prompt_tokens=prompt_tokens,
        generated_content_tokens=count_generated_content_tokens(tokenizer, raw_output),
        generated_token_ids=int(generated.shape[0]),
        output_ids=output_ids,
    )


def generate_outlines(
    generator: Any,
    tokenizer: Any,
    raw_prompt: str,
    max_new_tokens: int,
    use_cuda: bool,
) -> GenerationMeasurement:
    formatted_prompt = format_chat_prompt(tokenizer, raw_prompt)
    if use_cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    raw_output = generator(raw_prompt, max_new_tokens=max_new_tokens, do_sample=False)
    if use_cuda:
        torch.cuda.synchronize()
    content_tokens = count_generated_content_tokens(tokenizer, raw_output)
    return GenerationMeasurement(
        raw_output=raw_output,
        latency_ms=(time.perf_counter() - started) * 1000,
        prompt_tokens=len(
            tokenizer(formatted_prompt, add_special_tokens=False)["input_ids"]
        ),
        generated_content_tokens=content_tokens,
        generated_token_ids=content_tokens,
    )


def warm_up(model: Any, tokenizer: Any, formatted_prompt: str, use_cuda: bool) -> None:
    device = next(model.parameters()).device
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    with torch.inference_mode():
        model.generate(
            **inputs,
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    if use_cuda:
        torch.cuda.synchronize()


def run_config(
    *,
    model: str,
    revision: str,
    dataset: Path,
    dataset_role: str,
    representation: RuntimeRepresentation,
    backend: RuntimeBackend,
    seed: int,
    max_new_tokens: int,
    dtype: str,
    device_map_auto: bool,
    runner_sha256: str,
    runtime_sha256: str,
    exclude_item_ids: Iterable[str] = (),
) -> dict[str, Any]:
    spec = representation_spec(representation, backend)
    internal = schema_for_spec(spec)
    external = (
        canonical_external_schema(spec.field_order)
        if representation is RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING
        else external_schema(spec.field_order)
    )
    return {
        "runtime_version": RUNTIME_VERSION,
        "model": model,
        "revision": revision,
        "dataset_path": str(dataset),
        "dataset_role": dataset_role,
        "dataset_sha256": file_sha256(dataset),
        "excluded_item_ids": sorted(set(exclude_item_ids)),
        "condition": spec.name,
        "backend": backend.value,
        "answer_representation": representation.value,
        "field_order": list(spec.field_order),
        "prompt_version": PROMPT_VERSION,
        "seed": seed,
        "do_sample": False,
        "max_new_tokens": max_new_tokens,
        "dtype": dtype,
        "device_map_auto": device_map_auto,
        "xgrammar_any_whitespace": (
            XGRAMMAR_ANY_WHITESPACE if backend is RuntimeBackend.XGRAMMAR else None
        ),
        "xgrammar_separators": (
            list(XGRAMMAR_SEPARATORS) if backend is RuntimeBackend.XGRAMMAR else None
        ),
        "outlines_whitespace_pattern": (
            OUTLINES_WHITESPACE_PATTERN if backend is RuntimeBackend.OUTLINES else None
        ),
        "internal_schema_sha256": schema_sha256(internal),
        "external_schema_sha256": schema_sha256(external),
        "transducer_version": (
            TRANSDUCER_VERSION
            if representation is RuntimeRepresentation.INTEGER
            else None
        ),
        "plan_id": (
            "integer-string-representation-v1"
            if representation is RuntimeRepresentation.INTEGER
            else "canonical-signed-integer-string-control-v1"
            if representation is RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING
            else "external-broad-numeric-string-control-v1"
        ),
        "runner_sha256": runner_sha256,
        "runtime_sha256": runtime_sha256,
    }


def manifest_payload(
    config: dict[str, Any],
    loaded: LoadedModel,
    *,
    source_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "manifest_version": "contract-generation-manifest-v1",
        "run_config": config,
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count(),
        "gpus": [
            {
                "index": index,
                "name": torch.cuda.get_device_properties(index).name,
                "total_memory": torch.cuda.get_device_properties(index).total_memory,
            }
            for index in range(torch.cuda.device_count())
        ],
        "model_revision": loaded.model_revision,
        "tokenizer_revision": loaded.tokenizer_revision,
        "packages": package_versions(),
        "source_manifest_sha256": source_manifest_sha256,
    }


def write_or_verify_manifest(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        immutable_keys = (
            "run_config",
            "torch",
            "cuda_runtime",
            "gpus",
            "model_revision",
            "tokenizer_revision",
            "packages",
            "source_manifest_sha256",
        )
        mismatches = [key for key in immutable_keys if existing.get(key) != payload.get(key)]
        if mismatches:
            raise ValueError(f"{path} manifest mismatch: {mismatches}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def existing_state(
    path: Path,
    *,
    resume: bool,
    expected_signature: str,
) -> tuple[set[str], str | None]:
    if not path.exists():
        return set(), None
    if not resume:
        raise FileExistsError(f"refusing to overwrite {path}; pass --resume")
    rows = load_jsonl(path)
    signatures = {str(row.get("run_signature")) for row in rows}
    if signatures != {expected_signature}:
        raise ValueError(f"{path} contains a different run signature")
    item_ids = [str(row.get("item_id")) for row in rows]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError(f"{path} contains duplicate item IDs")
    run_ids = {str(row.get("run_id")) for row in rows}
    if len(run_ids) != 1:
        raise ValueError(f"{path} must contain exactly one run ID when resumed")
    return set(item_ids), next(iter(run_ids))


def score_output(
    raw_output: str,
    representation: RuntimeRepresentation,
    backend: RuntimeBackend,
    gold_answer: str,
) -> dict[str, Any]:
    spec = representation_spec(representation, backend)
    external = (
        canonical_external_schema(spec.field_order)
        if representation is RuntimeRepresentation.CANONICAL_SIGNED_INTEGER_STRING
        else external_schema(spec.field_order)
    )
    return score_alignment_output(
        raw_output,
        schema_for_spec(spec),
        external,
        spec.field_order,
        gold_answer,
        spec.answer_representation,
    )
