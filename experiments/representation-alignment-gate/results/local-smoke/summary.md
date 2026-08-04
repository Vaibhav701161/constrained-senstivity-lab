# Representation-alignment gate summary

All denominators retain generation errors and token-cap failures.

| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outlines_json_integer_reasoning_first | 5 | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0 | 0 | 2917.7 | 31.8 |
| outlines_json_unsigned_numeric_string_reasoning_first | 5 | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0 | 0 | 1863.3 | 28.6 |
| prompted_json_integer_reasoning_first | 5 | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0 | 0 | 1536.7 | 28.6 |
| xgrammar_json_integer_reasoning_first | 5 | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0 | 0 | 1545.7 | 28.6 |
| xgrammar_json_unsigned_numeric_string_reasoning_first | 5 | 1/5 (20.0%) | 5/5 (100.0%) | 1/5 (20.0%) | 5/5 (100.0%) | 0/5 (0.0%) | 0 | 0 | 1157.9 | 25.2 |

## Paired comparisons

Positive deltas favor the treatment. The contract-valid metric is the primary product metric.

| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |
|---|---:|---:|---:|---:|---:|---:|---:|
