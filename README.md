# Constrained Decoding Lab

Local experiments for measuring how JSON prompting and constrained decoding
affect output validity, semantic accuracy, latency, and token use.

## Setup

```bash
cd /home/vaibhav/constrained-decoding-lab
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
python scripts/00_env_probe.py
```

The verified local stack uses PyTorch 2.6.0+cu124 on an RTX 4050 Laptop GPU.
See `notes/SETUP_NOTES.md` for exact versions and troubleshooting details.

## Day 2 local baseline

Prepare the deterministic GSM8K subset:

```bash
python scripts/06_prepare_datasets.py \
  --count 50 \
  --seed 0 \
  --out data/gsm8k_50_seed0.jsonl
```

Run a condition:

```bash
python scripts/07_run_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --dataset data/gsm8k_50_seed0.jsonl \
  --condition prompted_json_reasoning_first \
  --limit 20 \
  --seed 0 \
  --resume \
  --out results/day2/gsm8k_qwen05_prompted_json_reasoning_first_seed0.jsonl
```

Supported conditions:

- `free`
- `prompted_json_reasoning_first`
- `prompted_json_answer_first`
- `outlines_json_reasoning_first`
- `outlines_json_answer_first`

The runner applies the model chat template, writes and flushes one JSONL row per
item, validates resume signatures, and keeps structural and semantic metrics
separate.

Results and interpretation are in `results/day2/summary.md` and
`notes/DAY2.md`.

## Day 0 scripts

The original tokenizer, generation, prompted-JSON, logit-masking, and three-item
smoke scripts remain under `scripts/01_*` through `scripts/05_*`; their outputs
are under `results/day0/`.
