#!/usr/bin/env python3
"""Run either contract representation through one shared generation runtime."""

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

import torch
from project_a.runtime import (
    AnswerBoundaryTraceProcessor,
    RuntimeBackend,
    RuntimeRepresentation,
    build_outlines_generator,
    build_xgrammar_grammar,
    existing_state,
    file_sha256,
    format_chat_prompt,
    generate_outlines,
    generate_transformers,
    load_jsonl,
    load_model,
    make_contract_prompt,
    manifest_payload,
    new_xgrammar_processor,
    representation_spec,
    run_config,
    score_output,
    select_examples,
    set_seed,
    stable_signature,
    warm_up,
    write_or_verify_manifest,
)
from project_a.schema_variants import schema_for_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--revision",
        required=True,
        help="Immutable model and tokenizer commit revision.",
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--dataset-role", choices=("fresh", "bridge", "parity", "golden"), required=True
    )
    parser.add_argument(
        "--representation",
        choices=tuple(item.value for item in RuntimeRepresentation),
        required=True,
    )
    parser.add_argument(
        "--backend",
        choices=tuple(item.value for item in RuntimeBackend),
        default=RuntimeBackend.XGRAMMAR.value,
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--exclude-item-id", action="append", default=[])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-warmup", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--device-map-auto", action="store_true")
    parser.add_argument(
        "--dtype", choices=("auto", "float16", "float32"), default="float32"
    )
    parser.add_argument("--trace-item-id", action="append", default=[])
    parser.add_argument("--trace-out", type=Path)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.start_index < 0:
        raise SystemExit("--start-index must not be negative")
    if args.end_index is not None and args.end_index < args.start_index:
        raise SystemExit("--end-index must not precede --start-index")
    if args.max_new_tokens <= 0:
        raise SystemExit("--max-new-tokens must be positive")
    if args.trace_item_id and args.trace_out is None:
        raise SystemExit("--trace-item-id requires --trace-out")
    if args.trace_item_id and args.backend != RuntimeBackend.XGRAMMAR.value:
        raise SystemExit("answer-boundary traces require XGrammar")


def write_trace(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()


def device_label(use_cuda: bool, device_map_auto: bool) -> str:
    if not use_cuda:
        return "cpu"
    return "cuda:auto" if device_map_auto else "cuda:0"


def commit_remote_checkpoint() -> None:
    """Persist the mounted Modal evidence volume after each completed row."""

    volume_name = os.environ.get("PROJECT_A_MODAL_EVIDENCE_VOLUME")
    if not volume_name:
        return
    import modal

    modal.Volume.from_name(volume_name).commit()


def main() -> None:
    args = parse_args()
    validate_args(args)
    representation = RuntimeRepresentation(args.representation)
    backend = RuntimeBackend(args.backend)
    runtime_path = ROOT / "src/project_a/runtime.py"
    source_manifest_sha256 = (
        file_sha256(args.source_manifest) if args.source_manifest is not None else None
    )
    config = run_config(
        model=args.model,
        revision=args.revision,
        dataset=args.dataset,
        dataset_role=args.dataset_role,
        representation=representation,
        backend=backend,
        seed=args.seed,
        max_new_tokens=args.max_new_tokens,
        dtype=args.dtype,
        device_map_auto=args.device_map_auto,
        runner_sha256=file_sha256(Path(__file__)),
        runtime_sha256=file_sha256(runtime_path),
        exclude_item_ids=args.exclude_item_id,
    )
    run_signature = stable_signature(config)
    examples = select_examples(
        load_jsonl(args.dataset),
        start_index=args.start_index,
        end_index=args.end_index,
        limit=args.limit,
        exclude_item_ids=args.exclude_item_id,
    )
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
            source_manifest_sha256=source_manifest_sha256,
        ),
    )
    spec = representation_spec(representation, backend)
    internal_schema = schema_for_spec(spec)
    compiled_grammar = (
        build_xgrammar_grammar(loaded.model, loaded.tokenizer, internal_schema)
        if backend is RuntimeBackend.XGRAMMAR
        else None
    )
    outlines_generator = (
        build_outlines_generator(loaded.model, loaded.tokenizer, internal_schema)
        if backend is RuntimeBackend.OUTLINES
        else None
    )
    if not args.skip_warmup:
        raw_warmup = make_contract_prompt(str(pending[0]["question"]), representation)
        warm_up(
            loaded.model,
            loaded.tokenizer,
            format_chat_prompt(loaded.tokenizer, raw_warmup),
            loaded.use_cuda,
        )
        set_seed(args.seed)

    run_id = existing_run_id or (
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{run_signature}"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.out.exists() else "x"
    trace_ids = set(args.trace_item_id)
    with args.out.open(mode, encoding="utf-8") as handle:
        for position, example in enumerate(pending, start=1):
            raw_prompt = make_contract_prompt(str(example["question"]), representation)
            formatted_prompt = format_chat_prompt(loaded.tokenizer, raw_prompt)
            measurement = None
            trace_records: list[dict[str, Any]] = []
            error: str | None = None
            try:
                if backend is RuntimeBackend.XGRAMMAR:
                    processor = new_xgrammar_processor(compiled_grammar)
                    trace_processor = None
                    if str(example["id"]) in trace_ids:
                        trace_processor = AnswerBoundaryTraceProcessor(
                            new_xgrammar_processor(compiled_grammar),
                            loaded.tokenizer,
                            len(
                                loaded.tokenizer(
                                    formatted_prompt, add_special_tokens=False
                                )["input_ids"]
                            ),
                        )
                        processor = trace_processor
                    measurement = generate_transformers(
                        loaded.model,
                        loaded.tokenizer,
                        formatted_prompt,
                        args.max_new_tokens,
                        processor,
                    )
                    if trace_processor is not None and measurement.output_ids is not None:
                        trace_records = trace_processor.finalize(measurement.output_ids)
                else:
                    measurement = generate_outlines(
                        outlines_generator,
                        loaded.tokenizer,
                        raw_prompt,
                        args.max_new_tokens,
                        loaded.use_cuda,
                    )
            except Exception as caught:  # Preserve every assigned row for auditing.
                error = f"{type(caught).__name__}: {caught}"
                if loaded.use_cuda:
                    torch.cuda.empty_cache()

            raw_output = measurement.raw_output if measurement is not None else ""
            scored = score_output(
                raw_output,
                representation,
                backend,
                str(example["gold_answer"]),
            )
            generated_token_ids = (
                measurement.generated_token_ids if measurement is not None else 0
            )
            row = {
                "row_version": "contract-generation-row-v1",
                "run_id": run_id,
                "run_signature": run_signature,
                "timestamp": datetime.now(UTC).isoformat(),
                "model": args.model,
                "model_revision": loaded.model_revision,
                "tokenizer_revision": loaded.tokenizer_revision,
                "device": device_label(loaded.use_cuda, args.device_map_auto),
                "dataset": "gsm8k",
                "dataset_role": args.dataset_role,
                "dataset_sha256": config["dataset_sha256"],
                "condition": config["condition"],
                "backend": backend.value,
                "answer_representation": representation.value,
                "field_order": list(spec.field_order),
                "seed": args.seed,
                "do_sample": False,
                "max_new_tokens": args.max_new_tokens,
                "device_map_auto": args.device_map_auto,
                "dtype": args.dtype,
                "prompt_version": config["prompt_version"],
                "plan_id": config["plan_id"],
                "internal_schema_sha256": config["internal_schema_sha256"],
                "external_schema_sha256": config["external_schema_sha256"],
                "xgrammar_any_whitespace": config["xgrammar_any_whitespace"],
                "xgrammar_separators": config["xgrammar_separators"],
                "outlines_whitespace_pattern": config[
                    "outlines_whitespace_pattern"
                ],
                "effective_chat_template_depth": 1,
                "item_id": example["id"],
                "source_index": example.get("source_index"),
                "question": example["question"],
                "prompt": raw_prompt,
                "formatted_prompt": formatted_prompt,
                "raw_output": raw_output,
                "gold_answer": example["gold_answer"],
                **scored,
                "correct_exact": scored["semantic_correct"],
                "correct_exact_strict": scored["contract_valid_correct"],
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
                "error": error,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            for record in trace_records:
                record.update(
                    {
                        "item_id": example["id"],
                        "condition": config["condition"],
                        "run_id": run_id,
                        "run_signature": run_signature,
                        "answer_representation": representation.value,
                    }
                )
            if args.trace_out is not None:
                write_trace(args.trace_out, trace_records)
            commit_remote_checkpoint()
            print(
                f"[{position}/{len(pending)}] {example['id']} "
                f"pred={scored['predicted_answer']!r} gold={example['gold_answer']!r} "
                f"semantic={scored['semantic_correct']} "
                f"external={scored['external_schema_valid']} error={error!r}",
                flush=True,
            )
    print(f"wrote {len(pending)} rows to {args.out}")
    print(json.dumps({"run_signature": run_signature, "run_config": config}, indent=2))


if __name__ == "__main__":
    main()
