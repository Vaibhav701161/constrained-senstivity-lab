# Canonical Schema-Equivalence Correction Decision

## Decision

**Close the native-integer quality-optimizer thesis and continue the project as a
contract-sensitivity evaluation harness.**

The exact canonical control remained better than the frozen integer treatment on
the preregistered 150-item Llama holdout. The correction therefore resolves the
schema-language mismatch without reversing the cross-family conclusion.

This is a negative result for a default optimizer. It is a positive result for the
research process and for the measurement-system direction.

## Question

On the same frozen Llama model, unseen GSM8K items, prompt, XGrammar backend,
decoding policy, precision, and token budget, does replacing this exact external
answer language:

```regex
^-?(?:0|[1-9][0-9]*)$
```

with a native JSON integer improve final contract-valid correctness after
deterministic stringification?

The prior Llama control had accidentally accepted a broader language containing
decimals, fractions, comma grouping, and leading zeros. This correction generated
only one new canonical-string control arm. The accepted integer treatment was not
regenerated.

## Frozen comparison

| Setting | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Model and tokenizer revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Dataset | 150 previously unseen GSM8K test items |
| Dataset SHA-256 | `70e7af8691a4b8273dc14fcb825140573fe5dcc570723b9d58e755dc3b36e154` |
| Backend | XGrammar 0.2.3 |
| Decoding | Greedy, seed 0, FP32, 256 maximum new tokens |
| New arm | Canonical signed integer string |
| Frozen treatment | Native integer plus deterministic stringification |
| Frozen treatment SHA-256 | `298d1a38ad8d95d89ca97ab1f98d14bef4853342bf388d080f57f06de9c47342` |
| Post-launch exclusions | None |

The five-row operational canary was semantically blind and expanded by resuming the
same artifact. A client heartbeat interruption occurred after row 23. The runner had
already persisted every completed row, so execution resumed at row 24 in detached
mode. No completed item was regenerated.

## Primary result

| Outcome | Canonical string control | Frozen integer treatment |
|---|---:|---:|
| Contract-valid correct | 92/150, 61.3% | 82/150, 54.7% |
| Semantic correct | 92/150, 61.3% | 82/150, 54.7% |
| Final external valid | 150/150, 100.0% | 149/150, 99.3% |
| Internal schema valid | 150/150, 100.0% | 149/150, 99.3% |
| Generation errors | 0 | 0 |
| Token-cap hits | 0 | 1 |
| Mean generated tokens | 78.2 | 78.9 |
| Median generated tokens | 75 | 75 |

The paired treatment-minus-control estimate is **-6.7 percentage points**. The
exact paired bootstrap 95% interval is **[-12.7, -0.7] points**. There are six
treatment-only wins and sixteen control-only wins, with exact two-sided McNemar
`p = 0.05248`.

The confidence interval excludes zero under the frozen deterministic bootstrap.
The exact McNemar result narrowly misses the conventional 0.05 threshold. These
facts are reported separately. The decision does not depend on calling the result
statistically significant because the preregistered correction rule asked whether
the canonical control still beat the treatment. It did, by ten net items.

The treatment's one cap hit was retained as a failure. That item was incorrect in
both arms and therefore did not create a discordant pair.

## Complete discordance audit

Every one of the 22 discordant pairs was inspected against the question, reference
answer, raw control output, and raw treatment output.

| Manual category | Count |
|---|---:|
| Problem-interpretation change | 10 |
| Reasoning and final-answer inconsistency | 8 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Truncation | 0 |
| Parser or validator issue | 0 |
| Other | 0 |

The mechanism is not a failure to emit a minus sign. No reference answer in this
holdout was negative, and neither arm predicted a negative final answer. Instead,
the model-facing schema changed broader generation behavior: which problem steps
were retained, how expressions were evaluated, and which intermediate number was
selected as the final answer.

Reasoning and final-answer consistency was 123/150 for the canonical control and
119/149 among assessable treatment outputs. This metric uses the preregistered
last-numeric-mention heuristic and is secondary, not a proof of faithful reasoning.

The item-level evidence, including a written rationale for every classification, is
in [`failure-attribution.jsonl`](failure-attribution.jsonl).

## What the corrected grammar changed

Compared with the earlier broad-string control, 134/150 raw canonical-control
outputs were byte-identical and 140/150 normalized answers were identical. Sixteen
raw outputs changed. Aggregate correctness remained 92/150, but one item moved from
wrong to correct and one moved from correct to wrong.

The canonical grammar eliminated the six observed noncanonical fresh-set values.
Those six broad-control values had all been incorrect, but eliminating them did not
improve aggregate correctness. This confirms why the mismatch required correction
while also showing that it was not the source of the ten-item treatment deficit.

## Preregistered interpretation

The protocol specified three possible outcomes:

1. If the canonical control still beats treatment, close the optimizer thesis.
2. If the conditions are approximately neutral, still reject default activation.
3. If treatment becomes positive, require a fresh holdout before any positive claim.

The first outcome occurred. There is no authorization for another GSM8K model,
prompt search, treatment regeneration, bridge arm, backend arm, or post-result item
exclusion.

## Supported and unsupported claims

Supported:

- The integer-to-canonical-string transducer is deterministic and contract
  preserving within its explicitly supported schema subset.
- Model-facing schema representations are not semantically transparent.
- On this frozen Llama workload, native-integer generation reduced contract-valid
  correctness relative to an exact canonical-string control.
- The positive corrected Qwen estimate did not independently replicate on Llama.
- Paired, workload-scoped measurement is necessary before activating a schema
  representation rewrite.

Not supported:

- Native integers generally improve numeric-string output contracts.
- A static schema rule can predict the direction or size of a model-quality effect.
- The bounded BFCL-derived pilot proves general tool-calling harm.
- Contract preservation after generation implies behavior preservation during
  generation.

## Product direction

The primary product is a **contract-sensitivity evaluation harness**:

```text
External contract
        |
        v
Candidate model-facing representations
        |
        v
Frozen paired workload
        |
        v
Matched constrained generations
        |
        v
External validation and deterministic dispatch
        |
        v
Paired correctness, uncertainty, and complete audit
        |
        v
Workload-scoped recommendation or refusal
```

The linter remains a secondary component. It may flag a representation-sensitive
boundary and recommend measurement. It must not claim that converting a string to
an integer will improve accuracy.

The BFCL-derived pilot is described precisely as deterministic tool dispatch and
post-state scoring. It did not execute arbitrary business functions.

## Evidence integrity

- 150/150 new rows are present in frozen dataset order.
- The control used the same raw prompts as the historical Llama control.
- The chat template was applied exactly once.
- Model, tokenizer, package, GPU, dataset, and run settings match the frozen
  treatment environment.
- The treatment artifact hash is unchanged and `frozen_treatment_regenerated` is
  false.
- There were no new-arm errors, cap hits, internal-schema failures, or
  external-schema failures.
- Replaying scores from raw output found zero mismatches.
- The broader repository replay reconstructs all 464 earlier GSM8K and tool-call
  scores and paired summaries with zero mismatches.
- No items were excluded, repaired, retried for semantic reasons, or removed from
  the denominator.

## Final conclusion

The exact schema-equivalence correction strengthens the negative conclusion. The
native-integer representation is a safe transduction utility, but it is not an
evidence-supported default quality optimization. The project should not spend more
compute trying to rescue that claim on GSM8K.

The durable contribution is the infrastructure and evidence that reveal contract
sensitivity: one canonical schema source, fail-closed transforms, paired generation,
artifact replay, exact paired statistics, and full repair/regression audits.
