# Representation Alignment Results

## Decision

**Green, continue the contract-alignment compiler for the supported schema
subset.**

On the frozen, cleaned 49-item Qwen2.5-7B-Instruct GSM8K evaluation, replacing
the hard-constrained model-facing signed numeric string with a native JSON
integer recovered 14.3 percentage points of contract-valid correctness for both
Outlines and XGrammar. A deterministic integer-to-string transducer preserved
the caller's original signed-string external contract for every output.

This is evidence for a restricted mechanism in one model, prompt, decoding
policy, schema, and task. It is not evidence that every structured-generation
failure can be fixed by representation alignment.

## Accepted evidence

The following artifacts passed independent validation with no warnings:

- Targeted gate: 18 rows for each of four conditions and six required trace
  records. See
  [`cloud-targeted/artifact-validation.json`](../experiments/representation-alignment-gate/results/cloud-targeted/artifact-validation.json).
- Full confirmation: 50 raw rows for each of three conditions, with the
  predeclared contradictory GSM8K item excluded only from the cleaned 49-item
  analysis. See
  [`cloud-full/artifact-validation.json`](../experiments/representation-alignment-gate/results/cloud-full/artifact-validation.json).

Every accepted full-confirmation row had a known source hash, a unique item ID,
no generation error, no token-cap hit, and a valid final external object.

## Full confirmation

| Condition | Semantic correctness | Contract-valid correctness | Final external validity | Negative answers |
|---|---:|---:|---:|---:|
| Prompted signed string | 39/49 (79.6%) | 0/49 (0.0%) | 0/49 (0.0%) | 1/49 (2.0%) |
| Prompted integer | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) |
| Outlines signed string | 30/49 (61.2%) | 30/49 (61.2%) | 49/49 (100.0%) | 12/49 (24.5%) |
| Outlines integer | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) |
| XGrammar signed string | 30/49 (61.2%) | 30/49 (61.2%) | 49/49 (100.0%) | 12/49 (24.5%) |
| XGrammar integer | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) |

The prompted signed-string condition is semantically scored independently of
the external schema. Its answers are JSON numbers, so it has zero strict
external-contract validity. The prompted integer condition is transduced before
external validation, as are the constrained integer conditions.

## Paired effects against the frozen constrained baselines

| Comparison | Contract-valid difference | 95% paired interval | Treatment-only / control-only correct | Exact paired p |
|---|---:|---:|---:|---:|
| Outlines integer minus Outlines signed string | +14.3 pp | [4.1, 26.5] pp | 8 / 1 | 0.0391 |
| XGrammar integer minus XGrammar signed string | +14.3 pp | [0.0, 28.6] pp | 10 / 3 | 0.0923 |

The Outlines comparison clears a two-sided exact paired test at 0.05. The
XGrammar comparison has the same point estimate, but its interval touches zero
and its exact paired p-value does not clear 0.05. The preregistered project
criterion is recovery, external validity, and absence of a systematic new
failure, not a p-value requirement. Both backends clear the 5-point recovery
threshold and preserve 100% external validity.

## Item-level changes

Outlines integer repaired eight baseline errors:
`gsm8k_test_173`, `gsm8k_test_183`, `gsm8k_test_244`, `gsm8k_test_482`,
`gsm8k_test_506`, `gsm8k_test_694`, `gsm8k_test_712`, and
`gsm8k_test_739`. It newly missed `gsm8k_test_629`.

XGrammar integer repaired ten baseline errors:
`gsm8k_test_1216`, `gsm8k_test_1284`, `gsm8k_test_173`, `gsm8k_test_183`,
`gsm8k_test_244`, `gsm8k_test_482`, `gsm8k_test_629`, `gsm8k_test_694`,
`gsm8k_test_712`, and `gsm8k_test_739`. It newly missed
`gsm8k_test_1003`, `gsm8k_test_12`, and `gsm8k_test_506`.

The eight shared signed-string losses were repaired on 7/8 Outlines items and
8/8 XGrammar items. The original 12/49 negative-answer rate for each
constrained signed-string backend fell to 0/49 in both integer conditions.

## Boundary traces

The XGrammar trace records three representative answer boundaries:
`gsm8k_test_12`, `gsm8k_test_173`, and `gsm8k_test_1216`. After JSON whitespace
at the internal integer value boundary, digit tokens were legal and selected.
For example, on the original shared sign-loss item `gsm8k_test_173`, token `1`
had a pre-mask score of 39.63 while the standalone minus token had a score of
-1.33; `1` was selected. The traces are consistent with the representation
hypothesis, but they do not prove a universal causal account of all signed
numeric-string behavior.

See the compact raw trace at
[`xgrammar-integer-answer-boundary.jsonl`](../experiments/representation-alignment-gate/results/cloud-full/results/representation-alignment-full/traces/xgrammar-integer-answer-boundary.jsonl).

## Operational observations

- The full run used Qwen2.5-7B-Instruct, greedy decoding, FP32, a fixed
  256-token cap, and the frozen 50-item order.
- Average latency was about 90.3 seconds for prompted integer, 92.8 seconds
  for Outlines integer, and 92.7 seconds for XGrammar integer. The matching
  signed-string baseline latencies were about 96.9, 99.6, and 100.0 seconds.
- Integer representation did not increase average generated tokens relative to
  the signed-string constrained baselines.
- A prior local XGrammar smoke exposed invalid reuse of a stateful logits
  processor. The runner now creates a fresh processor per generation; the
  accepted cloud artifacts contain no resulting errors.

## Scope and next work

The next implementation phase should build only the safe, explainable subset:
integer-string canonicalization, field-order restoration, key aliases,
canonical whitespace, final external validation, and refusal on unsupported
schemas. Cross-model and tool-call replication remain required before making a
general product or research claim.

The machine-readable paired summary is
[`cloud-full/paired-summary.json`](../experiments/representation-alignment-gate/results/cloud-full/paired-summary.json).
