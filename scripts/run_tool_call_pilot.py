#!/usr/bin/env python3
"""Run one bounded BFCL tool-call representation with resumable checkpoints."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "src").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from project_a.runtime import (  # noqa: E402
    build_xgrammar_grammar,
    existing_state,
    file_sha256,
    format_chat_prompt,
    generate_transformers,
    load_jsonl,
    load_model,
    manifest_payload,
    new_xgrammar_processor,
    set_seed,
    stable_signature,
    warm_up,
    write_or_verify_manifest,
)
from project_a.tool_runtime import make_tool_prompt, score_tool_output  # noqa: E402

RUNNER_VERSION = "bounded-bfcl-tool-runner-v1"
PROMPT_VERSION = "bounded-bfcl-tool-prompt-v1"
REPRESENTATIONS = ("external-integer-strings", "internal-integers")


def condition_name(representation: str) -> str:
    if representation == "external-integer-strings":
        return "xgrammar_tool_external_integer_strings"
    if representation == "internal-integers":
        return "xgrammar_tool_internal_integers"
    raise ValueError(f"unsupported representation: {representation}")


def tool_run_config(
    *,
    model: str,
    revision: str,
    dataset: Path,
    representation: str,
    seed: int,
    max_new_tokens: int,
    dtype: str,
    device_map_auto: bool,
    runner_sha256: str,
    runtime_sha256: str,
) -> dict[str, Any]:
    model_uses_integers = representation == "internal-integers"
    return {
        "runner_version": RUNNER_VERSION,
        "model": model,
        "revision": revision,
        "dataset_path": str(dataset),
        "dataset_sha256": file_sha256(dataset),
        "condition": condition_name(representation),
        "backend": "xgrammar",
        "representation": representation,
        "model_uses_integers": model_uses_integers,
        "prompt_version": PROMPT_VERSION,
        "seed": seed,
        "do_sample": False,
        "max_new_tokens": max_new_tokens,
        "dtype": dtype,
        "device_map_auto": device_map_auto,
        "xgrammar_any_whitespace": False,
        "xgrammar_separators": [",", ":"],
        "transducer_version": "recursive-integer-string-v1"
        if model_uses_integers
        else None,
        "heuristic_repairs": False,
        "runner_sha256": runner_sha256,
        "runtime_sha256": runtime_sha256,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--representation", choices=REPRESENTATIONS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--dtype", choices=("float16", "float32"), default="float32")
    parser.add_argument("--device-map-auto", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-warmup", action="store_true")
    return parser.parse_args()


def commit_remote_checkpoint() -> None:
    volume_name = os.environ.get("PROJECT_A_MODAL_EVIDENCE_VOLUME")
    if not volume_name:
        return
    import modal

    modal.Volume.from_name(volume_name).commit()


def device_label(use_cuda: bool, device_map_auto: bool) -> str:
    if not use_cuda:
        return "cpu"
    return "cuda:auto" if device_map_auto else "cuda:0"


def main() -> None:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.max_new_tokens <= 0:
        raise SystemExit("--max-new-tokens must be positive")
    source_manifest_hash = file_sha256(args.source_manifest)
    config = tool_run_config(
        model=args.model,
        revision=args.revision,
        dataset=args.dataset,
        representation=args.representation,
        seed=args.seed,
        max_new_tokens=args.max_new_tokens,
        dtype=args.dtype,
        device_map_auto=args.device_map_auto,
        runner_sha256=file_sha256(Path(__file__)),
        runtime_sha256=file_sha256(ROOT / "src/project_a/tool_runtime.py"),
    )
    run_signature = stable_signature(config)
    examples = load_jsonl(args.dataset)
    if args.limit is not None:
        examples = examples[: args.limit]
    selected_ids = [str(row["id"]) for row in examples]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("selected pilot rows contain duplicate IDs")
    completed, existing_run_id = existing_state(
        args.out, resume=args.resume, expected_signature=run_signature
    )
    pending = [row for row in examples if str(row["id"]) not in completed]
    if not pending:
        print(f"nothing to do: all {len(examples)} selected rows already exist")
        return

    set_seed(args.seed)
    loaded = load_model(
        args.model,
        revision=args.revision,
        force_cpu=args.cpu,
        device_map_auto=args.device_map_auto,
        dtype=args.dtype,
    )
    write_or_verify_manifest(
        args.manifest_out,
        manifest_payload(
            config,
            loaded,
            source_manifest_sha256=source_manifest_hash,
        ),
    )
    model_uses_integers = args.representation == "internal-integers"
    first_schema = (
        pending[0]["integer_call_schema"]
        if model_uses_integers
        else pending[0]["external_call_schema"]
    )
    first_prompt = make_tool_prompt(
        str(pending[0]["user_request"]),
        str(pending[0]["function_name"]),
        str(pending[0]["function_description"]),
        first_schema,
    )
    if not args.skip_warmup:
        warm_up(
            loaded.model,
            loaded.tokenizer,
            format_chat_prompt(loaded.tokenizer, first_prompt),
            loaded.use_cuda,
        )
        set_seed(args.seed)

    run_id = existing_run_id or (
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{run_signature}"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.out.exists() else "x"
    with args.out.open(mode, encoding="utf-8") as handle:
        for position, example in enumerate(pending, start=1):
            model_schema = (
                example["integer_call_schema"]
                if model_uses_integers
                else example["external_call_schema"]
            )
            raw_prompt = make_tool_prompt(
                str(example["user_request"]),
                str(example["function_name"]),
                str(example["function_description"]),
                model_schema,
            )
            formatted_prompt = format_chat_prompt(loaded.tokenizer, raw_prompt)
            measurement = None
            generation_error = None
            try:
                grammar = build_xgrammar_grammar(
                    loaded.model, loaded.tokenizer, model_schema
                )
                measurement = generate_transformers(
                    loaded.model,
                    loaded.tokenizer,
                    formatted_prompt,
                    args.max_new_tokens,
                    new_xgrammar_processor(grammar),
                )
            except Exception as error:  # preserve failures in the denominator
                generation_error = f"{type(error).__name__}: {error}"
            raw_output = measurement.raw_output if measurement is not None else ""
            scored = score_tool_output(
                raw_output,
                function_name=str(example["function_name"]),
                normalized_arguments_schema=example["normalized_arguments_schema"],
                acceptable_arguments=example["acceptable_arguments"],
                model_uses_integers=model_uses_integers,
            )
            generated_token_ids = (
                measurement.generated_token_ids if measurement is not None else 0
            )
            row = {
                "row_version": "bounded-bfcl-tool-row-v1",
                "run_id": run_id,
                "run_signature": run_signature,
                "timestamp": datetime.now(UTC).isoformat(),
                "model": args.model,
                "model_revision": loaded.model_revision,
                "tokenizer_revision": loaded.tokenizer_revision,
                "device": device_label(loaded.use_cuda, args.device_map_auto),
                "dataset": "BFCL_v4_simple_python",
                "dataset_sha256": config["dataset_sha256"],
                "condition": config["condition"],
                "backend": "xgrammar",
                "representation": args.representation,
                "seed": args.seed,
                "do_sample": False,
                "max_new_tokens": args.max_new_tokens,
                "dtype": args.dtype,
                "prompt_version": PROMPT_VERSION,
                "effective_chat_template_depth": 1,
                "item_id": example["id"],
                "source_index": example["source_index"],
                "subset": example["subset"],
                "user_request": example["user_request"],
                "function_name": example["function_name"],
                "required_integer_fields": example["required_integer_fields"],
                "negative_required_integer_references": example[
                    "negative_required_integer_references"
                ],
                "acceptable_arguments": example["acceptable_arguments"],
                "model_facing_schema": model_schema,
                "external_call_schema": example["external_call_schema"],
                "raw_prompt": raw_prompt,
                "formatted_prompt": formatted_prompt,
                "raw_output": raw_output,
                **scored,
                "latency_ms": round(
                    measurement.latency_ms if measurement is not None else 0.0, 3
                ),
                "prompt_tokens": measurement.prompt_tokens
                if measurement is not None
                else 0,
                "generated_tokens": measurement.generated_content_tokens
                if measurement is not None
                else 0,
                "generated_token_ids": generated_token_ids,
                "hit_max_new_tokens": generated_token_ids >= args.max_new_tokens,
                "error": generation_error,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            commit_remote_checkpoint()
            print(
                f"[{position}/{len(pending)}] {example['id']} "
                f"subset={example['subset']} external={scored['external_schema_valid']} "
                f"arguments={scored['argument_semantics_correct']} "
                f"executable={scored['executable_contract_success']} "
                f"error={generation_error!r}",
                flush=True,
            )
    print(f"wrote {len(pending)} rows to {args.out}")
    print(json.dumps({"run_signature": run_signature, "run_config": config}, indent=2))


if __name__ == "__main__":
    main()
