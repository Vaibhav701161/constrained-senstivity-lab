# Qwen2.5-7B Kaggle Run Ledger

Status (4 Aug 2026): **versions 1–23 documented; final v8 matrix complete and
validated; no follow-up worker running.**

This file records each Kaggle run separately. A completed worker is not automatically
a valid experiment: runs affected by missing hardware, dependency failures, token
corruption, or numeric corruption are explicitly classified as diagnostics and are
excluded from accuracy conclusions.

## Fixed experimental context

- Kaggle account: `vaibhav7011`
- Kernel: `vaibhav7011/constrained-decoding-qwen7b-smoke` (private)
- Source dataset: `vaibhav7011/constrained-decoding-day3-source` (private)
- Model: `Qwen/Qwen2.5-7B-Instruct`
- Evaluation data: deterministic `gsm8k_50_seed0.jsonl`
- Seed: `0`
- Maximum new tokens: `256`
- Final evaluated conditions:
  - `free`
  - `prompted_json_reasoning_first`
  - `outlines_json_reasoning_first`
  - `xgrammar_json_reasoning_first`
  - `prompted_json_answer_first`
  - `outlines_json_answer_first`
- Trust rule: inspect raw outputs and environment provenance before using summary
  accuracy.

## Version 1: optional diagnostic caused immediate failure

### Configuration

- Private Kaggle script with requested T4 and internet access.
- The wrapper called `nvidia-smi` as a mandatory first diagnostic.

### Outcome and observations

- Kaggle did not provide `nvidia-smi` on the command path.
- Python raised `FileNotFoundError` before package setup, CUDA inspection, model load,
  or inference.
- No GSM8K result rows were produced.

### Classification and lesson

- **Infrastructure diagnostic only; unusable for model conclusions.**
- `nvidia-smi` is convenient but not a reliable mandatory CUDA gate in a Kaggle
  script. The wrapper was changed to treat it as optional and use
  `torch.cuda.is_available()` as the real test.

## Version 2: internet/package setup failed before CUDA check

### Configuration

- Optional `nvidia-smi` behavior.
- Requested T4 and internet remained present in downloaded Kaggle metadata.
- Attempted to install the pinned evaluation environment from PyPI.

### Outcome and observations

- DNS resolution repeatedly failed while pip requested `transformers==4.51.3`.
- Pip reported no available versions only because it could not reach the package
  index; this was not a genuine package-version absence.
- The job failed before the explicit PyTorch CUDA probe and before model inference.

### Classification and lesson

- **Infrastructure diagnostic only; unusable for model conclusions.**
- Saved notebook metadata can request internet while a new/unverified Kaggle account
  still receives a restricted runtime.

## Version 3: pre-install probe proved that Kaggle supplied a CPU image

### Configuration

- Added package and CUDA inspection before pip installation.

### Outcome and observations

- Preinstalled PyTorch: `2.10.0+cpu`.
- CUDA runtime: `null`.
- `torch.cuda.is_available()`: `false`.
- Preinstalled relevant packages included Transformers 5.0.0, Accelerate 1.13.0,
  Datasets 5.0.0, and JSON Schema 4.26.0; Outlines and bitsandbytes were absent.
- The explicit CUDA guard stopped the job before inference.

### Classification and lesson

- **Infrastructure diagnostic only; unusable for model conclusions.**
- The problem was not merely a missing `nvidia-smi` executable: Kaggle had genuinely
  scheduled a CPU-only image.

## Version 4: explicit CLI T4 override was still ignored

### Configuration

- Launched with the explicit CLI accelerator argument
  `--accelerator NvidiaTeslaT4`.
- Server metadata still showed `enable_gpu: true`, internet enabled, and
  `machine_shape: NvidiaTeslaT4`.

### Outcome and observations

- Runtime again contained `torch 2.10.0+cpu`, no CUDA runtime, and no CUDA device.
- The job stopped at the CUDA guard.

### Classification and lesson

- **Infrastructure diagnostic only; unusable for model conclusions.**
- Correct notebook metadata and an explicit API accelerator override cannot bypass an
  account-level Kaggle prerequisite.

## Version 5: browser-selected T4 did not bypass account restriction

### Configuration

- Kaggle UI visibly showed `GPU T4 ×2` selected and internet enabled.
- Relaunched through the API with the explicit T4 override.

### Outcome and observations

- Kaggle again supplied `torch 2.10.0+cpu` with no CUDA device.
- The UI selection alone was insufficient before phone verification.

### Classification and lesson

- **Infrastructure diagnostic only; unusable for model conclusions.**
- The user then completed Kaggle phone verification. This was the missing one-time
  account prerequisite.

## Version 6: first GPU completion, but severe 4-bit token corruption

### Configuration

- Phone verification complete.
- GPU: one visible Tesla T4 for the single-device 4-bit load.
- PyTorch `2.10.0+cu128`; CUDA 12.8.
- Transformers 4.51.3; Outlines 1.3.2; bitsandbytes 0.45.5.
- Qwen2.5-7B-Instruct loaded from Hugging Face using bitsandbytes NF4 4-bit.
- Five items in each of the three main conditions (15 rows).

### Outcome and observations

- Worker completed and wrote all 15 assigned rows with zero generation exceptions.
- Outputs were not semantically usable: exclamation marks appeared between or inside
  ordinary tokens and digits, for example `Saman!ca!a!...` and `4!0!0`.
- Five rows hit the 256-token cap.
- Apparent summary metrics were: free 0/5, prompted JSON 0/5, Outlines 1/5.
- Prompted JSON schema validity was 0/5; Outlines schema validity was 4/5.
- These metrics describe corrupted generation and must not be interpreted as Qwen
  accuracy or an Outlines effect.

### Classification and evidence

- **Completed but invalid for accuracy conclusions.**
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_smoke_v6/`.

## Version 7: newer bitsandbytes installed, but documented model path was stale

### Configuration

- Updated bitsandbytes from 0.45.5 to 0.50.0.
- Attached Qwen's official Kaggle-hosted model artifact to avoid a 15 GB network
  download.
- Used the then-documented path
  `/kaggle/input/qwen2.5/transformers/7b-instruct/1`.

### Outcome and observations

- Package installation succeeded.
- Transformers rejected the path as a nonexistent local directory and then treated it
  as an invalid Hugging Face repository identifier.
- The current Kaggle runtime actually mounts models below
  `/kaggle/input/models/<owner>/<model>/<framework>/<variation>/<version>`.
- No inference rows were produced.

### Classification and lesson

- **Deployment diagnostic only; unusable for model conclusions.**
- The wrapper was changed to discover the unique mounted `config.json` instead of
  hard-coding Kaggle's mount layout.

## Version 8: bitsandbytes 0.50.0 did not solve token corruption

### Configuration

- PyTorch `2.10.0+cu128`; CUDA 12.8.
- Transformers 4.51.3; bitsandbytes 0.50.0.
- Dynamically discovered official model path:
  `/kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1`.
- Same five paired items and three conditions as version 6.

### Outcome and observations

- All 15 rows completed with zero generation exceptions.
- Token corruption remained. Prompted and Outlines raw-output hashes were identical to
  version 6, and free output remained heavily corrupted.
- Summary again reported free 0/5, prompted 0/5, and Outlines 1/5, with five capped
  rows.

### Classification and evidence

- **Completed but invalid for accuracy conclusions.**
- This ruled out the old bitsandbytes release as the sole cause.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_smoke_v8/`.

## Version 9: full FP16 also corrupted, ruling out 4-bit quantization alone

### Configuration

- One free-condition item.
- No 4-bit quantization.
- Full model forced to FP16 and split automatically across two T4 GPUs.
- PyTorch `2.10.0+cu128`; CUDA 12.8.

### Outcome and observations

- The job completed without a generation exception.
- The raw answer was still corrupted with interleaved exclamation marks.
- Predicted normalized answer was `0` instead of gold `400`.
- Latency was approximately 8.6 seconds for 127 generated tokens.

### Classification and evidence

- **Completed but invalid for accuracy conclusions.**
- This ruled out bitsandbytes/NF4 as the sole cause because full FP16 reproduced the
  phenomenon.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp16_probe_v9/`.

## Version 10: pinned PyTorch succeeded, incompatible torchvision blocked loading

### Configuration

- Replaced Kaggle's PyTorch with `2.6.0+cu124`, matching the known local CUDA family.
- Full FP16 model across two T4 GPUs.

### Outcome and observations

- The fresh-process probe confirmed PyTorch 2.6.0, CUDA 12.4, CUDA available, and two
  GPUs.
- Kaggle's leftover torchvision 0.25 required PyTorch 2.10.
- Importing the text model indirectly imported incompatible torchvision and failed on
  the missing `torchvision::nms` operator.
- No inference row was produced.

### Classification and lesson

- **Dependency diagnostic only; unusable for model conclusions.**
- Text-only jobs do not need torchvision, torchaudio, or torchcodec, so the ephemeral
  runtime now uninstalls those incompatible add-ons after pinning PyTorch.

## Version 11: older PyTorch did not solve FP16 token corruption

### Configuration

- PyTorch `2.6.0+cu124`; CUDA 12.4; two Tesla T4 GPUs.
- Incompatible vision/audio packages removed.
- Full model forced to FP16; one free-condition item.

### Outcome and observations

- Worker completed successfully.
- Raw output reproduced the same exclamation-mark corruption as version 9.
- Predicted normalized answer was `0` rather than `400`.
- Latency was approximately 8.5 seconds for 127 tokens.

### Classification and evidence

- **Completed but invalid for accuracy conclusions.**
- This ruled out Kaggle's PyTorch 2.10/CUDA 12.8 stack as the sole cause.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp16_torch26_probe_v11/`.

## Version 12: checkpoint-native BF16 removed punctuation corruption

### Configuration

- PyTorch `2.6.0+cu124`; CUDA 12.4; two T4 GPUs.
- Full model loaded with `torch_dtype="auto"`, preserving the checkpoint's declared
  BF16 dtype.
- One free-condition item.

### Outcome and observations

- Punctuation/token corruption disappeared.
- The response was coherent and followed the final-answer protocol.
- It was nevertheless numerically wrong: it changed problem values and predicted
  `148` instead of `400`.
- Generated 45 tokens in about 3.5 seconds, with no cap or generation error.

### Classification and evidence

- **Useful precision diagnostic, but not yet trustworthy for accuracy conclusions.**
- The clean syntax showed that forcing a BF16 checkpoint to FP16 caused the earlier
  token-level corruption.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_bf16_probe_v12/`.

## Version 13: BF16 structure was stable, but digits were systematically damaged

### Configuration

- Same PyTorch 2.6/CUDA 12.4 and checkpoint-native BF16 as version 12.
- Five paired items across free, prompted JSON, and Outlines JSON (15 rows).

### Integrity observations

- All 15 rows were present, with five unique shared item IDs per condition.
- Zero generation exceptions and zero token-cap hits.
- No exclamation-mark corruption.
- Free final-answer-marker compliance: 5/5.
- Prompted whole-response JSON: 5/5; prompted schema validity: 3/5 because two answers
  were JSON numbers instead of strings.
- Outlines whole-response JSON, schema validity, and field order: 5/5.
- Average latency was about 5.9 s free, 6.2 s prompted, and 7.3 s Outlines.

### Semantic observations

- All conditions scored 0/5.
- Raw calculations showed systematic input-number mutation, not ordinary isolated
  reasoning errors:
  - `100` became `10` or `1`.
  - `30` became `3`.
  - total age `20` became `22`.
  - `500` and `600` became values such as `550` and `652`.
  - `10` laps became `1` lap.
- Because the same digit damage appeared across free, prompted, and constrained
  conditions, the zero accuracy is a numerical-runtime artifact, not evidence that
  Outlines harms or helps reasoning.

### Classification and evidence

- **Structurally valid but semantically invalid for accuracy conclusions.**
- Tesla T4 does not provide the intended native BF16 execution path for this model;
  clean JSON alone is insufficient evidence of trustworthy inference.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_bf16_smoke_v13/`.

## Version 14: full FP32 produced the first trustworthy 7B answer

### Configuration

- PyTorch `2.6.0+cu124`; CUDA 12.4; two T4 GPUs.
- Full model loaded in FP32 with automatic multi-GPU placement and some likely CPU
  offload.
- One free-condition item.

### Outcome and observations

- The model preserved all input numbers exactly.
- Raw reasoning was coherent:
  Samantha `100 + 25 = 125`, Daisy `125 + 50 = 175`, total `400`.
- Final answer was exactly correct: `400`.
- Protocol compliance passed, there was no generation error, and the 62-token response
  did not hit the cap.
- Generation latency was approximately 91.8 seconds, much slower than FP16/BF16.

### Classification and evidence

- **Trustworthy precision control and eligible for accuracy interpretation.**
- This isolates precision as the cause of earlier corruption on T4: FP32 is faithful,
  while forced FP16 and checkpoint-native BF16 were not.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_probe_v14/`.

## Version 15: trustworthy FP32 paired smoke

### Configuration

- Same validated FP32 configuration as version 14.
- Five fixed items across free, prompted JSON, and Outlines JSON (15 planned rows).

### Integrity and environment observations

- The worker completed after roughly 36 minutes of batch wall time.
- The manifest recorded PyTorch `2.6.0+cu124`, CUDA 12.4, two Tesla T4 GPUs,
  `dtype=float32`, automatic multi-GPU placement, and no quantization.
- Exactly 15 rows were produced: five unique shared item IDs in each condition.
- There were zero generation exceptions, zero token-cap hits, and no punctuation or
  digit corruption.
- Free responses used the final-answer marker on all 5/5 rows.
- Prompted JSON achieved 5/5 whole-response JSON, schema validity, and field order.
- Outlines achieved 5/5 whole-response JSON, schema validity, and field order.

### Accuracy observations

- Free: 4/5 = 80%.
- Prompted JSON: 4/5 = 80%.
- Outlines JSON: 3/5 = 60%.
- Prompted JSON versus free had a paired delta of 0 points: the same four items were
  correct and the same age problem was wrong.
- Outlines versus prompted JSON had a paired delta of -20 points:
  - Outlines-only correct: 1 item.
  - Prompted-only correct: 2 items.
  - Both correct: 2 items.
  - Both wrong: 0 items.
- With only five pairs, this -20-point value is an unstable smoke-test observation,
  not evidence of a population-level constraint cost.

### Per-item observations

- `gsm8k_test_264` (three girls' money): all three conditions correctly predicted
  `400` with faithful arithmetic.
- `gsm8k_test_725` (cat/dog average time): free and prompted correctly predicted `25`.
  Outlines' reasoning also correctly derived `25`, but its answer field was `"}"`, so
  no numeric prediction could be extracted.
- `gsm8k_test_996` (children's ages):
  - Free stopped after setting up an equation and asserted `8`.
  - Prompted incorrectly reasoned that Wilfred was `0`.
  - Outlines correctly derived `3`, but emitted `"answer": "go3"` rather than a pure
    numeric string. The current scorer extracted the embedded `3` and counted it
    correct.
- `gsm8k_test_586` (water after exercise): free and prompted correctly accounted for
  both aerobics hours and predicted `800`. Outlines used `500 + 600` instead of
  `2*500 + 600` and predicted `550`.
- `gsm8k_test_1010` (track laps): all three conditions correctly predicted `5`.

### Schema and scoring observations

- The current JSON Schema requires `answer` to be a string but does not require that
  string to be numeric or non-empty.
- Consequently, `"answer": "}"` is schema-valid despite containing no answer.
- The scorer searches the answer string for a number rather than requiring the whole
  field to be numeric. Consequently, `"answer": "go3"` is schema-valid and counted
  as prediction `3`.
- Therefore, 100% schema validity overstates task-level answer-field compliance, and
  the reported 60% Outlines accuracy uses a lenient extraction rule.
- A stricter numeric-string schema and a strict whole-field answer metric should be
  added as separate measurements before a primary study conclusion. Existing results must
  remain preserved under the original schema/scorer for provenance.

### Latency observations

- Free average: approximately 124.3 seconds; median 111.3 seconds; average 84 tokens.
- Prompted average: approximately 112.4 seconds; median 103.7 seconds; average 74.2
  tokens.
- Outlines average: approximately 94.5 seconds; median 98.2 seconds; average 62.2
  tokens.
- Total measured generation latency across the 15 rows was about 27.6 minutes. The
  remaining batch wall time came from environment installation, three separate model
  loads/warmups, and summarization.
- Outlines' lower total latency here should not be interpreted as lower per-token
  overhead because its outputs were shorter on this tiny sample.

### Classification, decision, and evidence

- **Trustworthy smoke experiment, eligible for descriptive interpretation.**
- It is not large enough for a primary study constraint-effect conclusion.
- A direct 20-item FP32 expansion would be expensive. Before spending that quota, test
  stricter answer-field validation and consider a native GPTQ/AWQ model that performs
  stable FP16-compatible inference on T4.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_smoke_v15/`.

## Version 16: intended strict follow-up used stale deployment

### Intended configuration

- Same Qwen2.5-7B FP32, PyTorch 2.6/CUDA 12.4, two-T4 configuration validated in
  versions 14 and 15.
- Same five deterministic GSM8K items and 256-token cap.
- Runs only `outlines_json_reasoning_first` to isolate the schema change and avoid
  repeating unchanged deterministic free/prompted controls.
- New prompt/schema version: `day3-v6-strict-numeric-answer`.
- The answer schema now requires the entire answer string to match a numeric pattern.
- New result fields preserve both lenient and strict prediction/correctness metrics.

### Outcome and observations

- The worker completed five Outlines rows with zero generation exceptions and zero cap
  hits.
- Downloaded rows still recorded prompt version `day2-v5-numeric-answer-field`, not the
  intended `day3-v6-strict-numeric-answer`.
- New fields `answer_field_strict_numeric` and `correct_exact_strict` were absent/null.
- The downloaded summary used the old table without strict-metric columns.
- Raw outputs repeated the same substantive behavior as version 15, including
  `"answer": "}"` and `"answer": "go3"`.
- The apparent result remained 3/5 lenient accuracy and 5/5 old-schema validity, but it
  was not a test of the strict schema.

### Deployment hash audit

- Kaggle's then-latest remote runner hash was
  `b1b7edf916c5fbe3420e9f1a60e6d9526322972ea14e5312317e160169431a89`.
- Local strict runner hash was
  `658f86ce8a922c60fd977d69fc979a0d2565246e1d8ae5d7d6d7e23318604ba4`.
- Kaggle's then-latest remote summarizer hash was
  `68b334b149bbc743676dff8937b388c32ef1f86bca81b794c287fb4d0ebc3394`.
- Local strict summarizer hash was
  `35996fabebe39cd5d326d1596f548ec00426dc218b56d848fa87d005ff47f795`.
- The prior dataset-version command had stopped during upload; querying `ready` had
  only confirmed that the older version remained available.
- A persistent terminal upload subsequently completed successfully and Kaggle returned
  the dataset to `ready`. A post-upload download/hash comparison is still required at
  resume before any new job.

### Classification and evidence

- **Completed deployment diagnostic; invalid as a strict-schema experiment.**
- It must not be interpreted as evidence that strict validation failed.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_outlines_strict_v16/`.

## Resume gate after version 16

- The latest private Kaggle source dataset was downloaded before another GPU job was
  launched.
- The downloaded runner hash matched the strict local runner exactly:
  `658f86ce8a922c60fd977d69fc979a0d2565246e1d8ae5d7d6d7e23318604ba4`.
- The downloaded summarizer hash matched the strict local summarizer exactly:
  `35996fabebe39cd5d326d1596f548ec00426dc218b56d848fa87d005ff47f795`.
- This passed the deployment gate and authorized a new run as version 17. Version 16
  remains classified separately as a stale-deployment diagnostic.

## Version 17: verified strict-numeric FP32 Outlines validation

### Configuration and provenance

- Model artifact: Kaggle model input `qwen-lm/qwen2.5/transformers/7b-instruct/1`
  (Qwen2.5-7B-Instruct).
- One condition: `outlines_json_reasoning_first`.
- First five deterministic GSM8K subset items, seed 0, greedy decoding, and a
  256-token cap.
- Full precision: `dtype=float32`, no 4-bit quantization, and automatic model
  placement across two Tesla T4 GPUs.
- Python 3.12.13, PyTorch `2.6.0+cu124`, CUDA runtime 12.4, Transformers 4.51.3,
  Accelerate 1.6.0, Datasets 3.6.0, Jsonschema 4.23.0, Outlines 1.3.2, and
  Bitsandbytes 0.45.5.
- Prompt/schema version: `day3-v6-strict-numeric-answer`.
- The run manifest itself recorded the verified runner and summarizer hashes above,
  plus dataset hash
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.

### Worker and integrity observations

- Kaggle kernel version 17 reached `COMPLETE` and produced the manifest, one JSONL
  file, JSON and Markdown summaries, and a full log.
- Exactly 5/5 planned rows were present with five unique item IDs.
- There were zero generation errors and zero token-cap hits.
- No punctuation corruption, digit mutation, NaN, CUDA out-of-memory event, or
  truncated response was observed.
- Pip printed conflicts involving unrelated preinstalled Kaggle packages. The runner
  deliberately removed incompatible torchvision/torchaudio packages; the pinned
  inference stack imported and completed all generations. These warnings did not
  cause an observed experiment failure.

### Aggregate observations

- Lenient exact accuracy: 5/5 = 100%.
- Strict whole-answer-field accuracy: 5/5 = 100%.
- Strict numeric answer-field compliance: 5/5 = 100%.
- Whole-response valid JSON: 5/5 = 100%.
- JSON Schema validity: 5/5 = 100%.
- Required field order (`reasoning`, then `answer`): 5/5 = 100%.
- Average generation latency was 95,839.6 ms; median was 100,526.1 ms.
- Average generated length was 61.6 tokens. Individual lengths ranged from 52 to 67
  tokens.

### Per-item observations

#### `gsm8k_test_264`: combined money

- Gold answer: `400`; strict prediction: `400`; strictly correct.
- Output was whole valid JSON with the correct key order and a purely numeric answer
  string.
- Reasoning correctly derived Samantha's 125, Daisy's 175, and the 400 total.
- Generated 52 tokens in 88,895.6 ms; no error and no cap hit.

#### `gsm8k_test_725`: cat/dog average time

- Gold answer: `25`; strict prediction: `25`; strictly correct.
- Output was whole valid JSON with the correct key order and a purely numeric answer
  string.
- Reasoning correctly calculated the dog's 20 minutes and the 25-minute average.
- This repairs version 15/16's malformed `"answer": "}"` behavior on the same item.
- Generated 67 tokens in 102,292.7 ms; no error and no cap hit.

#### `gsm8k_test_996`: children's ages

- Gold answer: `3`; strict prediction: `3`; strictly correct.
- Output was whole valid JSON with the correct key order and a purely numeric answer
  string.
- Reasoning correctly calculated the average age as 5, Helene's age as 10, and
  Wilfred's age as 3.
- This repairs version 15/16's contaminated `"answer": "go3"` value; correctness no
  longer depends on lenient embedded-number extraction.
- Generated 56 tokens in 85,898.1 ms; no error and no cap hit.

#### `gsm8k_test_586`: water after exercise

- Gold answer: `800`; strict prediction: `800`; strictly correct.
- Output was whole valid JSON with the correct key order and a purely numeric answer
  string.
- Reasoning correctly included both aerobics hours: `2*500 + 1*600 = 1600`, then
  converted that to 800 ml. This repairs the earlier Outlines arithmetic omission
  that produced 550.
- Generated 67 tokens in 101,585.7 ms; no error and no cap hit.

#### `gsm8k_test_1010`: track laps

- Gold answer: `5`; strict prediction: `5`; strictly correct.
- Output was whole valid JSON with the correct key order and a purely numeric answer
  string.
- The arithmetic correctly derived Trey 14, Shaelyn 7, Quinn 5, and the difference 5.
- The reasoning contained four short calculation sentences even though the natural-
  language prompt requested one to three. The JSON Schema does not encode that prose
  length rule, so schema validity should not be interpreted as full prompt compliance.
- Generated 66 tokens in 100,526.1 ms; no error and no cap hit.

### Interpretation and decision

- **Trustworthy strict-schema smoke experiment.** Deployment hashes, precision,
  environment, row count, and scoring provenance are all auditable.
- On these same five deterministic items, the strict schema removed both malformed
  answer-field failures and produced 5/5 strict correctness. That is a strong
  engineering validation of the schema change, not a population-level accuracy
  conclusion.
- Because the strict smoke was stable, the planned next step is a 20-item strict
  Outlines expansion. It must still be compared against matching 20-item controls
  before drawing a constraint-effect conclusion.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_outlines_strict_v17/`.

## Version 18: strict-numeric FP32 Outlines 20-item expansion

### Configuration and provenance

- Same audited Qwen2.5-7B-Instruct model artifact, strict runner, dataset, pinned
  PyTorch/CUDA stack, two T4 GPUs, FP32 precision, seed 0, greedy decoding, and
  256-token cap as version 17.
- One condition, `outlines_json_reasoning_first`, expanded from the first 5 to the
  first 20 items of the deterministic GSM8K-50 subset.
- Manifest hashes matched version 17: runner
  `658f86ce8a922c60fd977d69fc979a0d2565246e1d8ae5d7d6d7e23318604ba4`,
  summarizer
  `35996fabebe39cd5d326d1596f548ec00426dc218b56d848fa87d005ff47f795`, and
  dataset
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.

### Integrity, structure, and aggregate observations

- Kernel version 18 reached `COMPLETE` after approximately 39.6 minutes of logged
  wall time and produced all expected evidence files.
- Exactly 20 rows and 20 unique item IDs were present under one run signature.
- There were zero generation errors, zero cap hits, and no punctuation/digit
  corruption.
- Strict numeric answer compliance, whole JSON validity, schema validity, and field
  order were each 20/20 = 100%.
- Official strict accuracy was 13/20 = 65%.
- One official-label failure is a documented internally inconsistent GSM8K item.
  Excluding that item gives data-cleaned accuracy of 13/19 = 68.4%. An alternative
  score that accepts the answer implied by the literal question is 14/20 = 70%.
- Average latency was 102,356.5 ms, median latency 93,778.3 ms, and average length
  66.7 generated tokens. The slowest response was the 163-token candy problem at
  244,552.4 ms; the fastest was the 43-token allowance problem at 67,227.3 ms.
- The first five raw outputs were identical to version 17 despite being generated in
  a new worker. This supports greedy-run repeatability for this audited setup.

### Per-item observations

1. `gsm8k_test_264`: gold `400`, prediction `400`, correct. The model faithfully
   derived 125, 175, and total 400. JSON/numeric/order checks passed; 52 tokens,
   86,266.6 ms.
2. `gsm8k_test_725`: gold `25`, prediction `25`, correct. It derived the dog's 20
   minutes and 25-minute average. All structural checks passed; 67 tokens,
   102,917.4 ms.
3. `gsm8k_test_996`: gold `3`, prediction `3`, correct. It correctly computed average
   age 5, Helene 10, and Wilfred 3. All structural checks passed; 56 tokens,
   86,997.6 ms.
4. `gsm8k_test_586`: gold `800`, prediction `800`, correct. Both aerobics hours were
   included and 1,600 calories converted to 800 ml. All structural checks passed;
   67 tokens, 102,795.6 ms.
5. `gsm8k_test_1010`: gold `5`, prediction `5`, correct. Trey, Shaelyn, Quinn, and the
   final difference were calculated correctly. All structural checks passed; 66
   tokens, 100,959.7 ms. The reasoning again used four sentences despite the prompt's
   one-to-three-sentence request.
6. `gsm8k_test_12`: gold `13`, prediction `15`, incorrect. The model made the basic
   arithmetic error `7 * 1.5 = 9` instead of 10.5, then computed the wrong annual net
   and break-even year. The output remained perfectly schema-compliant; 60 tokens,
   92,068.1 ms.
7. `gsm8k_test_904`: gold `8`, prediction `8`, correct. It computed 27 tickets and
   `216/27=8`. All structural checks passed; 50 tokens, 77,560.5 ms.
8. `gsm8k_test_130`: gold `30`, prediction `30`, correct. It removed one third of 60
   and then another 10. All structural checks passed; 52 tokens, 80,779.4 ms.
9. `gsm8k_test_209`: gold `145`, prediction `16.67`, incorrect. The model confused
   half a dozen plates with a $6,000 total, changed twenty dozen cups into 24 items,
   and mislabeled cups/plates. This is a quantity/unit parsing failure, not a format
   failure; 103 tokens, 155,841.1 ms.
10. `gsm8k_test_244`: gold `20`, prediction `20`, correct. It tracked the fries taken
    by Kyle, Billy, and Colby and solved the remaining difference. All structural
    checks passed; 81 tokens, 123,808.9 ms.
11. `gsm8k_test_237`: gold `90`, prediction `90`, correct. It summed the allowance and
    extra money, then tripled 30. All structural checks passed; 43 tokens, 67,227.3
    ms.
12. `gsm8k_test_689`: gold `7`, prediction `10.4`, incorrect. The model treated $3.20
    as the cost of four candies alone instead of the combined five-lollipop/four-candy
    purchase. All structural checks still passed; 163 tokens, 244,552.4 ms.
13. `gsm8k_test_601`: gold `104`, prediction `104`, correct. It correctly combined
    the initial five games, three years of monthly purchases, and three Christmas
    gifts. All structural checks passed; 70 tokens, 106,097.5 ms.
14. `gsm8k_test_98`: gold `5`, prediction `10`, incorrect. Its first equation was
    incoherent and it failed to account correctly for the 5 exiting cars. This is a
    state/accounting reasoning failure; 50 tokens, 76,433.4 ms.
15. `gsm8k_test_1284`: gold `25`, prediction `25`, correct. It doubled 5 to 10,
    tripled that group to 30, then removed the original 5. All structural checks
    passed; 62 tokens, 95,488.6 ms.
16. `gsm8k_test_1131`: gold `96`, prediction `96`, correct. It calculated usable wood,
    logs, planks, and revenue correctly. All structural checks passed; 66 tokens,
    100,693.1 ms.
17. `gsm8k_test_1272`: gold `296`, prediction `296`, correct. It calculated $240 hotel
    cost and $56 bus cost. All structural checks passed; 76 tokens, 115,541.8 ms.
18. `gsm8k_test_482`: gold `26`, prediction `-26`, incorrect. The reasoning itself
    correctly says `200 - 174 = 26`, but the constrained answer field adds a minus
    sign. This is a reasoning-to-answer semantic consistency failure that numeric JSON
    constraints cannot prevent; 47 tokens, 73,267.3 ms.
19. `gsm8k_test_992`: gold `52`, prediction `60`, incorrect. It treated quarterly as
    twelve times per year instead of four. All structural checks passed; 54 tokens,
    81,808.6 ms.
20. `gsm8k_test_454`: official gold `150`, prediction `240`, officially incorrect.
    The literal question says Marin and Nancy *each* eat four apples per day, which
    implies `2*4*30=240`; the reference solution instead silently uses `4+1` per day.
    This exact inconsistency is independently documented in the official dataset's
    discussion. Treat this as an invalid benchmark row for data-cleaned accuracy, not
    a Qwen arithmetic error. All structural checks passed; 49 tokens, 76,025.9 ms.

### Failure taxonomy and interpretation

- Of the six errors on internally consistent items, five originated in mathematical
  or language reasoning and one (`gsm8k_test_482`) arose when a correct reasoning
  value was converted into an incorrect numeric answer field.
- Strict constrained decoding completely solved the malformed-answer-field problem
  observed in version 15, but it did not and cannot guarantee that a syntactically
  numeric value agrees with the reasoning or gold answer.
- **Trustworthy 20-item constrained cell, suitable for paired comparison once matching
  controls exist.** It is not by itself evidence for or against an accuracy cost.
- Preserved locally at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_outlines_strict_v18/`.

## Version 19: trustworthy v6 control matrix, retained as a prompt probe

### Configuration and artifact acceptance

- Kaggle kernel version 19 completed successfully. Its log ended at 6,283.8 seconds,
  or **104.7 minutes** of worker wall time.
- Model: `Qwen/Qwen2.5-7B-Instruct`; model artifact
  `qwen-lm/qwen2.5/transformers/7b-instruct/1`; FP32; greedy; seed 0; 256-token
  cap; automatic placement over two Tesla T4 GPUs; no quantization.
- Runtime: Python 3.12.13, PyTorch 2.6.0+cu124, CUDA runtime 12.4,
  Transformers 4.51.3, Accelerate 1.6.0, Datasets 3.6.0, Jsonschema 4.23.0,
  and Outlines 1.3.2.
- Conditions: 20 `free`, 20 `prompted_json_reasoning_first`, and 20
  `prompted_json_answer_first` rows. All three cells contain the same ordered 20
  IDs, with no duplicates, generation errors, or cap hits.
- Machine validation passed for the expected conditions, item prefix, prompt
  versions, dataset hash, FP32 dtype, greedy mode, seed, and token cap. The report is
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_controls_v19/artifact_validation.json`.
- Manifest hashes: runner
  `658f86ce8a922c60fd977d69fc979a0d2565246e1d8ae5d7d6d7e23318604ba4`;
  summarizer
  `35996fabebe39cd5d326d1596f548ec00426dc218b56d848fa87d005ff47f795`;
  dataset
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- Kaggle's CLI returned HTTP 403 when asked to pull the immutable private kernel
  source for `/19`, and its dataset-download command exposes only the latest private
  dataset version. The old consumed payload is therefore identified by its manifest
  hashes and fully evidenced by the output/log, but is not duplicated locally as a
  historical source bundle.
- Result hashes: free
  `7ba744c02ebb2e59ec1cc8d93b17841edd0a997d08b3ab17e0ec940395499f65`;
  reasoning-first prompt
  `9a11c451a68d93e4ad5525b6aa96327e303825b2a92cbee4d5e18e6e91f9f48c`;
  answer-first prompt
  `0e2a8a5edb1f4d0b05f0371507f344a0c03026e7874e7a960ea8c2967c338bd5`.

### Aggregate results

The raw 20-item official scores were:

- Free: **11/20 = 55.0%**; every output ended with the requested final-answer
  marker.
- Prompted reasoning-first: 12/20 = 60.0% by lenient numeric recovery, but only
  **2/20 = 10.0% strict**. All 20 responses were valid JSON, but only 4/20 answer
  values were numeric strings satisfying the schema. Sixteen were unquoted JSON
  numbers.
- Prompted answer-first: **3/20 = 15.0% strict**; 20/20 whole JSON, numeric-string
  answer, schema, and key-order compliance.

After the predeclared exclusion of contradictory `gsm8k_test_454` (19 items):

- Free: **11/19 = 57.9%**, Wilson 95% CI 36.3%–76.9%.
- Prompted reasoning-first: **2/19 = 10.5% strict**, CI 2.9%–31.4%; lenient
  recovery was 12/19 = 63.2%; strict schema/numeric compliance was 4/19 = 21.1%.
- Prompted answer-first: **3/19 = 15.8% strict**, CI 5.5%–37.6%; compliance was
  19/19.
- Reasoning-first strict minus free was -47.4 points, paired bootstrap 95% interval
  -73.7 to -21.1, with 1 reasoning-first-only versus 10 free-only strict wins and
  exact McNemar p=0.0117. This is a v6 prompt-format failure contrast, not the final
  estimate of a generic JSON cost.
- Answer-first minus reasoning-first was +5.3 strict points (3 versus 2 discordant
  wins, exact p=1.0), but **-47.4 lenient points** (0 versus 9 discordant wins,
  exact p=0.0039). Strict scoring hides most of the semantic order damage because
  reasoning-first frequently has a correct but non-schema numeric JSON value.
- Clean mean latencies were 123.8 seconds for free, 104.8 seconds for
  reasoning-first, and 69.6 seconds for answer-first. Answer-first outputs averaged
  only 47.1 tokens versus 66.2 reasoning-first and 84.4 free, so this is descriptive
  end-to-end latency rather than backend overhead.

### Prompt and order mechanisms

- The v6 prompt contains a concrete `"answer": "42"` example. The reasoning-first
  model produced a final answer of 42 on three unrelated items (`gsm8k_test_1010`,
  `gsm8k_test_209`, and `gsm8k_test_992`). In each case it also distorted an
  otherwise available calculation toward 42. No free or answer-first output ended in
  42.
- Reasoning-first frequently did the calculation correctly but returned the answer
  as an unquoted JSON number. It therefore achieved high recoverable task accuracy
  while failing the declared string schema. This is exactly why strict and lenient
  outcomes must be reported separately.
- Answer-first perfectly learned the surface schema but often committed an answer
  before reasoning. Several rows contain reasoning that reaches the correct value
  while the already-emitted answer is wrong; one output explicitly says its answer
  field is mistaken. Field order is therefore a semantic intervention, not cosmetic
  serialization.
- Classification: **trustworthy generation and useful prompt/order diagnostic, but
  not the final primary prompt matrix**. v8 was frozen to remove the concrete answer
  while retaining an exact symbolic JSON template.

### Separate item-level observations

1. `gsm8k_test_264`, gold 400: free was correct. Reasoning-first calculated 400 and
   emitted it as an unquoted number, so lenient correct but strict invalid.
   Answer-first said 212 even though its component values 100, 125, and 175 sum to
   400: an arithmetic/answer-commitment error.
2. `gsm8k_test_725`, gold 25: free and reasoning-first both correctly averaged 30 and
   20 to 25; reasoning-first again used an unquoted number. Answer-first emitted 28,
   then its reasoning correctly computed 25, a direct answer–reasoning mismatch.
3. `gsm8k_test_996`, gold 3: free stopped after an unsolved equation and guessed 8.
   Reasoning-first incorrectly assigned all 13 remaining years to Helene and returned
   0. Answer-first correctly found Helene=10 but subtracted `3+4+10` incorrectly,
   returning 6 instead of 3.
4. `gsm8k_test_586`, gold 800: free and reasoning-first were correct, and this was one
   of reasoning-first's two strict successes. Answer-first emitted 420 and then wrote
   the false equality `1600/200*100=420`.
5. `gsm8k_test_1010`, gold 5: free was correct. Reasoning-first's steps found Quinn=5
   and even displayed `10-5`, but changed the result to the prompt's 42. Answer-first
   emitted 26, subsequently derived the correct 5, and explicitly stated that the
   answer field was mistaken.
6. `gsm8k_test_12`, gold 13: free found the 12-year break-even point but missed that
   earning positive money begins in year 13. Reasoning-first made `7*1.5=9`, yielding
   15 years. Answer-first used a chain of inconsistent profit calculations and
   returned 6.
7. `gsm8k_test_904`, gold 8: all three conditions reasoned to 8. Free and answer-first
   were strictly correct; reasoning-first used an unquoted answer and was only
   leniently correct.
8. `gsm8k_test_130`, gold 30: free and reasoning-first correctly removed 20 and then
   10; reasoning-first was non-strict. Answer-first emitted 28 while its own reasoning
   ended at 30.
9. `gsm8k_test_209`, gold 145: all conditions misread the dozen/plate pricing. Free
   returned 11,940. Reasoning-first's quantities became incoherent and converged on
   the prompt's 42. Answer-first returned 25 from unrelated divisions.
10. `gsm8k_test_244`, gold 20: free incorrectly treated Billy as also taking fries
    from Griffin and then mishandled the reverse final-state equation, returning 16.
    Reasoning-first accounted for the stated removals and returned the correct 20 as
    an unquoted number. Answer-first returned 10 from an inconsistent remaining count.
11. `gsm8k_test_237`, gold 90: all three solved the item. Free and answer-first were
    strictly correct; reasoning-first's 90 was unquoted.
12. `gsm8k_test_689`, gold 7: all conditions misread $3.20 as the candy subtotal
    rather than the combined purchase. Free and reasoning-first returned 12;
    answer-first returned 72 after dropping a decimal from 7.28.
13. `gsm8k_test_601`, gold 104: free listed the correct components
    `5+12+24+48+15` but output 105, a reasoning-to-answer arithmetic mismatch.
    Reasoning-first omitted the third year's 48 and returned 56; answer-first also
    omitted it and returned 65 despite reasoning text summing to 56.
14. `gsm8k_test_98`, gold 5: free set up an incorrect traffic-flow equation and
    returned 10. Reasoning-first used `30-20-5=5` and was the other strict success.
    Answer-first returned 15 from a nonsensical signed expression.
15. `gsm8k_test_1284`, gold 25: free and reasoning-first correctly doubled, tripled,
    and removed the original five; reasoning-first was non-strict. Answer-first only
    doubled the third-street group instead of tripling it and returned 15.
16. `gsm8k_test_1131`, gold 96: free and reasoning-first correctly obtained 64 feet,
    16 logs, 80 planks, and $96; reasoning-first was non-strict. Answer-first wrote the
    right multiplicative expression but evaluated it as 624 instead of 96.
17. `gsm8k_test_1272`, gold 296: free and reasoning-first correctly summed $240 hotel
    and $56 bus cost; reasoning-first was non-strict. Answer-first displayed the
    correct expression `3*80+7*8` but evaluated it as 357.
18. `gsm8k_test_482`, gold 26: all three solved `200-(83+91)=26`. Free and
    answer-first were strict successes; reasoning-first used an unquoted answer.
19. `gsm8k_test_992`, gold 52: free listed 12, 12, 24, and 4 checks but output 48,
    omitting the quarterly total at answer conversion. Reasoning-first incorrectly
    treated quarterly as `4*3` and then made its sum equal the prompt's 42.
    Answer-first made the same quarterly mistake and returned 60.
20. `gsm8k_test_454`, official gold 150: every condition returned 240, which follows
    the literal wording `2*4*30`. This is the predeclared contradictory dataset row,
    not a model failure in the cleaned analysis.

Evidence is preserved at `results/qwen2.5-7b/diagnostics/qwen7b_fp32_controls_v19/`, including raw
and cleaned recomputed summaries and the complete per-item matrix.

## Version 20: v8 cross-backend gate; Outlines passed, XGrammar failed

### Configuration and acceptance

- Kernel version 20 completed in 3,025.2 logged seconds (**50.4 minutes**).
- Five paired items under `free`, `prompted_json_reasoning_first`,
  `outlines_json_reasoning_first`, and `xgrammar_json_reasoning_first`; FP32, greedy,
  seed 0, 256-token cap, two T4 GPUs, no quantization.
- The prompt and backend gate criteria were written into
  `docs/methodology.md` while this version was still running and before
  its artifacts were available. Five-item task accuracy was explicitly excluded from
  the technical pass decision.
- Environment matched the trustworthy stack and added XGrammar 0.2.3. Runner hash
  `3de90d4a194a2874142a17d8bfbb25a340b59bc886b4f69fba6455f2172d381d`;
  summarizer hash
  `aa05868b1ac845c21dff6b8f2c9dbc92682ec6530c44244fa7780628bea9cd74`;
  dataset hash
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- All 20 rows had exact paired IDs/settings and zero generation exceptions. The
  validator correctly emitted a warning for one XGrammar token-cap hit.

### Gate result and aggregate observations

- **Outlines passed:** 5/5 whole JSON, strict numeric string, schema, and field order;
  zero errors and zero caps.
- **XGrammar failed the frozen gate:** 4/5 whole JSON/schema/order/numeric compliance
  and one cap. There was no package, compiler, parser-state, or numerical-token error.
- The failure trace identified a configuration mechanism. With
  `any_whitespace=True`, the JSON grammar permitted unlimited legal whitespace before
  the answer value. On `gsm8k_test_264`, Qwen emitted spaces/tabs until all 256 tokens
  were consumed, leaving the object incomplete.
- The protocol permits one debug rerun for an evident integration/configuration
  cause. Version 21 therefore changes only XGrammar's whitespace setting to
  `any_whitespace=False`, records that choice in the run signature/rows, and repeats
  these five items. If it fails, XGrammar is not expanded.
- Prompt-only v8 produced 5/5 parseable whole JSON and 4/5 leniently correct answers,
  but all five answer values were unquoted JSON numbers: 0/5 strict numeric-string
  and schema compliance. Removing the concrete 42 answer eliminated copying on these
  rows but did not make Qwen-7B honor the string type.
- Descriptive task scores were free 4/5, prompt-only 0/5 strict (4/5 lenient),
  Outlines 4/5 strict, and XGrammar 3/5 strict. These n=5 values did not decide the
  gate.
- Mean latency was 122.3 seconds free, 92.6 prompted, 130.7 Outlines, and 153.1
  XGrammar. XGrammar's mean is inflated by the 373.8-second cap row, so it is not a
  clean backend-overhead comparison.

### Separate item-level observations

1. `gsm8k_test_264`, gold 400: free, prompted, and Outlines all reasoned and answered
   400; prompted used an unquoted answer while Outlines supplied the required string.
   XGrammar produced the same correct reasoning, opened the answer field, then emitted
   only legal whitespace to the 256-token cap. This row isolates the whitespace-loop
   completion failure.
2. `gsm8k_test_725`, gold 25: all four conditions correctly averaged 30 and 20 to 25.
   Prompt-only's answer was unquoted; both constrained backends produced valid numeric
   strings. XGrammar inserted several legal spaces/tabs but completed normally.
3. `gsm8k_test_996`, gold 3: every condition was semantically wrong. Free stopped at
   an equation and guessed 8. Prompt and XGrammar used the same flawed equation and
   returned 6. Outlines constructed a different flawed algebraic derivation, reached
   `3W=19`, then incorrectly returned 5. Both constrained outputs were structurally
   valid; grammar did not repair the reasoning.
4. `gsm8k_test_586`, gold 800: all four conditions correctly computed 1,600 calories
   and 800 ml. Prompt-only again used an unquoted number; Outlines and XGrammar were
   fully compliant.
5. `gsm8k_test_1010`, gold 5: all four conditions correctly derived Quinn=5 and the
   five-lap difference. Prompt-only used an unquoted number; both constrained
   backends completed compliant JSON.

Classification: **trustworthy five-item deployment evidence**. It validates v8 and
Outlines for expansion, establishes a concrete prompt-only schema failure, and records
an XGrammar finite-cap failure that requires the single allowed configuration debug.
Evidence is preserved at `results/qwen2.5-7b/diagnostics/qwen7b_fp32_v8_gate_v20/`.

## Version 21: canonical-whitespace XGrammar debug passed

### Configuration and acceptance

- Version 21 changed only XGrammar JSON-schema compilation from unrestricted legal
  whitespace to `any_whitespace=False`. Model, prompt, first five items, FP32 greedy
  decoding, seed, cap, and environment remained fixed.
- The choice is explicit in the manifest and every row as
  `xgrammar_any_whitespace=false`; row run signature `6837154fadf4`.
- Runner hash
  `4091fa2a04838ba19e19e8880cb200c6725a29a4a0eec38eada247998366fb99`;
  summarizer and dataset hashes remained `aa05868...` and `3639f2...` respectively.
- Version 21 completed in 1,008.9 logged seconds (**16.8 minutes**). Artifact
  validation passed with exactly five planned unique rows, zero errors, and zero
  caps. Result hash
  `1c5cad90801258e22b1d4d543b97f9b6264a82fcc72eaac192c6b8ed1282b763`.

### Result and separate observations

- **The debug passed:** 5/5 whole JSON, strict numeric string, schema, and order;
  zero errors/caps. The prior whitespace loop disappeared.
- Descriptive accuracy was 4/5 and mean latency 106.5 seconds. Accuracy was not used
  to pass the gate.
1. `gsm8k_test_264`: correct 400; canonical compact whitespace; 71 tokens.
2. `gsm8k_test_725`: correct 25; canonical compact whitespace; 64 tokens.
3. `gsm8k_test_996`: incorrect 6 from the same flawed equation used by the v8
   prompt-only and permissive-XGrammar cells; structure was fully valid.
4. `gsm8k_test_586`: correct 800; 69 tokens; fully valid.
5. `gsm8k_test_1010`: correct 5; 67 tokens; fully valid.
- Decision: canonical-whitespace XGrammar qualifies for the 50-item expansion. A
  matching 0.5B 50-item cell was also run separately and preserved; configurations
  are never pooled.
- Classification: **trustworthy technical debug and expansion gate**. Evidence is at
  `results/qwen2.5-7b/diagnostics/qwen7b_fp32_v8_xgrammar_debug_v21/`.

## Version 22: final v8 reasoning-first primary matrix

### Configuration and provenance

- Version 22 ran the frozen `day3-v8-symbolic-json-template` primary matrix on all
  50 deterministic items under `free`, `prompted_json_reasoning_first`,
  `outlines_json_reasoning_first`, and `xgrammar_json_reasoning_first`.
- Model artifact: `qwen-lm/qwen2.5/transformers/7b-instruct/1`; FP32; greedy;
  seed 0; 256-token cap; no quantization; automatic placement over two Tesla T4s.
- XGrammar used the gate-approved canonical setting
  `xgrammar_any_whitespace=false`.
- Runtime: Python 3.12.13, PyTorch 2.6.0+cu124, CUDA 12.4,
  Transformers 4.51.3, Accelerate 1.6.0, Datasets 3.6.0,
  Jsonschema 4.23.0, Outlines 1.3.2, and XGrammar 0.2.3.
- Runner hash:
  `4091fa2a04838ba19e19e8880cb200c6725a29a4a0eec38eada247998366fb99`.
  Summarizer hash:
  `aa05868b1ac845c21dff6b8f2c9dbc92682ec6530c44244fa7780628bea9cd74`.
  Dataset hash:
  `3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
- The worker log reached 21,633.3 seconds, or **360.6 minutes (6.01 hours)**.

### Artifact acceptance

- All four files contained exactly 50 rows and 50 unique expected IDs: 200 complete
  generations in total.
- There were zero generation errors, zero cap hits, no duplicate IDs, no missing
  rows, and no precision/token corruption.
- Machine validation passed every manifest, dataset, source, condition, prompt,
  precision, decoding, order, and XGrammar-whitespace check with no warning.
- Result hashes were:
  - free: `84809fd375d9b8c0190b1b9c251c417a82ca15b6e09eced977b0a21f4604bee4`;
  - prompted RF: `c13da158e0080b94d57430e752510714d52656e22b3080231d701d39111996fe`;
  - Outlines RF: `4aeb56ce5f2dba5495b2a84f272dbf2882699ce177797cb542d819856319b297`;
  - XGrammar RF: `ce3fffa0213a1fb88d15b649ce5853298812dcbe9296a382a44aa6be2f9e8789`.

### Aggregate results

Raw official 50-item scores were free 36/50 = 72%, prompted RF 39/50 = 78%
recoverable but 0/50 strict, Outlines RF 30/50 = 60% strict, and XGrammar RF
30/50 = 60% strict. The contradictory `gsm8k_test_454` was wrong under the official
label in every condition, so the predeclared cleaned numerators stayed fixed while
the denominator became 49:

| Condition | Recoverable accuracy | Strict accuracy | Whole JSON | Schema | Order |
|---|---:|---:|---:|---:|---:|
| Free | 36/49 = 73.5% | n/a | n/a | n/a | n/a |
| Prompted RF | 39/49 = 79.6% | 0/49 = 0.0% | 100% | 0% | 100% |
| Outlines RF | 30/49 = 61.2% | 30/49 = 61.2% | 100% | 100% | 100% |
| XGrammar RF | 30/49 = 61.2% | 30/49 = 61.2% | 100% | 100% | 100% |

Every prompted RF response was valid whole JSON in the requested field order, but
all 50 answer values were JSON numbers rather than the required numeric strings.
This is a complete schema/type failure, not a JSON parsing failure. Both constrained
backends enforced every structural and answer-type requirement on every row.

### Paired findings

- Prompted RF minus free recoverable accuracy was +6.1 points, paired interval
  −6.1 to +18.4, with 6 prompt-only and 3 free-only wins; exact p=0.5078. There is no
  detectable semantic JSON-prompt cost for 7B in this cell.
- Outlines RF minus prompted RF recoverable accuracy was **−18.4 points**, paired
  interval −30.6 to −8.2. Prompt-only won all nine discordant items and Outlines won
  none; exact p=0.003906.
- XGrammar RF produced the same **−18.4-point** recoverable effect against the prompt,
  with the same 0 versus 9 discordant-win count and p=0.003906.
- Strict accuracy reverses the operational comparison because prompt-only violated
  the schema on every row: each grammar backend yielded +61.2 strict points versus
  prompt-only. Both semantic and strict views are reported; neither is substituted
  for the other.
- Outlines and XGrammar tied at 30/49 but were not output-identical. They shared 29
  correct and 18 wrong items; Outlines alone was correct on `gsm8k_test_629`, while
  XGrammar alone was correct on `gsm8k_test_506`. Forty-two of 49 strict predictions
  matched and only 20 raw responses were byte-identical. The direct accuracy delta is
  zero with one discordant win each (exact p=1.0).

The fact that neither constrained backend rescued a prompt-only error, while each
changed nine prompt-only correct answers into errors, is evidence of a semantic
generation effect in this setup rather than mere post-generation serialization.
It does not establish that the same effect occurs for other grammars, models, tasks,
or prompts.

### Latency and output length

Clean mean end-to-end generation latency was 127.2 seconds for free, 96.9 seconds
for prompted RF, 99.6 seconds for Outlines RF, and 100.0 seconds for XGrammar RF.
Mean generated lengths were 81.0, 62.9, 61.1, and 63.8 tokens respectively.
Because output lengths and model/offload behavior differ, these measurements do not
isolate grammar-engine overhead. The matched JSON cells are nevertheless close in
observed end-to-end latency on this stack.

### Classification, decision, and evidence

- **Trustworthy final reasoning-first experiment.** It passes the frozen completion
  and interpretation gates and supports a narrow 7B constrained-decoding semantic
  cost conclusion.
- It also demonstrates why whole-JSON validity cannot stand in for schema validity:
  prompt-only was 100% JSON-valid and 0% schema-valid.
- Evidence directory: `results/qwen2.5-7b/primary/reasoning-first/`.
  Aggregate and item-level reports are `summary_clean.md` and `items.md` there.

## Version 23: final v8 answer-order controls

### Configuration and provenance

- Version 23 changed the requested field order to answer first and ran all 50 items
  under `prompted_json_answer_first` and `outlines_json_answer_first`.
- Model artifact, v8 symbolic-template policy, FP32 precision, greedy decoding,
  seed, token cap, hardware, packages, source hashes, and dataset were identical to
  version 22. Only the planned conditions and corresponding field order changed.
- The worker log reached 7,408.2 seconds, or **123.5 minutes (2.06 hours)**.

### Artifact acceptance

- Both files contained exactly 50 rows and 50 expected unique IDs: 100 complete
  generations in total.
- There were zero generation errors, zero token-cap hits, no duplicates, no missing
  rows, and no numerical/token corruption.
- Machine validation passed every invariant with no failure or warning.
- Result hashes were prompted AF
  `ebe28ae7db25d2478a6fd51de0a99454b0f22489c7a9b209e9753225990e3119`
  and Outlines AF
  `03bb9e17f400a27d1e07f70f4b5afc80461ee5404f291729618466af0d3af85f`.

### Aggregate and structural results

The predeclared cleaned analysis contains 49 rows per condition:

| Condition | Recoverable accuracy | Strict accuracy | Whole JSON | Schema | Order |
|---|---:|---:|---:|---:|---:|
| Prompted AF | 11/49 = 22.4% | 8/49 = 16.3% | 98.0% | 65.3% | 98.0% |
| Outlines AF | 8/49 = 16.3% | 8/49 = 16.3% | 100% | 100% | 100% |

Across all 50 prompted AF rows, 32 answers were strings, 17 were JSON numbers, and
one response (`gsm8k_test_1292`) was malformed and unrecoverable. Three correct
recoverable answers were non-strict. Outlines enforced a numeric string, whole JSON,
schema, and field order on every response.

### Field-order findings

- Prompted AF minus prompted RF recoverable accuracy was **−57.1 points**, paired
  interval −71.4 to −40.8. There was one AF-only versus 29 RF-only wins, with 10
  correct under both and 9 wrong under both; exact p=5.77e−8.
- A strict-only comparison misleadingly favors prompted AF by 16.3 points because
  prompted RF violated the string type on all rows. Recoverable accuracy reveals the
  large semantic order cost, which is why both metrics must remain visible.
- Outlines AF minus Outlines RF was **−44.9 strict points**, paired interval −59.2
  to −30.6. There was one AF-only versus 23 RF-only wins, with 7 correct under both
  and 18 wrong under both; exact p=2.98e−6.
- This order effect is larger than the reasoning-first backend effect. In an
  autoregressive model, asking for the answer before the reasoning is a substantive
  intervention: the model must commit to a value before generating the calculation
  that would support it.

### Latency and output length

Prompted AF averaged 72.2 seconds and 49.7 generated tokens; Outlines AF averaged
68.5 seconds and 45.2 tokens. Their lower latency than reasoning-first cells follows
substantially shorter outputs and must not be read as evidence that answer-first is a
better or more efficient reasoning strategy.

### Classification, decision, and evidence

- **Trustworthy final answer-order experiment.** It establishes a large order effect
  in this setup and closes the frozen secondary control.
- The result supports keeping reasoning before the final answer in subsequent work,
  or separating reasoning from constrained serialization into two stages.
- Evidence directory: `results/qwen2.5-7b/primary/answer-first/`.
  The cross-version six-condition summary and per-item matrix are preserved at
  `results/qwen2.5-7b/primary/combined/`.

## Compute accounting through version 23

- The maximum worker timestamp in each of the 11 preserved completed logs sums to
  9,089.5 seconds, or **151.5 minutes (2.525 session-hours)**.
- This is a measured lower bound, not an exact Kaggle-account total: early versions
  1–5, 7, and 10 do not all have preserved local logs, although most failed during
  setup and were short.
- Version 19 added 6,283.8 logged seconds (104.7 minutes). The preserved completed
  total through version 19 is therefore **256.2 minutes, or 4.270 session-hours**.
- Version 20 added 3,025.2 logged seconds (50.4 minutes), bringing the preserved
  completed total through version 20 to **306.6 minutes, or 5.110 session-hours**.
- Version 21 added 1,008.9 logged seconds (16.8 minutes), bringing the preserved
  completed total through version 21 to **323.4 minutes, or 5.390 session-hours**.
- Version 22 added 21,633.3 logged seconds (360.6 minutes).
- Version 23 added 7,408.2 logged seconds (123.5 minutes).
- The preserved completed-log total through version 23 is therefore approximately
  **807.4 minutes, or 13.46 session-hours**. This remains a lower bound because some
  short early failed versions have no preserved local log.
- [Kaggle's GPU guidance](https://www.kaggle.com/docs/efficient-gpu-usage) describes
  allowance as a weekly quota that is commonly around 30 hours, not a monthly quota.
  Kaggle can vary the allowance, and the account UI is the authoritative
  remaining-quota display.

## Rules for any later runs

Every later Kaggle version must receive a separate section containing:

1. Exact model artifact, PyTorch/CUDA/package versions, GPU count, dtype, quantization,
   seed, item count, conditions, and token cap.
2. Worker outcome and file/row completeness.
3. Raw-output observations, including corruption, number fidelity, truncation, and
   protocol behavior.
4. Accuracy and structure metrics with explicit denominators.
5. Latency observations.
6. A classification of `trustworthy experiment`, `useful diagnostic`, or `invalid for
   conclusions`.
7. The decision caused by the run and the local evidence directory.

No diagnostic run will be silently combined with trustworthy results.
