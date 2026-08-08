---
title: Reproduce and audit
description: Choose the lightweight replay, full artifact audit, figure regeneration, or new-generation path
---

# Reproduce and audit

You do not need a GPU to verify the published row scores and paired summaries. Start
with the lightweight replay, then choose a deeper path only if your question requires
it.

## Choose an audit path

<div class="csl-card-grid">
  <div class="csl-card">
    <span class="csl-card__label">5 minutes</span>
    <h3>Run tests and replay</h3>
    <p>Recompute 398 second-family rows and 66 tool-call rows from raw outputs.</p>
    <a href="artifact-replay/">Open the replay guide</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Traceability</span>
    <h3>Inspect source artifacts</h3>
    <p>Follow protocols, hashes, JSONL rows, validators, audits, and decisions.</p>
    <a href="evidence-map/">Open the evidence map</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Visual QA</span>
    <h3>Regenerate figures</h3>
    <p>Build every overview plot from checked-in JSON and verify docs copies.</p>
    <a href="#figure-reproducibility">See the commands</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">New inference</span>
    <h3>Recreate generation</h3>
    <p>Install the pinned model and backend stack only when new GPU runs are needed.</p>
    <a href="../environment/">Inspect environments</a>
  </div>
</div>

## Lightweight verification

```bash
git clone https://github.com/Vaibhav701161/constrained-senstivity-lab.git
cd constrained-senstivity-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

python -m pytest
python scripts/replay_artifacts.py \
  --scope all \
  --out /tmp/replay-validation.json
```

Expected general replay scope:

```text
398 second-family rows
 66 tool-call rows
464 total rows
  0 row-score mismatches
  0 paired-summary mismatches
```

Corrected Qwen and canonical-correction rows use dedicated validators and are not
included in that `464` count.

## Figure reproducibility

```bash
python -m pip install -r requirements-analysis.txt

python scripts/build_figures.py
python scripts/build_corrected_replication_figures.py
python scripts/build_replication_gate_figures.py
python scripts/build_evidence_dashboard_figures.py
python scripts/sync_docs_figures.py --check
```

Every public figure has PNG and SVG output. New overview generators assert expected
sample sizes, paired counts, artifact validity, item ordering, and replay status
before drawing.

## Full model-generation environment

```bash
python -m pip install \
  -r requirements-generation.txt \
  -r requirements-backends.txt \
  -r requirements-analysis.txt
python scripts/probe_environment.py
```

Generation requires access to the pinned model weights and suitable GPU memory.
Consult each experiment protocol and deployment surface before running. Do not
replace pinned packages in an attempted reproduction.

## What is immutable

- raw JSONL outputs;
- dataset and source manifests;
- model and tokenizer revisions;
- run signatures and package environments;
- preregistered protocols and decision rules;
- artifact-validation reports;
- frozen decision reports and release tags.

Documentation pages can improve after a study. They are not substituted for frozen
artifacts when reconstructing what ran.

[Open the quickstart](../getting-started/quickstart.md){ .csl-button .csl-button--primary }
[Trace every accepted artifact](evidence-map.md){ .csl-button .csl-button--secondary }
