---
title: I Found a Runner Bug, Re-ran 200 Generations, and the Effect Survived
published: true
description: A corrected Qwen2.5-7B paired replication tests contract-preserving structured generation after fixing prompt templating, grammar policy, and measurement defects.
tags: ai, machinelearning, llm, opensource
cover_image: https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/corrected-replication-effect.png
---

I had a result I wanted to believe.

Changing the model-facing JSON answer from a signed numeric string to a native
integer, then deterministically converting it back to the caller's string contract,
appeared to recover 14.3 percentage points of constrained accuracy on Qwen2.5-7B.

Then an audit found a real problem in the experiment runner.

The historical Outlines path could receive a prompt after the Qwen chat template had
already been applied, while the Outlines Transformers adapter could apply that
template again. The accepted artifacts remained complete and provenance-valid, but
the control and treatment evidence could no longer support an architecture decision
without a corrected paired run.

So I froze a new protocol, corrected both sides of the comparison, ran 200 new cloud
generations, downloaded every row, and validated the bundle independently.

The effect survived in direction and practical size:

> Contract-valid correctness increased from 18/49 to 24/49, a paired gain of 12.2
> percentage points, while final external-schema validity remained 100%.

But the uncertainty matters. The exact bootstrap interval is `[0.0, 26.5]` points
and exact McNemar `p = 0.146`. This is evidence for a scoped next stage, not proof of
a general solution.

The complete code, protocol, raw rows, hashes, traces, validation report, and decision
are public in the repository.

{% github Vaibhav701161/constrained-decoding-lab %}

## The system boundary I am testing

Suppose an API requires this external object:

```json
{
  "reasoning": "...",
  "answer": "18000"
}
```

The answer must be a canonical signed-integer string. The model, however, may be
better aligned with a native JSON integer:

```json
{
  "reasoning": "...",
  "answer": 18000
}
```

The proposed compiler does not weaken the caller's contract. It creates a separate
model-facing contract, generates once under that grammar, applies an exact inverse
transformation, and validates the final object against the original schema.

```text
external schema
     |
     v
contract IR and applicability checks
     |
     v
model-facing schema plus replayable transform plan
     |
     v
one constrained generation
     |
     v
deterministic reverse transduction
     |
     v
original external-schema validation
```

For this experiment, the only semantic transform is:

```text
external canonical signed-integer string
    -> internal JSON integer
    -> arbitrary-precision base-10 stringification
    -> external validation
```

There is no second model call, sign repair, rounding, regex guessing, or fallback
coercion. A boolean is rejected even though Python treats it as an integer subtype.
Lexical values such as `"+26"`, `"00026"`, `"26.0"`, and `"2.6e1"` are not guessed
into the accepted language. Unsupported cases fail closed.

## What the audit found

The audit identified three separate defects or inconsistencies.

### 1. A double-chat-template risk

For string inputs, Outlines owns chat templating through its Transformers adapter.
The runner had passed an already formatted chat string into that layer. A Qwen prompt
could therefore be wrapped twice.

The corrected path passes the raw project prompt to Outlines. Direct Transformers
and XGrammar generation use the same shared formatting helper exactly once. Tests
compare effective token IDs and prove that the nested form is different.

### 2. Backend-dependent generated-token counts

Direct generation and XGrammar counted generated tensor IDs. Outlines counted the
visible text after decoding. A backend-only stop token could make those metrics
incomparable.

The corrected metric retokenizes visible generated content without special tokens
for every backend. This is a measurement fix, not a model behavior change.

### 3. Noncanonical whitespace policies

Permissive JSON whitespace loops add legal token paths and can create avoidable
stalls. The corrected runner pins compact separators in XGrammar and an empty
whitespace pattern in Outlines.

Real pinned-backend tests verify that compact valid JSON is accepted and a long
whitespace prefix is rejected.

These corrections changed the experimental system. Comparing a corrected treatment
to a historical control would mix runner versions, so I reran both representations.

## The protocol was frozen before the cloud run

The corrected question was narrow:

> Under greedy FP32 decoding on Qwen2.5-7B-Instruct, does a model-facing JSON integer
> improve contract-valid correctness over a signed numeric string when both sides use
> the same corrected source and the final object must satisfy the unchanged external
> contract?

The frozen design used:

| Component | Value |
|---|---|
| Model | Qwen2.5-7B-Instruct |
| Dataset | Deterministic GSM8K-50 test subset, seed 0 |
| Clean paired set | 49 items after one previously documented contradictory reference exclusion |
| Decoding | Greedy, seed 0, FP32, 256 maximum new tokens |
| Backends | Outlines 1.3.2 and XGrammar 0.2.3 |
| External contract | Reasoning string followed by signed numeric answer string |
| Treatment | Internal integer followed by deterministic stringification |
| Primary metric | Paired delta in contract-valid correctness |

The job first ran the same five deterministic items in all four conditions. Expansion
to 50 was allowed only if row identity, prompt equivalence, schema validity, run
signatures, nonblank output, and cap status passed. The canary reused the same result
files, so it did not create duplicate research rows.

The Green rule required at least five points of recovery, 100% final external
validity, paired wins exceeding losses, no systematic replacement failure, and
evidence consistent with a representation-boundary mechanism.

Importantly, semantic correctness was not part of the canary. Stopping or expanding
based on the first five answers would have biased the confirmation.

## The corrected result

The cloud job produced all 200 expected rows:

```text
2 backends x 2 representations x 50 items = 200 generations
```

The clean paired analysis retained 49 items under the audit policy.

![Corrected contract-valid accuracy with intervals and artifact integrity](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/corrected-replication-effect.png)

| Representation | Correct | Contract-valid accuracy | Final external validity | Negative answers |
|---|---:|---:|---:|---:|
| Signed numeric string | 18/49 | 36.7% | 49/49 | 2 |
| Internal integer plus transducer | 24/49 | 49.0% | 49/49 | 0 |

Paired effect:

```text
net improvement:                  6 items
accuracy delta:                  +12.2 percentage points
exact bootstrap 95% interval:    [0.0, 26.5] points
treatment-only repairs:           9
control-only regressions:         3
both correct:                    15
both wrong:                      22
exact two-sided McNemar p:        0.145996
```

![Full paired correctness transition matrix](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/corrected-replication-transitions.png)

The intervention repaired three times as many items as it broke. It also preserved
the external contract for every clean treatment output.

The point estimate clears the preregistered continuation threshold. It does not
clear a conventional `p < 0.05` threshold, and the interval touches zero. The honest
conclusion is not "the compiler works universally." It is "the corrected evidence is
strong enough to justify one bounded external-validity test."

## Every item remains inspectable

Aggregate accuracy can hide cherry-picked wins or a concentrated replacement
failure. The item map below shows both outcomes for every clean-analysis item in the
frozen dataset order.

![Item-level correctness for the signed-string control and integer treatment](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/master/assets/figures/corrected-replication-item-map.png)

The nine repaired items were:

```text
gsm8k_test_98
gsm8k_test_416
gsm8k_test_712
gsm8k_test_739
gsm8k_test_765
gsm8k_test_1205
gsm8k_test_1232
gsm8k_test_1251
gsm8k_test_1272
```

The three regressions were:

```text
gsm8k_test_506
gsm8k_test_601
gsm8k_test_996
```

The regressions remain in the primary denominator. They are not treated as outliers.

## The two backends became an implementation agreement check

Outlines and XGrammar emitted byte-identical raw output on all 50 signed-string items
and all 50 integer items.

That is strong evidence that both corrected integrations realized the same canonical
token path in this run. It also changes the statistical interpretation.

These are not two independent semantic replications. They are two implementations
agreeing on one effective 49-item paired experiment. Drawing separate effect bars and
calling the result replicated twice would overstate the evidence.

The observed semantic difference is associated with the model-facing representation,
not backend identity, under these matched settings.

## The mechanism is subtler than "integers forbid negatives"

Both negative signed-string outputs were repaired by the integer treatment:

```text
gsm8k_test_712:  -14 -> 14
gsm8k_test_1205:  -1 -> 4
```

But JSON integers allow negative values. The integer grammar did not prohibit the
minus token.

The XGrammar boundary traces show that the integer grammar removes quote and
structural-space continuations at the answer boundary while leaving minus legal. The
model therefore traverses a different legal token path. That path can affect the
first answer token and, because the answer follows reasoning, earlier generation as
well.

This is consistent with a representation-boundary mechanism. It is not proof that
every repair came from one local mask decision.

## A correct benchmark answer can still have unfaithful reasoning

One repaired item is an important counterexample.

For `gsm8k_test_712`, the integer output's reasoning still computes `-14`, but its
final answer is `14`. The benchmark score is correct. The generated explanation is
internally inconsistent.

So the evidence supports improved final-answer fidelity. It does not establish
improved reasoning faithfulness.

This distinction matters for any production system that exposes explanations,
executes intermediate values, or relies on chain-of-thought consistency.

## The artifact validator does not trust the remote summary

After the Kaggle run completed, a separate local validator checked:

- 200/200 expected rows;
- 50 unique items in every condition;
- source, runner, manifest, and result hashes;
- run signatures and frozen item order;
- prompt equivalence within each representation;
- byte equality across the two backends;
- generation errors, cap hits, and blank outputs;
- internal and external schema validity;
- the three preregistered boundary traces.

It reported zero failures and zero warnings. The run contained zero generation errors,
zero cap hits, zero blank outputs, and zero schema failures.

The summary was then regenerated locally. The paired bootstrap interval is computed
exactly from the empirical paired distribution by finite convolution, not estimated
from a random 10,000-resample loop.

## What exists beyond the experiment

The repository now contains a conservative compiler prototype rather than only a
one-off transducer:

- a canonical, hashable contract IR;
- explicit unsupported-construct records;
- deterministic, serializable alignment plans;
- backend capability and whitespace requirements;
- integer-string, key-alias, field-order, scratch-field, and whitespace transforms;
- exact reverse transduction;
- final validation against the original schema;
- typed fail-closed refusals;
- property and adversarial tests.

The implementation refuses references and schema features outside its initial
supported subset. That is intentional. A compiler that silently discards contract
semantics would be worse than no compiler.

The current test suite passes 87 tests, including 1,501 integer property cases and
real pinned-backend grammar probes. Those tests establish deterministic contract
behavior and integration. They do not substitute for external semantic evidence.

## What changed relative to the historical result

The historical mixed-runner paths reported:

```text
signed string:     61.2%
internal integer:  75.5%
delta:             +14.3 points
```

The corrected paired paths report:

```text
signed string:     36.7%
internal integer:  49.0%
delta:             +12.2 points
```

The absolute rates changed substantially. The direction and approximate treatment
effect survived. Historical and corrected rates must not be pooled because prompt
handling and canonical grammar behavior differ between runner versions.

This is why preserving old artifacts matters. A correction should create a new
evidence layer, not rewrite what happened.

## The decision: Green, but scoped

The corrected result satisfies the registered continuation rule:

1. The point recovery exceeds five percentage points.
2. Final external validity is 100%.
3. Paired wins exceed losses.
4. No systematic replacement failure was observed.
5. Boundary evidence remains consistent with the representation hypothesis.

The limitations are equally concrete:

- only 49 clean paired items;
- interval touching zero and `p = 0.146`;
- treatment accuracy only 49.0%;
- one model family and one benchmark;
- one correct answer with inconsistent reasoning;
- no independent semantic replication across backends.

The next authorized gate is not broad schema expansion. It is either:

1. the same paired contract test on a second model family; or
2. an executable tool-call task where contract-valid correctness has direct practical
   value.

If neither preserves a useful positive effect, the project should narrow into a
schema-risk linter and measurement system rather than continue claiming a general
compiler direction.

## Reproduce the evidence

The corrected evidence lives under:

```text
experiments/corrected-replication/
```

The main entry points are:

```bash
python scripts/validate_corrected_replication.py \
  --run-dir experiments/corrected-replication/results/qwen2.5-7b-corrected/results/corrected-replication \
  --dataset data/gsm8k_50_seed0.jsonl \
  --source-root deployment/kaggle/corrected-replication/source-snapshot \
  --kernel-source deployment/kaggle/corrected-replication/run_kaggle.py \
  --out /tmp/corrected-artifact-validation.json

python scripts/build_corrected_replication_figures.py

python -m pytest -q
```

Read the exact artifacts:

- [Frozen protocol](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/protocol.md)
- [Independent validation](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/artifact-validation.json)
- [Exact paired summary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/paired-summary-exact.md)
- [Decision report](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/decision-report.md)

I am treating the correction as part of the result, not as an embarrassing footnote.
The point of an evidence pipeline is not to protect a claim. It is to make the claim
survive contact with its own implementation.
