#!/usr/bin/env python3
"""Run a resumable, contract-preserving representation-alignment condition."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "src").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import torch
from project_a.metrics import score_alignment_output
from project_a.schema_variants import (
    CONDITIONS,
    AnswerRepresentation,
    make_prompt,
    schema_for_spec,
    schema_sha256,
    spec_for_condition,
)
from project_a.transducer import TRANSDUCER_VERSION
from transformers import LogitsProcessor

from run_evaluation import (  # noqa: E402
    OUTLINES_WHITESPACE_PATTERN,
    XGRAMMAR_ANY_WHITESPACE,
    XGRAMMAR_SEPARATORS,
    count_generated_content_tokens,
    file_sha256,
    format_chat_prompt,
    load_jsonl,
    load_model,
    select_examples,
    set_seed,
    warm_up,
)

PROMPT_VERSION = "representation-alignment-v1"
TRACE_VERSION = "answer-boundary-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-warmup", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--device-map-auto", action="store_true")
    parser.add_argument(
        "--dtype", choices=("auto", "float16", "float32"), default="float16"
    )
    parser.add_argument(
        "--trace-item-id",
        action="append",
        default=[],
        help="Item ID to trace at the answer boundary. Supported for XGrammar only.",
    )
    parser.add_argument(
        "--trace-out",
        type=Path,
        help="Append compact XGrammar answer-boundary records to this JSONL path.",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        help="Write or verify a run manifest before generating rows.",
    )
    parser.add_argument(
        "--plan-id", default="integer-string-representation-v1"
    )
    return parser.parse_args()


def run_config(args: argparse.Namespace) -> dict[str, Any]:
    spec = spec_for_condition(args.condition)
    internal_schema = schema_for_spec(spec)
    from project_a.schema_variants import external_schema

    external = external_schema(spec.field_order)
    return {
        "model": args.model,
        "condition": spec.name,
        "backend": spec.backend,
        "answer_representation": spec.answer_representation.value,
        "diagnostic_only": spec.diagnostic_only,
        "field_order": list(spec.field_order),
        "prompt_version": PROMPT_VERSION,
        "dataset_sha256": file_sha256(args.dataset),
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
        "device_map_auto": args.device_map_auto,
        "dtype": args.dtype,
        "xgrammar_any_whitespace": (
            XGRAMMAR_ANY_WHITESPACE if spec.backend == "xgrammar" else None
        ),
        "xgrammar_separators": (
            list(XGRAMMAR_SEPARATORS) if spec.backend == "xgrammar" else None
        ),
        "outlines_whitespace_pattern": (
            OUTLINES_WHITESPACE_PATTERN if spec.backend == "outlines" else None
        ),
        "internal_schema_sha256": schema_sha256(internal_schema),
        "external_schema_sha256": schema_sha256(external),
        "transducer_version": TRANSDUCER_VERSION,
        "plan_id": args.plan_id,
        "runner_sha256": file_sha256(Path(__file__)),
    }


def signature(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def existing_state(path: Path, resume: bool, expected_signature: str) -> tuple[set[str], str | None]:
    if not path.exists():
        return set(), None
    if not resume:
        raise FileExistsError(f"Refusing to overwrite {path}; pass --resume or use a new path")
    rows = load_jsonl(path)
    if any(str(row.get("run_signature")) != expected_signature for row in rows):
        raise ValueError(f"{path} contains rows with a different run signature")
    run_ids = {str(row["run_id"]) for row in rows}
    if len(run_ids) > 1:
        raise ValueError(f"{path} contains multiple run IDs")
    return {str(row["item_id"]) for row in rows}, next(iter(run_ids), None)


def build_outlines_generator(model, tokenizer, schema: dict[str, Any]):
    from outlines import Generator, from_transformers
    from outlines.types import JsonSchema

    return Generator(
        from_transformers(model, tokenizer),
        JsonSchema(schema, whitespace_pattern=OUTLINES_WHITESPACE_PATTERN),
    )


def build_xgrammar_grammar(model, tokenizer, schema: dict[str, Any]):
    import xgrammar as xgr

    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer, vocab_size=model.config.vocab_size
    )
    compiler = xgr.GrammarCompiler(tokenizer_info)
    grammar = compiler.compile_json_schema(
        schema,
        any_whitespace=XGRAMMAR_ANY_WHITESPACE,
        separators=XGRAMMAR_SEPARATORS,
        strict_mode=True,
        any_order=False,
    )
    return grammar


def new_xgrammar_processor(compiled_grammar):
    """Create a fresh stateful processor for one generation call."""

    import xgrammar as xgr

    return xgr.contrib.hf.LogitsProcessor(compiled_grammar)


def token_entry(tokenizer, token_id: int, score: float) -> dict[str, Any]:
    return {
        "token_id": int(token_id),
        "text": tokenizer.decode([int(token_id)], skip_special_tokens=False),
        "score": round(float(score), 6),
    }


class AnswerBoundaryTraceProcessor(LogitsProcessor):
    """Record a compact pre-mask and post-mask snapshot at the answer boundary."""

    def __init__(self, inner, tokenizer, prompt_tokens: int) -> None:
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
                        for token_id, value in zip(pre_ids.tolist(), pre_values.tolist())
                    ],
                    "top_post_mask": [
                        token_entry(self.tokenizer, token_id, value)
                        for token_id, value in zip(post_ids.tolist(), post_values.tolist())
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
    model,
    tokenizer,
    formatted_prompt: str,
    max_new_tokens: int,
    logits_processor=None,
) -> tuple[str, float, int, int, torch.Tensor]:
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
            logits_processor=[logits_processor] if logits_processor is not None else None,
        )
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    prompt_tokens = int(inputs["input_ids"].shape[1])
    generated = output_ids[0, prompt_tokens:]
    raw_output = tokenizer.decode(generated, skip_special_tokens=True)
    return (
        raw_output,
        (time.perf_counter() - started) * 1000,
        prompt_tokens,
        count_generated_content_tokens(tokenizer, raw_output),
        output_ids,
    )


def generate_outlines(
    generator,
    tokenizer,
    raw_prompt: str,
    max_new_tokens: int,
    use_cuda: bool,
) -> tuple[str, float, int, int]:
    # Outlines applies the chat template to raw string inputs. Keep the formatted
    # form only for measuring the effective prompt length.
    formatted_prompt = format_chat_prompt(tokenizer, raw_prompt)
    if use_cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    raw = generator(raw_prompt, max_new_tokens=max_new_tokens, do_sample=False)
    if use_cuda:
        torch.cuda.synchronize()
    return (
        raw,
        (time.perf_counter() - started) * 1000,
        len(tokenizer(formatted_prompt, add_special_tokens=False)["input_ids"]),
        count_generated_content_tokens(tokenizer, raw),
    )


def write_trace(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in ("transformers", "accelerate", "jsonschema", "outlines", "xgrammar"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def write_or_verify_manifest(
    path: Path,
    config: dict[str, Any],
    model,
) -> None:
    manifest = {
        "run_config": config,
        "started_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count(),
        "gpu": (
            torch.cuda.get_device_properties(0).name
            if torch.cuda.is_available()
            else None
        ),
        "model_revision": getattr(model.config, "_commit_hash", None),
        "packages": package_versions(),
    }
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("run_config") != config:
            raise ValueError(f"{path} does not match the requested run configuration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.max_new_tokens <= 0:
        raise SystemExit("--max-new-tokens must be positive")
    if args.trace_item_id and args.trace_out is None:
        raise SystemExit("--trace-item-id requires --trace-out")

    spec = spec_for_condition(args.condition)
    config = run_config(args)
    run_signature = signature(config)
    examples = select_examples(load_jsonl(args.dataset), args)
    if spec.diagnostic_only and any(
        str(row["gold_answer"]).lstrip().startswith("-") for row in examples
    ):
        raise SystemExit("unsigned diagnostic condition cannot run on negative gold answers")
    completed, existing_run_id = existing_state(args.out, args.resume, run_signature)
    pending = [row for row in examples if str(row["id"]) not in completed]
    if not pending:
        print(f"nothing to do: all {len(examples)} selected rows already exist in {args.out}")
        return

    internal_schema = schema_for_spec(spec)
    from project_a.schema_variants import external_schema

    external = external_schema(spec.field_order)
    set_seed(args.seed)
    tokenizer, model, use_cuda = load_model(
        args.model, args.cpu, False, args.device_map_auto, args.dtype
    )
    model_revision = getattr(model.config, "_commit_hash", None)
    outlines_generator = (
        build_outlines_generator(model, tokenizer, internal_schema)
        if spec.backend == "outlines"
        else None
    )
    xgrammar_grammar = (
        build_xgrammar_grammar(model, tokenizer, internal_schema)
        if spec.backend == "xgrammar"
        else None
    )
    if args.manifest_out is not None:
        write_or_verify_manifest(args.manifest_out, config, model)
    if not args.skip_warmup:
        warmup_prompt = format_chat_prompt(
            tokenizer, make_prompt(pending[0]["question"], spec)
        )
        warm_up(model, tokenizer, warmup_prompt, use_cuda)
        set_seed(args.seed)

    run_id = existing_run_id or f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{run_signature}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.out.exists() else "x"
    trace_ids = {str(item_id) for item_id in args.trace_item_id}
    with args.out.open(mode, encoding="utf-8") as handle:
        for position, example in enumerate(pending, start=1):
            prompt = make_prompt(example["question"], spec)
            formatted_prompt = format_chat_prompt(tokenizer, prompt)
            raw_output = ""
            latency_ms = 0.0
            prompt_tokens = 0
            generated_tokens = 0
            error: str | None = None
            trace_records: list[dict[str, Any]] = []
            try:
                if outlines_generator is not None:
                    raw_output, latency_ms, prompt_tokens, generated_tokens = generate_outlines(
                        outlines_generator,
                        tokenizer,
                        prompt,
                        args.max_new_tokens,
                        use_cuda,
                    )
                else:
                    processor = (
                        new_xgrammar_processor(xgrammar_grammar)
                        if spec.backend == "xgrammar"
                        else None
                    )
                    trace_processor = None
                    if spec.backend == "xgrammar" and str(example["id"]) in trace_ids:
                        trace_processor = AnswerBoundaryTraceProcessor(
                            new_xgrammar_processor(xgrammar_grammar),
                            tokenizer,
                            len(tokenizer(formatted_prompt, add_special_tokens=False)["input_ids"]),
                        )
                        processor = trace_processor
                    generated = generate_transformers(
                        model,
                        tokenizer,
                        formatted_prompt,
                        args.max_new_tokens,
                        processor,
                    )
                    raw_output, latency_ms, prompt_tokens, generated_tokens, output_ids = generated
                    if trace_processor is not None:
                        trace_records = trace_processor.finalize(output_ids)
            except Exception as caught:  # Preserve every assigned row for auditing.
                error = f"{type(caught).__name__}: {caught}"
                if use_cuda:
                    torch.cuda.empty_cache()

            scored = score_alignment_output(
                raw_output,
                internal_schema,
                external,
                spec.field_order,
                str(example["gold_answer"]),
                spec.answer_representation,
            )
            row = {
                "run_id": run_id,
                "run_signature": run_signature,
                "timestamp": datetime.now(UTC).isoformat(),
                "model": args.model,
                "model_revision": model_revision,
                "device": "cuda:auto" if use_cuda and args.device_map_auto else "cuda:0" if use_cuda else "cpu",
                "dataset": "gsm8k",
                "dataset_sha256": config["dataset_sha256"],
                "condition": spec.name,
                "backend": spec.backend,
                "answer_representation": spec.answer_representation.value,
                "diagnostic_only": spec.diagnostic_only,
                "field_order": list(spec.field_order),
                "seed": args.seed,
                "do_sample": False,
                "max_new_tokens": args.max_new_tokens,
                "device_map_auto": args.device_map_auto,
                "dtype": args.dtype,
                "prompt_version": PROMPT_VERSION,
                "plan_id": args.plan_id,
                "internal_schema_sha256": config["internal_schema_sha256"],
                "external_schema_sha256": config["external_schema_sha256"],
                "xgrammar_any_whitespace": config["xgrammar_any_whitespace"],
                "item_id": example["id"],
                "source_index": example.get("source_index"),
                "selection_reason": example.get("selection_reason"),
                "question": example["question"],
                "prompt": prompt,
                "formatted_prompt": formatted_prompt,
                "raw_output": raw_output,
                "gold_answer": example["gold_answer"],
                **scored,
                "correct_exact": scored["semantic_correct"],
                "correct_exact_strict": scored["contract_valid_correct"],
                "latency_ms": round(latency_ms, 3),
                "prompt_tokens": prompt_tokens,
                "generated_tokens": generated_tokens,
                "hit_max_new_tokens": generated_tokens >= args.max_new_tokens,
                "error": error,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            for record in trace_records:
                record.update(
                    {
                        "item_id": example["id"],
                        "condition": spec.name,
                        "run_id": run_id,
                        "run_signature": run_signature,
                        "answer_representation": spec.answer_representation.value,
                    }
                )
            if args.trace_out is not None:
                write_trace(args.trace_out, trace_records)
            print(
                f"[{position}/{len(pending)}] {example['id']} "
                f"pred={scored['predicted_answer']!r} gold={example['gold_answer']!r} "
                f"semantic={scored['semantic_correct']} external={scored['external_schema_valid']} "
                f"error={error!r}",
                flush=True,
            )
    print(f"wrote {len(pending)} rows to {args.out}")
    print(json.dumps({"run_signature": run_signature, "run_config": config}, indent=2))


if __name__ == "__main__":
    main()
