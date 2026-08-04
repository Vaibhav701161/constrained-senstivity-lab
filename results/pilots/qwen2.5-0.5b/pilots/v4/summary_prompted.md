# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 20 | 25.0% | n/a | n/a | n/a | n/a | 30.0% | 40.0% | 10225.3 | 10762.6 | 217.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 20 | 5.0% | 85.0% | 95.0% | 95.0% | 95.0% | n/a | 0.0% | 5311.8 | 5039.3 | 111.0 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 20 | 10.0% | 65.0% | 80.0% | 80.0% | 80.0% | n/a | 5.0% | 4613.0 | 3599.1 | 96.0 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 20 | -15.0% | 1 | 4 | 1 | 14 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 20 | -5.0% | 1 | 2 | 0 | 17 |
