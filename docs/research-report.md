# Constrained Decoding Under Matched Conditions

Status: **Primary evaluation matrix complete; all accepted artifacts validated**
Experiment dates: 2 to 4 Aug 2026

## Executive result

This study produced a qualified but concrete reproduction result. Hard JSON constraints
reliably fixed structure at both model sizes, but their semantic effect depended on
model scale. Qwen2.5-0.5B showed no detectable constrained-decoding accuracy cost over
the matched prompt-only JSON condition. On the separate recoverable-math outcome,
Qwen2.5-7B showed a statistically detectable **18.4 percentage-point loss** under
either Outlines or XGrammar, even though both backends raised strict schema compliance
from 0% to 100%.

The distinction between semantic and deployable success is essential:

- *Recoverable accuracy* asks whether the intended numeric value can be extracted,
  even when the response violates the declared schema.
- *Strict accuracy* requires both the correct numeric value and a schema-compliant
  whole-field numeric string.

For 7B reasoning-first JSON, prompt-only generation had the best recoverable accuracy
(39/49), but wrote every answer as an unquoted JSON number and therefore had zero
strict successes. Constrained decoding returned fewer correct values (30/49) but made
all 30 immediately usable under the declared contract.

### Qwen2.5-7B final v8 matrix

After the predeclared exclusion of one contradictory GSM8K row (49 paired items):

| Condition | Recoverable math accuracy | Strict accuracy | Schema compliance |
|---|---:|---:|---:|
| Free | 36/49 = 73.5% | n/a | n/a |
| Prompted JSON, reasoning-first | 39/49 = 79.6% | 0/49 = 0.0% | 0.0% |
| Outlines, reasoning-first | 30/49 = 61.2% | 30/49 = 61.2% | 100% |
| XGrammar, reasoning-first | 30/49 = 61.2% | 30/49 = 61.2% | 100% |
| Prompted JSON, answer-first | 11/49 = 22.4% | 8/49 = 16.3% | 65.3% |
| Outlines, answer-first | 8/49 = 16.3% | 8/49 = 16.3% | 100% |

The frozen **primary** outcome was strict correctness. On that outcome, prompt-only
reasoning-first JSON was 73.5 points below free response because every answer violated
the string schema (exact p=2.91e−11). Outlines and XGrammar were each 61.2 strict
points above their matched prompt-only condition (exact p=1.86e−9). Those are real
operational results, but they combine semantic correctness with format compliance.

The separate recoverable-math view isolates whether the intended value was present
despite a schema violation. Key paired findings across both views were:

| Contrast | Outcome | Paired delta | 95% interval | Exact p | Discordant wins |
|---|---|---:|---:|---:|---:|
| Prompted RF − Free | recoverable | +6.1 pp | −6.1 to +18.4 pp | 0.508 | 6 vs 3 |
| Prompted RF − Free | strict | **−73.5 pp** | −85.7 to −61.2 pp | 2.9e−11 | 0 vs 36 |
| Outlines RF − Prompted RF | recoverable | **−18.4 pp** | −30.6 to −8.2 pp | 0.0039 | 0 vs 9 |
| Outlines RF − Prompted RF | strict | **+61.2 pp** | +46.9 to +75.5 pp | 1.9e−9 | 30 vs 0 |
| XGrammar RF − Prompted RF | recoverable | **−18.4 pp** | −30.6 to −8.2 pp | 0.0039 | 0 vs 9 |
| XGrammar RF − Prompted RF | strict | **+61.2 pp** | +46.9 to +75.5 pp | 1.9e−9 | 30 vs 0 |
| Prompted AF − Prompted RF | recoverable | **−57.1 pp** | −71.4 to −40.8 pp | 5.8e−8 | 1 vs 29 |
| Outlines AF − Outlines RF | strict | **−44.9 pp** | −59.2 to −30.6 pp | 3.0e−6 | 1 vs 23 |

Outlines and XGrammar tied in aggregate reasoning-first accuracy. Their outputs were
not identical: each backend had one unique correct item, 29 items were correct under
both, and 18 were wrong under both (exact paired p=1.0).

### Qwen2.5-0.5B final v8 matrix

After excluding one predeclared contradictory GSM8K item (49 paired items):

| Condition | Primary accuracy | 95% CI | Strict JSON/schema compliance |
|---|---:|---:|---:|
| Free | 14/49 = 28.6% | 17.8%–42.4% | n/a |
| Prompted JSON, reasoning-first | 3/49 = 6.1% | 2.1%–16.5% | 42.9% |
| Outlines, reasoning-first | 5/49 = 10.2% | 4.4%–21.8% | 100% |
| XGrammar, reasoning-first | 4/49 = 8.2% | 3.2%–19.2% | 100% |
| Prompted JSON, answer-first | 2/49 = 4.1% | 1.1%–13.7% | 79.6% |
| Outlines, answer-first | 3/49 = 6.1% | 2.1%–16.5% | 98.0% |

Primary paired effects:

| Contrast | Strict delta | Paired 95% interval | Discordant wins | Exact p |
|---|---:|---:|---:|---:|
| Prompted JSON RF − Free | **−22.4 pp** | −36.7 to −8.2 pp | 2 vs 13 | 0.0074 |
| Outlines RF − Prompted JSON RF | +4.1 pp | −4.1 to +12.2 pp | 3 vs 1 | 0.625 |
| XGrammar RF − Prompted JSON RF | +2.0 pp | 0.0 to +6.1 pp | 1 vs 0 | 1.000 |

Interpretation: structured output tasking strongly harms this small model relative to
free response. Grammar constraints repair structure. With this sample and low base
accuracy, neither constrained backend has a detectable semantic cost or benefit over
matched prompting. The completed 7B result shows that this small-model null does not
generalize even within the Qwen2.5 family.

## Research question and protocol

The research question is whether an accuracy or quality difference between unconstrained,
prompted JSON, and constrained decoding can be reproduced under matched conditions.
The protocol, outcomes, exclusions, contrasts, and interpretation gates were frozen
before the final prompt matrix was observed in
[`methodology.md`](methodology.md).

Key controls:

- identical item IDs across conditions;
- greedy decoding rather than pseudo-replicated seeds;
- identical prompt text for prompt-only and constrained comparisons;
- FP32 primary inference after lower precision was shown to corrupt 7B tokens/digits;
- strict whole-field numeric accuracy for JSON cells;
- errors and cap hits retained in denominators;
- exact paired tests, paired bootstrap intervals, and Wilson group intervals;
- raw official scores reported alongside the predeclared data-cleaned analysis.

## Data

- Source: `openai/gsm8k`, test split.
- Subset: 50 deterministic items selected with seed 0.
- Dataset SHA-256:
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- Every row records source index, question, reference solution, gold answer, prompt,
  formatted chat-template prompt, raw output, parsing/validation fields, latency,
  token counts, model configuration, and run signature.

### Audited dataset defect

`gsm8k_test_454` says Marin and Nancy *each* eat four apples daily, implying 240 in
30 days, while the reference silently computes `4 + 1` and labels 150. The same defect
is independently documented in the
[GSM8K dataset discussion](https://huggingface.co/datasets/openai/gsm8k/discussions/20).

Policy:

- retain it in raw official scores;
- exclude it from the primary data-cleaned analysis;
- exclude no other item;
- preserve the machine-readable rationale in `data/gsm8k_item_audit.json`.

## Models and environments

### Qwen2.5-0.5B-Instruct

- Local RTX 4050 Laptop GPU, 6 GB.
- PyTorch 2.6.0+cu124, CUDA 12.4.
- FP32, greedy, seed 0, maximum 256 generated tokens.

### Qwen2.5-7B-Instruct

- Kaggle model artifact `qwen-lm/qwen2.5/transformers/7b-instruct/1`.
- Public execution records: [reasoning-first version 22](https://www.kaggle.com/code/vaibhav7011/constrained-decoding-qwen7b-evaluation?scriptVersionId=339899508) and [answer-first version 23](https://www.kaggle.com/code/vaibhav7011/constrained-decoding-qwen7b-evaluation?scriptVersionId=339962138).
- Public frozen source: [Constrained Decoding Evaluation Source](https://www.kaggle.com/datasets/vaibhav7011/constrained-decoding-day3-source).
- Two Tesla T4 GPUs, automatic device placement.
- Python 3.12.13, PyTorch 2.6.0+cu124, CUDA 12.4, Transformers 4.51.3,
  Accelerate 1.6.0, Datasets 3.6.0, Jsonschema 4.23.0, Outlines 1.3.2.
- FP32 for trustworthy task results.

## Prompt and schema controls

### Final primary prompt: v8 symbolic JSON template

`day3-v8-symbolic-json-template` shows exact JSON syntax and field order using symbolic
angle-bracket placeholders. It contains no example answer. Prompt-only, Outlines, and
XGrammar receive the same prompt text.

The answer schema requires the entire string to match a signed integer, decimal, or
fraction pattern. Strict scoring rejects answer strings with units, currency symbols,
prose, or embedded numbers.

### Why earlier prompt versions remain in the report

- v6 used a valid example containing `"answer": "42"`. Qwen-0.5B copied 42 on many
  unrelated rows. It is retained as example-copying evidence, not selected as primary.
- v7 removed both the answer example and JSON syntax. Prompted reasoning-first then
  achieved essentially zero JSON validity, creating an artificial +16.3-point
  Outlines advantage. It is retained as a prompt-scaffolding diagnostic.
- v8 was selected by a methodological rule: valid syntax without a task answer, not by
  observed accuracy.

## Qwen2.5-0.5B primary results

### Task accuracy and paired effects

The table in the executive result is the predeclared cleaned analysis. Raw official
and cleaned summaries are preserved separately. The principal results are:

1. Requiring JSON through prompting reduces strict accuracy by 22.4 points versus
   free response (exact p=0.0074).
2. Outlines is 4.1 points above the matched prompt, but the interval includes harm and
   benefit and the exact p-value is 0.625.
3. XGrammar is 2.0 points above the matched prompt, based on one discordant strict win;
   exact p=1.000.
4. Answer-first is descriptively worse than reasoning-first, but neither order effect
   is detectable at this sample size.

### Structure and completion

- Prompted RF: 42.9% strict numeric/schema compliance and 81.6% whole JSON.
- Outlines RF: 100% strict numeric/schema/whole JSON, zero caps.
- XGrammar RF: 100% strict numeric/schema/whole JSON, zero caps.
- Prompted AF: 79.6% strict compliance, 87.8% whole JSON, one cap.
- Outlines AF: 98.0% strict compliance, 98.0% whole JSON, one cap.
- Free: 46.9% cap rate and only 12.2% ended with the requested final-answer marker.

Constrained decoding guarantees allowed continuations but not semantic correctness.
One Outlines probe spent the entire budget looping inside a reasoning string and never
reached the required answer field. Constraints therefore do not guarantee completion
under a finite token cap.

### Backend latency

Cleaned mean end-to-end generation latency:

- Prompted RF: 3,062.2 ms.
- Outlines RF: 2,938.3 ms.
- XGrammar RF: 2,634.2 ms.

Generated lengths differ, so these values are descriptive end-to-end latency, not a
pure grammar-processing benchmark. XGrammar 0.2.3 was used because current 0.2.4 had no
compatible Linux x86-64/Python 3.12 wheel. Integration followed the
[official XGrammar Transformers workflow](https://xgrammar.mlc.ai/docs/start/quick_start.html).

### Evidence

- Aggregate: `results/qwen2.5-0.5b/primary/summary_clean.md`
- Per item: `results/qwen2.5-0.5b/primary/items.md`
- Raw JSONL: `results/qwen2.5-0.5b/primary/*.jsonl`
- Free JSONL: `results/qwen2.5-0.5b/schema-development/free.jsonl`
- Full local ledger: `docs/run-ledgers/qwen2.5-0.5b.md`

## Qwen2.5-7B diagnostics and trustworthy evidence

All Kaggle versions are documented separately in
`docs/run-ledgers/qwen2.5-7b.md`. Key findings:

1. Versions 1–5 diagnosed missing GPU attachment/account verification.
2. Versions 6, 8, 9, and 11 showed severe token corruption under 4-bit or FP16 paths.
3. BF16 removed punctuation corruption but systematically damaged digits (versions
   12–13).
4. FP32 produced the first faithful answer in version 14 and a trustworthy paired
   five-item smoke in version 15.
5. Version 16 detected a stale private-dataset deployment; it is not treated as a
   strict-schema experiment.
6. Version 17 verified source hashes and achieved 5/5 strict Outlines accuracy and
   structure on the first five items.
7. Version 18 expanded strict Outlines to 20 items: 13/20 official accuracy and 13/19
   cleaned accuracy, with 20/20 strict structural compliance and zero errors/caps.

Version 18's six genuine errors comprised five reasoning/language failures and one
reasoning-to-answer mismatch: reasoning correctly derived 26, but the answer field was
`-26`. A numeric grammar cannot guarantee agreement between reasoning and answer.

### Completed 7B primary evidence

- Version 19 completed the v6 20-item free/prompt/order controls. On 19 audited items,
  free scored 11/19 strict-correct, reasoning-first prompt scored 2/19 strict but
  12/19 by lenient recovery, and answer-first scored 3/19 strict. Reasoning-first
  copied the concrete 42 example on three unrelated items; answer-first achieved
  perfect structure but often emitted a wrong answer before subsequently deriving a
  different value. This is trustworthy prompt-probe/control evidence, not the primary
  prompt estimate.
- Version 20 completed the v8 five-item cross-backend gate. Outlines passed 5/5
  structural compliance with zero errors/caps. XGrammar completed only 4/5 because
  `any_whitespace=True` allowed the model to loop on legal whitespace before the
  answer until the 256-token cap. Prompt-only produced 5/5 whole JSON but 0/5 string
  schema compliance because every answer was an unquoted number.
- Version 21 completed the single protocol-permitted XGrammar configuration debug.
  Canonical JSON whitespace achieved 5/5 strict structure with zero errors/caps, so
  XGrammar passed the technical gate.
- Version 22 completed the v8 symbolic-template FP32 GSM8K-50 primary matrix across
  free, prompt-only, Outlines, and canonical-whitespace XGrammar. Artifact validation
  accepted all 200 rows with zero errors, caps, duplicates, warnings, or provenance
  mismatches.
- Version 23 completed the two 50-item answer-order controls. Artifact validation
  accepted all 100 rows with zero errors, caps, duplicates, warnings, or provenance
  mismatches.
- The combined data-cleaned six-condition result is preserved at
  `results/qwen2.5-7b/primary/combined/summary_clean.md`; the complete per-item
  matrix is `results/qwen2.5-7b/primary/combined/items.md`.

The cross-scale contrast is therefore part of the finding rather than a pending cell:
0.5B showed no detectable semantic constraint effect, while 7B showed the same
−18.4-point effect for two independently integrated grammar backends.

## Relationship to prior work

The broad ideas tested here are not new claims. XGrammar's paper presents grammar
execution as an efficient way to guarantee structured generation and reports near-zero
end-to-end overhead in optimized serving settings. JSONSchemaBench evaluates multiple
constrained-decoding frameworks, including Outlines and XGrammar, across compliance,
coverage, efficiency, and output quality. CRANE specifically argues that overly
restrictive output grammars can reduce reasoning accuracy and reports that a
reasoning-augmented grammar can recover it.

Primary references:

- [XGrammar: Flexible and Efficient Structured Generation Engine for Large Language
  Models](https://arxiv.org/abs/2411.15100)
- [Generating Structured Outputs from Language Models: Benchmark and
  Studies](https://arxiv.org/abs/2501.10868)
- [CRANE: Reasoning with Constrained LLM
  Generation](https://arxiv.org/abs/2502.09061)

The contribution is therefore a controlled reproduction and engineering audit,
not a claim to have invented constrained decoding or discovered its general trade-off.
The evidence is specific in ways that matter operationally: identical prompt text for
prompt-only and constrained cells; paired item-level GSM8K scoring; two Qwen model
sizes; two independent grammar backends; prompt-copying and missing-template probes;
strict versus recoverable-answer separation; and preservation of precision-corrupted,
stale-deployment, and failed runs rather than silently discarding them. The final 7B
matrix shows that the local 0.5B effect does not generalize even within this narrow
two-size Qwen setup.

## Reproducibility safeguards

- Kaggle source files are downloaded and hash-checked before a kernel push.
- Run manifests record source hashes, model artifact, environment, precision, GPUs,
  packages, conditions, item limit, seed, and cap.
- `scripts/validate_artifacts.py` machine-checks manifest invariants, dataset
  and source hashes, exact planned item IDs/order, row counts, prompt versions,
  decoding settings, duplicate IDs, errors, and cap hits before a run is accepted.
- Output files are append-only/resumable locally and refuse mismatched signatures.
- Every failed/diagnostic run remains in its own evidence directory.
- Accepted evidence and reporting changes are committed only after validation.

## Current limitations

- GSM8K only; no MATH500, BFCL, JSONSchemaBench, or tool-use benchmark yet.
- Two model sizes from one model family.
- Greedy decoding only; conclusions do not cover stochastic sampling.
- Fifty selected items yield wide intervals, especially at low 0.5B accuracy.
- Several paired contrasts are reported. Exact p-values are not presented as a
  universal confirmatory family; the duplicated −18.4-point backend result remains
  below 0.05 under a simple two-backend Bonferroni correction, but needs independent
  replication.
- FP32 is trustworthy but slow on T4; lower-precision behavior was invalid in this
  setup and may not generalize to other hardware/kernels.
- Prompt wording is a major causal variable; v6/v7 probes demonstrate that careless
  prompt baselines can reverse the apparent constrained-decoding effect.

## Conclusion

**The primary study is complete and supports continuing the project.** The defensible conclusion
is not that constrained decoding always harms reasoning. It is narrower and more
useful:

1. Hard constraints reliably enforce the declared JSON contract; prompt-only JSON
   can look valid while violating a field type on every row.
2. Syntax guarantees do not imply semantic preservation. Under the matched 7B v8
   setup, both Outlines and XGrammar lost 18.4 points of recoverable GSM8K accuracy
   versus prompt-only generation.
3. The effect is configuration-dependent. It was not detectable on 0.5B, and the 7B
   result is limited to one deterministic subset, model family, prompt, schema, and
   greedy-decoding setup.
4. Output order is a major causal variable. Forcing the answer before the reasoning
   caused much larger accuracy losses than the backend choice itself.
5. The practical trade-off is two-dimensional: constrained decoding improved usable,
   contract-compliant correctness while reducing the model's underlying recoverable
   math correctness.

The next research phase should test mechanisms rather than merely repeat this matrix: constrain only a
final answer after unconstrained reasoning, use a two-stage reason-then-serialize
pipeline, add at least one additional model family and task, and separate grammar
overhead from output-length effects. Until then, these results are a controlled
reproduction and engineering audit, not a universal claim.
