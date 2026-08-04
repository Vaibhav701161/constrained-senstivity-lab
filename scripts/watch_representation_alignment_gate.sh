#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

kernel="${KAGGLE_KERNEL:-vaibhav7011/contract-alignment-representation-gate}"
target="${ALIGNMENT_OUTPUT_TARGET:-experiments/representation-alignment-gate/results/cloud-targeted}"
poll_seconds="${KAGGLE_POLL_SECONDS:-60}"
dataset="experiments/representation-alignment-gate/targeted-items.jsonl"
source_root="deployment/kaggle/representation-alignment/source-snapshot"
run_dir="$target/results/representation-alignment-targeted"

if [[ -e "$target" ]]; then
    printf 'refusing to overwrite existing output target: %s\n' "$target" >&2
    exit 1
fi

while true; do
    status=$(timeout 30s kaggle kernels status "$kernel" 2>&1) || {
        printf '%s status API error: %s\n' "$(date -u +'%FT%TZ')" "$status"
        sleep "$poll_seconds"
        continue
    }
    printf '%s %s\n' "$(date -u +'%FT%TZ')" "$status"
    if [[ "$status" == *'KernelWorkerStatus.COMPLETE'* ]]; then
        break
    fi
    if [[ "$status" == *'KernelWorkerStatus.ERROR'* ]] ||
       [[ "$status" == *'KernelWorkerStatus.CANCEL'* ]]; then
        printf 'remote run did not complete; refusing artifact collection\n' >&2
        exit 1
    fi
    sleep "$poll_seconds"
done

mkdir -p "$target"
kaggle kernels output "$kernel" -p "$target" --quiet

.venv/bin/python scripts/validate_alignment_artifacts.py \
    --run-dir "$run_dir" \
    --dataset "$dataset" \
    --conditions \
        prompted_json_integer_reasoning_first \
        outlines_json_integer_reasoning_first \
        xgrammar_json_integer_reasoning_first \
        xgrammar_json_unsigned_numeric_string_reasoning_first \
    --limit 18 \
    --runner "$source_root/run_representation_alignment.py" \
    --summarizer "$source_root/summarize_alignment_gate.py" \
    --source-manifest "$source_root/source-manifest.json" \
    --trace "$run_dir/traces/xgrammar-integer-answer-boundary.jsonl" \
    --trace-item-id gsm8k_test_173 \
    --trace-item-id gsm8k_test_1216 \
    --trace-item-id gsm8k_test_12 \
    --out "$target/artifact-validation.json"

.venv/bin/python scripts/build_alignment_gate_report.py \
    --stage targeted \
    --summary "$run_dir/summary.json" \
    --validation "$target/artifact-validation.json" \
    --targeted-manifest experiments/representation-alignment-gate/targeted-suite-manifest.json \
    --baseline-prompted results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/prompted_json_reasoning_first.jsonl \
    --baseline-outlines results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/outlines_json_reasoning_first.jsonl \
    --baseline-xgrammar results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/xgrammar_json_reasoning_first.jsonl \
    --integer-outlines "$run_dir/outlines_json_integer_reasoning_first.jsonl" \
    --integer-xgrammar "$run_dir/xgrammar_json_integer_reasoning_first.jsonl" \
    --trace "$run_dir/traces/xgrammar-integer-answer-boundary.jsonl" \
    --out "$target/representation-alignment-targeted-report.md"

printf '%s targeted artifacts downloaded, validated, and reported\n' "$(date -u +'%FT%TZ')"
