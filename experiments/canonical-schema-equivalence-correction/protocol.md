# Canonical schema-equivalence correction protocol

## Freeze boundary

This protocol is frozen before generating the new canonical-string control. The
accepted second-family raw artifacts remain immutable.

The correction repairs one discovered experimental mismatch. It is not a prompt
search, model search, dataset search, backend comparison, or transform expansion.

## Why the correction is required

The accepted second-family control schema used this broad language:

```regex
^-?(?:(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?|(?:\d+|\d{1,3}(?:,\d{3})+)/(?:\d+|\d{1,3}(?:,\d{3})+))$
```

It admits integers, decimals, fractions, comma grouping, and leading zeros. The
compiler's safe transform accepts only:

```regex
^-?(?:0|[1-9][0-9]*)$
```

The original cross-family result therefore tested a broad numeric-string-to-integer
intervention, not an exactly language-equivalent canonical integer-string transform.

A post-result audit found eight broad-control outputs outside the canonical language:
six on the fresh set and two on the bridge set. All eight were incorrect in both
representations, so they do not directly account for the ten-net-answer fresh loss.
The mismatch still prevents the strongest exact-transform conclusion.

## Frozen components

| Component | Value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Model and tokenizer revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Dataset | `data/gsm8k_unseen_150_seed20260815.jsonl` |
| Dataset SHA-256 | `70e7af8691a4b8273dc14fcb825140573fe5dcc570723b9d58e755dc3b36e154` |
| Dataset role | Fresh confirmatory holdout |
| Backend | XGrammar 0.2.3 |
| Decoding | Greedy, `do_sample=False`, seed 0 |
| Dtype | FP32 |
| Placement | `device_map="auto"` on Modal L4 |
| Maximum new tokens | 256 |
| Chat template | Llama template applied exactly once |
| Prompt | Byte-identical raw prompt text to the accepted signed-string control |
| Field order | `reasoning`, then `answer` |
| Whitespace | Canonical compact XGrammar separators |
| Post-launch exclusions | None |

The package environment must remain the pinned project environment. The model,
tokenizer, prompt wording, item order, backend, decoding policy, precision, and token
budget cannot change.

## Frozen treatment

The comparison reuses, without regeneration or modification:

```text
experiments/second-family-replication/results/fresh/
    xgrammar_json_integer_reasoning_first.jsonl
```

Frozen treatment properties:

- 150 assigned rows;
- result SHA-256
  `298d1a38ad8d95d89ca97ab1f98d14bef4853342bf388d080f57f06de9c47342`;
- run ID `20260807T180428Z-a2fa2f3f8dfb`;
- one retained token-cap and invalid-object failure;
- no generation exceptions; and
- no post-launch exclusions.

Treatment raw outputs are rescored against the corrected canonical external schema.
The stored raw outputs, timing, tokens, errors, and cap flags remain unchanged.

## One authorized new arm

Generate exactly one new condition:

```text
xgrammar_json_canonical_integer_string_reasoning_first
```

Its model-facing and external answer field is:

```json
{
  "type": "string",
  "pattern": "^-?(?:0|[1-9][0-9]*)$"
}
```

The internal integer treatment schema must be produced by applying the same
`IntegerStringTransform` applicability and rewrite path to this external schema. The
canonical pattern must have one source of truth shared by the compiler, experiment,
and tool-call runtime.

Only the JSON Schema grammar changes relative to the accepted broad string control.
The raw prompt must remain byte-identical because both controls request a quoted
numeric answer through the same symbolic template.

No new integer arm, bridge arm, Outlines arm, model family, prompt variant, or seed is
authorized.

## Operational canary

The first five assigned items run into the same resumable result file. Expansion may
check only:

- exact first-five IDs and order;
- no duplicates;
- raw prompt equality with the accepted broad control;
- one chat-template application;
- nonempty outputs;
- no generation exceptions;
- no token-cap hits;
- 100% internal and external canonical-schema validity;
- exact model and tokenizer revision;
- frozen dataset and source hashes;
- one package and GPU environment; and
- a valid run signature.

Semantic correctness and whether the canonical control wins cannot be inspected or
used for expansion. The same file resumes from 5 to 150.

## Scoring and denominator

Both arms are recomputed from `raw_output` under the corrected schemas. Replay must
recompute:

- whole-object JSON parsing;
- internal-schema validation;
- integer inverse transduction where applicable;
- validation against the canonical external schema;
- normalized final-answer extraction;
- semantic correctness against the frozen gold answer;
- contract-valid correctness; and
- paired summary statistics.

Errors, cap hits, invalid JSON, invalid internal objects, transduction failures, and
external-schema failures remain in the assigned denominator. There are no retries,
repairs, output recovery, or post-launch exclusions.

## Primary analysis

The sole primary comparison is:

```text
new canonical-string control, 150 rows
versus
frozen integer treatment, 150 rows
```

Report:

- contract-valid correctness in both arms;
- semantic correctness before contract requirements;
- final external validity;
- treatment-only and control-only wins;
- paired percentage-point difference, defined as treatment minus control;
- exact paired bootstrap 95% interval;
- exact two-sided McNemar test;
- generated tokens, errors, caps, and descriptive latency;
- reasoning-to-final-answer consistency;
- every repaired item ID;
- every newly broken item ID; and
- a manual audit of every discordant item.

The historical broad control remains reported separately and is never pooled with
the corrected comparison.

## Interpretation gate

### Exact transform remains negative

If the treatment-minus-canonical-control estimate is negative, or control-only wins
equal or exceed treatment-only wins, the exact optimizer thesis closes confidently
for this model and workload. The product remains a contract-sensitivity evaluation
harness.

### Approximately neutral or uncertain

If the absolute point estimate is below 5 percentage points, or its interval crosses
zero without a directional loss imbalance, the default optimizer remains rejected.
The conclusion becomes that the earlier Llama harm was partly or wholly associated
with the broader numeric language, while the exact transform has no demonstrated
benefit.

### Post-discovery positive

If the treatment improves by at least 5 points, treatment-only wins exceed
control-only wins, external validity is 100%, and there is no coherent regression
cluster, record a post-discovery positive correction. Do not call it an independent
replication. A new fresh paired holdout would be required before any positive
cross-family claim.

## Required artifacts

```text
experiments/canonical-schema-equivalence-correction/
|-- HYPOTHESIS.md
|-- protocol.md
|-- mismatch-audit.json
|-- source-manifest.json
|-- canary-gate.json
|-- artifact-validation.json
|-- replay-validation.json
|-- paired-summary.json
|-- paired-summary.md
|-- failure-attribution.jsonl
|-- decision-report.md
|-- manifests/
`-- results/
```

The final report must update the claim scope even if the correction produces an
unfavorable, neutral, or post-discovery positive result.

## Compute policy

The Modal free-credit gate remains active with a $27 launch ceiling and $3 reserve.
No run may launch if billed cost is nonzero or metered monthly use reaches the
ceiling. Only the one authorized 150-row arm may consume new GPU compute.
