# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | free | 20 | 25.0% | n/a | n/a | n/a | n/a | 30.0% | 40.0% | 10225.3 | 10762.6 | 217.3 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_json_reasoning_first | 5 | 40.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 5418.8 | 4697.8 | 84.4 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_answer_first | 20 | 5.0% | 65.0% | 95.0% | 55.0% | 95.0% | n/a | 5.0% | 4982.9 | 4572.1 | 105.4 | 0 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_json_reasoning_first | 20 | 20.0% | 50.0% | 80.0% | 55.0% | 80.0% | n/a | 5.0% | 3929.5 | 3147.8 | 83.7 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Treatment-only correct | Control-only correct | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-0.5B-Instruct | json_prompt_cost | 20 | -5.0% | 2 | 3 | 2 | 13 |
| Qwen/Qwen2.5-0.5B-Instruct | prompted_field_order_effect | 20 | -15.0% | 0 | 3 | 1 | 16 |
| Qwen/Qwen2.5-0.5B-Instruct | outlines_constraint_effect | 5 | 20.0% | 2 | 1 | 0 | 2 |
