# Canonical schema correction

## Purpose

The correction tested exact language equivalence. It did not change the model,
dataset, prompt, treatment, backend, decoding policy, software environment, or
analysis rule.

Control language:

```regex
^-?(?:0|[1-9][0-9]*)$
```

Treatment representation:

```json
{"type": "integer"}
```

After generation, the treatment integer was deterministically stringified and the
reconstructed object was validated against the unchanged external schema.

## Frozen execution

- One new 150-row canonical-string control
- Existing 150-row integer treatment reused byte for byte
- Same Llama model and tokenizer revision
- Same unseen GSM8K item IDs and order
- XGrammar 0.2.3, greedy FP32, seed 0, 256-token cap
- No post-launch exclusions

The operational canary checked configuration and artifact integrity only. Semantic
performance was not used as an expansion criterion.

## Corrected result

| Metric | Canonical string | Integer treatment |
|---|---:|---:|
| Contract-valid correctness | 92/150 (61.3%) | 82/150 (54.7%) |
| Final external validity | 150/150 (100.0%) | 149/150 (99.3%) |
| Internal schema validity | 150/150 (100.0%) | 149/150 (99.3%) |
| Errors | 0 | 0 |
| Token-cap hits | 0 | 1 |

The paired effect was **-6.7 percentage points**, with exact paired bootstrap
interval **[-12.7, -0.7]**, six treatment-only wins, sixteen control-only losses,
and exact McNemar `p = 0.05248`.

![Canonical correction result and complete discordance attribution](../assets/figures/canonical-schema-correction.png)

## Complete discordance audit

All 22 discordant items were manually classified:

| Category | Count |
|---|---:|
| Problem-interpretation change | 10 |
| Reasoning and final-answer inconsistency | 8 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Parser, validator, or transducer issue | 0 |
| Truncation | 0 |

The schema mismatch was real, but it was not the cause of the negative direction.
Compared with the original broad control, 134/150 raw outputs were byte-identical
and aggregate correctness remained 92/150.

## Final decision

The safe transducer remains supported. The claim that this representation should be
selected as a default model-quality optimization is closed. Future work targets a
contract-sensitivity analyzer that measures workload-specific effects before a
rewrite is deployed.

## Primary records

- [Preregistered protocol](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/protocol.md)
- [Source manifest](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/source-manifest.json)
- [Artifact validation](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/artifact-validation.json)
- [Complete failure attribution](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/failure-attribution.jsonl)
- [Decision report](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/decision-report.md)
