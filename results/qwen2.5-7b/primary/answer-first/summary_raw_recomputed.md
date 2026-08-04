# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_answer_first | 50 | 16.0% | [8.3%, 28.5%] | 16.0% | [8.3%, 28.5%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 68016.5 | 65162.2 | 44.9 | 1527.1 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_answer_first | 50 | 22.0% | [12.8%, 35.2%] | 16.0% | [8.3%, 28.5%] | 64.0% | 98.0% | 98.0% | 64.0% | 98.0% | n/a | 0.0% | 71604.6 | 68515.9 | 49.3 | 1456.4 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
