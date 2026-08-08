---
title: Contract sensitivity
description: Why equivalent caller information can create different model generation paths and outcomes
---

# Contract sensitivity

Contract sensitivity is the degree to which a model's semantic behavior changes
when the model-facing output contract changes.

Two schemas can represent the same caller-visible information but create different
generation paths for the model. For example:

=== "External representation"

    ```json
    {
      "type": "string",
      "pattern": "^-?(?:0|[1-9][0-9]*)$"
    }
    ```

=== "Internal representation"

    ```json
    {
      "type": "integer"
    }
    ```

A deterministic function can map any generated integer to the canonical external
string. This proves representation preservation inside the supported domain. It
does not prove model-behavior preservation.

## Three different claims

1. **Structural claim:** the generated object satisfies the internal schema.
2. **Transformation claim:** inverse transduction reconstructs an object satisfying
   the unchanged external schema.
3. **Quality claim:** using the internal representation preserves or improves the
   model's semantic answer.

The first two can often be established through validators and property tests. The
third requires paired empirical evidence.

## Paired measurement

For each item, run a control and treatment under matched conditions. Classify the
pair as:

| Control | Treatment | Interpretation |
|---|---|---|
| Correct | Correct | Concordant success |
| Wrong | Wrong | Concordant failure |
| Wrong | Correct | Treatment-only win |
| Correct | Wrong | Control-only loss |

The treatment effect is the difference between the treatment-only and control-only
rates. Exact McNemar tests and paired bootstrap intervals quantify discordance and
uncertainty without pretending the two arms are independent samples.

## Why aggregate validity is insufficient

A system can achieve 100% external validity while changing which answers are
correct. The Llama canonical correction had complete control validity and 99.3%
treatment validity, yet the treatment lost ten net correct items. Manual audit
attributed the discordances to interpretation, answer consistency, and arithmetic,
not to parsing or sign conversion.

## Practical policy

A production system should treat a model-facing schema rewrite like a prompt or
model change:

1. compile only transformations with a proven inverse;
2. fail closed on unsupported schema features;
3. validate the reconstructed object against the original contract;
4. run paired task and execution evaluations;
5. ship only when the workload-specific evidence clears a predefined gate.

## Related evaluation work

The [JSONSchemaBench study](https://arxiv.org/abs/2501.10868) evaluates structured
generation across schema coverage, efficiency, and output quality. Constrained
Sensitivity Lab focuses more narrowly on paired semantic and executable transitions
caused by changing the model-facing contract while the caller-facing contract stays
fixed.
