# Quickstart

The fastest trustworthy check requires Python 3.11 or 3.12. It does not download a
language model and does not require CUDA.

## Install the lightweight environment

```bash
git clone https://github.com/Vaibhav701161/constrained-decoding-lab.git
cd constrained-decoding-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Replay the accepted artifacts

```bash
python scripts/replay_artifacts.py \
  --scope all \
  --out /tmp/replay-validation.json
```

Expected terminal result:

```text
464 rows replayed
0 row-score mismatches
0 paired-summary mismatches
```

The command recomputes metrics from the checked-in raw rows. It does not trust the
published summaries as input evidence.

## Run the tests

```bash
python -m pytest
```

The full lightweight suite covers contract compilation, transduction, paired
analysis, artifact validation, prompt parity fixtures, and refusal behavior.

## Optional generation environment

Install model and backend dependencies only if you intend to generate new outputs:

```bash
python -m pip install \
  -r requirements-generation.txt \
  -r requirements-backends.txt \
  -r requirements-analysis.txt
python scripts/probe_environment.py
```

!!! warning "Do not reinterpret a frozen experiment"

    New generations must use a new protocol and output directory. Do not overwrite
    accepted JSONL files, change the denominator after viewing outputs, or replace
    frozen package versions in an existing study.

## Next steps

- Review the [evidence overview](../studies/evidence-overview.md).
- Understand the [runtime architecture](../architecture.md).
- Locate raw artifacts through the [evidence map](../reproducibility/evidence-map.md).
