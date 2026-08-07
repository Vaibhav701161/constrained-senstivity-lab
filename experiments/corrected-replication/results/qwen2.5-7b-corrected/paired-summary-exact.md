# Representation-alignment gate summary

All denominators retain generation errors and token-cap failures.

| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outlines_json_integer_reasoning_first | 49 | 24/49 (49.0%) | 49/49 (100.0%) | 24/49 (49.0%) | 49/49 (100.0%) | 0/49 (0.0%) | 0 | 0 | 79276.4 | 49.3 |
| outlines_json_reasoning_first | 49 | 18/49 (36.7%) | 49/49 (100.0%) | 18/49 (36.7%) | 49/49 (100.0%) | 2/49 (4.1%) | 0 | 0 | 80074.9 | 48.8 |
| xgrammar_json_integer_reasoning_first | 49 | 24/49 (49.0%) | 49/49 (100.0%) | 24/49 (49.0%) | 49/49 (100.0%) | 0/49 (0.0%) | 0 | 0 | 80066.7 | 49.3 |
| xgrammar_json_reasoning_first | 49 | 18/49 (36.7%) | 49/49 (100.0%) | 18/49 (36.7%) | 49/49 (100.0%) | 2/49 (4.1%) | 0 | 0 | 81662.1 | 48.8 |

## Paired comparisons

Positive deltas favor the treatment. The contract-valid metric is the primary product metric.

| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |
|---|---:|---:|---:|---:|---:|---:|---:|
| outlines_integer_vs_signed | 49 | 12.2% ([0.0%, 26.5%]) | 9/3 | 0.145996 | 12.2% ([0.0%, 26.5%]) | 9/3 | 0.145996 |
| xgrammar_integer_vs_signed | 49 | 12.2% ([0.0%, 26.5%]) | 9/3 | 0.145996 | 12.2% ([0.0%, 26.5%]) | 9/3 | 0.145996 |
