# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_answer_first | 49 | 16.3% | [8.5%, 29.0%] | 16.3% | [8.5%, 29.0%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 68508.0 | 65590.1 | 45.2 | 1526.3 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_answer_first | 49 | 22.4% | [13.0%, 35.9%] | 16.3% | [8.5%, 29.0%] | 65.3% | 98.0% | 98.0% | 65.3% | 98.0% | n/a | 0.0% | 72200.7 | 69928.8 | 49.7 | 1456.3 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
