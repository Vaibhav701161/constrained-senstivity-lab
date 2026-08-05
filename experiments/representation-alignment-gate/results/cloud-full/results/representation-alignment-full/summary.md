# Representation-alignment gate summary

All denominators retain generation errors and token-cap failures.

| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outlines_json_integer_reasoning_first | 50 | 37/50 (74.0%) | 50/50 (100.0%) | 37/50 (74.0%) | 50/50 (100.0%) | 0/50 (0.0%) | 0 | 0 | 92835.4 | 60.3 |
| prompted_json_integer_reasoning_first | 50 | 37/50 (74.0%) | 50/50 (100.0%) | 37/50 (74.0%) | 50/50 (100.0%) | 0/50 (0.0%) | 0 | 0 | 90322.9 | 62.8 |
| xgrammar_json_integer_reasoning_first | 50 | 37/50 (74.0%) | 50/50 (100.0%) | 37/50 (74.0%) | 50/50 (100.0%) | 0/50 (0.0%) | 0 | 0 | 92697.3 | 62.8 |

## Paired comparisons

Positive deltas favor the treatment. The contract-valid metric is the primary product metric.

| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |
|---|---:|---:|---:|---:|---:|---:|---:|
