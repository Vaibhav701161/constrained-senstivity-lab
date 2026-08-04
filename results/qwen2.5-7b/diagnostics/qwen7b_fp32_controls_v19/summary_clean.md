# Baseline summary

All accuracy denominators include generation errors. JSON validity metrics are not applicable to the free condition.

| Model | Condition | n | Accuracy | Accuracy 95% CI | Strict accuracy | Strict 95% CI | Numeric answer | Whole JSON | Recoverable | Schema | Order | Final marker | Hit cap | Avg ms | Median ms | Avg tokens | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | free | 19 | 57.9% | [36.3%, 76.9%] | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 100.0% | 0.0% | 123762.5 | 115581.9 | 84.4 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_answer_first | 19 | 15.8% | [5.5%, 37.6%] | 15.8% | [5.5%, 37.6%] | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | n/a | 0.0% | 69608.0 | 60516.4 | 47.1 | 0 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_json_reasoning_first | 19 | 63.2% | [41.0%, 80.9%] | 10.5% | [2.9%, 31.4%] | 21.1% | 100.0% | 100.0% | 21.1% | 100.0% | n/a | 0.0% | 104767.4 | 92739.6 | 66.2 | 0 |

## Paired comparisons

Positive delta favors treatment; negative delta favors control.

| Model | Comparison | Paired n | Delta | Delta 95% CI | Strict delta | Strict delta 95% CI | Exact p | Strict exact p | Treatment-only correct | Control-only correct | Strict treatment-only | Strict control-only | Both correct | Both wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | json_prompt_cost | 19 | 5.3% | [-10.5%, 21.1%] | -47.4% | [-73.7%, -21.1%] | 1.000 | 0.012 | 2 | 1 | 1 | 10 | 10 | 6 |
| /kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1 | prompted_field_order_effect | 19 | -47.4% | [-68.4%, -26.3%] | 5.3% | [-15.8%, 26.3%] | 0.004 | 1.000 | 0 | 9 | 3 | 2 | 3 | 7 |
