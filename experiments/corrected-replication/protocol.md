# Corrected Representation-Alignment Replication Protocol

## Research rule

No architecture stage advances merely because its code executes. Advancement requires a written question, frozen conditions, an explicit primary metric, an operational gate, and a decision rule that can return continue, narrow, or stop. Failed and contradictory evidence is preserved.

## Why this replication is required

The accepted 7B artifacts remain immutable and provenance-valid, but review found that the historical Outlines path could apply the tokenizer chat template twice. The current runner also makes JSON whitespace and visible generated-token measurement consistent across backends. A comparison between a corrected integer treatment and the historical signed-string Outlines baseline would therefore mix runner versions.

This replication reruns both sides of the constrained comparison with the same corrected source. It does not overwrite or relabel historical evidence.

## Question

For Qwen2.5-7B-Instruct under greedy FP32 decoding, does replacing a hard-constrained signed numeric string with a model-facing JSON integer improve contract-valid correctness after deterministic stringification, when both representations use the corrected prompt and backend paths?

## Frozen design

- Model: Qwen2.5-7B-Instruct, Kaggle model revision `qwen-lm/qwen2.5/transformers/7b-instruct/1`.
- Dataset: deterministic GSM8K-50 subset with SHA-256 `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- Clean paired analysis: 49 items after excluding only the previously documented contradictory reference `gsm8k_test_454`.
- Decoding: greedy, seed 0, FP32, 256 maximum new tokens.
- Backends: Outlines 1.3.2 and XGrammar 0.2.3.
- External contract: reasoning string followed by signed numeric answer string.
- Treatment: model-facing integer followed by deterministic arbitrary-precision stringification and final external validation.
- No prompt tuning, schema tuning, item removal, or threshold changes after launch.

## Conditions

| Backend | Control | Treatment |
| --- | --- | --- |
| Outlines | `outlines_json_reasoning_first` | `outlines_json_integer_reasoning_first` |
| XGrammar | `xgrammar_json_reasoning_first` | `xgrammar_json_integer_reasoning_first` |

Prompt-only conditions are not rerun because they do not exercise either corrected constrained backend path. Historical prompt-only rows may be used as descriptive context, not as a primary paired control in this replication.

## Operational canary gate

The first five deterministic items are generated for every condition. Those same result files are resumed to 50, so the canary consumes no duplicate research rows.

Expansion is permitted only if:

1. every condition has exactly the same five unique item IDs in frozen order;
2. every row has non-empty output, no generation exception, and no token-cap hit;
3. all constrained outputs validate against their model-facing schemas;
4. every integer output transduces successfully and validates against the original external schema;
5. Outlines and XGrammar receive identical effective prompts within each representation;
6. manifests and run signatures are internally consistent.

The canary does not require correct mathematics. Conditioning expansion on early semantic wins would bias the confirmation.

## Metrics

Primary metric:

- paired delta in contract-valid correctness on the cleaned 49-item set, integer treatment minus matching signed-string control.

Secondary metrics:

- representation-independent semantic correctness;
- final external validity;
- internal schema validity;
- wrong-valid rate;
- paired treatment-only and control-only counts;
- exact McNemar p-value and deterministic bootstrap interval;
- repaired and newly broken item IDs;
- errors, cap hits, negative-answer rate, generated content tokens, and latency.

Latency is descriptive because the run is not randomized or designed as a dedicated performance benchmark.

## Decision rule

Green, continue the compiler direction:

- at least one backend improves contract-valid correctness by at least 5 percentage points on the cleaned paired set;
- treatment outputs preserve 100 percent final external validity;
- paired wins exceed paired losses for that backend;
- no backend shows a systematic semantic regression of at least 5 percentage points; and
- the repaired outputs are consistent with the representation-boundary mechanism rather than a scoring or validation artifact.

Yellow, narrow the direction:

- there is a positive paired effect below 5 points;
- only a narrow backend or schema domain benefits;
- corrected baselines remove most of the historical effect but retain a localized mechanism; or
- evidence is directionally useful but uncertainty or newly broken cases prevents the green claim.

Red, stop the general compiler build:

- neither backend has a positive paired contract-valid effect;
- treatment creates an equal or larger systematic failure cluster;
- external validity is not preserved; or
- corrected evidence contradicts the proposed representation mechanism.

A red result preserves the measurement study and supports a schema-risk linter or a concluded negative result. It does not authorize searching through unregistered prompts or transforms until a favorable result appears.

## Compute budget

Kaggle reported 20.78 of 30 GPU hours used and 9.22 hours remaining immediately before packaging. Historical per-condition timings predict approximately 5.3 hours of generation and 5.5 to 6 hours including setup, model loads, validation, and summarization.

## Evidence requirements

The accepted result must include:

- exact source snapshot and SHA-256 manifest;
- kernel and per-condition manifests;
- all 200 raw rows, including failures;
- canary-gate report;
- paired summary with the single frozen exclusion;
- XGrammar boundary traces for the three preregistered items;
- local post-download provenance and completeness validation;
- an explicit green, yellow, or red conclusion with limitations.
