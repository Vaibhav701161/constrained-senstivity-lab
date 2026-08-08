---
title: Constraints Cost 18 Points. Compiling the Schema Recovered 14.
published: true
description: A 222-generation Qwen2.5-7B follow-up tests whether a model-aligned internal JSON representation can recover constrained-decoding accuracy without weakening the external contract.
tags: ai, machinelearning, llm, opensource
cover_image: https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/representation-alignment-recovery.png
---

> ## Update, 8 Aug 2026
>
> This Qwen result remains valid for its frozen setup, but it did not generalize.
> A fresh Llama replication was negative, and an external review later found that
> the first Llama string control accepted a broader numeric language than the safe
> compiler transform. I preregistered an exact canonical correction. The canonical
> string control still scored 92/150 versus 82/150 for the frozen integer treatment,
> with a paired interval of [-12.7, -0.7] points. The default optimizer thesis is
> closed. See the [complete correction decision](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/decision-report.md).

My previous experiment ended with an uncomfortable result.

On the same 49 audited GSM8K questions, Qwen2.5-7B-Instruct answered 39 correctly
when prompted to produce JSON. When I enforced the declared schema with Outlines or
XGrammar, each backend answered only 30 correctly.

The constraints fixed compliance and cost 18.4 percentage points of recoverable
mathematical accuracy.

That result raised a more useful question than "are constraints bad?"

> Was the model failing because it was constrained, or because the external contract
> forced it through a poorly aligned lexical representation?

I have now completed the follow-up: 72 targeted and 150 full-confirmation generations
on Qwen2.5-7B, plus local integration probes, boundary traces, paired statistics, and
independent artifact validation.

The short result is this:

> Replacing a model-facing signed numeric string with a native JSON integer, then
> deterministically restoring the original string contract, improved both constrained
> backends from 30/49 to 37/49 contract-valid correct.

That is a 14.3 percentage-point recovery while retaining 100% final external-schema
validity.

This article explains what changed, what stayed frozen, what the trace showed, and
why this is a Green light for a small contract-alignment compiler rather than proof of
a universal solution.

The first study is here:
[Structured Output Fixed My JSON and Cut Math Accuracy by 18 Points](https://dev.to/vaibhav_mittal_ac22a2c5d6/structured-output-fixed-my-json-and-cut-math-accuracy-by-18-points-jm5).

All new code, raw rows, manifests, hashes, traces, and reports are in the repository.

{% github Vaibhav701161/constrained-decoding-lab %}

## The failure was more specific than "constraints hurt reasoning"

The external schema required this:

```json
{
  "reasoning": "...",
  "answer": "18000"
}
```

The model naturally preferred this:

```json
{
  "reasoning": "...",
  "answer": 18000
}
```

The prompt-only output was valid JSON and often mathematically correct, but it did
not satisfy the contract because `answer` was a JSON number rather than a string.

Hard constraints solved that type mismatch. They also changed the generated answer.

In the frozen reasoning-first baseline:

| Condition | Semantic correctness | External-schema validity | Negative answers |
|---|---:|---:|---:|
| Prompt-only JSON | 39/49 (79.6%) | 0/49 | 1/49 |
| Outlines signed string | 30/49 (61.2%) | 49/49 | 12/49 |
| XGrammar signed string | 30/49 (61.2%) | 49/49 | 12/49 |

Both constrained backends had the same paired transition against prompting:

```text
correct in both:                  30
correct only with prompting:       9
correct only with constraints:     0
wrong in both:                    10
exact paired p:             0.003906
```

Eight of the nine losses were shared across Outlines and XGrammar. In seven shared
cases, the reasoning contained the correct positive magnitude and the final answer
field emitted its negative.

For example, the reasoning concluded `18000`, then the constrained answer became
`-18000`.

That pattern suggested a representation problem at the answer boundary, not a reason
to build another grammar engine.

## The hypothesis: compile the contract before generation

The caller's external contract remains authoritative. But the model does not
necessarily need to generate that exact wire representation directly.

The intervention was:

```text
External contract
{"reasoning": "...", "answer": "18000"}

        compile
           ↓

Internal model-facing contract
{"reasoning": "...", "answer": 18000}

        constrained generation
           ↓

Deterministic transducer
integer 18000 -> canonical string "18000"

        external validation
           ↓

Returned contract
{"reasoning": "...", "answer": "18000"}
```

![Engineering diagram of the implemented external contract, safe compiler, model-facing schema, constrained generation, and deterministic validation boundary](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/contract-alignment-pipeline.png)

This design has four important properties:

1. It uses one model call.
2. It does not relax the external schema.
3. It does not use an LLM to repair another LLM's output.
4. It fails closed on ambiguous or unsupported values.

The core transducer is deliberately boring:

```python
def canonical_integer_string(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("internal answer must be a JSON integer and not a boolean")
    return str(value)


def transduce_integer_object(internal_value):
    if set(internal_value) != {"reasoning", "answer"}:
        raise ValueError("internal object must contain exactly reasoning and answer")
    if not isinstance(internal_value["reasoning"], str):
        raise TypeError("internal reasoning must be a string")
    return {
        "reasoning": internal_value["reasoning"],
        "answer": canonical_integer_string(internal_value["answer"]),
    }
```

After conversion, the rebuilt object is validated against the original signed
numeric-string schema. If parsing, typing, transformation, or external validation
fails, no external object is returned.

This is not post-hoc answer correction. The sign and magnitude generated by the
model are preserved exactly.

## I wrote the decision rule before running the new matrix

The gate question was frozen before launching the 7B intervention:

> Does a native JSON integer as the hard-constrained, model-facing answer
> representation recover the semantic losses observed with a signed numeric string,
> while deterministic stringification restores validity under the original external
> contract?

The Green criteria were:

- At least five percentage points of recovery over the matching constrained
  signed-string baseline.
- A majority of the shared sign-loss cases repaired.
- 100% final external validity after transduction.
- No new systematic semantic failure.

The model, dataset, item order, chat template, greedy decoding, seed, FP32 precision,
256-token cap, and backend versions remained frozen.

Relative to the previous prompt, the integer prompt changed only the symbolic answer
representation:

```text
signed-string template: "answer": "<final numeric answer>"
integer template:       "answer": <integer>
```

A regression test compares the new prompt to the first accepted baseline row and
asserts that this replacement is the only change.

## Layered scoring prevented a misleading result

The experiment reports four separate outcomes:

1. **Semantic correctness**: does the extracted numeric value match the gold answer?
2. **Internal validity**: did the model satisfy the model-facing integer schema?
3. **External validity**: did deterministic transduction produce an object satisfying
   the unchanged caller schema?
4. **Contract-valid correctness**: is the answer both semantically correct and
   externally valid?

This separation matters. A system that emits perfect JSON with the wrong number is
not successful. A mathematically correct response with the wrong API type is not
immediately usable either.

The primary product metric was contract-valid correctness after transduction.

## First gate: an 18-item targeted suite

I mechanically derived the targeted suite from the frozen baseline artifacts. It
contained:

- The union of all constrained semantic losses.
- Matched controls where prompting, Outlines, and XGrammar were all correct.
- Shared difficult cases where all conditions were wrong.
- A recorded inclusion reason for every item.

The manifest recorded 9 Outlines losses, 9 XGrammar losses, 8 shared losses, and 10
unique losses across the two backends. The resulting suite had 18 items.

I ran four conditions:

1. Prompt-only integer.
2. Outlines integer.
3. XGrammar integer.
4. XGrammar unsigned numeric string, explicitly labeled diagnostic.

The unsigned-string condition was useful because every gold answer in this subset
was positive. But it was not contract-equivalent: the original external schema permits
negative integers, so an unsigned internal language cannot be the general solution.

### Targeted result

| Condition | Semantic correct | External valid |
|---|---:|---:|
| Prompted integer | 13/18 | 18/18 |
| Outlines integer | 13/18 | 18/18 |
| XGrammar integer | 13/18 | 18/18 |
| XGrammar unsigned-string diagnostic | 13/18 | 18/18 |

The aggregate tie hid useful paired information:

- Outlines integer repaired 7/8 shared signed-string losses.
- XGrammar integer repaired 8/8.
- Prompted integer, XGrammar integer, and XGrammar unsigned string had the same
  item-level correctness set.

The result cleared the preregistered threshold to advance. It did not count as final
confirmation because the suite was deliberately enriched for known failures.

## What the answer-boundary trace showed

I wrapped the XGrammar Hugging Face logits processor and captured compact diagnostics
near the answer boundary. The trace records top pre-mask and post-mask candidates,
selected tokens, known sign and digit scores, and the number of masked vocabulary
entries. It does not store a full-vocabulary tensor.

Three items were traced:

- `gsm8k_test_173`, a shared sign flip.
- `gsm8k_test_1216`, a backend-difference case.
- `gsm8k_test_12`, a matched control.

For `gsm8k_test_173`, the generated reasoning ended with the correct value `18000`.
At the integer answer boundary after whitespace:

```text
token "1" pre-mask score:  39.63
token "-" pre-mask score:  -1.33
selected token:             "1"
```

The integer grammar still permits legitimate negative values. The intervention did
not simply ban the minus sign. Instead, the changed representation exposed a token
path on which the digit was overwhelmingly preferred.

That is consistent with the hypothesis, but three traces are diagnostic evidence,
not a universal causal proof.

## Full confirmation: 150 new 7B generations

After the targeted gate passed, I ran the three integer conditions on the complete
frozen 50-item subset:

- 50 prompt-only integer generations.
- 50 Outlines integer generations.
- 50 XGrammar integer generations.

One contradictory GSM8K reference remained in every raw artifact and was excluded
only from the predeclared cleaned analysis. No other row was removed.

Independent validation accepted all 150 rows:

- 50 unique item IDs in every condition.
- Expected dataset, runner, schema, and source hashes.
- No generation errors.
- No token-cap hits.
- 100% final external validity.
- Complete trace coverage.

## The complete result

| Condition | Semantic correct | Contract-valid correct | External valid | Negative answers |
|---|---:|---:|---:|---:|
| Prompted signed-string baseline | 39/49 (79.6%) | 0/49 | 0/49 | 1/49 |
| Prompted integer + transducer | 37/49 (75.5%) | 37/49 | 49/49 | 0/49 |
| Outlines signed-string baseline | 30/49 (61.2%) | 30/49 | 49/49 | 12/49 |
| Outlines integer + transducer | 37/49 (75.5%) | 37/49 | 49/49 | 0/49 |
| XGrammar signed-string baseline | 30/49 (61.2%) | 30/49 | 49/49 | 12/49 |
| XGrammar integer + transducer | 37/49 (75.5%) | 37/49 | 49/49 | 0/49 |

![Data-derived diagram showing the 14.3-point recovery for Outlines and XGrammar, paired repairs and regressions, and removal of 12 negative answers per backend](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/representation-alignment-recovery.png)

The architecture figure is generated from the implemented path. The recovery figure
is generated directly from the accepted `paired-summary.json`; its counts and rates
are not manually typed into the image.

Both constrained backends gained 7 net correct answers, or 14.3 percentage points,
while preserving 100% external validity.

The original constrained gap was 18.4 points. The intervention recovered about 78%
of that gap.

The negative-answer cluster also disappeared in this matrix. Both constrained
backends moved from 12/49 negative answers to 0/49.

## Paired effects, including the new failures

Aggregate improvement is not enough. A treatment can repair some items and silently
break others.

### Outlines

```text
signed-string correct:                 30/49
integer + transducer correct:          37/49
difference:                      +14.3 points
paired 95% interval:          [+4.1, +26.5]
newly correct / newly wrong:            8 / 1
two-sided exact paired p:              0.0391
```

### XGrammar

```text
signed-string correct:                 30/49
integer + transducer correct:          37/49
difference:                      +14.3 points
paired 95% interval:           [0.0, +28.6]
newly correct / newly wrong:           10 / 3
two-sided exact paired p:              0.0923
```

Outlines clears the conventional 0.05 threshold. XGrammar has the same point
estimate, but more discordant items, a wider interval touching zero, and a p-value
above 0.05.

The project threshold was not defined as "obtain p < 0.05 on every backend." It was
defined as meaningful recovery, majority repair, perfect final validity, and no
systematic replacement failure. Both backends passed that rule, but the uncertainty
around XGrammar belongs in the conclusion.

## The incremental constraint cost disappeared under the integer representation

The cleanest comparison is not integer-constrained versus signed-string prompted.
Those conditions use different representations.

The matched comparison is integer-constrained versus integer-prompted.

All three integer conditions scored 37/49.

At the item level:

- Outlines versus prompted integer had 3 treatment-only and 3 control-only correct
  items, for zero net difference.
- XGrammar and prompted integer had the same correctness vector: 0 treatment-only
  and 0 control-only items.

So, in this experiment, I no longer observed an aggregate semantic tax from applying
the grammar after the representation was aligned.

That is the most important engineering result of the follow-up.

## What did not work perfectly

The intervention did not restore every answer.

Prompted signed-string generation had 39/49 recoverable semantic correctness, while
all integer conditions had 37/49. The prompted representation difference was -4.1
points with a paired interval from -12.2 to +4.1 and exact `p = 0.625`.

The aligned systems also retained ordinary reasoning errors:

- 12/49 items were still wrong.
- Outlines repaired 8 baseline errors and newly missed 1.
- XGrammar repaired 10 and newly missed 3.

Representation alignment fixes a representation-associated failure. It does not
turn a 7B model into a perfect arithmetic solver.

## An integration bug the local smoke test caught

The local Qwen2.5-0.5B smoke test exposed a separate XGrammar issue in my runner.

I initially reused one stateful Hugging Face logits processor across multiple
generations. The first item passed and later items failed with assertions. The fix was
to build a fresh processor for every generation.

The failed attempt is preserved as a diagnostic. The corrected five-item XGrammar
smoke passed 5/5 external validity, and the accepted cloud artifacts contain no such
errors.

This was a useful reminder: a structured-generation benchmark can be invalidated by
state management even when its schema and scoring logic are correct.

## What this result proves

Within the declared setup, the evidence supports these statements:

1. The model-facing answer representation was materially associated with the
   constrained semantic loss.
2. A native integer plus deterministic external transduction recovered 14.3 points
   for both tested backends.
3. The original external signed-string contract remained 100% valid.
4. The observed negative-answer cluster disappeared.
5. Under the integer representation, neither backend had an aggregate accuracy loss
   relative to matched integer prompting.

## What it does not prove

The evidence does not establish that:

- Native integers improve every model or schema.
- Every constrained-decoding failure is a representation problem.
- The mechanism generalizes beyond Qwen2.5-7B, GSM8K, greedy FP32 decoding, and the
  tested library versions.
- The result holds for legitimate negative gold answers. The transducer is tested on
  negatives, but this GSM8K subset contains positive targets.
- The 49-item confirmation is an independent replication. The intervention was
  frozen before the new runs, but the underlying evaluation set also produced the
  original failure observation.
- The complete contract compiler already exists.

The XGrammar confidence interval touching zero is another reason to keep the claim
narrow even though its point recovery matches Outlines.

## The project decision

The gate is Green.

The result justifies building a bounded compiler layer with a small, auditable set of
safe transformations:

1. Canonical integer-string representation.
2. Field-order restoration.
3. Key aliases with exact inverse mapping.
4. Canonical whitespace policies.
5. Final validation against the unchanged external contract.
6. Explicit refusal when a transformation is ambiguous or unsupported.

The compiler should sit above existing engines such as Outlines and XGrammar. The
goal is not to compete with their grammar execution. It is to choose a safer internal
language for the model, prove that the transformation back is sound, and preserve the
caller's contract.

Before making a general product claim, the next evidence gates are:

- Replication on an independent model family.
- An executable tool-call task.
- A fresh evaluation split.
- Property tests over the supported schema subset.
- Integration through a production inference path.

## Inspect or reproduce the evidence

The repository contains the protocol, failure catalogue, schema variants,
transducer, tests, raw JSONL rows, manifests, compact traces, validation reports, and
paired summary:

- [Complete repository](https://github.com/Vaibhav701161/constrained-decoding-lab)
- [Representation-alignment results](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/docs/representation-alignment-results.md)
- [Frozen gate protocol](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/representation-alignment-gate/protocol.md)
- [Full artifact validation](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/representation-alignment-gate/results/cloud-full/artifact-validation.json)
- [Machine-readable paired summary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/representation-alignment-gate/results/cloud-full/paired-summary.json)
- [Compact XGrammar trace](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/representation-alignment-gate/results/cloud-full/results/representation-alignment-full/traces/xgrammar-integer-answer-boundary.jsonl)

The practical lesson is simple:

> Do not assume the caller's wire format is the best language for the model.

Sometimes the safest way to preserve the external contract is to compile it into a
different internal representation, generate there, and transform back with code that
is deterministic enough to audit.

In this experiment, that small change recovered most of the lost accuracy without
weakening the guarantee.
