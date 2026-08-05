# Representation-alignment gate summary

All denominators retain generation errors and token-cap failures.

| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outlines_json_integer_reasoning_first | 18 | 13/18 (72.2%) | 18/18 (100.0%) | 13/18 (72.2%) | 18/18 (100.0%) | 0/18 (0.0%) | 0 | 0 | 110502.8 | 74.3 |
| prompted_json_integer_reasoning_first | 18 | 13/18 (72.2%) | 18/18 (100.0%) | 13/18 (72.2%) | 18/18 (100.0%) | 0/18 (0.0%) | 0 | 0 | 114882.5 | 78.2 |
| xgrammar_json_integer_reasoning_first | 18 | 13/18 (72.2%) | 18/18 (100.0%) | 13/18 (72.2%) | 18/18 (100.0%) | 0/18 (0.0%) | 0 | 0 | 114302.3 | 78.2 |
| xgrammar_json_unsigned_numeric_string_reasoning_first | 18 | 13/18 (72.2%) | 18/18 (100.0%) | 13/18 (72.2%) | 18/18 (100.0%) | 0/18 (0.0%) | 0 | 0 | 105532.1 | 72.2 |

## Paired comparisons

Positive deltas favor the treatment. The contract-valid metric is the primary product metric.

| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |
|---|---:|---:|---:|---:|---:|---:|---:|
