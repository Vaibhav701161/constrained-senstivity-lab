# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Avg ms/token | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 50 | 28.0% | [17.5%, 41.7%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 14.0% | 46.0% | 11237.9 | 12317.4 | 223.1 | 50.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_answer_first | 50 | 6.0% | [2.1%, 16.2%] | 6.0% | [2.1%, 16.2%] | 98.0% | 98.0% | 98.0% | 98.0% | 98.0% | n/a | 2.0% | 6332.4 | 6264.5 | 106.8 | 59.8 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 50 | 10.0% | [4.3%, 21.4%] | 10.0% | [4.3%, 21.4%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 2938.1 | 2148.5 | 48.9 | 62.8 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 50 | 4.0% | [1.1%, 13.5%] | 4.0% | [1.1%, 13.5%] | 80.0% | 88.0% | 88.0% | 80.0% | 88.0% | n/a | 2.0% | 5771.2 | 5553.1 | 115.8 | 49.6 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 50 | 8.0% | [3.2%, 18.8%] | 6.0% | [2.1%, 16.2%] | 44.0% | 82.0% | 94.0% | 44.0% | 88.0% | n/a | 0.0% | 3031.3 | 2189.6 | 59.7 | 51.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_json_reasoning_first | 50 | 8.0% | [3.2%, 18.8%] | 8.0% | [3.2%, 18.8%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 2620.0 | 1859.2 | 40.9 | 64.8 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 50 | -20.0% | [-34.0%, -6.0%] | -22.0% | [-36.0%, -8.0%] | 0.0213 | 0.00739 | 3 | 13 | 2 | 13 | 1 | 33 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 50 | -4.0% | [-12.0%, 4.0%] | -2.0% | [-8.0%, 4.0%] | 0.625 | 1 | 1 | 3 | 1 | 2 | 1 | 45 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 50 | 2.0% | [-6.0%, 10.0%] | 4.0% | [-4.0%, 12.0%] | 1 | 0.625 | 3 | 2 | 3 | 1 | 2 | 43 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_field_order_effect | 50 | -4.0% | [-14.0%, 6.0%] | -4.0% | [-14.0%, 6.0%] | 0.688 | 0.688 | 2 | 4 | 2 | 4 | 1 | 43 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_constraint_effect | 50 | 0.0% | [-6.0%, 6.0%] | 2.0% | [0.0%, 6.0%] | 1 | 1 | 1 | 1 | 1 | 0 | 3 | 45 |
| Qwen/Qwen2.5-0.5B-Instruct | xgrammar_vs_outlines | 50 | -2.0% | [-8.0%, 4.0%] | -2.0% | [-10.0%, 4.0%] | 1 | 1 | 1 | 2 | 1 | 2 | 3 | 44 |
