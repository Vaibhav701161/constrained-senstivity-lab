# Practical Day 0

## What I ran

- 01_tokenizer_probe.py
- 02_generate_once.py
- 03_prompted_json_validate.py
- 04_ban_digit_logits_processor.py
- 05_run_smoke_eval.py

## What worked

- The Python environment imports `torch`, `transformers`, `datasets`, and `jsonschema`.
- The first smoke eval script supports `--condition free` and `--condition json`.
- Smoke eval rows are logged as JSONL with prompt, raw output, parsed JSON fields, scoring, token counts, and latency.

## What broke

- CUDA is not usable with the current driver/runtime combination, so local generation runs on CPU.

## Things I physically saw today

### Tokenization

- JSON punctuation, spaces, quoted keys, and numbers can tokenize differently depending on context.

### Generation

- Small local model generation works, but CPU generation can be slow.

### JSON validity

- Prompted JSON still needs parsing and schema validation; asking for JSON is not the same as guaranteeing JSON.

### Logit masking

- The digit-ban processor edits scores before decoding by setting selected token logits to `-inf`.

### Evaluation/logging

- `05_run_smoke_eval.py` writes one row per example and condition.
- Free-form answer extraction uses the last number in the text, which is intentionally simple and can be wrong.

## Numbers

| Condition | Examples | Valid JSON | Correct |
|---|---:|---:|---:|
| free | 3 | n/a | 3/3 |
| json | 3 | 0/3 | 0/3 |

## Biggest confusion

- Prompting for JSON produced answer-looking content, but the simple parser failed because the model emitted markdown fences, extra prose, or repeated JSON objects.

## Tomorrow's first task

- Replace the three hardcoded examples with 10 real GSM8K examples and add proper multi-seed runs.
