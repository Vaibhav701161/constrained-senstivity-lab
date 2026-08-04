# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 5 | 0.0% | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 5933.6 | 5299.7 | 78.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 5 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 7289.0 | 7358.7 | 75.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 5 | 0.0% | 100.0% | 100.0% | 60.0% | 100.0% | n/a | 0.0% | 6196.0 | 6541.8 | 80.6 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 5 | 0.0% | 0 | 0 | 0 | 5 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 5 | 0.0% | 0 | 0 | 0 | 5 |
