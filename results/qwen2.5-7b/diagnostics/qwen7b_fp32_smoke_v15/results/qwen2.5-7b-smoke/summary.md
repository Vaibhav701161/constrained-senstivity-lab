# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 5 | 80.0% | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 124254.9 | 111326.8 | 84.0 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 5 | 60.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 94523.1 | 98182.0 | 62.2 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 5 | 80.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 112423.1 | 103686.6 | 74.2 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 5 | 0.0% | 0 | 0 | 4 | 1 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 5 | -20.0% | 1 | 2 | 2 | 0 |
