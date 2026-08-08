# Second-Family Replication Hypothesis

## Confirmatory hypothesis

On 150 randomly selected, previously unseen GSM8K test items, under greedy FP32
generation with `meta-llama/Llama-3.2-3B-Instruct` and XGrammar 0.2.3, replacing a
model-facing signed numeric string with a native JSON integer followed by
deterministic stringification will improve final external-contract-valid correctness.

## Primary estimand

The primary estimand is the paired percentage-point difference in contract-valid
correctness on the fresh 150-item holdout:

```text
integer treatment minus signed-string control
```

The existing cleaned 49-item Qwen set is a bridge set. It does not carry the
confirmatory claim.

## Mechanistic hypothesis

The two representations expose different legal token paths while preserving the
same final external contract. The integer grammar does not prohibit negative values.
Any effect must therefore be interpreted as representation-sensitive generation,
not as automatic sign correction.

## Falsification conditions

The cross-family hypothesis is not supported if the fresh-set estimate is zero or
negative, control-only wins equal or exceed treatment-only wins, final external
validity falls below 100%, or the treatment creates a coherent new failure mode.

All errors, cap hits, invalid objects, transduction failures, and reasoning-inconsistent
answers remain visible. No post-output item exclusion or prompt search is permitted.
