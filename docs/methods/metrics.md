---
title: Metric definitions
description: Exact structural, semantic, executable, paired, and operational measures used by the harness
---

# Metric definitions

This reference defines what each reported number means and what it does not mean.
Fields are kept separate so structural success cannot hide semantic failure.

## Structural metrics

### Whole-response valid JSON

The complete generated text parses as one JSON value. Recovering the first object
from surrounding prose does not count.

### Internal-schema validity

The parsed generated object satisfies the schema given to the constrained backend.
For treatment rows, this may be an internal representation rather than the caller's
original schema.

### Final external-schema validity

After any deterministic inverse transduction, the caller-facing object validates
against the unchanged original JSON Schema.

### Field-order match

Keys appear in the expected generated order. This is measured because autoregressive
generation order can alter behavior even when object semantics are nominally
unordered.

## Semantic metrics

### Recoverable correctness

The expected task answer can be extracted and normalized from the output, even when
the complete response violates the requested schema. This diagnostic distinguishes
mathematical ability from contract compliance.

### Strict correctness

The answer is correct and the required strict representation checks pass.

### Contract-valid correctness

The final answer is semantically correct and the final external object is valid.
This is the primary GSM8K outcome for the representation studies.

### Reasoning and final-answer consistency

For the frozen Llama analysis, the last numeric mention in the reasoning is compared
with the final answer. This is a diagnostic heuristic. It is not a second correctness
oracle and does not override final-answer scoring.

## Executable metrics

### Tool-selection correctness

The emitted function name exactly matches the expected deterministic wrapper.

### Argument-semantics correctness

The normalized arguments exactly match one of the accepted argument sets for the
case. Valid types alone are insufficient.

### Execution success

The reconstructed call passes validation and the local wrapper executes without an
exception. This does not imply the resulting state is correct.

### Correct post-execution state

The deterministic execution receipt matches the expected state transition.

### Executable-contract success

Tool selection, argument semantics, final external validity, execution, and
post-execution state all succeed. This is the practical pilot's primary outcome.

## Paired metrics

### Treatment-only wins

Items that fail under control and succeed under treatment.

### Control-only wins

Items that succeed under control and fail under treatment.

### Paired difference

```text
(treatment-only wins - control-only wins) / paired item count
```

The paired difference is reported in percentage points.

### Exact McNemar test

An exact test using only discordant pairs. It asks whether treatment-only and
control-only counts are symmetric under the null. It does not measure practical
importance.

### Exact paired-bootstrap interval

The frozen analysis resamples paired item transitions and reports the predeclared
95% interval. Pairing is preserved on every resample.

## Operational metrics

### Token-cap hit

Generation consumed the full maximum-new-token budget. Cap-hit rows remain in the
denominator and may be structurally invalid.

### Generation error

The model or backend raised an exception for the row. Errors remain in the
denominator.

### Generated tokens

Visible continuation tokens only. Prompt tokens are recorded separately where
available.

### Latency

Wall-clock generation latency recorded by the runner. It is descriptive and should
not be compared causally across hardware or hosted environments.

## Terms intentionally avoided

The project does not publish a single "quality score." It also avoids calling
backend parity an independent replication or calling a confidence interval a proof
of mechanism.
