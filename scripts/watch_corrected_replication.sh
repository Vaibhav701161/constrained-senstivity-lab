#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

kernel="${KAGGLE_KERNEL:-vaibhav7011/contract-alignment-corrected-replication}"
target="${REPLICATION_OUTPUT_TARGET:-experiments/corrected-replication/results/qwen2.5-7b-corrected}"
poll_seconds="${KAGGLE_POLL_SECONDS:-60}"
run_dir="$target/results/corrected-replication"
source_root="deployment/kaggle/corrected-replication/source-snapshot"

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
        printf 'remote run did not complete; refusing artifact acceptance\n' >&2
        exit 1
    fi
    sleep "$poll_seconds"
done

mkdir -p "$target"
kaggle kernels output "$kernel" -p "$target" --quiet

.venv/bin/python scripts/validate_corrected_replication.py \
    --run-dir "$run_dir" \
    --dataset data/gsm8k_50_seed0.jsonl \
    --source-root "$source_root" \
    --kernel-source deployment/kaggle/corrected-replication/run_kaggle.py \
    --out "$target/artifact-validation.json"

printf '%s corrected replication downloaded and independently validated\n' "$(date -u +'%FT%TZ')"
