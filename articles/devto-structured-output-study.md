---
title: Structured Output Fixed My JSON and Cut Math Accuracy by 18 Points
published: true
description: A controlled 300-generation study of prompt-only JSON, Outlines, XGrammar, and field order on GSM8K with Qwen2.5-7B.
tags: ai, machinelearning, llm, opensource
cover_image: https://raw.githubusercontent.com/Vaibhav701161/constrained-senstivity-lab/master/assets/figures/accuracy-compliance-tradeoff.png
---

I expected constrained decoding to change formatting.

I did not expect it to change which math problems the model could solve.

In a controlled Qwen2.5-7B experiment, both Outlines and XGrammar raised JSON Schema compliance from 0% to 100%. At the same time, recoverable mathematical accuracy fell from 79.6% to 61.2%.

That is an 18.4 percentage-point drop on the same questions, with the same prompt text, model, precision, decoding settings, and scoring code.

The paired result was even harder to dismiss:

- 30 questions were correct with both prompt-only and constrained generation.
- 9 were correct with prompting but wrong with constrained generation.
- 0 were rescued by constrained generation.
- 10 were wrong in both conditions.
- Two-sided exact McNemar `p = 0.003906`.

This article explains how I reached that result, why "valid JSON" turned out to be an inadequate metric, and why moving one JSON field changed accuracy more than switching constraint backends.

All source code, raw outputs, validation reports, and accepted cloud runs are public.

{% github Vaibhav701161/constrained-senstivity-lab %}

## The engineering problem

Production applications rarely want an essay from an LLM. They want something a program can consume:

```json
{
  "reasoning": "...",
  "answer": "42"
}
```

Prompting a model to return JSON is not a guarantee. It may add prose, omit a field, use the wrong type, or stop halfway through an object.

Constrained decoding addresses this at generation time. A grammar engine masks tokens that would make the output invalid, leaving the model only allowed continuations. Libraries such as [Outlines](https://github.com/dottxt-ai/outlines) and [XGrammar](https://xgrammar.mlc.ai/) make this practical.

The obvious expectation is:

> Constrained decoding changes the syntax, not the answer.

But token masking changes the model's available next-token distribution. If reasoning and serialization happen in the same sequence, syntax and semantics may not remain independent.

That led to the question I wanted to test:

> Can a decoder guarantee the output contract without changing the model's recoverable mathematical accuracy?

## What I measured

I used a deterministic 50-question sample from the GSM8K test split and evaluated Qwen2.5-7B-Instruct under six conditions:

1. Free response.
2. Prompt-only JSON, reasoning first.
3. Outlines JSON, reasoning first.
4. XGrammar JSON, reasoning first.
5. Prompt-only JSON, answer first.
6. Outlines JSON, answer first.

The final matrix contains 300 validated generations.

One sampled GSM8K row had a contradictory reference answer. The question implies `240`, while its stored reference is `150`. I retained that row in the raw results, documented it in a machine-readable audit, and excluded it from the predeclared clean analysis. No other row was excluded.

The primary analysis therefore contains 49 paired questions per condition.

### Controls held constant

| Component | Setting |
|---|---|
| Model | Qwen2.5-7B-Instruct |
| Data | Deterministic GSM8K test subset, seed 0 |
| Dataset SHA-256 | `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a` |
| Prompt formatting | `tokenizer.apply_chat_template(..., add_generation_prompt=True)` |
| Decoding | Greedy |
| Random seed | 0 |
| Maximum output | 256 tokens |
| Precision | FP32 |
| Constraint libraries | Outlines 1.3.2 and XGrammar 0.2.3 |
| Primary sample | 49 audited paired items per condition |

For a matched comparison, the dataset item, prompt text, chat template, model, precision, decoding configuration, and scoring logic were held fixed. Only the treatment being tested changed.

## Valid JSON is not the same as a valid contract

This distinction became central to the study.

I reported two correctness metrics:

**Recoverable accuracy** asks whether the intended numeric answer can be extracted from the response, even if the response violates the schema.

**Strict accuracy** requires the correct value to appear inside a schema-compliant `answer` field. This measures output that an application can use immediately without repair.

Consider this output:

```json
{
  "reasoning": "40 + 2 = 42",
  "answer": 42
}
```

It is valid JSON. It is also mathematically correct. But it violates a schema requiring `answer` to be a numeric string:

```json
{
  "reasoning": "40 + 2 = 42",
  "answer": "42"
}
```

The prompt-only reasoning-first condition exposed this exact failure mode:

- 100% valid JSON.
- 79.6% recoverable mathematical accuracy.
- 0% schema compliance.
- 0% strict accuracy.

The model consistently emitted an unquoted JSON number instead of the required string.

If I had measured only JSON parse success, I would have called this condition perfect. If I had measured only strict accuracy, I would have called every answer wrong. Both conclusions would have hidden important information.

## The complete result

![Grouped horizontal bar chart comparing recoverable accuracy, strict accuracy, and schema compliance across six Qwen2.5-7B conditions](https://raw.githubusercontent.com/Vaibhav701161/constrained-senstivity-lab/master/assets/figures/accuracy-compliance-tradeoff.png)

| Condition | Recoverable accuracy | Strict accuracy | Schema compliance |
|---|---:|---:|---:|
| Free response | 36/49 (73.5%) | n/a | n/a |
| Prompted JSON, reasoning first | 39/49 (79.6%) | 0/49 (0.0%) | 0.0% |
| Outlines, reasoning first | 30/49 (61.2%) | 30/49 (61.2%) | 100% |
| XGrammar, reasoning first | 30/49 (61.2%) | 30/49 (61.2%) | 100% |
| Prompted JSON, answer first | 11/49 (22.4%) | 8/49 (16.3%) | 65.3% |
| Outlines, answer first | 8/49 (16.3%) | 8/49 (16.3%) | 100% |

Constrained decoding clearly solved the output-contract problem. Every Outlines and XGrammar reasoning-first response satisfied the schema.

But the recoverable view tells a second story. Relative to matched prompt-only JSON, Outlines and XGrammar each lost 18.4 percentage points of mathematical accuracy.

![Forest plot of paired recoverable-accuracy effects with bootstrap confidence intervals](https://raw.githubusercontent.com/Vaibhav701161/constrained-senstivity-lab/master/assets/figures/paired-effects.png)

For each constraint backend:

```text
accuracy difference: -18.4 percentage points
paired bootstrap 95% CI: [-30.6, -8.2]
two-sided exact McNemar p: 0.003906
```

Under the frozen strict metric, the interpretation reverses. Prompt-only JSON scored 0%, while both constrained backends scored 61.2%.

So these statements are simultaneously true:

1. Constraints greatly improved immediately usable correctness.
2. Constraints reduced recoverable mathematical correctness.

Schema compliance and semantic accuracy are separate outcomes. A structured-output evaluation should report both.

## Aggregate accuracy was not enough

Because every condition used the same 49 questions, I could inspect correctness transitions item by item.

![Three paired correctness contingency tables comparing prompt-only JSON, Outlines, and XGrammar](https://raw.githubusercontent.com/Vaibhav701161/constrained-senstivity-lab/master/assets/figures/paired-transitions.png)

Against prompt-only reasoning-first generation, both constraint backends produced the same contingency table:

| Paired outcome | Items |
|---|---:|
| Correct in both | 30 |
| Correct only with prompting | 9 |
| Correct only with the constraint | 0 |
| Wrong in both | 10 |

This is more informative than comparing `79.6%` and `61.2%` as independent proportions. The effect came from nine one-directional losses, not a balanced exchange of wins and losses.

Outlines and XGrammar also tied at 30/49, but they were not behaviorally identical:

- 29 items were correct under both.
- One was correct only under Outlines.
- One was correct only under XGrammar.
- 18 were wrong under both.
- Only 20/49 raw responses were byte-identical.

An aggregate tie can conceal different generation paths.

## Field order mattered more than backend choice

I initially treated JSON field order as a serialization detail. It was not.

The reasoning-first schema required:

```json
{
  "reasoning": "...",
  "answer": "..."
}
```

The answer-first schema required:

```json
{
  "answer": "...",
  "reasoning": "..."
}
```

Within each paired comparison, only that order changed.

![Two-panel line plot showing accuracy and schema compliance under reasoning-first and answer-first field order](https://raw.githubusercontent.com/Vaibhav701161/constrained-senstivity-lab/master/assets/figures/field-order-sensitivity.png)

For prompt-only JSON:

```text
reasoning first: 79.6% recoverable accuracy
answer first:    22.4% recoverable accuracy
paired change:  -57.1 percentage points
95% CI:         [-71.4, -40.8]
exact p:         5.77e-8
```

For Outlines:

```text
reasoning first: 61.2% recoverable accuracy
answer first:    16.3% recoverable accuracy
paired change:  -44.9 percentage points
95% CI:         [-59.2, -30.6]
exact p:         2.98e-6
```

Outlines maintained 100% schema compliance in both orders. Its 44.9-point decline therefore cannot be explained by an improvement in formatting.

In this setup, asking the model to commit to the answer before generating its reasoning changed task performance far more than switching between Outlines and XGrammar.

## Trusting the GPU output required its own investigation

The final results ran on two Tesla T4 GPUs, but the first successful-looking runs were not necessarily trustworthy.

During the environment and precision diagnostics:

- Some 4-bit and FP16 paths produced visibly corrupted tokens.
- BF16 restored much of the structure but damaged digits in answers.
- FP32 produced the first outputs accepted as task evidence.

These observations are specific to the tested Kaggle software and T4 hardware path. They do not establish that FP16 or BF16 universally fail for Qwen.

They do establish a broader engineering rule:

> A completed GPU job is not automatically a valid experiment.

Before accepting a run, the validation pipeline checked:

- Source-file hashes.
- Dataset hash and exact item order.
- Model artifact and environment.
- Prompt and schema version.
- Precision and decoding settings.
- Expected row counts.
- Duplicate item IDs.
- Generation errors.
- Token-cap hits.

Failed, corrupted, stale-deployment, and diagnostic runs remain in the repository instead of disappearing from the history.

## What this result does not prove

This is not evidence that constrained decoding always harms reasoning.

The accepted evidence covers:

- One deterministic GSM8K subset.
- One final prompt family.
- Two sizes from one model family.
- Greedy decoding.
- One primary precision.
- Two grammar backends.
- A sample of 49 audited paired questions.

The smaller Qwen2.5-0.5B experiment did not detect the same semantic constraint cost at its low base accuracy. That alone warns against turning the 7B observation into a universal rule.

The result also sits within existing research. [JSONSchemaBench](https://arxiv.org/abs/2501.10868) argues that structured generation should be evaluated across compliance, coverage, efficiency, and output quality. The [XGrammar paper](https://arxiv.org/abs/2411.15100) focuses on efficient grammar execution. [CRANE](https://arxiv.org/abs/2502.09061) explicitly studies how restrictive grammars can diminish reasoning and proposes reasoning-augmented constrained generation.

My contribution here is narrower: a reproducible engineering audit with matched prompt text, paired GSM8K scoring, two independent backends, field-order controls, strict versus recoverable metrics, and preserved failure evidence.

## The next experiment I would run

The most useful follow-up is not another copy of the same matrix. It is a mechanism test.

I would separate reasoning from serialization:

```text
problem
  -> unconstrained reasoning and answer
  -> constrained final JSON serialization
  -> schema-valid application output
```

That creates three pipelines to compare:

1. Prompt-only, single-stage generation.
2. Grammar-constrained, single-stage generation.
3. Unconstrained reasoning followed by constrained serialization.

If the two-stage approach preserves prompt-only accuracy while achieving 100% compliance, it would provide a practical way to keep the contract guarantee without applying a grammar across the reasoning trajectory.

After that, I would replicate on another model family, increase the preregistered sample, and add both a harder reasoning benchmark and a schema-centric benchmark.

## Reproduce or inspect the evidence

The repository contains the deterministic dataset, runners, raw JSONL outputs, summaries, item-level reports, figures, environment records, and validation manifests:

- [Complete GitHub repository](https://github.com/Vaibhav701161/constrained-senstivity-lab)
- [Research report](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/docs/research-report.md)
- [Methodology](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/docs/methodology.md)
- [Per-item 7B evidence](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/results/qwen2.5-7b/primary/combined/items.md)
- [Reasoning-first Kaggle run](https://www.kaggle.com/code/vaibhav7011/constrained-decoding-qwen7b-evaluation?scriptVersionId=339899508)
- [Answer-first Kaggle run](https://www.kaggle.com/code/vaibhav7011/constrained-decoding-qwen7b-evaluation?scriptVersionId=339962138)
- [Frozen Kaggle source dataset](https://www.kaggle.com/datasets/vaibhav7011/constrained-decoding-day3-source)

The core lesson is simple:

> Do not evaluate structured generation with one number.

Measure whether the output parses. Measure whether it satisfies the schema. Measure whether the answer remains correct. Then compare the same items, not just aggregate percentages.

Constrained decoding can solve the contract problem. That does not make its semantic effect zero.
