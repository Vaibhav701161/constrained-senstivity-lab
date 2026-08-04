# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Strict accuracy | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 49 | 28.6% | n/a | n/a | n/a | n/a | n/a | n/a | 12.2% | 46.9% | 11288.3 | 12340.7 | 223.9 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 49 | 6.1% | 6.1% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 6534.5 | 6546.3 | 112.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 49 | 8.2% | 8.2% | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 3532.0 | 2519.0 | 58.1 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 49 | 6.1% | 6.1% | 91.8% | 65.3% | 91.8% | 91.8% | 91.8% | n/a | 0.0% | 5004.2 | 4710.2 | 102.8 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 49 | 16.3% | 10.2% | 73.5% | 75.5% | 93.9% | 73.5% | 93.9% | n/a | 0.0% | 4407.7 | 4295.1 | 87.5 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Strict delta | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 49 | -12.2% | -18.4% | 0.146 | 0.022 | 3 | 9 | 2 | 11 | 5 | 32 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 49 | -10.2% | -4.1% | 0.227 | 0.727 | 3 | 8 | 3 | 5 | 0 | 38 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 49 | -8.2% | -2.0% | 0.289 | 1.000 | 2 | 6 | 3 | 4 | 2 | 39 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 49 | -2.0% | -2.0% | 1.000 | 1.000 | 3 | 4 | 3 | 4 | 0 | 42 |
