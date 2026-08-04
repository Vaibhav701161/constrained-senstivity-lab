# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 49 | 28.6% | [17.8%, 42.4%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 12.2% | 46.9% | 11288.3 | 12340.7 | 223.9 | 50.4 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 49 | 6.1% | [2.1%, 16.5%] | 6.1% | [2.1%, 16.5%] | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 6372.3 | 6300.1 | 107.5 | 59.8 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 49 | 10.2% | [4.4%, 21.8%] | 10.2% | [4.4%, 21.8%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 2938.3 | 2134.9 | 48.9 | 62.9 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 49 | 4.1% | [1.1%, 13.7%] | 4.1% | [1.1%, 13.7%] | 79.6% | 87.8% | 87.8% | 79.6% | 87.8% | n/a | 2.0% | 5837.2 | 5585.3 | 117.1 | 49.6 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 49 | 8.2% | [3.2%, 19.2%] | 6.1% | [2.1%, 16.5%] | 42.9% | 81.6% | 93.9% | 42.9% | 87.8% | n/a | 0.0% | 3062.2 | 2197.6 | 60.4 | 51.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_json_reasoning_first | 49 | 8.2% | [3.2%, 19.2%] | 8.2% | [3.2%, 19.2%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 2634.2 | 1856.3 | 41.2 | 64.8 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 49 | -20.4% | [-34.7%, -6.1%] | -22.4% | [-36.7%, -8.2%] | 0.0213 | 0.00739 | 3 | 13 | 2 | 13 | 1 | 32 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 49 | -4.1% | [-12.2%, 4.1%] | -2.0% | [-8.2%, 4.1%] | 0.625 | 1 | 1 | 3 | 1 | 2 | 1 | 44 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 49 | 2.0% | [-6.1%, 10.2%] | 4.1% | [-4.1%, 12.2%] | 1 | 0.625 | 3 | 2 | 3 | 1 | 2 | 42 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 49 | -4.1% | [-14.3%, 6.1%] | -4.1% | [-14.3%, 6.1%] | 0.688 | 0.688 | 2 | 4 | 2 | 4 | 1 | 42 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_constraint_effect | 49 | 0.0% | [-6.1%, 6.1%] | 2.0% | [0.0%, 6.1%] | 1 | 1 | 1 | 1 | 1 | 0 | 3 | 44 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_vs_outlines | 49 | -2.0% | [-8.2%, 4.1%] | -2.0% | [-8.2%, 4.1%] | 1 | 1 | 1 | 2 | 1 | 2 | 3 | 43 |
