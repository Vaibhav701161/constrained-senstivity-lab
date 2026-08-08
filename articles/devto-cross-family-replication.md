---
title: The Optimization Worked on Qwen. It Failed on Llama and Tool Calls.
published: true
description: A preregistered cross-family replication and executable BFCL-based pilot overturn a promising structured-output optimization and define a more honest product direction.
tags: ai, machinelearning, llm, opensource
cover_image: https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/f99b9f6975cd0e600003bb46ab02b524bbf8beb8/assets/figures/cross-family-evidence.png
---

I had a promising compiler result.

On Qwen2.5-7B, changing one model-facing JSON field from a signed numeric string to a
native integer, then deterministically converting it back to the caller's unchanged
string contract, improved contract-valid GSM8K correctness from 18/49 to 24/49.

The paired estimate was +12.2 percentage points. The transform preserved 100%
external validity. The implementation had property tests, exact inverse
transduction, fail-closed validation, frozen artifacts, and two grammar backends that
produced byte-identical outputs.

It looked like the beginning of a contract compiler for LLMs.

Then I ran the test that mattered:

> Does the improvement survive on a different model family, unseen items, and an
> executable tool-call task?

It did not.

On 150 unseen GSM8K items with Llama 3.2 3B, the same treatment reduced correctness
from 92/150 to 82/150. On a separate 30-case executable primary sample built from
pinned BFCL V4 cases, it reduced exact executable-call success from 26/30 to 24/30.

The honest conclusion is not that the implementation failed. The transducer and
validator worked perfectly in the practical pilot.

The conclusion is more important:

> A contract-preserving representation change is still a semantic intervention on
> the model, and a local win is not a portable optimizer.

The code, protocols, raw generations, exact hashes, paired statistics, validators,
and complete discordance audits are public.

{% github Vaibhav701161/constrained-decoding-lab %}

## What was being optimized?

Suppose a caller requires this object:

```json
{
  "name": "adjust_inventory",
  "arguments": {
    "sku": "ABC-14",
    "quantity_delta": "-12"
  }
}
```

The externally required `quantity_delta` is a canonical signed integer string. Its
language is:

```regex
^-?(0|[1-9][0-9]*)$
```

The proposed internal contract lets the model emit a native JSON integer:

```json
{
  "name": "adjust_inventory",
  "arguments": {
    "sku": "ABC-14",
    "quantity_delta": -12
  }
}
```

The runtime then performs an exact inverse:

```text
external JSON Schema
        |
        v
contract IR and applicability analysis
        |
        v
internal JSON Schema
        |
        v
one constrained model generation
        |
        v
deterministic integer-to-string transduction
        |
        v
validation against the original external schema
        |
        v
caller-facing object
```

There is no second model call. There is no sign repair, rounding, regex extraction,
default insertion, key guessing, or fallback coercion. A generated boolean is
rejected even though Python treats booleans as integer subclasses. Unsupported
schemas fail closed.

This proves a useful engineering property: the internal object can be converted back
without changing the generated sign or magnitude.

It does not prove a model-quality property: that asking the model for an integer
will make it choose better values.

That second claim needed replication.

## The evidence before replication

The project started with a matched Qwen2.5-7B study of constrained JSON generation.
Prompt-only JSON achieved 79.6% recoverable GSM8K accuracy but 0% compliance with a
numeric-string answer schema. Outlines and XGrammar achieved 100% schema compliance
but only 61.2% recoverable accuracy.

That -18.4 point semantic difference showed that schema compliance and task
correctness were separate outcomes.

The native-integer transform was a narrow attempt to recover some of the lost
correctness without weakening the caller's contract. After finding and correcting a
double-chat-template risk in the historical runner, I reran both representations
from a frozen source.

The corrected Qwen result was:

| Representation | Contract-valid correct | External valid |
|---|---:|---:|
| Signed numeric string | 18/49 (36.7%) | 49/49 |
| Native integer plus transducer | 24/49 (49.0%) | 49/49 |

Paired statistics:

```text
difference:                 +12.2 percentage points
exact bootstrap interval:   [0.0, 26.5] points
treatment-only wins:         9
control-only wins:           3
exact McNemar p:             0.145996
```

This was valid, positive, and uncertain. The interval touched zero. It was enough to
authorize one independent replication, not enough to say the compiler worked in
general.

## I froze the Llama test before generation

The confirmatory question was:

> On a non-Qwen model and unseen GSM8K items, does replacing a model-facing signed
> numeric string with a native JSON integer improve final external-contract-valid
> correctness after deterministic stringification?

The fixed design used:

| Component | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Exact revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Primary backend | XGrammar 0.2.3 |
| Decoding | Greedy, seed 0, FP32, 256 maximum new tokens |
| Confirmatory set | 150 randomly selected, previously unseen GSM8K test items |
| Bridge set | Existing cleaned 49-item set |
| Primary outcome | Paired contract-valid correctness on the fresh 150 |
| Error policy | Every error, cap, invalid object, and transduction failure stays in the denominator |
| Post-launch exclusions | None |

The unseen-set preparation scanned existing JSONL artifacts under `results/`,
`experiments/`, and `deployment/`, removed every previously used source ID, shuffled
the remaining GSM8K test items with seed `20260815`, and selected 150. The manifest
records the excluded set, selected IDs, source, split, seed, and hashes.

Control and treatment used one shared generation runtime. Model loading, tokenizer
handling, chat templating, grammar compilation, output decoding, token counting,
latency measurement, error handling, manifests, and resumable writing were
identical. Only the model-facing schema, symbolic representation in the prompt, and
treatment inverse transduction differed.

The first five paired items were an operational canary. Expansion depended on IDs,
ordering, prompt-template depth, outputs, errors, caps, validity, revisions,
environment, signatures, and dataset hashes.

Semantic wins were explicitly forbidden from influencing expansion.

## The cross-family result was negative

The complete XGrammar matrix contained 398 generations:

```text
fresh set:   150 control + 150 treatment
bridge set:   49 control +  49 treatment
total:       398 generations
```

The fresh confirmatory result was:

| Metric | String control | Integer treatment |
|---|---:|---:|
| Contract-valid correct | 92/150 (61.3%) | 82/150 (54.7%) |
| Final external valid | 150/150 | 149/150 |
| Internal-schema valid | 150/150 | 149/150 |
| Generation errors | 0 | 0 |
| Token-cap hits | 0 | 1 |

Paired effect:

```text
difference:                 -6.7 percentage points
exact bootstrap interval:   [-12.7, -1.3] points
treatment-only wins:         5
control-only wins:          15
exact McNemar p:             0.041389
```

The single treatment cap hit stayed in the denominator. It was not retried or
repaired.

The bridge set also moved slightly negative:

```text
control:                    21/49
treatment:                  20/49
difference:                 -2.0 points
interval:                   [-10.2, 6.1] points
wins : losses:               2 : 3
```

The primary interval was entirely below zero. This was not a merely inconclusive
replication. Under the frozen gate it was Red: no cross-family replication.

![Paired effects across the corrected Qwen, unseen Llama, and executable gates](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/f99b9f6975cd0e600003bb46ab02b524bbf8beb8/assets/figures/cross-family-evidence.png)

## The failure audit changed the mechanism story

I manually inspected every discordant item, not a sample of them.

Across the fresh and bridge sets there were 25 discordances:

| Category | Count |
|---|---:|
| Problem-interpretation change | 12 |
| Reasoning-to-final inconsistency | 9 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Parser or validator issue | 0 |
| Truncation among discordants | 0 |

The representation change did not simply remove friction at a local quote or minus
boundary. It changed broader generation behavior. Some final answers stopped
matching the model's own reasoning. Other outputs interpreted the same word problem
differently.

That matters because a compiler analogy can become misleading. A conventional
compiler transform is expected to preserve program semantics. Here, changing the
schema shown to the model changes the probability distribution that produces the
semantics in the first place.

The inverse transducer can be exact while the generation intervention is not
semantics-preserving at the model level.

## I checked that XGrammar was not the culprit

After freezing the XGrammar result and discordant set, I ran Outlines only on:

- all 20 fresh discordant items; and
- 20 concordant items selected with a frozen seed.

Both representations used the same 40 IDs.

Results:

```text
signed-string outputs matching byte for byte: 40/40
integer outputs matching byte for byte:       40/40
all prompt and scoring fields matching:       80/80
same treatment cap hit reproduced:            yes
```

This is implementation-parity evidence, not a second statistical replication. It
shows that the negative result on the audited subset was not specific to XGrammar's
implementation.

## Red authorized one bounded practical pilot

A negative math replication did not automatically prove the idea useless for tool
calls. The protocol allowed exactly one bounded practical pilot.

The question became:

> Does contract alignment improve the probability that an LLM emits an externally
> valid call that actually executes with the correct arguments and state?

I used pinned BFCL V4 `simple_python` cases and official acceptable arguments as the
reference foundation. I did not claim an official BFCL leaderboard evaluation. The
external numeric-string contract was a project-defined adaptation, and deterministic
local wrappers replaced real business functions.

The wrappers had no external side effects. They checked:

- exact function selection;
- whole-object JSON validity;
- internal-schema validity;
- deterministic inverse transduction;
- reconstructed external-schema validity;
- exact typed argument semantics;
- dispatch and execution acceptance;
- correct post-execution state; and
- zero heuristic repairs.

## The executable dataset was selected mechanically

An eligible pinned BFCL case had to contain one turn, one function, an object-like
parameter schema, at least one required integer, a single unambiguous ground-truth
call, and only supported schema constructs.

The preparation code found 194 eligible cases out of 400.

The primary pilot selected 30 uniformly without replacement using seed `20260817`.
Because negative required integers were rare, all 3 eligible negative cases formed a
separate sign-stress set. They were never pooled into the primary effect.

The two representations produced 66 total generations:

```text
30 primary + 3 stress = 33 cases
33 control + 33 treatment = 66 generations
```

The three-case canary checked 20 operational invariants without looking at semantic
outcomes. The same files then resumed to the complete set.

## The practical pilot was also Red

Every one of the 66 calls was valid JSON, internally schema-valid, externally
schema-valid after treatment transduction, and accepted by the deterministic
dispatcher. There were zero generation errors, cap hits, transduction failures,
execution failures, or heuristic repairs.

That is excellent contract-boundary behavior.

It still did not improve exact calls.

![Executable pilot component outcomes and paired transition matrix](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/f99b9f6975cd0e600003bb46ab02b524bbf8beb8/assets/figures/tool-call-pilot-result.png)

| Primary metric | String control | Integer treatment |
|---|---:|---:|
| Executable-contract success | 26/30 (86.7%) | 24/30 (80.0%) |
| Internal-schema validity | 30/30 | 30/30 |
| External-schema validity | 30/30 | 30/30 |
| Exact argument semantics | 26/30 | 24/30 |
| Execution acceptance | 30/30 | 30/30 |
| Correct post-execution state | 26/30 | 24/30 |

Paired statistics:

```text
difference:                 -6.7 percentage points
exact bootstrap interval:   [-20.0, 6.7] points
treatment-only wins:         1
control-only wins:           3
exact McNemar p:             0.625
```

The sample is small and the interval crosses zero. I am not claiming statistically
proven harm in tool calling generally.

But the preregistered decision rule was directional. A zero or negative estimate, or
losses greater than or equal to wins, was sufficient for Red. Both occurred.

## Every practical discordance was inspected

There were five discordant calls across the primary and stress sets.

### Treatment correction: emissions

Both conditions emitted the correct integer duration, `3`. The control used the
wrong non-integer energy type, `solar`; the treatment used the accepted value,
`renewable`.

This was a real correction, but not an integer-boundary repair.

### Treatment regression: magnetic permeability

Both required integer fields remained correct. The treatment changed an optional
floating-point permeability from the pinned accepted value to a more precise physical
constant. It was plausible, structurally valid, and wrong under the frozen call
semantics.

### Treatment regression: cooking conversion

The user asked to convert `2` pounds to ounces. The control passed `quantity=2`. The
treatment passed `quantity=16`, apparently substituting the conversion result for the
function input.

### Treatment regression: restaurant threshold

The request required a minimum rating of more than 4, represented by the pinned
argument `4`. The treatment emitted `5`, strengthening and therefore changing the
requested threshold.

### Stress-set correction: quadratic roots

Both conditions preserved `a=3`, `b=-11`, and `c=-4` exactly. The treatment won only
because a separate string field changed from `root_type="real"` to
`root_type="all"`.

So even the sole sign-stress repair was not a sign repair.

The complete audit contained two semantic corrections and three semantic
regressions. No discordance came from validation, transduction, dispatch, truncation,
or parsing.

## Why I am stopping the optimizer thesis

The three decision gates now tell a coherent story:

```text
Qwen corrected GSM8K:       +12.2 points, positive and uncertain
Llama unseen GSM8K:          -6.7 points, interval below zero
Llama executable pilot:      -6.7 points, small and uncertain
```

It would be easy to rescue the narrative by pooling the positive three-case stress
set, changing prompts, trying more model families, or emphasizing perfect validity
while hiding incorrect arguments.

That would be research theater.

The external contract was preserved. The model's call meaning was not reliably
improved. The broad claim failed twice after the initial Qwen result.

The optimizing-compiler thesis is closed under the current evidence.

## What remains genuinely useful

The negative result does not make the infrastructure useless. It changes what the
product should be.

The repository already has:

- canonical contract IR and stable hashing;
- deterministic, serializable alignment plans;
- conservative transducers with exact inverses;
- final validation against the original schema;
- typed fail-closed refusals;
- unified matched runners;
- resumable artifact writing;
- source, dataset, environment, and run manifests;
- paired bootstrap intervals and exact McNemar tests;
- deterministic execution receipts; and
- complete item-level discordance audits.

Those components are the foundation for a different product:

### 1. Schema-risk linter

Identify contract features that may create fragile lexical or generation boundaries.
Do not automatically rewrite them. Explain the risk and the evidence scope.

### 2. Contract-sensitivity analyzer

Run frozen paired interventions on the user's actual workload. Report validity,
semantic wins, regressions, uncertainty, cap hits, latency, and failure mechanisms
separately.

### 3. Reproducible measurement harness

Preserve prompts, chat templates, model revisions, schemas, environments, raw
outputs, execution state, and exact artifact hashes so that a structured-output
change can be audited before deployment.

The integer-to-string transducer remains useful as a deterministic utility. It is
not a default quality optimization.

## What I learned

### Contract correctness and task correctness are orthogonal

The executable treatment reconstructed 100% valid external calls and executed 100%
of them. It still produced fewer exactly correct calls.

### Schema changes can perturb untouched fields

Three discordances changed fields whose types were identical across conditions. A
local schema edit can alter the entire autoregressive path.

### Backend agreement is not independent replication

Byte-identical XGrammar and Outlines outputs show implementation parity. They do not
turn one model result into two replications.

### An uncertainty interval does not replace a frozen decision rule

The small practical pilot cannot prove general harm. It can still fail a
preregistered continuation gate.

### Negative replication is product information

The most valuable result was not another positive chart. It was learning which claim
the system could no longer honestly make.

## Reproducibility status

```text
Llama primary XGrammar rows:       398/398 validated
Llama discordances audited:         25/25
Outlines parity outputs:            80/80 byte-identical
Executable pilot rows:              66/66 validated
Executable discordances audited:     5/5
Post-launch exclusions:               0
Semantic retries:                     0
Modal billed cost:                 $0.00
```

The canonical reports are:

- [Llama replication decision](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/llama32-second-family/experiments/second-family-replication/decision-report.md)
- [Llama paired summary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/llama32-second-family/experiments/second-family-replication/paired-summary.md)
- [Executable pilot decision](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/llama32-second-family/experiments/tool-call-gate/decision-report.md)
- [Complete practical discordance audit](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/llama32-second-family/experiments/tool-call-gate/failure-attribution.jsonl)
- [Current evidence and product status](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/llama32-second-family/docs/evidence-status.md)

I started this stage trying to validate an optimizing compiler.

I finished it with a more defensible system: one that can tell you when a contract
change is safe, when it is harmful, and when the evidence is too weak to decide.

That is less dramatic than claiming a universal optimization.

It is also much more useful.
