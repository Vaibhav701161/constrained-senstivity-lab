# Second-Family Contract-Alignment Replication Protocol

## Registration status

This protocol is frozen before viewing any Llama generation output. The dataset is
selected mechanically from previously unseen GSM8K test items. Model outputs cannot
change the sample, prompt, primary metric, thresholds, or exclusion policy.

## Question

On a non-Qwen model and unseen GSM8K items, does replacing a model-facing signed
numeric string with a native JSON integer improve final external-contract-valid
correctness after deterministic stringification?

## Frozen system

| Component | Specification |
|---|---|
| Primary model | `meta-llama/Llama-3.2-3B-Instruct` |
| Model revision | Frozen in the source and run manifests before the canary |
| Tokenizer revision | Identical to the frozen model revision |
| Primary dataset | 150 previously unseen `openai/gsm8k` test items |
| Holdout seed | `20260815` |
| Bridge dataset | Existing cleaned 49 items from the corrected Qwen replication |
| Primary backend | XGrammar 0.2.3 |
| Control | `signed-numeric-string` representation |
| Treatment | `integer` representation plus deterministic stringification |
| Prompt family | Frozen reasoning-first symbolic two-field JSON prompt |
| Decoding | Greedy, `do_sample=False`, seed 0, FP32, 256 maximum new tokens |
| Model placement | `device_map="auto"` on one frozen Modal GPU type |
| Package environment | Existing accepted Torch, Transformers, XGrammar, Outlines, JSON Schema, Accelerate, and Datasets versions |
| Failure policy | Errors, cap hits, invalid objects, and transduction failures remain in the denominator as failures |

The accepted prototype tagged `contract-alignment-prototype-v1` is the architectural
baseline. Package upgrades and transform expansion are prohibited in this experiment.

## Conditions

| Representation | Model-facing answer | Final external answer |
|---|---|---|
| Signed-string control | JSON string matching the signed numeric-string schema | The generated string after original-schema validation |
| Integer treatment | Native JSON integer | Exact base-10 stringification followed by original-schema validation |

Every other generation path is shared: model and tokenizer loading, chat templating,
grammar compilation, decoding, visible-token counting, latency measurement, error
handling, manifests, row writing, and resume validation.

## Dataset construction

`scripts/prepare_unseen_gsm8k.py` scans every JSONL artifact under `results/`,
`experiments/`, and `deployment/`. It records all observed `item_id`, `id`, and
`source_index` values, removes those GSM8K indices from the full test split, shuffles
the remaining indices with Python's seeded MT19937 implementation using seed
`20260815`, and selects the first 150.

The generated manifest records:

- every excluded ID and source index;
- the excluded-set hash;
- the selected dataset hash;
- dataset source, configuration, split, fingerprint, and seed;
- scan roots and JSONL file count;
- integrity-check results.

Selection is random after exclusion. No negative-answer or otherwise interesting
case is selected manually.

Gold answers are parsed and validated before generation. A dataset defect may be
excluded only if documented before any model output is viewed. A questionable
reference discovered after output inspection remains in the primary denominator.

## Analysis sets

### Primary fresh holdout

The 150 unseen items carry the confirmatory claim.

```text
150 signed-string control generations
150 integer treatment generations
300 primary fresh generations
```

### Bridge set

The 49 cleaned corrected-Qwen items measure comparability with historical evidence.

```text
49 signed-string control generations
49 integer treatment generations
98 bridge generations
```

The full primary XGrammar matrix contains 398 generations over 199 paired items.
Fresh and bridge results are never pooled for the confirmatory estimate.

## Operational canary

The first five frozen fresh items run under both representations. The same files
resume from 5 to 150, so the canary creates no duplicate research rows.

Expansion requires:

1. identical five item IDs in identical order;
2. no duplicates;
3. exactly one chat-template application;
4. nonempty raw outputs;
5. no generation exceptions;
6. no token-cap hits;
7. 100% model-facing schema validity;
8. 100% final external validity after treatment transduction;
9. one model revision and one tokenizer revision;
10. one package environment;
11. matching dataset hashes and representation-specific run signatures;
12. a complete environment and source manifest.

The canary cannot inspect or gate on semantic correctness, repair counts, or which
representation wins. If hardware memory is insufficient, the canary is discarded
without semantic inspection and rerun in full on one newly frozen GPU type.

## Primary outcome

The primary outcome is the paired difference in contract-valid correctness on the
fresh 150-item set:

```text
integer treatment rate minus signed-string control rate
```

Contract-valid correctness requires both semantic correctness and validity under the
unchanged external signed-string contract.

## Required metrics

Fresh and bridge sets are reported separately.

Primary metrics:

- contract-valid correctness;
- final external validity;
- treatment-only wins;
- control-only wins;
- paired percentage-point difference;
- exact two-sided McNemar test;
- exact empirical paired-bootstrap percentile interval.

Secondary metrics:

- semantic correctness before external-contract requirements;
- internal-schema validity;
- generated visible-token counts;
- cap hits and generation errors;
- negative-answer counts;
- latency, explicitly labeled descriptive;
- reasoning and final-answer consistency;
- every repaired item ID;
- every newly broken item ID.

All denominators remain visible. Backend errors cannot be dropped from a condition.

## Discordant-item audit

Every fresh-set discordant item is manually inspected after the XGrammar result is
frozen. Each transition receives one primary category and optional notes:

1. sign or lexical-boundary change;
2. arithmetic correction;
3. arithmetic regression;
4. problem-interpretation change;
5. reasoning-final-answer inconsistency;
6. truncation;
7. parser or validator issue;
8. other.

Reasoning-inconsistent correct answers remain correct under the final-answer metric
and are separately marked inconsistent. They are never excluded.

## Outlines implementation-parity check

After the fresh XGrammar result and discordant set are frozen, Outlines runs on:

- every discordant fresh item; and
- 20 concordant fresh items selected with a separately frozen random seed.

Both representations are checked on this subset. This is an implementation-parity
probe, not an independent semantic result. It does not change the primary estimate.

## Decision gate

The practical effect threshold is five percentage points. "Meaningful harm" is
predefined as a paired effect below `-5` percentage points. Therefore, the Green
interval requirement is that the exact 95% paired interval has a lower bound of at
least `-5` points.

### Green: continue the compiler thesis

All conditions must hold on the fresh set:

1. treatment improves contract-valid correctness by at least 5 points;
2. final external validity is 100%;
3. treatment-only wins exceed control-only wins;
4. the exact paired interval does not extend below -5 points;
5. the bridge set does not show an effect of at least 5 points in the opposite direction;
6. no coherent new systematic regression cluster is observed.

### Green+: strong independent replication

Green holds, the exact paired interval is strictly above zero, and the exact paired
test reaches `p < 0.05`. Only Green+ authorizes describing the result publicly as an
independent replication and beginning broad company or recruiter outreach.

### Yellow: promising but not independently validated

Yellow applies when the estimate is positive but below five points, the interval
crosses zero while avoiding meaningful harm, fresh and bridge estimates materially
disagree, benefit is restricted to a narrow error category, or regressions prevent a
clean preservation claim.

Yellow authorizes the executable tool-call gate. It does not authorize broad schema
features or a broad outreach campaign.

### Red: no cross-family replication

Red applies if the fresh estimate is zero or negative, control-only wins equal or
exceed treatment-only wins, final external validity is below 100%, the interval
extends into meaningful harm alongside no persuasive benefit, or a coherent new
failure mode appears.

No prompt search follows a Red result. Red authorizes exactly one smaller practical
tool-call pilot. If that pilot is also Red, the project narrows to a schema-risk
linter, measurement harness, and contract-sensitivity analyzer.

## Compute and cost policy

Modal metered cost must remain within the account's free monthly compute credit. The
run uses CPU for preparation and validation, one GPU for generation, persistent
checkpoints, and no redundant greedy seeds. Metered cost is checked after image
build, canary, fresh control, fresh treatment, bridge control, bridge treatment, and
the Outlines subset.

The execution halts before expansion if projected total spend would exceed the
remaining free credit with a safety reserve. Avoiding a bill takes priority over
finishing a remote phase in the same billing cycle. No change to statistical rules
is permitted to reduce cost after outputs are viewed.

## Required release artifacts

The frozen result must contain:

```text
experiments/second-family-replication/
|-- HYPOTHESIS.md
|-- protocol.md
|-- dataset-manifest.json
|-- source-manifest.json
|-- manifests/
|-- results/
|-- traces/
|-- canary-gate.json
|-- artifact-validation.json
|-- paired-summary.json
|-- paired-summary.md
|-- failure-attribution.jsonl
`-- decision-report.md
```

The README is updated only after the decision report is frozen. The Qwen result is
preserved separately. A technical update is published only after the repository
evidence is complete, and a merely positive uncertain estimate is not described as
replicated.
