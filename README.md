<div align="center">

# Contract Sensitivity Lab

**Artifact-backed evaluation of how structured-output contracts change model behavior.**

[![Evidence CI](https://github.com/Vaibhav701161/constrained-decoding-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Vaibhav701161/constrained-decoding-lab/actions/workflows/ci.yml)
[![Documentation](https://github.com/Vaibhav701161/constrained-decoding-lab/actions/workflows/docs.yml/badge.svg)](https://vaibhav701161.github.io/constrained-decoding-lab/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-155eef)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-087a55)](LICENSE)

[Documentation](https://vaibhav701161.github.io/constrained-decoding-lab/) ·
[Results](#evidence-at-a-glance) ·
[Quickstart](#quickstart) ·
[Artifacts](docs/reproducibility/evidence-map.md)

</div>

---

Constrained decoding can make every output schema-valid while still changing what
the model gets right. This repository measures that semantic effect with paired,
preregistered experiments, immutable raw artifacts, exact validators, and complete
discordance audits.

The central conclusion is deliberately narrow:

> A compiler can prove that a representation rewrite preserves an external
> contract. It cannot assume that the rewrite preserves or improves model quality.

The project therefore continues as a **contract-sensitivity evaluation harness**,
with a conservative schema linter and fail-closed transduction utilities. It is not
positioned as a general model-quality optimizer.

## Evidence at a glance

| Decision gate | Control | Integer treatment | Paired effect | Outcome |
|---|---:|---:|---:|---|
| Corrected Qwen2.5 7B, GSM8K, n=49 | 36.7% | 49.0% | +12.2 pp, CI [0.0, 26.5] | Scoped positive signal |
| Llama 3.2 3B, unseen GSM8K, n=150 | 61.3% | 54.7% | -6.7 pp, CI [-12.7, -0.7] | Optimizer thesis closed |
| Llama 3.2 3B, executable pilot, n=30 | 86.7% | 80.0% | -6.7 pp, CI [-20.0, 6.7] | No practical benefit detected |

![Paired effects across the principal research gates](assets/figures/cross-family-evidence.png)

The Llama result is the authoritative cross-family decision. An external review
found that its original control allowed a broader numeric-string language than the
compiler supported. We preregistered one exact correction, generated only the new
canonical control, reused the immutable treatment, and audited all 22 discordant
items. The negative estimate survived unchanged in magnitude.

| Canonical Llama audit category | Count |
|---|---:|
| Problem-interpretation change | 10 |
| Reasoning and final-answer inconsistency | 8 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign, parser, validator, transducer, or truncation issue | 0 |

[Read the complete evidence chain →](https://vaibhav701161.github.io/constrained-decoding-lab/studies/evidence-overview/)

## What the system evaluates

```text
External JSON Schema
        ↓
ContractIR and alignment analysis
        ↓
Internal model-facing schema
        ↓
XGrammar or Outlines generation
        ↓
Deterministic inverse transducer
        ↓
Original external-schema validation
        ↓
Paired semantic and execution analysis
```

The runtime keeps model loading, tokenizer handling, chat-template application,
decoding, error handling, visible-token counting, and artifact writing identical
between paired representations. Only the declared representation and required
inverse transduction may differ.

### Supported now

- Canonical signed integer strings
- JSON integer to canonical-string transduction
- Original-contract revalidation after reconstruction
- Conservative field-order and key-alias prototypes
- Paired semantic, validity, latency, and executable-state analysis
- Artifact replay with source, dataset, model, and run-signature verification
- Typed refusal of unsafe or unsupported transformations

### Refused by design

- `$ref` resolution
- unions and ambiguous schema branches
- arbitrary regular-expression transformation
- rewrites that drop bounds, enumerations, constants, or `multipleOf`
- heuristic output repair in scored paths

See the [supported-contract matrix](https://vaibhav701161.github.io/constrained-decoding-lab/supported-contracts/)
for the exact evidence level behind each feature.

## Quickstart

Artifact replay does not require model weights, a GPU, Outlines, or XGrammar.

```bash
git clone https://github.com/Vaibhav701161/constrained-decoding-lab.git
cd constrained-decoding-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

python -m pytest
python scripts/replay_artifacts.py \
  --scope all \
  --out /tmp/replay-validation.json
```

Accepted replay result:

```text
464 rows replayed
0 row-score mismatches
0 paired-summary mismatches
```

Install the pinned generation and backend layers only when new model inference is
required:

```bash
python -m pip install \
  -r requirements-generation.txt \
  -r requirements-backends.txt \
  -r requirements-analysis.txt
python scripts/probe_environment.py
```

[Open the full reproducibility guide →](https://vaibhav701161.github.io/constrained-decoding-lab/reproducibility/artifact-replay/)

## Documentation

The documentation site is the primary reading surface. The README stays focused on
the result, interface, and audit path.

| Section | Use it for |
|---|---|
| [Start here](https://vaibhav701161.github.io/constrained-decoding-lab/getting-started/overview/) | Choose a learning, audit, or extension path |
| [Concepts](https://vaibhav701161.github.io/constrained-decoding-lab/concepts/constrained-decoding/) | Learn constrained decoding and contract sensitivity |
| [Research](https://vaibhav701161.github.io/constrained-decoding-lab/studies/evidence-overview/) | Follow every decision gate and corrected conclusion |
| [Architecture](https://vaibhav701161.github.io/constrained-decoding-lab/architecture/) | Understand ContractIR, plans, runtime, and fail-closed boundaries |
| [Reproducibility](https://vaibhav701161.github.io/constrained-decoding-lab/reproducibility/artifact-replay/) | Replay results and inspect validation controls |
| [Evidence map](https://vaibhav701161.github.io/constrained-decoding-lab/reproducibility/evidence-map/) | Reach protocols, manifests, raw rows, audits, and decisions |

Build the site locally with:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
```

## Repository map

```text
assets/          Data-derived technical figures
data/            Frozen datasets and audit manifests
deployment/      Exact Kaggle and Modal execution surfaces
docs/            Documentation site source and research records
experiments/     Protocols, raw rows, manifests, audits, decisions
scripts/         Preparation, execution, validation, replay, figures
src/project_a/   Contract IR, analysis, plans, runtime, transducers
tests/           Unit, property, parity, and artifact regression tests
```

## Evidence policy

- Random holdouts are selected before generation and bound by hashes.
- Canary gates evaluate operational integrity, never early semantic success.
- Generation errors, cap hits, and invalid objects remain in denominators.
- Post-launch exclusions are forbidden unless a dataset defect is documented before
  model outputs are viewed.
- Every discordant confirmatory item is retained and audited.
- Negative results and runner defects remain part of the public record.
- New prompts or models require a new question and protocol, not a rescue search.

## Publications

The eight-part technical series follows the work from token-level grammar mechanics
through the final canonical correction. Start with the latest report:

[**I Fixed a Schema Mismatch. The Negative Result Survived.**](https://dev.to/vaibhav_mittal_ac22a2c5d6/i-fixed-a-schema-mismatch-the-negative-result-survived-192l)

[Browse every article and retained source →](https://vaibhav701161.github.io/constrained-decoding-lab/publications/)

## Citation

If this work informs your research or engineering, cite the exact archived revision
you used. Repository metadata is available in [CITATION.cff](CITATION.cff).

```bibtex
@software{mittal_contract_sensitivity_lab,
  author  = {Vaibhav Mittal},
  title   = {Contract Sensitivity Lab},
  year    = {2026},
  url     = {https://github.com/Vaibhav701161/constrained-decoding-lab}
}
```

Released under the [MIT License](LICENSE).
