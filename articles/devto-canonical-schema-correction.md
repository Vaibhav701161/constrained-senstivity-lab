---
title: I Fixed a Schema Mismatch. The Negative Result Survived.
published: true
description: A preregistered 150-generation correction tests exact schema equivalence after an external review found that my Llama control accepted a broader numeric-string language than the compiler.
tags: ai, machinelearning, llm, opensource
cover_image: https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/a5fecda6f7724fed377ace3d59233265b60523c3/assets/figures/canonical-schema-correction.png
---

An external reviewer found a real mismatch in my experiment.

I had tested whether an LLM should generate a numeric string directly or generate a
JSON integer that a deterministic transducer converts back to the caller's string
contract.

The Llama result was negative: the integer representation lost ten net correct
answers on 150 unseen GSM8K items.

But the two model-facing languages were not exactly equivalent.

My string control accepted integers, decimals, fractions, comma grouping, and
leading zeros. The compiler transform supported only canonical signed integers.

That meant I had tested a representation change plus a domain-narrowing change.

I did not explain the mismatch away. I preregistered one correction, generated one
new 150-row control arm, reused the frozen treatment, audited every disagreement,
and accepted the outcome.

The negative result survived.

> Exact canonical string control: 92/150 correct. Frozen integer treatment: 82/150.
> Paired effect: -6.7 percentage points, with interval [-12.7, -0.7].

This closes the default optimizer thesis for this project. More importantly, it
shows why model-facing schemas must be treated as semantic context, not transparent
serialization wrappers.

{% github Vaibhav701161/constrained-decoding-lab %}

## The mismatch

The original Llama control used this broad numeric-string grammar:

```regex
^-?(?:(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?|(?:\d+|\d{1,3}(?:,\d{3})+)/(?:\d+|\d{1,3}(?:,\d{3})+))$
```

It accepts values such as:

```text
"001"
"1.0"
"36/2"
"1,000"
"-5.5"
```

The safe compiler transform accepts only:

```regex
^-?(?:0|[1-9][0-9]*)$
```

It maps exactly between:

```text
external JSON string "-12"
        |
        v
internal JSON integer -12
        |
        v
deterministic base-10 stringification
        |
        v
external JSON string "-12"
```

No rounding, parsing heuristic, sign repair, or second model call is allowed.

Eight actual broad-control outputs were outside the canonical language: six on the
fresh set and two on the bridge set. Examples included `"13.33"`, `"55.5"`,
`"94.98"`, and `"36/2"`.

All eight were incorrect in both arms. So the mismatch did not directly explain the
ten-answer Llama deficit. It still blocked the strongest claim about the exact
compiler-supported transform.

That distinction matters. A result can be directionally meaningful and still need a
targeted correction before supporting its most specific interpretation.

## The only new run I allowed

I froze the correction before generation:

| Component | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Dataset | Same 150 previously unseen GSM8K test items |
| Backend | XGrammar 0.2.3 |
| Decoding | Greedy, seed 0, FP32 |
| Token budget | 256 maximum new tokens |
| Prompt | Byte-identical raw prompt |
| New arm | Exact canonical signed integer string |
| Treatment | Existing frozen integer artifact |
| Exclusions | None |

The frozen treatment SHA-256 was:

```text
298d1a38ad8d95d89ca97ab1f98d14bef4853342bf388d080f57f06de9c47342
```

The new run was not allowed to change the model, prompt, backend, package versions,
precision, decoding settings, holdout, or treatment. It was also not allowed to add
a bridge arm or Outlines arm.

This was a correction, not a search for a favorable result.

## Semantic-blind canary and resumability

The first five rows were evaluated only for operational integrity:

- same item IDs and order;
- byte-identical prompts;
- one chat-template application;
- frozen model and tokenizer revisions;
- matching package and GPU environment;
- no duplicate rows;
- no exceptions or cap hits;
- 100% internal and external validity.

The canary did not inspect correctness before expansion.

One operational interruption happened after row 23 when the local Modal client lost
its heartbeat. Every completed row had already been committed to the remote evidence
volume. I relaunched in detached resume mode, starting at row 24. No completed row
was regenerated.

The final new artifact contains 150 rows in the frozen dataset order, with zero
errors, zero cap hits, zero internal-schema failures, and zero external-schema
failures.

## Result

![Canonical schema-equivalence correction outcome, paired transitions, and complete discordance audit](https://raw.githubusercontent.com/Vaibhav701161/constrained-decoding-lab/a5fecda6f7724fed377ace3d59233265b60523c3/assets/figures/canonical-schema-correction.png)

| Outcome | Canonical string control | Frozen integer treatment |
|---|---:|---:|
| Contract-valid correct | 92/150, 61.3% | 82/150, 54.7% |
| Semantic correct | 92/150, 61.3% | 82/150, 54.7% |
| Final external valid | 150/150, 100.0% | 149/150, 99.3% |
| Internal schema valid | 150/150, 100.0% | 149/150, 99.3% |
| Errors | 0 | 0 |
| Token-cap hits | 0 | 1 |
| Mean generated tokens | 78.2 | 78.9 |

The paired transition matrix was:

| | Treatment correct | Treatment wrong |
|---|---:|---:|
| Control correct | 76 | 16 |
| Control wrong | 6 | 52 |

So the treatment had six unique wins and sixteen unique losses.

The treatment-minus-control estimate was **-6.7 percentage points**. The exact paired
bootstrap 95% interval was **[-12.7, -0.7] points**. The exact two-sided McNemar test
was `p = 0.05248`.

Those two uncertainty summaries answer related but different questions. I report
both rather than selecting the one with the cleaner threshold. The deterministic
paired bootstrap interval excludes zero. The exact McNemar result narrowly misses
0.05.

The preregistered decision did not depend on calling the result statistically
significant. It said that if the exact canonical control still beat the frozen
treatment, the optimizer thesis would close. The control beat it by ten net items.

The treatment's one cap hit remained in the denominator. That item was wrong in both
arms, so it did not create a discordant pair.

## What changed relative to the broad control

The canonical grammar did change model behavior:

- 134/150 raw outputs were byte-identical to the broad control;
- 140/150 normalized final answers were identical;
- 16 raw outputs changed;
- one item changed from wrong to correct;
- one item changed from correct to wrong;
- aggregate control correctness remained 92/150.

The six noncanonical fresh-set values disappeared, as required. But canonicalization
did not improve aggregate accuracy or remove the treatment deficit.

This is an important negative mechanism result. The broad language mismatch was
real, but it was not the cause of the overall direction.

## I inspected every discordant item

There were 22 discordant pairs after the correction. I inspected all of them against
the question, reference answer, raw control output, and raw treatment output.

| Category | Count |
|---|---:|
| Problem-interpretation change | 10 |
| Reasoning and final-answer inconsistency | 8 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Parser or validator issue | 0 |
| Truncation | 0 |

The dominant pattern was not an inability to emit a minus sign.

For example, in one control-only win both conditions produced the same correct
reasoning that Sam should receive 20 feet of fence. The integer treatment emitted
`40` anyway.

In another, both conditions derived two trays of eggnog. The treatment selected the
intermediate count of ten glasses as its final answer.

In a treatment-only win, the string control stopped after calculating 4,750
remaining graduation seats. The integer treatment completed the requested division
by 950 graduates and returned five tickets each.

These are trajectory-level changes. A one-field schema rewrite can alter which
steps are retained, which arithmetic is executed, and which number becomes final.

> Contract preservation after generation does not imply behavioral equivalence
> during generation.

## Engineering corrections beyond the run

The review also exposed engineering work worth fixing regardless of the result.

I made the following changes:

1. Defined the canonical signed-integer regex once and generated the experimental
   schema through the same compiler rewrite path.
2. Added one-command replay that reparses raw outputs, revalidates schemas,
   retransduces objects, recomputes task and execution scores, and reconstructs paired
   summaries.
3. Made integer-to-string rewrites fail closed when `enum`, `const`, bounds, or
   `multipleOf` would otherwise be dropped.
4. Replaced generic float coercion with exact integer and deliberate decimal
   comparison.
5. Added `pyproject.toml`, MIT licensing, dependency extras, and CI on Python 3.11
   and 3.12.
6. Split lightweight replay dependencies from GPU and backend dependencies.

In a clean lightweight environment, 129 tests passed and eight generation or backend
tests skipped explicitly. The replay command reconstructed 464 earlier GSM8K and
tool-dispatch rows with zero row-score mismatches and zero paired-summary mismatches.

The full pinned environment currently reports 143 passed and three Llama prompt
parity tests skipped locally because they require the frozen Modal image.

## The product decision

I started by asking whether caller contracts could be compiled into model-friendlier
internal representations that improve quality.

The corrected Qwen experiment produced a positive estimate:

```text
18/49 canonical contract-valid correct
        to
24/49 integer + transducer contract-valid correct
```

But the exact canonical Llama correction went the other way:

```text
92/150 canonical contract-valid correct
        to
82/150 integer + transducer contract-valid correct
```

A separate 30-item BFCL-derived deterministic tool-dispatch and post-state pilot also
found no evidence of practical benefit. That pilot did not execute arbitrary
business functions, and its interval was wide, so I do not claim general tool-calling
harm.

The project now has this primary loop:

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

The product is a **contract-sensitivity evaluation harness**.

The linter is secondary. It can say:

```text
This contract contains a representation-sensitive boundary.
Measure it before deployment.
```

It cannot say:

```text
Convert this string to an integer; accuracy will improve.
```

## Reproduce the evidence without a GPU

The default replay path is intentionally lightweight:

```bash
git clone https://github.com/Vaibhav701161/constrained-decoding-lab.git
cd constrained-decoding-lab
git checkout exp/canonical-schema-correction

uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -e ".[dev]"
source .venv/bin/activate

python -m pytest
python scripts/replay_artifacts.py \
  --scope all \
  --out /tmp/replay-validation.json
```

The complete correction record includes:

- [preregistered protocol](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/protocol.md);
- [operational canary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/canary-gate.json);
- [raw 150-row control artifact](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/results/xgrammar_json_canonical_integer_string_reasoning_first.jsonl);
- [artifact validation](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/artifact-validation.json);
- [paired summary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/paired-summary.md);
- [complete 22-item audit](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/failure-attribution.jsonl);
- [final decision report](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/exp/canonical-schema-correction/experiments/canonical-schema-equivalence-correction/decision-report.md).

## Final lesson

The compiler utility is still useful. It preserves the supported external contract,
fails closed, and makes representation alternatives executable.

What failed was the assumption that a model-friendlier representation would be a
portable quality optimization.

That is the result I am keeping.

If a schema rewrite changes the tokens available to a model, it can change the whole
generation trajectory. Measure it on the actual model and workload. Preserve every
regression. Refuse to search until the story becomes positive.

That is a stronger engineering system than an optimizer built from one encouraging
experiment.
