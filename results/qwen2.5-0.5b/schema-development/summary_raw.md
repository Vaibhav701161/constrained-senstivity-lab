# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Strict accuracy | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 50 | 28.0% | n/a | n/a | n/a | n/a | n/a | n/a | 14.0% | 46.0% | 11237.9 | 12317.4 | 223.1 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 50 | 6.0% | 6.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 6519.4 | 6450.2 | 112.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 50 | 8.0% | 8.0% | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 3542.5 | 2534.6 | 58.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 50 | 6.0% | 6.0% | 92.0% | 66.0% | 92.0% | 92.0% | 92.0% | n/a | 0.0% | 5021.7 | 4776.4 | 103.0 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 50 | 16.0% | 10.0% | 74.0% | 76.0% | 94.0% | 74.0% | 94.0% | n/a | 0.0% | 4399.0 | 4132.4 | 87.4 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Strict delta | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 50 | -12.0% | -18.0% | 0.146 | 0.022 | 3 | 9 | 2 | 11 | 5 | 33 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 50 | -10.0% | -4.0% | 0.227 | 0.727 | 3 | 8 | 3 | 5 | 0 | 39 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 50 | -8.0% | -2.0% | 0.289 | 1.000 | 2 | 6 | 3 | 4 | 2 | 40 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 50 | -2.0% | -2.0% | 1.000 | 1.000 | 3 | 4 | 3 | 4 | 0 | 43 |
