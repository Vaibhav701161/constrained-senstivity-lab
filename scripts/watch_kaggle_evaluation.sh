#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

kernel="vaibhav7011/constrained-decoding-qwen7b-smoke"
dataset="data/gsm8k_50_seed0.jsonl"
runner="scripts/run_evaluation.py"
summarizer="scripts/summarize_results.py"
validator="scripts/validate_artifacts.py"
item_report="scripts/build_item_report.py"
python_bin=".venv/bin/python"

wait_for_complete() {
    local label=$1
    while true; do
        local output
        output=$(timeout 30s kaggle kernels status "$kernel" 2>&1) || {
            printf '%s status API error: %s\n' "$(date -u +'%FT%TZ')" "$output"
            sleep 60
            continue
        }
        printf '%s %s: %s\n' "$(date -u +'%FT%TZ')" "$label" "$output"
        if [[ "$output" == *'KernelWorkerStatus.COMPLETE'* ]]; then
            return 0
        fi
        if [[ "$output" == *'KernelWorkerStatus.ERROR'* ]] ||
           [[ "$output" == *'KernelWorkerStatus.CANCEL'* ]]; then
            printf '%s did not complete; refusing follow-up launch\n' "$label" >&2
            return 1
        fi
        sleep 60
    done
}

download_version() {
    local version=$1
    local target=$2
    if [[ -e "$target" ]]; then
        printf 'refusing existing output target: %s\n' "$target" >&2
        return 1
    fi
    mkdir -p "$target"
    kaggle kernels output "$kernel/$version" -p "$target" --quiet
}

primary_target="results/qwen2.5-7b/primary/reasoning-first"
primary_base="$primary_target/results/qwen2.5-7b-smoke"

wait_for_complete "version22-primary"
download_version 22 "$primary_target"

"$python_bin" "$validator" \
    --run-dir "$primary_base" \
    --dataset "$dataset" \
    --conditions free prompted_json_reasoning_first \
        outlines_json_reasoning_first xgrammar_json_reasoning_first \
    --limit 50 \
    --prompt-version day3-v8-symbolic-json-template \
    --runner "$runner" \
    --summarizer "$summarizer" \
    --xgrammar-any-whitespace false \
    --out "$primary_target/artifact_validation.json"

primary_files=(
    "$primary_base/free.jsonl"
    "$primary_base/prompted_json_reasoning_first.jsonl"
    "$primary_base/outlines_json_reasoning_first.jsonl"
    "$primary_base/xgrammar_json_reasoning_first.jsonl"
)
"$python_bin" "$summarizer" "${primary_files[@]}" \
    --out-json "$primary_target/summary_raw_recomputed.json" \
    --out-md "$primary_target/summary_raw_recomputed.md"
"$python_bin" "$summarizer" "${primary_files[@]}" \
    --exclude-item-id gsm8k_test_454 \
    --out-json "$primary_target/summary_clean.json" \
    --out-md "$primary_target/summary_clean.md"
"$python_bin" "$item_report" "${primary_files[@]}" \
    --exclude-item-id gsm8k_test_454 \
    --out-md "$primary_target/items.md"

printf 'version 22 passed artifact validation; launching answer-order controls\n'
kaggle kernels push -p deployment/kaggle/kernel

answer_target="results/qwen2.5-7b/primary/answer-first"
answer_base="$answer_target/results/qwen2.5-7b-smoke"

wait_for_complete "version23-answer-order"
download_version 23 "$answer_target"

"$python_bin" "$validator" \
    --run-dir "$answer_base" \
    --dataset "$dataset" \
    --conditions prompted_json_answer_first outlines_json_answer_first \
    --limit 50 \
    --prompt-version day3-v8-symbolic-json-template \
    --runner "$runner" \
    --summarizer "$summarizer" \
    --out "$answer_target/artifact_validation.json"

answer_files=(
    "$answer_base/prompted_json_answer_first.jsonl"
    "$answer_base/outlines_json_answer_first.jsonl"
)
"$python_bin" "$summarizer" "${answer_files[@]}" \
    --out-json "$answer_target/summary_raw_recomputed.json" \
    --out-md "$answer_target/summary_raw_recomputed.md"
"$python_bin" "$summarizer" "${answer_files[@]}" \
    --exclude-item-id gsm8k_test_454 \
    --out-json "$answer_target/summary_clean.json" \
    --out-md "$answer_target/summary_clean.md"
"$python_bin" "$item_report" "${answer_files[@]}" \
    --exclude-item-id gsm8k_test_454 \
    --out-md "$answer_target/items.md"

printf '%s all scheduled Kaggle evaluation cells downloaded and validated\n' \
    "$(date -u +'%FT%TZ')"
