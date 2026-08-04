# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_json_reasoning_first | 5 | 80.0% | [37.6%, 96.4%] | 80.0% | [37.6%, 96.4%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 106517.5 | 110999.6 | 64.6 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
