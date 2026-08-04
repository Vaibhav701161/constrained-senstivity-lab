# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 49 | 73.5% | [59.7%, 83.8%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 127153.6 | 121221.8 | 81.0 | 1568.4 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 49 | 61.2% | [47.2%, 73.6%] | 61.2% | [47.2%, 73.6%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 99609.3 | 99750.3 | 61.1 | 1643.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 49 | 79.6% | [66.4%, 88.5%] | 0.0% | [0.0%, 7.3%] | 0.0% | 100.0% | 100.0% | 0.0% | 100.0% | n/a | 0.0% | 96914.9 | 95780.0 | 62.9 | 1541.7 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_json_reasoning_first | 49 | 61.2% | [47.2%, 73.6%] | 61.2% | [47.2%, 73.6%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 100003.7 | 97086.5 | 63.8 | 1573.3 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 49 | 6.1% | [-6.1%, 18.4%] | -73.5% | [-85.7%, -61.2%] | 0.508 | 2.91e-11 | 6 | 3 | 0 | 36 | 33 | 7 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 49 | -18.4% | [-30.6%, -8.2%] | 61.2% | [46.9%, 75.5%] | 0.00391 | 1.86e-09 | 0 | 9 | 30 | 0 | 30 | 10 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_constraint_effect | 49 | -18.4% | [-30.6%, -8.2%] | 61.2% | [46.9%, 75.5%] | 0.00391 | 1.86e-09 | 0 | 9 | 30 | 0 | 30 | 10 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_vs_outlines | 49 | 0.0% | [-6.1%, 6.1%] | 0.0% | [-6.1%, 6.1%] | 1 | 1 | 1 | 1 | 1 | 1 | 29 | 18 |
