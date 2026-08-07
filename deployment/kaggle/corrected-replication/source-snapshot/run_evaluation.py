#!/usr/bin/env python3
"""Run resumable, item-level GSM8K baseline evaluations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import re
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any

import torch
from jsonschema import ValidationError, validate
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
FREE_PROMPT_VERSION = "day2-v4-reasoning-before-answer"
JSON_PROMPT_VERSION = "day3-v8-symbolic-json-template"
XGRAMMAR_ANY_WHITESPACE = False
XGRAMMAR_SEPARATORS = (",", ":")
OUTLINES_WHITESPACE_PATTERN = ""
CONDITIONS = (
    "free",
    "prompted_json_reasoning_first",
    "prompted_json_answer_first",
    "outlines_json_reasoning_first",
    "outlines_json_answer_first",
    "xgrammar_json_reasoning_first",
)
NUMBER_PATTERN = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?(?:/\d[\d,]*)?")
NUMERIC_ANSWER_PATTERN = re.compile(
    r"^-?(?:(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?|"
    r"(?:\d+|\d{1,3}(?:,\d{3})+)/(?:\d+|\d{1,3}(?:,\d{3})+))$"
)


def prompt_version(condition: str) -> str:
    return FREE_PROMPT_VERSION if condition == "free" else JSON_PROMPT_VERSION


def schema_for_condition(condition: str) -> dict[str, Any]:
    if condition.endswith("reasoning_first"):
        fields = (
            ("reasoning", {"type": "string"}),
            ("answer", {"type": "string", "pattern": NUMERIC_ANSWER_PATTERN.pattern}),
        )
    elif condition.endswith("answer_first"):
        fields = (
            ("answer", {"type": "string", "pattern": NUMERIC_ANSWER_PATTERN.pattern}),
            ("reasoning", {"type": "string"}),
        )
    else:
        raise ValueError(f"No JSON schema for condition {condition}")
    return {
        "type": "object",
        "properties": dict(fields),
        "required": [name for name, _ in fields],
        "additionalProperties": False,
    }


def make_prompt(question: str, condition: str) -> str:
    if condition == "free":
        return (
            "Solve this grade-school math problem. First give only 1-3 short calculation "
            "sentences, without lists or headings. Do not state the final answer before the "
            "reasoning. On the final line write exactly: Final answer: <number>\n\n"
            f"Question:\n{question}"
        )

    schema = schema_for_condition(condition)
    ordered_keys = ", then ".join(f'"{key}"' for key in schema["properties"])
    template = {
        key: "<final numeric answer>" if key == "answer" else "<calculation sentences>"
        for key in schema["properties"]
    }
    return (
        "Solve this grade-school math problem. The reasoning value must contain only 1-3 "
        "short calculation sentences, without lists or headings. "
        "The answer value must contain only the final numeric answer, with no units, "
        "currency symbol, or reasoning. "
        "Return only one valid JSON object, with no markdown or extra text. "
        f"Use exactly two keys in this field order: {ordered_keys}. "
        "Replace both angle-bracket placeholders in this template and do not output "
        "the angle brackets themselves:\n"
        f"{json.dumps(template, ensure_ascii=False)}\n\n"
        f"Question:\n{question}"
    )


def format_chat_prompt(tokenizer, prompt: str) -> str:
    """Apply the model chat template exactly once to a raw project prompt."""

    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )


def count_generated_content_tokens(tokenizer, raw_output: str) -> int:
    """Count visible generated content consistently across wrapper backends."""

    return len(tokenizer(raw_output, add_special_tokens=False)["input_ids"])


def canonical_number(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip().replace(",", "").replace("$", "")
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        return None
    try:
        if "/" in cleaned and re.fullmatch(r"-?\d+/\d+", cleaned):
            return str(Fraction(cleaned))
        number = Decimal(cleaned)
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return cleaned.casefold()

    if number == number.to_integral():
        return str(number.quantize(Decimal(1)))
    return format(number.normalize(), "f")


def extract_number(text: str) -> str | None:
    matches = NUMBER_PATTERN.findall(text)
    return matches[-1] if matches else None


def score_free(text: str) -> dict[str, Any]:
    marker_matches = list(
        re.finditer(r"Final answer\s*:\s*", text, flags=re.IGNORECASE)
    )
    method = "last_number_fallback"
    answer = None
    marker_at_end = False
    if marker_matches:
        candidate_text = text[marker_matches[-1].end() :]
        number_match = NUMBER_PATTERN.search(candidate_text)
        if number_match:
            answer = number_match.group(0)
            trailing = candidate_text[number_match.end() :].strip()
            marker_at_end = trailing in {"", "."}
        method = "final_answer_marker"
    else:
        answer = extract_number(text)
    return {
        "parsed_json": None,
        "whole_response_valid_json": None,
        "first_object_recoverable": None,
        "schema_valid": None,
        "json_key_order": None,
        "field_order_matches": None,
        "final_answer_marker_present": bool(marker_matches),
        "final_answer_marker_at_end": marker_at_end,
        "predicted_answer": answer,
        "predicted_answer_strict": None,
        "answer_field_strict_numeric": None,
        "answer_extraction_method": method if answer is not None else "not_found",
        "validation_error": None,
    }


def parse_whole_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return None, f"expected object, got {type(value).__name__}"
    return value, None


def recover_first_object(
    text: str,
) -> tuple[dict[str, Any] | None, int | None, str | None]:
    decoder = json.JSONDecoder()
    errors: list[str] = []
    for position, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError as exc:
            errors.append(f"offset {position}: {exc.msg}")
            continue
        if isinstance(value, dict):
            return value, position, None
    error = "; ".join(errors[:3]) if errors else "no JSON object start found"
    return None, None, error


def score_json(text: str, condition: str) -> dict[str, Any]:
    schema = schema_for_condition(condition)
    expected_order = list(schema["properties"])
    whole, whole_error = parse_whole_json(text)
    recovered, _, recovery_error = recover_first_object(text)
    parsed = whole if whole is not None else recovered
    schema_valid = False
    validation_error = whole_error

    if parsed is not None:
        try:
            validate(instance=parsed, schema=schema)
            schema_valid = True
        except ValidationError as exc:
            validation_error = f"ValidationError: {exc.message}"
    elif recovery_error:
        validation_error = (
            f"{whole_error}; recovery failed: {recovery_error}"
            if whole_error
            else recovery_error
        )

    key_order = list(parsed) if parsed is not None else None
    answer_value = parsed.get("answer") if parsed is not None else None
    answer_text = str(answer_value) if answer_value is not None else None
    answer = extract_number(answer_text) if answer_text is not None else None
    strict_answer = (
        answer_text.strip()
        if isinstance(answer_value, str)
        and NUMERIC_ANSWER_PATTERN.fullmatch(answer_text.strip())
        else None
    )
    return {
        "parsed_json": parsed,
        "whole_response_valid_json": whole is not None,
        "first_object_recoverable": recovered is not None,
        "schema_valid": schema_valid,
        "json_key_order": key_order,
        "field_order_matches": key_order == expected_order
        if key_order is not None
        else False,
        "final_answer_marker_present": None,
        "final_answer_marker_at_end": None,
        "predicted_answer": answer,
        "predicted_answer_strict": strict_answer,
        "answer_field_strict_numeric": strict_answer is not None,
        "answer_extraction_method": "json_answer_field"
        if answer is not None
        else "not_found",
        "validation_error": validation_error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-warmup", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="Load the model with bitsandbytes NF4 quantization (CUDA only)",
    )
    parser.add_argument(
        "--device-map-auto",
        action="store_true",
        help="Let Accelerate split a full-precision model across all CUDA GPUs",
    )
    parser.add_argument(
        "--dtype",
        choices=("auto", "float16", "float32"),
        default="float16",
        help="Model dtype; auto preserves the checkpoint's declared dtype",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        help="Write or verify an environment and run-configuration manifest.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}:{line_number}: {exc}"
                ) from exc
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_signature(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    config = {
        "model": args.model,
        "prompt_version": prompt_version(args.condition),
        "dataset_sha256": file_sha256(args.dataset),
        "condition": args.condition,
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
        "do_sample": args.do_sample,
        "temperature": args.temperature if args.do_sample else None,
        "top_p": args.top_p if args.do_sample else None,
        "load_in_4bit": args.load_in_4bit,
        "device_map_auto": args.device_map_auto,
        "dtype": args.dtype,
        "xgrammar_any_whitespace": (
            XGRAMMAR_ANY_WHITESPACE if args.condition.startswith("xgrammar_") else None
        ),
        "xgrammar_separators": (
            list(XGRAMMAR_SEPARATORS)
            if args.condition.startswith("xgrammar_")
            else None
        ),
        "outlines_whitespace_pattern": (
            OUTLINES_WHITESPACE_PATTERN
            if args.condition.startswith("outlines_")
            else None
        ),
    }
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12], config


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
    run_config: dict[str, Any],
    model,
) -> None:
    manifest = {
        "run_config": run_config,
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
        "runner_sha256": file_sha256(Path(__file__)),
    }
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("run_config") != run_config:
            raise ValueError(f"{path} does not match the requested run configuration")
        if existing.get("runner_sha256") != manifest["runner_sha256"]:
            raise ValueError(f"{path} was created by a different runner source")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_model(
    model_name: str,
    force_cpu: bool,
    load_in_4bit: bool,
    device_map_auto: bool,
    dtype: str,
):
    use_cuda = torch.cuda.is_available() and not force_cpu
    if load_in_4bit and not use_cuda:
        raise RuntimeError("--load-in-4bit requires an available CUDA GPU")
    if device_map_auto and not use_cuda:
        raise RuntimeError("--device-map-auto requires an available CUDA GPU")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    config = AutoConfig.from_pretrained(model_name)
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
        "torch_dtype": torch_dtype,
        "low_cpu_mem_usage": True,
        "attn_implementation": "eager",
    }
    if use_cuda:
        if device_map_auto:
            load_kwargs["device_map"] = "auto"
            load_kwargs["max_memory"] = {
                index: f"{max(1, int(torch.cuda.get_device_properties(index).total_memory / 2**30) - 2)}GiB"
                for index in range(torch.cuda.device_count())
            }
        else:
            load_kwargs["device_map"] = {"": "cuda:0"}
    if load_in_4bit:
        from transformers import BitsAndBytesConfig

        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
    model.eval()
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    return tokenizer, model, use_cuda


def generation_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": args.do_sample,
    }
    if args.do_sample:
        kwargs.update({"temperature": args.temperature, "top_p": args.top_p})
    return kwargs


def timed_transformers_generate(
    model,
    tokenizer,
    formatted_prompt: str,
    args: argparse.Namespace,
    logits_processor=None,
) -> tuple[str, float, int, int]:
    device = next(model.parameters()).device
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    kwargs = generation_kwargs(args)
    kwargs["pad_token_id"] = tokenizer.eos_token_id
    if logits_processor is not None:
        kwargs["logits_processor"] = [logits_processor]
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    with torch.inference_mode():
        output_ids = model.generate(**inputs, **kwargs)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    latency_ms = (time.perf_counter() - started) * 1000
    prompt_tokens = int(inputs["input_ids"].shape[1])
    generated_ids = output_ids[0, prompt_tokens:]
    raw_output = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return (
        raw_output,
        latency_ms,
        prompt_tokens,
        count_generated_content_tokens(tokenizer, raw_output),
    )


def build_outlines_generator(model, tokenizer, condition: str):
    from outlines import Generator, from_transformers
    from outlines.types import JsonSchema

    outlines_model = from_transformers(model, tokenizer)
    output_type = JsonSchema(
        schema_for_condition(condition),
        whitespace_pattern=OUTLINES_WHITESPACE_PATTERN,
    )
    return Generator(outlines_model, output_type)


def timed_outlines_generate(
    generator,
    tokenizer,
    raw_prompt: str,
    args: argparse.Namespace,
    use_cuda: bool,
) -> tuple[str, float, int, int]:
    # Outlines owns chat templating for string inputs. Passing an already formatted
    # string would cause its Transformers adapter to apply the template a second time.
    formatted_prompt = format_chat_prompt(tokenizer, raw_prompt)
    kwargs = generation_kwargs(args)
    if use_cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    raw_output = generator(raw_prompt, **kwargs)
    if use_cuda:
        torch.cuda.synchronize()
    latency_ms = (time.perf_counter() - started) * 1000
    prompt_tokens = len(
        tokenizer(formatted_prompt, add_special_tokens=False)["input_ids"]
    )
    generated_tokens = count_generated_content_tokens(tokenizer, raw_output)
    return raw_output, latency_ms, prompt_tokens, generated_tokens


def build_xgrammar_compiled_grammar(model, tokenizer, condition: str):
    import xgrammar as xgr

    tokenizer_info = xgr.TokenizerInfo.from_huggingface(
        tokenizer,
        vocab_size=model.config.vocab_size,
    )
    compiler = xgr.GrammarCompiler(tokenizer_info)
    return compiler.compile_json_schema(
        schema_for_condition(condition),
        any_whitespace=XGRAMMAR_ANY_WHITESPACE,
        separators=XGRAMMAR_SEPARATORS,
        strict_mode=True,
        any_order=False,
    )


def xgrammar_logits_processor(compiled_grammar):
    import xgrammar as xgr

    return xgr.contrib.hf.LogitsProcessor(compiled_grammar)


def select_examples(
    rows: list[dict[str, Any]], args: argparse.Namespace
) -> list[dict[str, Any]]:
    end = args.end_index if args.end_index is not None else len(rows)
    selected = rows[args.start_index : end]
    if args.limit is not None:
        selected = selected[: args.limit]
    ids = [str(row["id"]) for row in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("Selected dataset rows contain duplicate IDs")
    return selected


def existing_run_state(
    path: Path,
    resume: bool,
    signature: str,
) -> tuple[set[str], str | None]:
    if not path.exists():
        return set(), None
    if not resume:
        raise FileExistsError(
            f"Refusing to overwrite {path}; pass --resume or use a new path"
        )
    rows = load_jsonl(path)
    if any(row.get("run_signature") != signature for row in rows):
        raise ValueError(f"Existing rows in {path} do not match this run configuration")
    completed = {str(row["item_id"]) for row in rows}
    run_ids = {str(row["run_id"]) for row in rows}
    if len(run_ids) > 1:
        raise ValueError(f"Existing rows in {path} contain multiple run IDs")
    return completed, next(iter(run_ids), None)


def warm_up(model, tokenizer, formatted_prompt: str, use_cuda: bool) -> None:
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


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.max_new_tokens <= 0:
        raise SystemExit("--max-new-tokens must be positive")

    examples = select_examples(load_jsonl(args.dataset), args)
    signature, run_config = make_signature(args)
    completed_ids, existing_run_id = existing_run_state(
        args.out, args.resume, signature
    )
    pending = [row for row in examples if str(row["id"]) not in completed_ids]
    if not pending:
        print(
            f"nothing to do: all {len(examples)} selected rows already exist in {args.out}"
        )
        return

    set_seed(args.seed)
    tokenizer, model, use_cuda = load_model(
        args.model,
        args.cpu,
        args.load_in_4bit,
        args.device_map_auto,
        args.dtype,
    )
    if args.manifest_out is not None:
        write_or_verify_manifest(args.manifest_out, run_config, model)
    model_revision = getattr(model.config, "_commit_hash", None)
    run_id = (
        existing_run_id or f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{signature}"
    )
    is_outlines = args.condition.startswith("outlines_")
    outlines_generator = (
        build_outlines_generator(model, tokenizer, args.condition)
        if is_outlines
        else None
    )
    is_xgrammar = args.condition.startswith("xgrammar_")
    xgrammar_compiled = (
        build_xgrammar_compiled_grammar(model, tokenizer, args.condition)
        if is_xgrammar
        else None
    )

    if not args.skip_warmup:
        first_prompt = make_prompt(pending[0]["question"], args.condition)
        first_formatted = format_chat_prompt(tokenizer, first_prompt)
        warm_up(model, tokenizer, first_formatted, use_cuda)
        set_seed(args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.out.exists() else "x"
    with args.out.open(mode, encoding="utf-8") as output_file:
        for position, example in enumerate(pending, start=1):
            prompt = make_prompt(example["question"], args.condition)
            formatted_prompt = format_chat_prompt(tokenizer, prompt)
            raw_output = ""
            latency_ms = 0.0
            prompt_tokens = 0
            generated_tokens = 0
            generation_error = None
            try:
                if outlines_generator is not None:
                    generated = timed_outlines_generate(
                        outlines_generator,
                        tokenizer,
                        prompt,
                        args,
                        use_cuda,
                    )
                elif xgrammar_compiled is not None:
                    generated = timed_transformers_generate(
                        model,
                        tokenizer,
                        formatted_prompt,
                        args,
                        logits_processor=xgrammar_logits_processor(xgrammar_compiled),
                    )
                else:
                    generated = timed_transformers_generate(
                        model,
                        tokenizer,
                        formatted_prompt,
                        args,
                    )
                raw_output, latency_ms, prompt_tokens, generated_tokens = generated
            except Exception as exc:  # noqa: BLE001 - preserve every assigned item.
                generation_error = f"{type(exc).__name__}: {exc}"
                if use_cuda:
                    torch.cuda.empty_cache()

            scored = (
                score_free(raw_output)
                if args.condition == "free"
                else score_json(raw_output, args.condition)
            )
            predicted_normalized = canonical_number(scored["predicted_answer"])
            predicted_strict_normalized = canonical_number(
                scored["predicted_answer_strict"]
            )
            gold_normalized = canonical_number(example["gold_answer"])
            row = {
                "run_id": run_id,
                "run_signature": signature,
                "timestamp": datetime.now(UTC).isoformat(),
                "model": args.model,
                "model_revision": model_revision,
                "device": (
                    "cuda:auto"
                    if use_cuda and args.device_map_auto
                    else "cuda:0"
                    if use_cuda
                    else "cpu"
                ),
                "dataset": "gsm8k",
                "dataset_sha256": run_config["dataset_sha256"],
                "condition": args.condition,
                "seed": args.seed,
                "do_sample": args.do_sample,
                "temperature": args.temperature if args.do_sample else None,
                "top_p": args.top_p if args.do_sample else None,
                "max_new_tokens": args.max_new_tokens,
                "load_in_4bit": args.load_in_4bit,
                "device_map_auto": args.device_map_auto,
                "dtype": args.dtype,
                "prompt_version": prompt_version(args.condition),
                "xgrammar_any_whitespace": (
                    XGRAMMAR_ANY_WHITESPACE if is_xgrammar else None
                ),
                "xgrammar_separators": list(XGRAMMAR_SEPARATORS)
                if is_xgrammar
                else None,
                "outlines_whitespace_pattern": OUTLINES_WHITESPACE_PATTERN
                if is_outlines
                else None,
                "item_id": example["id"],
                "source_index": example.get("source_index"),
                "question": example["question"],
                "prompt": prompt,
                "formatted_prompt": formatted_prompt,
                "raw_output": raw_output,
                **scored,
                "predicted_answer_normalized": predicted_normalized,
                "predicted_answer_strict_normalized": predicted_strict_normalized,
                "gold_answer": example["gold_answer"],
                "gold_answer_normalized": gold_normalized,
                "correct_exact": (
                    predicted_normalized is not None
                    and gold_normalized is not None
                    and predicted_normalized == gold_normalized
                ),
                "correct_exact_strict": (
                    predicted_strict_normalized is not None
                    and gold_normalized is not None
                    and predicted_strict_normalized == gold_normalized
                )
                if args.condition != "free"
                else None,
                "latency_ms": round(latency_ms, 3),
                "prompt_tokens": prompt_tokens,
                "generated_tokens": generated_tokens,
                "hit_max_new_tokens": generated_tokens >= args.max_new_tokens,
                "error": generation_error,
            }
            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            output_file.flush()
            print(
                f"[{position}/{len(pending)}] {example['id']} "
                f"pred={scored['predicted_answer']!r} gold={example['gold_answer']!r} "
                f"correct={row['correct_exact']} error={generation_error!r}"
            )

    print(f"wrote {len(pending)} rows to {args.out}")


if __name__ == "__main__":
    main()
