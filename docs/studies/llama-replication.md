---
title: Llama second-family replication
description: Preregistered cross-family replication on 150 previously unseen GSM8K items
---

# Llama second-family replication

<div class="csl-study-header">
  <div class="csl-study-header__item"><span>Model</span><strong>Llama 3.2 3B Instruct</strong></div>
  <div class="csl-study-header__item"><span>Fresh holdout</span><strong>150 unseen items</strong></div>
  <div class="csl-study-header__item"><span>Backend</span><strong>XGrammar 0.2.3</strong></div>
  <div class="csl-study-header__item"><span>Initial decision</span><strong>Red</strong></div>
</div>

## Confirmatory question

Does the signed-string to internal-integer improvement survive on a non-Qwen model
and 150 previously unseen GSM8K items?

## Frozen design

| Component | Specification |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Primary data | 150 randomly selected, repository-unseen GSM8K test items |
| Bridge data | Existing cleaned 49-item Qwen set |
| Backend | XGrammar 0.2.3 |
| Decoding | Greedy, seed 0, FP32, 256 maximum new tokens |
| Primary outcome | Paired difference in contract-valid correctness |
| Failure policy | Errors, cap hits, invalid objects, and transduction failures remain failures |

One shared runtime handled model loading, tokenization, chat formatting, generation,
visible-token counting, latency, manifests, and errors. Only the model-facing schema,
prompted representation, and inverse-transduction step differed.

## Initial result

| Dataset | String control | Integer treatment | Difference | Wins : losses |
|---|---:|---:|---:|---:|
| Fresh holdout, n=150 | 92/150 (61.3%) | 82/150 (54.7%) | -6.7 pp | 5 : 15 |
| Bridge set, n=49 | 21/49 (42.9%) | 20/49 (40.8%) | -2.0 pp | 2 : 3 |

The fresh result reached the preregistered Red gate. The treatment also retained one
token-cap failure in the denominator. A post-result Outlines parity check generated
only the predeclared discordant and random concordant subset; its 80 outputs matched
XGrammar byte for byte.

## Schema mismatch discovered during review

The control allowed a broader numeric-string language than the compiler could
transform. It accepted decimals, fractions, comma grouping, and leading zeros,
whereas the transformation proved equivalence only for canonical signed integers.

That was a legitimate experimental mismatch. It required one bounded correction,
not an attempt to tune the result. The [canonical correction](canonical-correction.md)
therefore replaced only the control arm and reused the immutable treatment.

## Primary records

- [Preregistered protocol](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/second-family-replication/protocol.md)
- [Unseen-set manifest](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/data/gsm8k_unseen_150_seed20260815.manifest.json)
- [Paired summary](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/second-family-replication/paired-summary.md)
- [Decision report](https://github.com/Vaibhav701161/constrained-senstivity-lab/blob/master/experiments/second-family-replication/decision-report.md)
