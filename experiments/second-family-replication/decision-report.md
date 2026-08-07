# Second-family replication decision report

## Decision

**Red: no cross-family replication.**

On the fresh 150-item holdout, replacing the model-facing signed numeric string with a native JSON integer reduced final contract-valid correctness by 6.7 percentage points. The control scored 92/150 (61.3%) and the treatment scored 82/150 (54.7%). There were 5 treatment-only wins and 15 control-only wins. The exact paired bootstrap 95% interval was [-12.7, -1.3] percentage points, and the exact McNemar p-value was 0.0414.

This is evidence of harm in this model and protocol, not an independent replication of the earlier Qwen improvement. The result must not be described as positive, promising, or replicated.

The primary artifacts are in [results](results), the complete paired statistics are in [paired-summary.json](paired-summary.json), and all discordant transitions are recorded in [failure-attribution.jsonl](failure-attribution.jsonl).

## Question tested

On a non-Qwen model and unseen GSM8K items, does replacing a model-facing canonical signed numeric string with a native JSON integer improve final external-contract-valid correctness after deterministic stringification?

The frozen experiment used:

- `meta-llama/Llama-3.2-3B-Instruct` at revision `0cb88a4f764b7a12671c53f0838cd831a0843b95`;
- XGrammar 0.2.3 as the primary backend;
- greedy decoding, seed 0, FP32, and 256 maximum new tokens;
- 150 randomly selected unseen GSM8K test items as the confirmatory set;
- the corrected 49-item Qwen set as a bridge set;
- one unified generation runner for both representations;
- deterministic integer-to-string transduction followed by validation against the unchanged external schema; and
- failures, invalid objects, and cap hits retained in every denominator.

The operational canary passed all 21 checks without using semantic outcomes. The first canary attempt was discarded before expansion because the validator referenced the wrong field in the frozen dataset manifest. Its run IDs and hashes are preserved in [canary-attempts.json](canary-attempts.json). The corrected source was refrozen, the fixed canary was rerun, and only that clean attempt expanded.

## Confirmatory fresh-holdout result

| Metric | Signed-string control | Integer treatment |
|---|---:|---:|
| Assigned examples | 150 | 150 |
| Contract-valid correct | 92 (61.3%) | 82 (54.7%) |
| Semantic correct before contract requirements | 92 (61.3%) | 82 (54.7%) |
| Final external valid | 150 (100.0%) | 149 (99.3%) |
| Internal schema valid | 150 (100.0%) | 149 (99.3%) |
| Generation errors | 0 | 0 |
| Token-cap hits | 0 | 1 |
| Mean visible generated tokens | 79.2 | 78.9 |
| Median visible generated tokens | 76 | 75 |
| Mean latency, descriptive only | 4698.2 ms | 4727.3 ms |
| Median latency, descriptive only | 4511.7 ms | 4478.5 ms |
| Reasoning-consistent among assessed | 128/150 (85.3%) | 119/149 (79.9%) |

Primary paired effect:

- difference: -6.7 percentage points;
- treatment-only wins: 5;
- control-only wins: 15;
- both correct: 77;
- both incorrect: 53;
- exact paired bootstrap 95% interval: [-12.7, -1.3] points; and
- exact McNemar p-value: 0.041389.

The treatment's single cap hit was `gsm8k_test_894`. Its incomplete object remained in the denominator and counted as internally invalid, externally invalid, semantically incorrect, and contract-valid incorrect. It was not retried or repaired.

The random fresh sample contained no negative gold final answers. Therefore, it tests the general string-versus-integer representation claim but does not independently isolate a negative-sign boundary mechanism. This is an important limitation when comparing the result with the earlier Qwen cases.

### Fresh treatment-only wins

- `gsm8k_test_955`
- `gsm8k_test_449`
- `gsm8k_test_330`
- `gsm8k_test_1236`
- `gsm8k_test_538`

### Fresh control-only wins

- `gsm8k_test_1084`
- `gsm8k_test_1273`
- `gsm8k_test_1176`
- `gsm8k_test_1173`
- `gsm8k_test_446`
- `gsm8k_test_924`
- `gsm8k_test_33`
- `gsm8k_test_646`
- `gsm8k_test_668`
- `gsm8k_test_279`
- `gsm8k_test_762`
- `gsm8k_test_31`
- `gsm8k_test_207`
- `gsm8k_test_211`
- `gsm8k_test_299`

## Bridge-set result

| Metric | Signed-string control | Integer treatment |
|---|---:|---:|
| Assigned examples | 49 | 49 |
| Contract-valid correct | 21 (42.9%) | 20 (40.8%) |
| Semantic correct | 21 (42.9%) | 20 (40.8%) |
| Final external valid | 49 (100.0%) | 49 (100.0%) |
| Internal schema valid | 49 (100.0%) | 49 (100.0%) |
| Errors | 0 | 0 |
| Cap hits | 0 | 0 |
| Mean visible generated tokens | 77.6 | 77.8 |
| Mean latency, descriptive only | 4733.7 ms | 4529.8 ms |

The paired bridge effect was -2.0 points with a 95% paired interval of [-10.2, 6.1]. There were 2 treatment-only wins and 3 control-only wins, with exact McNemar p = 1.0. The bridge result is uncertain but does not rescue the clearly negative fresh result.

Bridge treatment-only wins were `gsm8k_test_1020` and `gsm8k_test_1216`. Bridge control-only wins were `gsm8k_test_1010`, `gsm8k_test_12`, and `gsm8k_test_739`.

## Mechanism audit

Every one of the 25 discordant items across the fresh and bridge sets was manually inspected. The primary categories were:

| Category | Count |
|---|---:|
| Problem-interpretation change | 12 |
| Reasoning-final-answer inconsistency | 9 |
| Arithmetic regression | 3 |
| Arithmetic correction | 1 |
| Sign or lexical-boundary change | 0 |
| Truncation among discordants | 0 |
| Parser or validator issue | 0 |
| Other | 0 |

The five fresh treatment wins were genuine changes in reasoning or interpretation, not deterministic repair effects. The fifteen fresh losses were also genuine model-behavior changes. Nine audited discordances involved an answer field that did not follow the displayed reasoning, and twelve involved a changed interpretation of the word problem.

This mechanism pattern is a systematic regression cluster. It does not support a narrow claim that native integers simply remove signed-string lexical friction. On Llama 3.2 3B, the representation change perturbed broader generation behavior and produced substantially more losses than wins.

Reasoning consistency is a secondary diagnostic based on whether the last numeric mention in reasoning equals the final answer. It is not a substitute for full mathematical proof checking. Correct but reasoning-inconsistent final answers remain correct in the primary metric.

## Backend implementation parity

After the XGrammar result and discordant set were frozen, Outlines ran on all 20 fresh discordants plus 20 concordant items selected with seed 20260816. Both representations used the same 40 IDs.

Results:

- 40/40 signed-string raw outputs were byte-identical between XGrammar and Outlines;
- 40/40 integer raw outputs were byte-identical between XGrammar and Outlines;
- all 80 effective prompts, normalized answers, correctness fields, validity fields, cap flags, and error fields matched; and
- the same integer cap hit reproduced under both backends.

The full parity evidence is in [parity-report.json](parity-report.json). This check does not create a second statistical estimate and does not change the primary Red decision. It shows that the observed behavior is not specific to the XGrammar implementation on the audited subset.

## Predeclared gate evaluation

| Gate condition | Result |
|---|---|
| Treatment improves by at least 5 points | Failed: treatment decreased by 6.7 points |
| Final external validity remains 100% | Failed: treatment was 99.3% |
| Treatment-only wins exceed control-only wins | Failed: 5 versus 15 |
| Interval excludes meaningful harm below -5 points | Failed: lower bound was -12.7 points |
| Bridge does not oppose by at least 5 points | Passed: bridge estimate was -2.0 points |
| No systematic regression cluster | Failed: interpretation and answer-consistency regressions were coherent |

Green and Green+ are ruled out. Yellow is also ruled out because the fresh estimate is negative, its interval is fully below zero, control-only wins exceed treatment-only wins, and external validity dropped below 100%.

The result satisfies multiple predeclared Red examples:

1. the fresh-holdout difference is negative;
2. control-only wins exceed treatment-only wins;
3. external validity drops below 100%; and
4. the treatment creates a coherent regression pattern.

## What this result does and does not mean

This result falsifies the broad claim that the accepted signed-string-to-integer transform reliably improves GSM8K contract-valid correctness across the tested Qwen and Llama model families. It also prevents a public claim of independent replication.

It does not prove that all contract alignment is harmful. The experiment tests one transform, one Llama model, one task family, one prompt, greedy decoding, and one random holdout. The earlier Qwen improvement remains a valid narrow observation in its accepted artifacts, but it is now model-dependent evidence rather than a general compiler optimization.

The exact Outlines parity result strengthens the internal validity of this negative finding. The absence of negative gold answers limits conclusions about a specifically negative-sign mechanism. Any future sign-focused study would need a separately preregistered sign-stress dataset and could not replace this confirmatory result.

## Authorized next step

The preregistered Red path authorizes exactly one bounded practical tool-call pilot. It does not authorize prompt searching, model-family searching, broad schema expansion, or a company/recruiter campaign.

The pilot must use pinned BFCL `simple_python` cases, single-turn single-function calls, the same canonical numeric-string-to-integer transform, deterministic local execution wrappers, exact argument scoring, no heuristic repairs, and explicit post-execution state checks.

If that bounded pilot is also Red, the product thesis narrows to:

> a schema-risk linter, measurement harness, and contract-sensitivity analyzer

rather than a general optimizing compiler.

## Reproducibility status

- Primary XGrammar artifacts: structurally validated, 398/398 rows.
- Manual discordant audit: complete, 25/25 rows.
- Outlines parity subset: structurally valid, 80/80 exact output matches.
- Model and tokenizer revision: frozen and identical.
- Package environment: frozen and identical across primary runs.
- Modal metered free-credit use after parity: approximately $1.45.
- Modal billed cost: $0.00.
- Post-launch exclusions: none on the fresh set; only the bridge defect declared before launch.

The machine-readable validation is in [artifact-validation.json](artifact-validation.json), and the complete protocol is in [protocol.md](protocol.md).
