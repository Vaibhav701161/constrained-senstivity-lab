# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Strict accuracy | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 49 | 28.6% | n/a | n/a | n/a | n/a | n/a | n/a | 12.2% | 46.9% | 11288.3 | 12340.7 | 223.9 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 49 | 4.1% | 4.1% | 93.9% | 93.9% | 93.9% | 93.9% | 93.9% | n/a | 2.0% | 4887.8 | 4925.4 | 84.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 49 | 16.3% | 16.3% | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 5957.6 | 5289.6 | 94.9 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 49 | 6.1% | 2.0% | 2.0% | 2.0% | 73.5% | 2.0% | 73.5% | n/a | 4.1% | 8260.3 | 7840.8 | 130.7 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 49 | 12.2% | 0.0% | 2.0% | 0.0% | 73.5% | 2.0% | 73.5% | n/a | 2.0% | 5493.5 | 4084.6 | 81.0 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Strict delta | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 49 | -16.3% | -28.6% | 0.039 | 0.000 | 2 | 10 | 0 | 14 | 4 | 33 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 49 | -6.1% | 2.0% | 0.508 | 1.000 | 3 | 6 | 1 | 0 | 0 | 40 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 49 | 4.1% | 16.3% | 0.774 | 0.008 | 7 | 5 | 8 | 0 | 1 | 36 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 49 | -12.2% | -12.2% | 0.031 | 0.031 | 0 | 6 | 0 | 6 | 2 | 41 |
