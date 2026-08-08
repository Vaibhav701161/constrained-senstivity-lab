<div align="center">

# Constrained Sensitivity Lab

### Measuring how structured-output contracts change LLM behavior

An artifact-backed research and evaluation system for separating structural
validity, semantic correctness, and executable success under constrained decoding.

[![Evidence CI](https://github.com/Vaibhav701161/constrained-senstivity-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Vaibhav701161/constrained-senstivity-lab/actions/workflows/ci.yml)
[![Documentation](https://github.com/Vaibhav701161/constrained-senstivity-lab/actions/workflows/docs.yml/badge.svg)](https://vaibhav701161.github.io/constrained-senstivity-lab/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-155eef)](https://www.python.org/)
[![Artifact replay](https://img.shields.io/badge/artifact_replay-464_rows-087a55)](experiments/replay-validation.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-52647a)](LICENSE)

[**Documentation**](https://vaibhav701161.github.io/constrained-senstivity-lab/) ·
[Evidence](#evidence-at-a-glance) ·
[Architecture](#system-architecture) ·
[Reproduce](#reproduce-the-evidence) ·
[Publications](#technical-publications)

</div>

---

## Why this project exists

Structured-output systems are usually judged by a simple question: did the model
return valid JSON?

That question is necessary, but incomplete. A grammar can make every response
schema-valid while changing which answers the model gets right. A schema rewrite
can preserve the caller-facing contract while changing the model's reasoning,
interpretation, or final answer.

Constrained Sensitivity Lab measures those changes directly.

It treats the model-facing contract as an experimental variable and separately
scores:

- semantic correctness before contract requirements;
- internal-schema validity;
- reconstructed external-schema validity;
- contract-valid correctness;
- exact tool arguments and execution success;
- paired repairs and regressions;
- token counts, cap hits, errors, and descriptive latency;
- reasoning and final-answer consistency.

> **Core finding:** a compiler can prove that a representation rewrite preserves
> an external contract. It cannot assume that the rewrite preserves or improves
> model quality.

![Controlled evaluation design showing matched prompts, models, decoding, schemas, and scoring](assets/figures/evaluation-design.png)

## Evidence at a glance

The research moved through increasingly strict gates. Earlier positive evidence is
preserved, but the final architecture follows the independent cross-family result.

| Decision gate | Control | Integer treatment | Paired effect | Wins : losses | Decision |
|---|---:|---:|---:|---:|---|
| Corrected Qwen2.5 7B, GSM8K, n=49 | 18/49 (36.7%) | 24/49 (49.0%) | +12.2 pp, CI [0.0, 26.5] | 9 : 3 | Scoped positive signal |
| Llama 3.2 3B, broad-string holdout, n=150 | 92/150 (61.3%) | 82/150 (54.7%) | -6.7 pp, CI [-12.7, -1.3] | 5 : 15 | Negative, mismatch later corrected |
| Llama 3.2 3B, canonical holdout, n=150 | 92/150 (61.3%) | 82/150 (54.7%) | -6.7 pp, CI [-12.7, -0.7] | 6 : 16 | Optimizer thesis closed |
| Llama 3.2 3B, executable pilot, n=30 | 26/30 (86.7%) | 24/30 (80.0%) | -6.7 pp, CI [-20.0, 6.7] | 1 : 3 | No practical benefit detected |

![Paired effects across the corrected Qwen, unseen Llama, and executable decision gates](assets/figures/cross-family-evidence.png)

### Current decision

The project continues as a **contract-sensitivity evaluation harness**, supported
by conservative contract analysis and deterministic transduction utilities.

The following claim is closed by the completed evidence:

> Replacing a model-facing canonical signed numeric string with a JSON integer is a
> generally useful model-quality optimization.

The deterministic transformation remains safe inside its supported domain. What
failed to generalize was the quality improvement.

[Read the complete decision chain](https://vaibhav701161.github.io/constrained-senstivity-lab/studies/evidence-overview/)

---

## Research record

### 1. Baseline: validity improved while semantic accuracy fell

The primary baseline compared six matched conditions on a deterministic GSM8K
subset using `Qwen/Qwen2.5-7B-Instruct`, greedy decoding, FP32, and a 256-token cap.
One contradictory reference item was retained in the raw record and excluded only
from the predeclared clean analysis.

| Qwen2.5 7B condition | Recoverable accuracy | Strict accuracy | Schema compliance |
|---|---:|---:|---:|
| Free response | 36/49 (73.5%) | Not applicable | Not applicable |
| Prompted JSON, reasoning first | 39/49 (79.6%) | 0/49 (0.0%) | 0.0% |
| Outlines, reasoning first | 30/49 (61.2%) | 30/49 (61.2%) | 100.0% |
| XGrammar, reasoning first | 30/49 (61.2%) | 30/49 (61.2%) | 100.0% |
| Prompted JSON, answer first | 11/49 (22.4%) | 8/49 (16.3%) | 65.3% |
| Outlines, answer first | 8/49 (16.3%) | 8/49 (16.3%) | 100.0% |

![Recoverable accuracy, strict correctness, and schema compliance across the six primary conditions](assets/figures/accuracy-compliance-tradeoff.png)

The reasoning-first constrained conditions reached 100% compliance and lost nine
paired mathematical answers against prompt-only JSON, with no gains. The prompt-only
outputs were valid JSON but used unquoted numbers where the schema required strings,
which is why recoverable and strict accuracy are reported separately.

### 2. Field order behaved like a causal variable

Changing only the required JSON field order produced a larger effect than switching
between Outlines and XGrammar.

| System | Reasoning-first recoverable | Answer-first recoverable | Paired change | Schema compliance |
|---|---:|---:|---:|---:|
| Prompt-only JSON | 79.6% | 22.4% | -57.1 pp | 0.0% to 65.3% |
| Outlines JSON | 61.2% | 16.3% | -44.9 pp | 100.0% to 100.0% |

![Recoverable accuracy and schema compliance under reasoning-first and answer-first field order](assets/figures/field-order-sensitivity.png)

Under Outlines, compliance stayed fixed at 100%. The 44.9-point decline therefore
cannot be explained by malformed JSON. Generation order itself changed model
behavior in this setup.

### 3. A narrow contract-preserving transform looked promising on Qwen

The baseline localized one possible sensitivity boundary: a signed numeric string.
The prototype allowed the model to emit a native JSON integer, deterministically
converted that integer to canonical base-10 text, rebuilt the external object, and
validated it against the original schema.

![Contract-preserving model-facing schema transformation and validation pipeline](assets/figures/contract-alignment-pipeline.png)

The first historical alignment gate estimated a +14.3 point recovery for both
backends. A later audit found runner-divergence risks, so the result was not accepted
as the final evidence.

The corrected shared-path replication produced:

| Corrected Qwen representation | Contract-valid correct | External validity |
|---|---:|---:|
| Signed numeric string | 18/49 (36.7%) | 49/49 (100.0%) |
| Integer plus deterministic stringification | 24/49 (49.0%) | 49/49 (100.0%) |

![Corrected Qwen paired effect, validity, and artifact-integrity summary](assets/figures/corrected-replication-effect.png)

The +12.2 point estimate cleared the frozen continuation threshold, but its interval
touched zero and exact McNemar `p = 0.145996`. This authorized an independent model
family and unseen holdout. It did not authorize a general optimization claim.

### 4. The improvement reversed on Llama and unseen items

The confirmatory replication changed the model family to
`meta-llama/Llama-3.2-3B-Instruct` and selected 150 previously unseen GSM8K test
items after scanning repository artifacts for prior exposure.

The runner froze:

- one model and tokenizer revision;
- XGrammar 0.2.3;
- greedy decoding, seed 0, FP32, and 256 maximum new tokens;
- identical chat-template and generation paths;
- one dataset order and hash;
- no post-launch exclusions;
- errors and cap hits as failures in the denominator.

The initial broad-string control scored 92/150 while the integer treatment scored
82/150. An external review then found that the string schema accepted decimals,
fractions, comma grouping, and leading zeros, while the compiler proved equivalence
only for canonical signed integers.

That mismatch was real. It required correction before a final claim.

### 5. Exact schema equivalence did not rescue the result

The correction preregistered exactly one new 150-row canonical string control:

```regex
^-?(?:0|[1-9][0-9]*)$
```

It reused the same model revision, dataset, prompt, backend, decoding environment,
analysis rule, and immutable integer treatment. No new treatment output was
generated.

![Canonical-schema correction result, paired transitions, and complete manual attribution](assets/figures/canonical-schema-correction.png)

The corrected outcome remained 92/150 versus 82/150, a **-6.7 point effect** with
paired interval **[-12.7, -0.7]**. There were six treatment-only wins and sixteen
control-only losses.

Every discordant item was manually inspected:

| Attribution category | Count |
|---|---:|
| Problem-interpretation change | 10 |
| Reasoning and final-answer inconsistency | 8 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Parser, validator, transducer, or truncation issue | 0 |

The schema mismatch did not explain away the negative direction. The final decision
closed the default optimizer thesis.

### 6. A bounded executable pilot also found no benefit

The Red replication path authorized one practical pilot based on pinned BFCL V4
`simple_python` cases. It used deterministic local wrappers with no external side
effects and scored the complete chain from tool selection through post-execution
state.

![Executable tool-call component outcomes and paired transition matrix](assets/figures/tool-call-pilot-result.png)

Both arms reached 100% internal validity, reconstructed external validity, and
execution acceptance. The semantic result was still negative: 26/30 successful
control calls versus 24/30 treatment calls. The failures came from argument
semantics, not from parsing, validation, or transduction.

---

## System architecture

```text
External JSON Schema
        ↓
ContractIR
        ↓
Alignment analysis
        ↓
AlignmentPlan or typed refusal
        ↓
Internal JSON Schema
        ↓
XGrammar / Outlines
        ↓
Internal object
        ↓
Deterministic inverse transducer
        ↓
Original external-schema validation
        ↓
Caller-facing object
        ↓
Paired semantic and execution analysis
```

The shared runtime keeps model loading, tokenizer handling, chat-template
application, generation, visible-token counting, latency measurement, error
handling, manifests, and artifact writing identical between paired representations.

Only three elements may differ:

1. the model-facing schema;
2. the symbolic representation described in the prompt;
3. whether deterministic inverse transduction is required.

### Implemented surfaces

| Surface | Responsibility |
|---|---|
| `ContractIR` | Canonical internal representation of the supported external schema |
| Alignment analysis | Detect eligible boundaries and reject unsafe rewrites |
| `AlignmentPlan` | Serializable transformation and inverse-transduction plan |
| Shared runtime | Enforce generation parity across experimental arms |
| Inverse transducer | Reconstruct the caller-facing representation without heuristics |
| Final validator | Revalidate against the original, unchanged external schema |
| Paired analyzer | Compute transitions, intervals, exact tests, and mechanism audits |
| Artifact replay | Recompute accepted scores without model weights or cloud compute |

### Supported and refused contracts

Supported or evidence-backed:

- canonical signed integer strings;
- JSON integer to canonical-string transduction;
- strict original-contract revalidation;
- deterministic, serializable alignment plans;
- field ordering and key aliases as explicitly scoped prototypes;
- matched paired evaluation and artifact replay.

Refused by design:

- `$ref` resolution;
- unions and ambiguous schema branches;
- arbitrary regular-expression transformation;
- rewrites that drop bounds, enumerations, constants, or `multipleOf`;
- heuristic repairs, rounding, or silent coercion in scored paths.

[Inspect the architecture](https://vaibhav701161.github.io/constrained-senstivity-lab/architecture/) ·
[Open the support matrix](https://vaibhav701161.github.io/constrained-senstivity-lab/supported-contracts/)

## Research integrity controls

- Datasets are selected before generation and bound by hashes.
- Previously seen item IDs are removed before unseen-set sampling.
- Operational canaries do not inspect early semantic wins.
- Completed rows are persisted individually and resume safely after interruption.
- Model revisions, tokenizer revisions, packages, prompts, and run signatures are
  frozen in manifests.
- Generation errors, invalid objects, and token-cap hits remain in denominators.
- No confirmatory output is removed after viewing model behavior.
- Every confirmatory discordance is retained and manually categorized.
- Negative results, runner defects, and corrected interpretations remain public.
- New prompts or model families require a new protocol, not a rescue search.

## Reproduce the evidence

The lightweight audit path requires Python 3.11 or 3.12. It does not require a GPU,
model download, Outlines, or XGrammar.

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

Accepted replay result:

```text
464 rows replayed
0 row-score mismatches
0 paired-summary mismatches
```

The replay recomputes row scores and paired summaries from checked-in JSONL. It does
not trust the published Markdown reports as input evidence.

Install generation dependencies only when performing new model inference:

```bash
python -m pip install \
  -r requirements-generation.txt \
  -r requirements-backends.txt \
  -r requirements-analysis.txt
python scripts/probe_environment.py
```

[Open the complete reproducibility guide](https://vaibhav701161.github.io/constrained-senstivity-lab/reproducibility/artifact-replay/)

## Documentation

The documentation site is the primary long-form reading surface. It provides
searchable, structured navigation without forcing the README to contain every
protocol and artifact link.

| Section | Purpose |
|---|---|
| [Learn](https://vaibhav701161.github.io/constrained-senstivity-lab/getting-started/overview/) | Concepts and orientation for new readers |
| [Evidence](https://vaibhav701161.github.io/constrained-senstivity-lab/studies/evidence-overview/) | Complete experimental sequence and decisions |
| [System](https://vaibhav701161.github.io/constrained-senstivity-lab/architecture/) | Runtime, compiler boundary, and support policy |
| [Reproduce](https://vaibhav701161.github.io/constrained-senstivity-lab/reproducibility/artifact-replay/) | Tests, artifact replay, environments, and ledgers |
| [Evidence map](https://vaibhav701161.github.io/constrained-senstivity-lab/reproducibility/evidence-map/) | Protocols, manifests, raw rows, audits, and reports |
| [Publications](https://vaibhav701161.github.io/constrained-senstivity-lab/publications/) | Eight-part public technical series |

Build the site locally:

```bash
python -m pip install -r requirements-docs.txt
mkdocs serve
```

## Repository map

```text
constrained-senstivity-lab/
|-- assets/                 # deterministic data-derived technical figures
|-- articles/               # retained sources for public technical reports
|-- data/                   # frozen datasets and integrity manifests
|-- deployment/             # exact Kaggle and Modal execution surfaces
|-- docs/                   # documentation site and research records
|-- experiments/            # protocols, raw rows, audits, and decisions
|-- scripts/                # preparation, execution, analysis, and replay
|-- src/project_a/          # ContractIR, plans, runtime, and transducers
`-- tests/                  # unit, property, parity, and artifact tests
```

## Technical publications

The public series records the project from token-level grammar mechanics through
the final schema correction. The latest report is:

[**I Fixed a Schema Mismatch. The Negative Result Survived.**](https://dev.to/vaibhav_mittal_ac22a2c5d6/i-fixed-a-schema-mismatch-the-negative-result-survived-192l)

[Browse all eight articles](https://vaibhav701161.github.io/constrained-senstivity-lab/publications/)

## Citation

If this work informs research or engineering, cite the exact archived revision used.
Repository metadata is available in [CITATION.cff](CITATION.cff).

```bibtex
@software{mittal_constrained_sensitivity_lab,
  author  = {Vaibhav Mittal},
  title   = {Constrained Sensitivity Lab},
  year    = {2026},
  url     = {https://github.com/Vaibhav701161/constrained-senstivity-lab}
}
```

Released under the [MIT License](LICENSE).
