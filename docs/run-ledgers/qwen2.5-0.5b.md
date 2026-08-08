---
title: Qwen2.5 0.5B run ledger
description: Frozen operational ledger for local pilot and primary Qwen2.5 0.5B runs
search:
  exclude: true
---

# Qwen2.5 0.5B run ledger

!!! info "Document status: frozen operational record"

    This ledger is preserved for provenance and excluded from normal search.

This ledger keeps prompt probes separate from the frozen primary matrix. Raw JSONL
rows are never overwritten or pooled across prompt versions.

## Shared environment and method

- Model: `Qwen/Qwen2.5-0.5B-Instruct`, revision recorded in every row.
- Hardware: NVIDIA GeForce RTX 4050 Laptop GPU with 6 GB VRAM.
- PyTorch `2.6.0+cu124`, CUDA 12.4 available.
- FP32 model loading, greedy decoding, seed 0, 256-token cap.
- Deterministic GSM8K-50 subset with dataset SHA-256
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- `gsm8k_test_454` is retained in raw official scores and excluded only from the
  predeclared data-cleaned analysis because its question/reference are contradictory.
- Generation errors and token-cap failures remain in denominators.

## Free response: shared 50-item control

- 50/50 rows completed with zero generation exceptions.
- Official accuracy: 14/50 = 28.0%; cleaned accuracy: 14/49 = 28.6%.
- Cleaned Wilson 95% interval: 17.8% to 42.4%.
- 23/50 rows hit the 256-token cap; only 7/50 ended with the requested final-answer
  marker. Free response is therefore more accurate than JSON conditions but weakly
  protocol-compliant for this model.
- Mean cleaned latency was 11,288.3 ms and mean output length 223.9 tokens.
- Evidence: `results/qwen2.5-0.5b/schema-development/free.jsonl`.

## Prompt probe v6: strict schema with literal answer example `42`

### Configuration

- Prompt version `day3-v6-strict-numeric-answer`.
- The prompt showed a valid JSON example containing `"answer": "42"`.
- Four JSON conditions, 50 rows each; all 200 rows completed without generation
  exceptions.

### Cleaned aggregate observations (n=49 per condition)

- Prompted reasoning-first: 8/49 lenient accuracy but 5/49 = 10.2% strict accuracy;
  strict numeric/schema compliance 37/49 = 75.5%.
- Outlines reasoning-first: 4/49 = 8.2% strict accuracy; compliance 48/49 = 98.0%;
  one token-cap non-completion.
- Prompted answer-first: 3/49 = 6.1% strict accuracy; strict compliance 45/49 =
  91.8%.
- Outlines answer-first: 3/49 = 6.1% strict accuracy; 49/49 compliance.
- Strict Outlines reasoning-first minus matched prompt: -2.0 points, 3
  Outlines-only wins versus 4 prompt-only wins, exact McNemar p=1.000.
- Strict prompted reasoning-first minus free: -18.4 points, 2 prompt-only versus 11
  free-only wins, exact p=0.0225.

### Mechanism observations and classification

- The 0.5B model emitted the literal demonstration value `42` on 11/50 prompted
  reasoning-first rows, 11/50 prompted answer-first rows, 7/50 Outlines
  reasoning-first rows, and 3/50 Outlines answer-first rows.
- This is a concrete example-copying confound. The matrix remains useful for studying
  prompt-example sensitivity but is not the frozen primary cross-model estimate.
- Evidence: `results/qwen2.5-0.5b/schema-development/`.

## Prompt probe v7: field order in prose, no JSON template

### Configuration

- Prompt version `day3-v7-no-answer-example`.
- The literal `42` example and all JSON syntax examples were removed. Field order was
  stated only in prose.
- Four JSON conditions, 50 rows each; all 200 rows completed without generation
  exceptions.

### Cleaned aggregate observations (n=49 per condition)

- Prompted reasoning-first: 6/49 lenient accuracy, **0/49 strict accuracy**, 0/49
  whole-response JSON, and only 1/49 strict numeric/schema compliance.
- Outlines reasoning-first: 8/49 = 16.3% strict accuracy and 48/49 = 98.0%
  compliance; one cap non-completion.
- Prompted answer-first: 1/49 = 2.0% strict accuracy and 1/49 compliance; two cap
  hits in the 49 included rows.
- Outlines answer-first: 2/49 = 4.1% strict accuracy and 46/49 = 93.9%
  compliance.
- Strict Outlines reasoning-first minus matched prompt: +16.3 points, 8
  Outlines-only wins and zero prompt-only wins, exact p=0.0078.
- Outlines answer-first minus reasoning-first: -12.2 points, exact p=0.0313.

### Mechanism observations and classification

- Removing the numeric example eliminated `42` copying completely.
- Removing JSON syntax simultaneously made prompt-only JSON almost impossible for the
  0.5B model. The large apparent Outlines benefit is therefore largely a weak-prompt
  structure effect, not a fair final decoder comparison.
- This is a useful prompt-scaffolding diagnostic, not the primary matrix.
- Evidence: `results/qwen2.5-0.5b/prompt-ablation/`.

## Primary v8 matrix: symbolic JSON template, no task answer

### Configuration and integrity

- Prompt version `day3-v8-symbolic-json-template`, frozen in
  `docs/methodology.md` before its outputs were observed.
- The prompt shows exact JSON syntax with symbolic angle-bracket placeholders and no
  concrete answer number. Prompted and Outlines conditions receive identical text.
- Four JSON conditions produced all 200 planned rows with zero generation exceptions.
- All files have one prompt version and one run signature per condition.

### Cleaned condition results (n=49)

- Free: 14/49 = 28.6%, Wilson 95% interval 17.8%–42.4%.
- Prompted reasoning-first: 3/49 = 6.1% strict accuracy, interval 2.1%–16.5%;
  strict numeric/schema compliance 21/49 = 42.9%; whole JSON 40/49 = 81.6%.
- Outlines reasoning-first: 5/49 = 10.2% strict accuracy, interval 4.4%–21.8%;
  strict numeric/schema/whole-JSON compliance 49/49 = 100%; no cap hits.
- Prompted answer-first: 2/49 = 4.1% strict accuracy; strict compliance 39/49 =
  79.6%; whole JSON 43/49 = 87.8%; one cap hit.
- Outlines answer-first: 3/49 = 6.1% strict accuracy; compliance 48/49 = 98.0%; one
  cap hit.

### Predeclared paired results

- JSON prompt cost (prompted reasoning-first minus free): **-22.4 points**, paired
  bootstrap 95% interval -36.7 to -8.2 points; 2 prompt-only wins versus 13 free-only
  wins; exact McNemar p=0.0074.
- Incremental Outlines effect (Outlines reasoning-first minus prompted
  reasoning-first): **+4.1 points**, paired interval -4.1 to +12.2 points; 3
  Outlines-only wins versus 1 prompt-only win; exact p=0.625.
- Prompted answer-first minus reasoning-first: -2.0 points, interval -8.2 to +4.1;
  exact p=1.000.
- Outlines answer-first minus reasoning-first: -4.1 points, interval -14.3 to +6.1;
  exact p=0.688.

### Interpretation

- Requiring structured JSON causes a detectable task-accuracy loss relative to free
  response for Qwen2.5-0.5B under this prompt and cap.
- Outlines dramatically improves strict format compliance over matched prompting.
- There is **no detectable Outlines accuracy degradation** relative to the matched
  prompt; the point estimate is positive but its interval includes meaningful harm
  and benefit.
- This is a concrete primary small-model result, not evidence about the 7B model or
  other constrained backends.
- Aggregate evidence: `results/qwen2.5-0.5b/primary/summary_clean.md`.
- Every item and condition: `results/qwen2.5-0.5b/primary/items.md`.
- Raw evidence: `results/qwen2.5-0.5b/primary/*.jsonl` and the shared free
  JSONL above.

## XGrammar v8 reasoning-first expansion

### Integration and smoke observations

- XGrammar 0.2.4 was the current release but had no compatible Linux x86-64 wheel for
  Python 3.12. The immediately preceding official release, XGrammar 0.2.3, installed
  successfully and is pinned in `requirements.txt`.
- Integration followed the official Transformers API: Hugging Face tokenizer metadata,
  `GrammarCompiler.compile_json_schema`, and `xgrammar.contrib.hf.LogitsProcessor`.
- The five-item smoke produced 5/5 strict numeric, whole JSON, schema-valid, ordered
  rows with zero errors and caps, satisfying the predeclared expansion gate.
- Smoke accuracy was 1/5 and average latency was 2,456.2 ms.

### Cleaned 49-item result

- XGrammar reasoning-first: 4/49 = 8.2% strict accuracy, Wilson 95% interval
  3.2%–19.2%.
- Strict numeric, whole JSON, schema, and field-order compliance were all 49/49 =
  100%; there were zero generation errors and zero cap hits.
- Mean latency was 2,477.1 ms and median 1,562.6 ms, versus Outlines reasoning-first
  mean 2,938.3 ms on the same items. Generated lengths differ, so this is descriptive
  end-to-end latency rather than isolated grammar-overhead measurement.
- XGrammar minus matched prompted reasoning-first: +2.0 points strict accuracy,
  bootstrap interval 0.0 to +6.1 points; one XGrammar-only strict win, zero
  prompt-only strict wins, three both correct, 45 both wrong; exact McNemar p=1.000.

### Interpretation

- XGrammar and Outlines both raise strict structure compliance from 42.9% under
  prompting to 100% on this primary order.
- Neither backend shows a detectable task-accuracy difference from matched prompting:
  XGrammar +2.0 points (p=1.000), Outlines +4.1 points (p=0.625).
- There is no evidence here that one constrained backend causes a larger semantic
  penalty than the other. Low base task accuracy makes modest differences difficult
  to resolve.
- XGrammar rows are included in the aggregate and per-item evidence under
  `results/qwen2.5-0.5b/primary/`.

## XGrammar canonical-whitespace debug

After Qwen-7B version 20 exposed an unlimited legal-whitespace loop under
`any_whitespace=True`, the single protocol-permitted configuration debug was first
tested on the local 0.5B model. The only grammar change was
`xgrammar_any_whitespace=false`; it is now included in the run signature and every
XGrammar row.

- First five deterministic items, FP32, greedy, seed 0, 256-token cap.
- 5/5 whole JSON, strict numeric string, schema, and field-order compliance.
- Zero errors and zero cap hits; run signature `80097bb4cd50`.
- Task accuracy was 1/5. This did not decide the technical check and does not replace
  the existing 50-item `any_whitespace=True` local result.
- The optional `torch-c-dlpack-ext` warning recurred but remained non-fatal.
- Evidence:
  `results/qwen2.5-0.5b/primary/xgrammar_json_reasoning_first_canonical_whitespace_gate.jsonl`.

The canonical-whitespace configuration was then run over all 50 items to keep a
matched local comparator available if the 7B debug passes:

- 50/50 whole JSON, numeric string, schema, and field-order compliance; zero errors
  and caps.
- Raw 4/50 and predeclared-clean 4/49 = 8.2% strict accuracy, Wilson 95% CI
  3.2%–19.2%.
- Canonical XGrammar minus matched prompting: +2.0 strict points, paired interval
  0.0 to +6.1; one XGrammar-only strict win and zero prompt-only wins; exact p=1.0.
- Mean cleaned latency 2,634.2 ms, median 1,856.3 ms, average 41.2 tokens. The
  permissive-whitespace run averaged 2,477.1 ms and 100% compliance, so canonical
  whitespace did not improve this model's already-stable completion behavior.
- The aggregate count matches the permissive configuration, but individual outputs
  changed; the two files are not pooled or treated as replicated samples.
- Evidence:
  `xgrammar_json_reasoning_first_canonical_whitespace.jsonl`,
  `summary_canonical_xgrammar_clean.md`, and `items_canonical_xgrammar.md` in the same
  result directory.
