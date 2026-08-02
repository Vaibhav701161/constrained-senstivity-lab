# Setup Notes

Verified on 2 Aug 2026.

## Machine

- OS: WSL2 Linux 6.18.33.2
- Python: 3.12.3
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU
- VRAM: 6141 MiB reported by `nvidia-smi`; 5.997 GiB reported by PyTorch
- NVIDIA driver: 560.94
- GPU compute capability: 8.9

## Working environment

The old `.venv` was missing. It was recreated with:

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Important direct versions:

- PyTorch 2.6.0+cu124
- Transformers 4.51.3
- Accelerate 1.6.0
- Datasets 3.6.0
- Outlines 1.3.2
- JSON Schema 4.23.0

The default package resolver would have selected a CUDA 13 PyTorch build. The
project instead pins the CUDA 12.4 wheel, which works with the installed driver.

## Verification

`scripts/00_env_probe.py` completed a real matrix multiplication on `cuda:0`.
The result is saved in `results/day2/env_probe.txt`.

```text
torch.cuda.is_available(): true
CUDA tensor test: true
```

`uv pip check` reports that all 78 installed packages are compatible.

## Download note

Hugging Face's Xet transfer stalled while downloading Qwen. Standard HTTP
completed the download successfully:

```bash
HF_HUB_DISABLE_XET=1 python scripts/07_run_baseline.py ...
```

The model is now cached locally, so normal reruns do not need another download.
