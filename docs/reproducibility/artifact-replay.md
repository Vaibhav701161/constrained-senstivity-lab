---
title: Artifact replay
description: Recompute second-family and tool-call row scores and paired summaries from checked-in raw outputs
---

# Artifact replay

The repository distinguishes **generation reproduction** from **artifact replay**.
Generation reproduction requires model weights, backend packages, GPU resources,
and access to pinned model revisions. Artifact replay recomputes stored metrics
from the immutable JSONL rows already stored in the repository.

Artifact replay is the default audit path because it is fast, deterministic, and
available without cloud compute.

## One-command replay

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/replay_artifacts.py \
  --scope all \
  --out /tmp/replay-validation.json
```

The expected output is:

```text
464 rows replayed
0 row-score mismatches
0 paired-summary mismatches
```

The checked-in reference report is
[`experiments/replay-validation.json`](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/replay-validation.json).

## What is replayed

| Scope | Rows | Checks |
|---|---:|---|
| Second-family replication | 398 | Row scores, paired summaries, fresh and bridge separation |
| Tool-call pilot | 66 | Argument semantics, validation, execution, post-state, paired summaries |
| Total | 464 | Zero score or summary mismatches required |

The canonical correction validator separately binds its new control to the original
immutable treatment and verifies source hashes, item order, prompt parity, model
revision, scoring, and complete discordance attribution.

## Dedicated artifact validators

```bash
python scripts/validate_second_family_artifacts.py \
  --run-dir experiments/second-family-replication \
  --fresh-dataset data/gsm8k_unseen_150_seed20260815.jsonl \
  --bridge-dataset data/gsm8k_50_seed0.jsonl \
  --source-root . \
  --out /tmp/second-family-validation.json \
  --require-analysis

python scripts/validate_tool_call_artifacts.py \
  --run-dir experiments/tool-call-gate \
  --dataset data/bfcl_tool_pilot_seed20260817.jsonl \
  --source-root . \
  --out /tmp/tool-call-validation.json \
  --require-analysis

python scripts/validate_canonical_correction_artifacts.py \
  --run-dir experiments/canonical-schema-equivalence-correction \
  --dataset data/gsm8k_unseen_150_seed20260815.jsonl \
  --source-root . \
  --historical-control experiments/second-family-replication/results/fresh/xgrammar_json_reasoning_first.jsonl \
  --frozen-treatment experiments/second-family-replication/results/fresh/xgrammar_json_integer_reasoning_first.jsonl \
  --frozen-treatment-manifest experiments/second-family-replication/manifests/fresh/xgrammar_json_integer_reasoning_first.json \
  --out /tmp/canonical-correction-validation.json \
  --require-analysis
```

## Continuous verification

GitHub Actions runs the lightweight tests and artifact replay on Python 3.11 and
3.12. The replay summaries are byte-identical across those runtimes. Documentation
is built separately with strict navigation and anchor checks.

## Reproducing generation

Generation is more expensive and should be attempted only when the exact frozen
environment can be recreated. Each accepted experiment directory includes its own
protocol, source manifest, run manifests, model revision, dataset hash, and failure
policy. Follow that experiment's records rather than treating the current runner as
a substitute for historical source.

!!! danger "Preserve accepted artifacts"

    Never resume a new configuration into an accepted output file. Run signatures
    prevent many accidental mixtures, but the experimental protocol is the final
    authority.
