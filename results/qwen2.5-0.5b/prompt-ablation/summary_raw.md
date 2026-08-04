# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Strict accuracy | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 50 | 28.0% | n/a | n/a | n/a | n/a | n/a | n/a | 14.0% | 46.0% | 11237.9 | 12317.4 | 223.1 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 50 | 4.0% | 4.0% | 94.0% | 94.0% | 94.0% | 94.0% | 94.0% | n/a | 2.0% | 4869.4 | 4885.3 | 84.1 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 50 | 16.0% | 16.0% | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 5910.4 | 5236.0 | 94.1 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 50 | 6.0% | 2.0% | 2.0% | 2.0% | 74.0% | 2.0% | 74.0% | n/a | 4.0% | 8211.9 | 7781.5 | 129.9 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 50 | 12.0% | 0.0% | 2.0% | 0.0% | 74.0% | 2.0% | 74.0% | n/a | 2.0% | 5451.8 | 4024.5 | 80.5 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Strict delta | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 50 | -16.0% | -28.0% | 0.039 | 0.000 | 2 | 10 | 0 | 14 | 4 | 34 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 50 | -6.0% | 2.0% | 0.508 | 1.000 | 3 | 6 | 1 | 0 | 0 | 41 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 50 | 4.0% | 16.0% | 0.774 | 0.008 | 7 | 5 | 8 | 0 | 1 | 37 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 50 | -12.0% | -12.0% | 0.031 | 0.031 | 0 | 6 | 0 | 6 | 2 | 42 |
