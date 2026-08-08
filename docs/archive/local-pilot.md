---
title: Local pilot
description: Historical Qwen2.5 0.5B local pilot and early constrained-generation observations
search:
  exclude: true
---

# Local pilot: trustworthy evaluation pipeline

Date: 2 Aug 2026

## Outcome

The local evaluation pipeline now runs on the RTX 4050, uses real GSM8K data
and Qwen's chat template, writes resumable item-level JSONL, separates syntax
from semantic accuracy, and compares prompt-only JSON with Outlines-constrained
JSON on the same 20 examples.

This is a pilot baseline, not enough evidence to accept or reject the project
premise.

## Frozen setup

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Model revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Dataset: 20-item prefix of `data/gsm8k_50_seed0.jsonl`
- Dataset SHA-256: `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`
- Decoding: greedy (`do_sample=false`), seed 0, 256 maximum new tokens
- Device: `cuda:0`
- Chat formatting: `tokenizer.apply_chat_template(..., add_generation_prompt=True)`
- All four conditions use the same item IDs and model revision.

The free prompt is version `day2-v4-reasoning-before-answer`. The JSON prompt
is version `day2-v5-numeric-answer-field`; v5 adds the necessary instruction
that the `answer` value should contain only the final number. Earlier prompt
iterations are retained under `results/pilots/qwen2.5-0.5b/pilots/` and excluded from the
final summary.

## Results

| Condition | n | Accuracy | Whole JSON | Recoverable | Schema valid | Correct |
|---|---:|---:|---:|---:|---:|---:|
| free | 20 | 25% | n/a | n/a | n/a | 5 |
| prompted JSON, reasoning first | 20 | 20% | 50% | 80% | 55% | 4 |
| prompted JSON, answer first | 20 | 5% | 65% | 95% | 55% | 1 |
| Outlines JSON, reasoning first | 20 | 15% | 95% | 95% | 95% | 3 |

Paired semantic differences:

| Treatment minus control | Delta | Treatment-only correct | Control-only correct |
|---|---:|---:|---:|
| prompted reasoning-first minus free | -5 points | 2 | 3 |
| prompted answer-first minus prompted reasoning-first | -15 points | 0 | 3 |
| Outlines reasoning-first minus prompted reasoning-first | -5 points | 2 | 3 |

All 80 assigned generations completed without a runtime error.

## Observations

### 1. Answer-first is the largest observed effect

Prompted answer-first lost 15 percentage points relative to prompted
reasoning-first. It rescued no item that reasoning-first missed, while
reasoning-first alone solved three items. This is consistent with premature
commitment, but the model is tiny, the baseline accuracy is low, and `n=20` is
too small for a strong claim.

### 2. The incremental Outlines effect is small and mixed

Outlines was five points below matched prompted reasoning-first. It solved two
items the prompted condition missed and lost three items the prompted condition
solved. That is mixed item-level behavior, not a clean global degradation.

### 3. Valid JSON is not the same as a correct answer

Outlines substantially improved structural validity but achieved only 3/20
semantic accuracy. Prompt-only JSON often remained recoverable despite markdown
fences or extra text. Several prompt-only objects used a JSON number for
`answer` even though the schema required a string, which explains part of the
gap between recoverability and schema validity.

### 4. Outlines produced one deterministic invalid output

For `gsm8k_test_1284`, Outlines returned an unterminated `answer` string and no
runtime error. The output did not hit the 256-token cap. An isolated rerun
produced byte-for-byte identical output, recorded in
`results/pilots/qwen2.5-0.5b/outlines_invalid_reproduction_gsm8k_test_1284.jsonl`.

This means the observed guarantee is 19/20 in this integration, not 20/20. It
needs investigation as a possible EOS/guide integration problem before larger
runs.

### 5. The free baseline often ignored the output protocol

Only 6/20 free responses ended with the requested final-answer marker. Eight
responses hit the 256-token cap, and none of those eight were correct. Thirteen
answers required the documented last-number fallback. Therefore, the free
condition is useful context, but the main constrained-decoding comparison should
remain Outlines versus matched prompted JSON.

### 6. Latency is exploratory

Median latency was approximately 10.8 seconds for free, 3.1 seconds for
prompted reasoning-first, 4.6 seconds for prompted answer-first, and 3.6 seconds
for Outlines. Output lengths differ substantially, and the first constrained
call can include backend setup, so these numbers are not yet a clean decoding
overhead benchmark.

## Commands

```bash
source .venv/bin/activate
python scripts/probe_environment.py | tee results/pilots/qwen2.5-0.5b/env_probe.txt
python scripts/prepare_dataset.py --count 50 --seed 0 \
  --out data/gsm8k_50_seed0.jsonl

python scripts/run_evaluation.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --dataset data/gsm8k_50_seed0.jsonl \
  --condition free --limit 20 --seed 0 --resume \
  --out results/pilots/qwen2.5-0.5b/gsm8k_qwen05_free_seed0.jsonl
```

Use the same command with these condition/output pairs:

- `prompted_json_reasoning_first` → `gsm8k_qwen05_prompted_json_reasoning_first_seed0.jsonl`
- `prompted_json_answer_first` → `gsm8k_qwen05_prompted_json_answer_first_seed0.jsonl`
- `outlines_json_reasoning_first` → `gsm8k_qwen05_outlines_json_reasoning_first_seed0.jsonl`

The final summary command is:

```bash
python scripts/summarize_results.py \
  results/pilots/qwen2.5-0.5b/gsm8k_qwen05_free_seed0.jsonl \
  results/pilots/qwen2.5-0.5b/gsm8k_qwen05_prompted_json_reasoning_first_seed0.jsonl \
  results/pilots/qwen2.5-0.5b/gsm8k_qwen05_prompted_json_answer_first_seed0.jsonl \
  results/pilots/qwen2.5-0.5b/gsm8k_qwen05_outlines_json_reasoning_first_seed0.jsonl \
  --out-json results/pilots/qwen2.5-0.5b/summary.json \
  --out-md results/pilots/qwen2.5-0.5b/summary.md
```

## Next local gates

1. Investigate the reproducible Outlines invalid-output case.
2. Add a separately named numeric-answer schema condition so answer-first truly
   prevents reasoning inside the answer string.
3. Raise the free-form generation cap or improve concise prompting, then rerun
   before treating free-versus-JSON accuracy as meaningful.
4. Repeat the matched prompt/Outlines comparison on Qwen 1.5B and GSM8K-50.
5. Add uncertainty intervals only after the larger paired runs exist.
