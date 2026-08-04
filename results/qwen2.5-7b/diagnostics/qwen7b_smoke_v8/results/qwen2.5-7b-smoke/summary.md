# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 5 | 0.0% | n/a | n/a | n/a | n/a | 0.0% | 60.0% | 10800.3 | 13240.5 | 200.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_json_reasoning_first | 5 | 20.0% | 80.0% | 80.0% | 80.0% | 80.0% | n/a | 0.0% | 7503.4 | 4583.4 | 92.8 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 5 | 0.0% | 40.0% | 40.0% | 0.0% | 0.0% | n/a | 40.0% | 11027.0 | 13349.3 | 201.8 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 5 | 0.0% | 0 | 0 | 0 | 5 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | outlines_constraint_effect | 5 | 20.0% | 1 | 0 | 0 | 4 |
