---
title: Current evidence status
description: The final claim boundary and implementation direction after every completed decision gate
---

# Current evidence status

## Status

The completed evidence closes the general contract-alignment quality-optimizer
thesis. The supported direction is primarily a contract-sensitivity analyzer and
reproducible measurement harness, with a secondary fail-closed schema linter.

This document is the current interpretation layer. The public
[`architecture.md`](architecture.md) and
[`supported-contracts.md`](supported-contracts.md) are living documentation and
have evolved after the second-family launch. The exact versions used by that run
remain recoverable through its
[source manifest](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/second-family-replication/source-manifest.json)
and the `llama32-second-family-replication-v1` tag. Frozen artifacts, not the current
documentation pages, define the executed environment.

!!! info "Document status: current"

    This page reflects the final canonical correction and executable pilot. When a
    historical report disagrees with it about current direction, this page and the
    latest frozen decision report take precedence.

## Evidence sequence

| Gate | Paired treatment effect | Wins : losses | Decision |
|---|---:|---:|---|
| Corrected Qwen2.5-7B GSM8K, 49 items | +12.2 pp, interval [0.0, 26.5] | 9 : 3 | Scoped continuation at that gate |
| Llama 3.2 3B broad-string GSM8K, 150 items | -6.7 pp, interval [-12.7, -1.3] | 5 : 15 | Negative, later corrected for schema equivalence |
| Llama 3.2 3B canonical-string correction, 150 items | -6.7 pp, interval [-12.7, -0.7] | 6 : 16 | Optimizer thesis closed |
| Llama 3.2 3B tool-dispatch primary pilot, 30 calls | -6.7 pp, interval [-20.0, 6.7] | 1 : 3 | No evidence of practical benefit |

The Qwen observation remains valid for its frozen model, dataset, prompt, precision,
and runner. It did not reproduce on a different model family and unseen items. An
external review found that the first Llama control accepted a broader numeric-string
language than the compiler. A preregistered one-arm correction reused the immutable
integer treatment and exact canonical schema. The negative estimate survived. The
bounded practical pilot also failed its directional gate.

## Current contract status

| Capability or claim | Current status | Evidence |
|---|---|---|
| Parse canonical signed integer strings | Supported utility | Adversarial lexical tests and exact parser behavior |
| Integer to canonical string transduction | Supported utility | 1,501 property cases, arbitrary-precision cases, boolean refusal, and original-schema validation |
| Validate against the unchanged external schema | Supported utility | Property tests, compiler probes, Llama matrix, and 66 executable pilot generations |
| Deterministic tool-dispatch harness | Supported measurement capability | Exact dispatch, strict typed arguments, state receipts, and zero heuristic repairs |
| Cross-family paired evaluation | Supported measurement capability | Frozen unseen dataset, unified runner, source manifests, exact paired statistics, and complete discordance audit |
| Native integer as a default quality optimization | Rejected by current evidence | Positive Qwen estimate did not reproduce; both later primary gates were negative |
| Field ordering as a quality optimization | Prototype only | Strong historical sensitivity evidence, but no independent quality validation |
| Key aliases | Prototype only | Unit tested without task-level validation |
| Scratch fields | Experimental | Safety tested without task-level quality validation |
| `$ref`, unions, arbitrary regex transforms | Refused | Preservation and invertibility are not proven |
| Heuristic or model-based repair | Refused | Would alter semantics and obscure provenance |

Contract safety and quality benefit are separate claims. A transducer can be
correctly implemented and still perturb model behavior in a harmful direction.

## Supported product loop

```text
External schema and workload
        |
        v
Static schema-risk analysis
        |
        v
Frozen paired representation plan
        |
        v
Matched constrained generations
        |
        v
External validation and deterministic execution
        |
        v
Paired statistics and complete discordance audit
        |
        v
Workload-scoped recommendation, warning, or refusal
```

The analyzer must preserve negative and uncertain interventions. It cannot search
prompts, models, or subsets until an effect becomes positive. A static linter may
identify a representation boundary as risky or measurable, but it cannot promise
that a particular transform will improve semantic correctness.

## Authorized implementation direction

1. Keep the existing ContractIR, alignment plans, transducers, and final validation
   as audited mechanisms.
2. Treat transforms as explicit experimental variants rather than automatic
   optimizations.
3. Make paired workload evaluation and provenance the primary interface.
4. Report validity, task semantics, execution, uncertainty, and regressions
   separately.
5. Refuse unsupported schema constructs and unproven inverse mappings.
6. Store workload-specific evidence with each recommendation.
7. Preserve control-only failures and treatment-only wins at item level.

## What is closed

The current evidence closes these claims:

- native-integer generation generally improves canonical numeric-string contracts;
- the corrected Qwen gain independently replicated on Llama;
- perfect schema validity implies preserved call semantics; and
- the bounded BFCL-based result supports broad optimizing-compiler expansion.

The exact canonical correction resolves the prior schema mismatch, so no more copies
of the same Qwen or Llama matrices are needed to decide those claims.
Future research should evaluate the analyzer itself: whether its warnings and paired
measurements predict deployment regressions across real workloads. That is a new
research question and requires its own frozen protocol.

## Canonical decisions

- [Corrected Qwen decision](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/decision-report.md)
- [Second-family replication decision](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/second-family-replication/decision-report.md)
- [Canonical schema-equivalence correction](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/canonical-schema-equivalence-correction/decision-report.md)
- [Executable tool-call pilot decision](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/tool-call-gate/decision-report.md)
- [Executable discordance audit](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/tool-call-gate/failure-attribution.jsonl)

The latest decision report takes precedence for product scope. Historical reports
remain immutable evidence of what was known at each gate.
