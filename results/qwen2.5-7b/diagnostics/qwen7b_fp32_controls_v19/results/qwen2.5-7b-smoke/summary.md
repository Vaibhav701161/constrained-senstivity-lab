# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Strict accuracy | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 20 | 55.0% | n/a | n/a | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 122985.4 | 113196.7 | 83.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_answer_first | 20 | 15.0% | 15.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 68834.7 | 58861.6 | 46.5 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 20 | 60.0% | 10.0% | 20.0% | 100.0% | 100.0% | 20.0% | 100.0% | n/a | 0.0% | 103423.4 | 89909.7 | 65.3 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 20 | 5.0% | 2 | 1 | 10 | 7 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_field_order_effect | 20 | -45.0% | 0 | 9 | 3 | 8 |
