---
title: Contract alignment pivot
description: Historical architecture decision that authorized the narrow representation-alignment prototype
search:
  exclude: true
---

# Contract-alignment pivot decision

## Decision

Proceed with a bounded representation-alignment investigation before building a
general compiler.

## Evidence

The accepted Qwen2.5-7B, reasoning-first matrix contains 49 audited GSM8K items.
Prompt-only JSON answered 39 items correctly but did not satisfy the declared
numeric-string schema. Outlines and XGrammar each answered 30 items correctly and
satisfied that schema for every item. Against the same prompt-only rows, each backend
lost nine correct answers and gained none.

The loss pattern is localized enough to test. Eight losses are shared by the two
backends. Seven shared losses preserve the correct magnitude in the reasoning and
emit its negative in the final answer field. The model-facing grammar currently
requires a quoted string with an optional leading minus sign, while prompt-only JSON
naturally emits a number.

## Hypothesis

For canonical integer answers, a hard-constrained internal JSON integer can avoid the
quoted signed-string boundary. A deterministic integer-to-string transducer can then
restore the caller's external numeric-string contract without another model call.

## Safety requirement

The external schema remains authoritative. An internal output is returned only after
it is parsed, transduced, and validated against the original external schema. Unsafe
or ambiguous lexical conversions fail closed.

## Decision rule

The investigation advances to the compiler implementation only when a preregistered
safe transform recovers at least five percentage points on the frozen 49-item
confirmation set, repairs a majority of shared sign-loss items, preserves 100% final
external validity, and introduces no new systematic semantic failure.

If the mechanism is real but narrow, the deliverable narrows to an auditable
schema-risk analyzer or optimizer. If no safe intervention recovers fidelity, the
project concludes as a measurement study rather than expanding into speculative
decoder work.
