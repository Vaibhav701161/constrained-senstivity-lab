---
title: From research to StructTrace
description: How the accepted contract-sensitivity evidence became a reusable product
---

# From research to StructTrace

[StructTrace](https://github.com/Vaibhav701161/structtrace) is the product built from this lab's
accepted conclusion: structured-output contract changes must be measured on matched workload cases,
not assumed to preserve or improve semantic behavior.

## The handoff

```text
Constrained Sensitivity Lab
  frozen protocols, raw generations, corrections, paired evidence
                         |
                         v
  accepted boundary: syntax guarantees do not imply semantic preservation
                         |
                         v
StructTrace
  reusable paired runner, deterministic evaluators, replay, regression suite, CI gates
```

The handoff is evidence-backed rather than rhetorical. StructTrace pins the lab source revision and
SHA-256 digests of the accepted corrected Qwen, canonical Llama, and executable tool-call summaries
in its
[`provenance/research-foundation.json`](https://github.com/Vaibhav701161/structtrace/blob/main/provenance/research-foundation.json).

## Finding-to-feature traceability

| Accepted observation | Engineering requirement | StructTrace implementation |
|---|---|---|
| Schema compliance improved while semantic accuracy fell | Validity and correctness cannot share one metric | Separate parse, schema, semantic, executable, valid-but-wrong, and deployment states |
| Field order changed model behavior at fixed validity | A contract change is an experimental treatment | Identical case IDs, baseline/candidate variants, and a paired transition matrix |
| A positive Qwen estimate reversed on canonical Llama | Never generalize a rewrite from one model family | No automatic optimizer; every team measures its own workload |
| Cap hits, invalid objects, and execution failures affected conclusions | No favorable row filtering | Every known case remains in the deployment denominator |
| Corrections changed which artifact was authoritative | Evidence must be immutable and replayable | Hash-bound manifests, retained inputs, deterministic replay, and explicit integrity state |
| A product must survive repeated candidate changes | One-off reports are insufficient | Persistent projects, accepted baselines, pinned regression cases, and CI export |

## Authority boundary

Constrained Sensitivity Lab remains authoritative for:

- model and tokenizer revisions;
- frozen datasets and prompts;
- XGrammar and Outlines experiment rows;
- preregistration, mismatch corrections, and mechanism attribution;
- study-specific statistics and decision reports.

StructTrace is authoritative for:

- new user-supplied workload comparisons;
- deterministic evaluator configuration;
- local run artifacts and replay;
- recurring pinned-case status;
- project-specific release and CI decisions.

`structtrace demo research` normalizes the three accepted paired matrices into offline product
fixtures. It verifies that StructTrace reports the published transition counts and intervals. It is
not a byte-for-byte replay of the original remote inference runs, and it does not pool the studies.

## Why this is not a pivot away from the research

The negative replication narrowed the claim and improved the product direction. The lab showed
that contract rewrites can be safe as deterministic transformations yet unpredictable as model
quality interventions. StructTrace operationalizes that exact distinction: prove what can be proven
statically, measure what remains empirical, preserve failures, and refuse deployment authority when
the evidence is incomplete.
