---
title: Cross-study methodology
description: The current design rules shared by paired contract-sensitivity experiments
---

# Cross-study methodology

This is the current methodology layer for the completed research program. Earlier
protocols remain frozen under each experiment and may differ in scope. When this
page summarizes a rule, the experiment-specific protocol and manifest remain the
authority for what was actually executed.

## What this methodology establishes

The experiments ask whether changing a model-facing structured-output contract
changes model behavior while other relevant factors remain fixed. The core unit is
a paired item, not an independent aggregate score.

```text
same item + same model + same prompt + same decoding + same backend
                              |
                    model-facing representation
                         control vs treatment
                              |
              paired structural and semantic outcomes
```

The method separates three questions:

1. Is the transformation contract-preserving within its declared domain?
2. Does each output satisfy the internal and final external contracts?
3. Does the model remain semantically or executably correct?

A positive answer to one question does not imply a positive answer to the next.

## Frozen comparison surface

For a primary paired run, both conditions share:

- dataset items and ordering;
- model and tokenizer revisions;
- chat-template implementation and application depth;
- prompt wording except for the symbolic representation description;
- decoding policy, seed, precision, and token cap;
- constrained backend and package environment;
- visible-token counting and latency instrumentation;
- error handling, row format, and manifest construction;
- semantic and execution oracles.

Only the following may differ:

- the model-facing schema;
- the representation named in the prompt;
- whether deterministic inverse transduction is required.

Any other difference is experimental surface area and must be declared rather than
treated as cleanup.

## Datasets and exposure control

The confirmatory Llama study scanned JSONL artifacts under `results/`,
`experiments/`, and `deployment/` for previously used GSM8K identifiers. It removed
those identifiers, shuffled the remainder with seed `20260815`, and selected 150
items. The selected dataset and complete exclusion set were hashed before model
generation.

The earlier cleaned 49-item set remained a bridge comparison rather than the
confirmatory primary set. Repeatedly inspected items cannot carry the same claim as
a new holdout.

The executable pilot used a pinned BFCL V4 foundation and selected single-turn,
single-function `simple_python` cases. Local wrappers made execution deterministic
and side-effect free.

## Operational canaries

A canary tests only whether the run is safe to expand:

- identical item IDs and order across conditions;
- no duplicate rows;
- exactly one chat-template application;
- nonempty outputs;
- no unexpected generation exceptions;
- expected schema and transduction behavior;
- one model revision and tokenizer revision;
- one package environment;
- matching dataset hashes and paired run signatures.

Canary expansion never depends on early semantic success. Looking at whether the
treatment wins before deciding to continue would bias the experiment.

## Denominator policy

Generation errors, token-cap hits, parse failures, invalid internal objects,
external validation failures, and transduction failures remain in the denominator
and count as failures for the relevant final outcome.

No confirmatory item is removed after its model output is viewed. The sole cleaned
baseline exclusion was a contradictory dataset reference identified and documented
under the predeclared analysis rule. Later questionable cases remain visible.

## Outcome hierarchy

The harness records outcomes separately:

| Outcome | Meaning |
|---|---|
| Whole-response JSON | The complete generated response parses as one JSON value |
| Internal-schema validity | The generated object satisfies the model-facing schema |
| External-schema validity | The caller-facing object satisfies the unchanged original schema |
| Semantic correctness | The extracted answer or exact expected fields are correct |
| Contract-valid correctness | Semantic correctness and final external validity both hold |
| Tool selection | The requested deterministic wrapper was selected exactly |
| Argument semantics | Arguments match an accepted normalized argument set |
| Execution success | The validated wrapper accepted and executed the call |
| Post-execution state | The deterministic state receipt matches the oracle |

There is no single composite quality score. A 100% structural result and an 80%
semantic result are both reported because they answer different questions.

## Paired statistics

For every paired binary outcome, items are divided into four cells:

| Control | Treatment | Interpretation |
|---|---|---|
| Correct | Correct | Both correct |
| Incorrect | Correct | Treatment-only repair |
| Correct | Incorrect | Control-only regression |
| Incorrect | Incorrect | Both incorrect |

The primary effect is:

```text
(treatment-only - control-only) / paired item count
```

Reports include:

- paired percentage-point difference;
- exact McNemar test on the discordant cells;
- deterministic exact paired-bootstrap interval under the frozen analysis code;
- repaired and newly broken item identifiers;
- marginal rates for context.

The studies are not pooled. Their models, tasks, and some outcome definitions differ.

## Manual mechanism audit

Every canonical Llama discordance was inspected. Categories were frozen before the
final audit:

- sign or lexical-boundary change;
- arithmetic correction;
- arithmetic regression;
- problem-interpretation change;
- reasoning and final-answer inconsistency;
- truncation;
- parser or validator issue;
- other.

These labels describe observed transition patterns. They are not formal causal
proof. Reasoning consistency is reported separately from final-answer correctness,
and a correct answer with inconsistent reasoning remains correct under the primary
final-answer outcome.

## Correction policy

When an external review found that the broad Llama control accepted a larger string
language than the compiler proved equivalent, the project did not reinterpret the
existing run as final. It:

1. recorded the mismatch before new generation;
2. preregistered one canonical control;
3. reused the immutable treatment rows;
4. preserved the model, prompt, dataset, backend, and analysis;
5. allowed no post-launch exclusions;
6. reported both the intermediate and corrected results.

This isolates the correction without searching prompts or subsets for a preferred
answer.

## Latency and resource metrics

Latency, generated tokens, and cap hits are retained per row. Latency is descriptive
because experiments ran on different hardware and service environments. No causal
speed claim is made across Kaggle and Modal runs.

Greedy decoding is deterministic under the tested stack. Repeating identical seeds
would add little evidence, so compute was spent on more paired items instead.

## Evidence lifecycle

Each complete gate contains, where applicable:

```text
hypothesis or protocol
        -> dataset and source manifests
        -> canary gate
        -> raw JSONL rows
        -> artifact validation
        -> paired machine-readable summary
        -> complete discordance audit
        -> frozen decision report
```

Public documentation is a living interpretation layer. Frozen JSONL, manifests,
source hashes, tags, and decision reports define the executed record.

## Limitations

- Two model families do not represent all LLMs.
- GSM8K is not a complete structured-output workload.
- The executable pilot is small, local, and single-turn.
- Greedy decoding does not characterize sampling variability.
- Manual attributions can be reviewed but are not automated causal inference.
- Supported schema transforms are deliberately narrow.

[Open metric definitions](metrics.md){ .csl-button .csl-button--secondary }
[Trace the evidence files](../reproducibility/evidence-map.md){ .csl-button .csl-button--secondary }
[Inspect the final results](../results/index.md){ .csl-button .csl-button--primary }
