# Representation-alignment gate summary

All denominators retain generation errors and token-cap failures.

| Condition | n | Semantic correctness | External validity | Contract-valid correctness | Internal validity | Negative answers | Errors | Cap hits | Avg latency ms | Avg tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| outlines_json_integer_reasoning_first | 49 | 37/49 (75.5%) | 49/49 (100.0%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) | 0 | 0 | 93431.6 | 60.7 |
| outlines_json_reasoning_first | 49 | 30/49 (61.2%) | 49/49 (100.0%) | 30/49 (61.2%) | 49/49 (100.0%) | 12/49 (24.5%) | 0 | 0 | 99609.3 | 61.1 |
| prompted_json_integer_reasoning_first | 49 | 37/49 (75.5%) | 49/49 (100.0%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) | 0 | 0 | 90962.4 | 63.2 |
| prompted_json_reasoning_first | 49 | 39/49 (79.6%) | 0/49 (0.0%) | 0/49 (0.0%) | 0/49 (0.0%) | 1/49 (2.0%) | 0 | 0 | 96914.9 | 62.9 |
| xgrammar_json_integer_reasoning_first | 49 | 37/49 (75.5%) | 49/49 (100.0%) | 37/49 (75.5%) | 49/49 (100.0%) | 0/49 (0.0%) | 0 | 0 | 93355.3 | 63.2 |
| xgrammar_json_reasoning_first | 49 | 30/49 (61.2%) | 49/49 (100.0%) | 30/49 (61.2%) | 49/49 (100.0%) | 12/49 (24.5%) | 0 | 0 | 100003.7 | 63.8 |

## Paired comparisons

Positive deltas favor the treatment. The contract-valid metric is the primary product metric.

| Comparison | Paired n | Semantic delta (95% CI) | Semantic treatment-only/control-only | Semantic exact p | Contract-valid delta (95% CI) | Contract-valid treatment-only/control-only | Contract-valid exact p |
|---|---:|---:|---:|---:|---:|---:|---:|
| prompted_integer_vs_signed | 49 | -4.1% ([-12.2%, 4.1%]) | 1/3 | 0.625 | 75.5% ([63.3%, 85.7%]) | 37/0 | 1.45519e-11 |
| outlines_integer_vs_signed | 49 | 14.3% ([4.1%, 26.5%]) | 8/1 | 0.0390625 | 14.3% ([4.1%, 26.5%]) | 8/1 | 0.0390625 |
| xgrammar_integer_vs_signed | 49 | 14.3% ([0.0%, 28.6%]) | 10/3 | 0.0922852 | 14.3% ([0.0%, 28.6%]) | 10/3 | 0.0922852 |
| outlines_integer_vs_prompted_integer | 49 | 0.0% ([-10.2%, 10.2%]) | 3/3 | 1 | 0.0% ([-10.2%, 10.2%]) | 3/3 | 1 |
| xgrammar_integer_vs_prompted_integer | 49 | 0.0% ([0.0%, 0.0%]) | 0/0 | 1 | 0.0% ([0.0%, 0.0%]) | 0/0 | 1 |
