#!/usr/bin/env python3
"""Run resumable, item-level GSM8K baseline evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
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
JSON_PROMPT_VERSION = "day2-v5-numeric-answer-field"
CONDITIONS = (
    "free",
    "prompted_json_reasoning_first",
    "prompted_json_answer_first",
    "outlines_json_reasoning_first",
    "outlines_json_answer_first",
)
NUMBER_PATTERN = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?(?:/\d[\d,]*)?")


def prompt_version(condition: str) -> str:
    return FREE_PROMPT_VERSION if condition == "free" else JSON_PROMPT_VERSION


def schema_for_condition(condition: str) -> dict[str, Any]:
    if condition.endswith("reasoning_first"):
        fields = (("reasoning", {"type": "string"}), ("answer", {"type": "string"}))
    elif condition.endswith("answer_first"):
        fields = (("answer", {"type": "string"}), ("reasoning", {"type": "string"}))
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
    example = {key: "..." for key in schema["properties"]}
    return (
        "Solve this grade-school math problem. The reasoning value must contain only 1-3 "
        "short calculation sentences, without lists or headings. "
        "The answer value must contain only the final numeric answer, with no units, "
        "currency symbol, or reasoning. "
        "Return only one valid JSON object, with no markdown or extra text. "
        "Use exactly this field order:\n"
        f"{json.dumps(example, ensure_ascii=False)}\n\n"
        f"Question:\n{question}"
    )


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
    }
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12], config


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_model(model_name: str, force_cpu: bool):
    use_cuda = torch.cuda.is_available() and not force_cpu
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    config = AutoConfig.from_pretrained(model_name)
    if not getattr(config, "use_sliding_window", False):
        config.sliding_window = None
    load_kwargs: dict[str, Any] = {
        "config": config,
        "torch_dtype": torch.float16 if use_cuda else torch.float32,
        "low_cpu_mem_usage": True,
        "attn_implementation": "eager",
    }
    if use_cuda:
        load_kwargs["device_map"] = {"": "cuda:0"}
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
) -> tuple[str, float, int, int]:
    device = next(model.parameters()).device
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    kwargs = generation_kwargs(args)
    kwargs["pad_token_id"] = tokenizer.eos_token_id
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
    return raw_output, latency_ms, prompt_tokens, int(generated_ids.shape[0])


def build_outlines_generator(model, tokenizer, condition: str):
    from outlines import Generator, from_transformers
    from outlines.types import JsonSchema

    outlines_model = from_transformers(model, tokenizer)
    output_type = JsonSchema(schema_for_condition(condition))
    return Generator(outlines_model, output_type)


def timed_outlines_generate(
    generator,
    tokenizer,
    formatted_prompt: str,
    args: argparse.Namespace,
    use_cuda: bool,
) -> tuple[str, float, int, int]:
    kwargs = generation_kwargs(args)
    if use_cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    raw_output = generator(formatted_prompt, **kwargs)
    if use_cuda:
        torch.cuda.synchronize()
    latency_ms = (time.perf_counter() - started) * 1000
    prompt_tokens = len(
        tokenizer(formatted_prompt, add_special_tokens=False)["input_ids"]
    )
    generated_tokens = len(tokenizer(raw_output, add_special_tokens=False)["input_ids"])
    return raw_output, latency_ms, prompt_tokens, generated_tokens


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
    tokenizer, model, use_cuda = load_model(args.model, args.cpu)
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

    if not args.skip_warmup:
        first_prompt = make_prompt(pending[0]["question"], args.condition)
        first_formatted = tokenizer.apply_chat_template(
            [{"role": "user", "content": first_prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
        warm_up(model, tokenizer, first_formatted, use_cuda)
        set_seed(args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.out.exists() else "x"
    with args.out.open(mode, encoding="utf-8") as output_file:
        for position, example in enumerate(pending, start=1):
            prompt = make_prompt(example["question"], args.condition)
            formatted_prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
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
                        formatted_prompt,
                        args,
                        use_cuda,
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
            gold_normalized = canonical_number(example["gold_answer"])
            row = {
                "run_id": run_id,
                "run_signature": signature,
                "timestamp": datetime.now(UTC).isoformat(),
                "model": args.model,
                "model_revision": model_revision,
                "device": "cuda:0" if use_cuda else "cpu",
                "dataset": "gsm8k",
                "dataset_sha256": run_config["dataset_sha256"],
                "condition": args.condition,
                "seed": args.seed,
                "do_sample": args.do_sample,
                "temperature": args.temperature if args.do_sample else None,
                "top_p": args.top_p if args.do_sample else None,
                "max_new_tokens": args.max_new_tokens,
                "prompt_version": prompt_version(args.condition),
                "item_id": example["id"],
                "source_index": example.get("source_index"),
                "question": example["question"],
                "prompt": prompt,
                "formatted_prompt": formatted_prompt,
                "raw_output": raw_output,
                **scored,
                "predicted_answer_normalized": predicted_normalized,
                "gold_answer": example["gold_answer"],
                "gold_answer_normalized": gold_normalized,
                "correct_exact": (
                    predicted_normalized is not None
                    and gold_normalized is not None
                    and predicted_normalized == gold_normalized
                ),
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
