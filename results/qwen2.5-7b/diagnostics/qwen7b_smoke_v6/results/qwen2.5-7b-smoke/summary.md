# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-7B-Instruct | free | 5 | 0.0% | n/a | n/a | n/a | n/a | 0.0% | 60.0% | 10962.6 | 13527.2 | 203.6 | 0 |
| Qwen/Qwen2.5-7B-Instruct | outlines_json_reasoning_first | 5 | 20.0% | 80.0% | 80.0% | 80.0% | 80.0% | n/a | 0.0% | 9206.3 | 5441.5 | 92.8 | 0 |
| Qwen/Qwen2.5-7B-Instruct | prompted_json_reasoning_first | 5 | 0.0% | 40.0% | 40.0% | 0.0% | 0.0% | n/a | 40.0% | 11913.1 | 14125.6 | 201.8 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-7B-Instruct | json_prompt_cost | 5 | 0.0% | 0 | 0 | 0 | 5 |
| Qwen/Qwen2.5-7B-Instruct | outlines_constraint_effect | 5 | 20.0% | 1 | 0 | 0 | 4 |
