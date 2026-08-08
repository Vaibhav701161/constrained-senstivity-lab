---
title: Baseline analysis protocol
description: Frozen Qwen baseline protocol from 3 August 2026, preserved as historical evidence
search:
  exclude: true
---

# Baseline analysis protocol

!!! warning "Document status: frozen historical protocol"

    This page defines the original Qwen baseline only. Use the
    [current cross-study methodology](methods/index.md) for the methodology shared
    across the completed program.

Frozen on 3 Aug 2026 before the final prompt and backend matrix was observed.
The explicit five-item technical gate below was added on 3 Aug while Kaggle version
20 was still running and before any version 20 artifact was available.

Execution status (4 Aug 2026): **complete**. Version 22 fulfilled the four
reasoning-first primary cells and Version 23 fulfilled the two answer-order cells;
both passed artifact validation. This note remains the frozen protocol. Results and
post-run interpretation are recorded in [`research-report.md`](research-report.md) and
[`run-ledgers/qwen2.5-7b.md`](run-ledgers/qwen2.5-7b.md).

## Question

Can we reproduce a task-accuracy or quality difference between free generation,
prompt-only JSON generation, and grammar-constrained JSON generation under matched
model, items, prompt content, field order, precision, and decoding settings?

## Experimental units and scope

- Unit: one model-condition-GSM8K-item generation.
- Dataset: the deterministic `gsm8k_50_seed0.jsonl` subset.
- Models: Qwen2.5-0.5B-Instruct locally and Qwen2.5-7B-Instruct on Kaggle.
- Decoding: greedy. Seed replication is not treated as independent evidence because
  greedy outputs are deterministic in the validated setup.
- Precision: FP32 for the primary matrix. Earlier FP16/BF16 7B outputs are precision
  diagnostics and are excluded from task-accuracy conclusions because they showed
  token/digit corruption.
- Primary field order: reasoning first, then answer.
- Secondary order control: answer first, then reasoning.

## Prompt policy

- `day3-v6-strict-numeric-answer`, which contains the literal example answer `42`, is
  retained as a prompt-probe condition. It is not the final cross-model prompt because
  0.5B repeatedly copied `42` on unrelated questions.
- `day3-v7-no-answer-example`, which gives order in prose without a JSON template, is
  retained as the opposite prompt probe.
- The final primary prompt will be frozen as `day3-v8-symbolic-json-template`: it will
  show JSON syntax and symbolic angle-bracket placeholders but contain no concrete
  task answer. Both prompted and constrained conditions will receive identical prompt
  text. No further prompt selection will be based on observed task accuracy.

## Data-quality rule

- Raw official GSM8K accuracy is always reported.
- The primary data-cleaned analysis excludes only `gsm8k_test_454`. Its literal
  question implies 240, while its reference silently changes one person's daily
  amount and labels 150. This inconsistency was identified before the final matrix and
  is independently documented at
  <https://huggingface.co/datasets/openai/gsm8k/discussions/20>.
- The exclusion and rationale are machine-readable in
  `data/gsm8k_item_audit.json`.
- No item may be excluded because a model found it difficult or because exclusion
  changes an effect estimate.

## Planned conditions

1. `free`
2. `prompted_json_reasoning_first`
3. `outlines_json_reasoning_first`
4. `prompted_json_answer_first`
5. `outlines_json_answer_first`
6. XGrammar reasoning-first, only after a five-item technical smoke passes; otherwise
   its failure is reported as a backend-compatibility result rather than omitted.

### Five-item cross-backend gate

The v8 five-item gate is a deployment/compatibility check, not an accuracy-based
selection step. It passes only if:

- the manifest and rows match the frozen source/dataset hashes, v8 prompt versions,
  FP32 greedy settings, exact first five IDs, and planned condition names;
- every condition contains five unique paired rows with no generation exception;
- Outlines and XGrammar each achieve 5/5 whole-response JSON, strict numeric-answer,
  schema, and field-order compliance, with no token-cap hit or visible numerical token
  corruption.

Free and prompt-only cells may naturally be non-JSON or schema-noncompliant; their
accuracy and compliance do not decide the gate. No prompt/backend is promoted or
discarded because of its five-item task accuracy. A backend failing the technical gate
is debugged once if the cause is an evident integration error; otherwise the failure
is preserved and reported rather than silently excluded.

## Outcomes

### Primary task outcome

- Free: normalized exact correctness from the required final-answer marker.
- JSON conditions: strict normalized exact correctness, requiring the entire answer
  field to be a numeric string. Embedded-number recovery is not primary accuracy.

### Primary paired contrasts

1. Prompted JSON reasoning-first minus free: cost of requiring JSON through prompting.
2. Outlines reasoning-first minus prompted JSON reasoning-first: incremental effect of
   hard constrained decoding under the same JSON task and prompt.

### Secondary contrasts

- Answer-first minus reasoning-first within prompting.
- Answer-first minus reasoning-first within Outlines.
- XGrammar minus its matched prompted condition.
- Difference in the above effects between 0.5B and 7B.

### Engineering and mechanism outcomes

- Whole-response JSON validity, recoverability, strict numeric-answer compliance,
  schema validity, field order, token-cap rate, and generation-error rate.
- Per-example latency, generated tokens, latency per generated token, and wall time.
- Failure classes: arithmetic, quantity/language interpretation, incomplete reasoning,
  reasoning-to-answer mismatch, prompt-example copying, malformed structure,
  constraint/token-cap non-completion, precision corruption, and dataset defect.

## Statistics

- Report raw counts and percentage-point paired differences.
- Report treatment-only wins, control-only wins, both-correct, and both-wrong counts.
- Use the two-sided exact McNemar test over discordant pairs for paired accuracy.
- Report 95% uncertainty intervals for group accuracy and paired differences.
- Primary contrasts are interpreted as a family; multiplicity and small-sample
  uncertainty must be acknowledged.
- A non-significant result is described as “no detectable difference at this sample
  size,” never as proof of equality.

## Completion and interpretation gates

- A primary cell must contain all 50 planned rows, the expected unique IDs, verified
  prompt/schema version, and no unexplained file mismatch.
- Generation errors and cap hits remain in denominators.
- Diagnostic, stale-deployment, and corrupted-precision runs are never pooled with
  trustworthy cells.
- Every Kaggle version and every local prompt-probe matrix is preserved separately.
- The conclusion may be strong about this reproduction setup, but must not be
  generalized beyond the tested models, GSM8K subset, prompts, backends, and greedy
  decoding.
