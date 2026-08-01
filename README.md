# Constrained Decoding Lab

Practical Day 0 repo for touching the basic constrained-decoding workflow:
tokenization, local generation, prompted JSON, toy logits masking, and JSONL
logging.

## Setup

```bash
cd /home/vaibhav/constrained-decoding-lab
source .venv/bin/activate
python -c "import torch, transformers, datasets, jsonschema; print('ok')"
```

The current environment runs on CPU. `torch.cuda.is_available()` is false on
this machine because the installed NVIDIA driver is older than the CUDA runtime
bundled with the installed torch wheel.

## Day 0 Commands

```bash
python scripts/01_tokenizer_probe.py | tee results/day0/tokenizer_probe.txt
python scripts/02_generate_once.py | tee results/day0/generation_once.txt
python scripts/03_prompted_json_validate.py
python scripts/04_ban_digit_logits_processor.py
python scripts/05_run_smoke_eval.py --condition free
python scripts/05_run_smoke_eval.py --condition json
```

The smoke eval writes:

```text
results/day0/smoke_eval_free.jsonl
results/day0/smoke_eval_json.jsonl
```
