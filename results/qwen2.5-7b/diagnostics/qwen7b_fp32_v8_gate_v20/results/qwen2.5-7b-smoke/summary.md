# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 5 | 80.0% | [37.6%, 96.4%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 122306.3 | 111558.0 | 84.0 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 5 | 80.0% | [37.6%, 96.4%] | 80.0% | [37.6%, 96.4%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 130657.2 | 101312.3 | 85.4 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 5 | 80.0% | [37.6%, 96.4%] | 0.0% | [0.0%, 43.4%] | 0.0% | 100.0% | 100.0% | 0.0% | 100.0% | n/a | 0.0% | 92628.8 | 96444.0 | 63.6 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_json_reasoning_first | 5 | 60.0% | [23.1%, 88.2%] | 60.0% | [23.1%, 88.2%] | 80.0% | 80.0% | 80.0% | 80.0% | 80.0% | n/a | 20.0% | 153147.8 | 104134.7 | 104.6 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 5 | 0.0% | [0.0%, 0.0%] | -80.0% | [-100.0%, -40.0%] | 1.000 | 0.125 | 0 | 0 | 0 | 4 | 4 | 1 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 5 | 0.0% | [0.0%, 0.0%] | 80.0% | [40.0%, 100.0%] | 1.000 | 0.125 | 0 | 0 | 4 | 0 | 4 | 1 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | xgrammar_constraint_effect | 5 | -20.0% | [-60.0%, 0.0%] | 60.0% | [20.0%, 100.0%] | 1.000 | 0.250 | 0 | 1 | 3 | 0 | 3 | 1 |
