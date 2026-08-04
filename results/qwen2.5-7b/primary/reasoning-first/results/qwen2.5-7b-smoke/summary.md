# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 50 | 72.0% | [58.3%, 82.5%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 126831.5 | 119551.4 | 80.9 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 50 | 60.0% | [46.2%, 72.4%] | 60.0% | [46.2%, 72.4%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 98912.9 | 99394.2 | 60.7 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 50 | 78.0% | [64.8%, 87.2%] | 0.0% | [0.0%, 7.1%] | 0.0% | 100.0% | 100.0% | 0.0% | 100.0% | n/a | 0.0% | 96219.3 | 93924.6 | 62.4 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_json_reasoning_first | 50 | 60.0% | [46.2%, 72.4%] | 60.0% | [46.2%, 72.4%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 99296.6 | 96088.9 | 63.4 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 50 | 6.0% | [-6.0%, 18.0%] | -72.0% | [-84.0%, -60.0%] | 0.508 | 0.000 | 6 | 3 | 0 | 36 | 33 | 8 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 50 | -18.0% | [-30.0%, -8.0%] | 60.0% | [46.0%, 74.0%] | 0.004 | 0.000 | 0 | 9 | 30 | 0 | 30 | 11 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_constraint_effect | 50 | -18.0% | [-30.0%, -8.0%] | 60.0% | [46.0%, 74.0%] | 0.004 | 0.000 | 0 | 9 | 30 | 0 | 30 | 11 |
