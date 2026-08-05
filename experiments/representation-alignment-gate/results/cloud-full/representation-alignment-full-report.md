# Representation-Alignment Gate Report

## Scope

This is the `full` stage of the preregistered representation-alignment gate. It tests a native internal integer followed by deterministic stringification against the frozen signed-numeric-string baseline.

## Artifact acceptance

- Independent artifact validation: `True`.
- Validation warnings: none.
- Targeted suite: 18 items, mechanically derived from frozen rows.
- Baseline shared losses: 8 items: `gsm8k_test_1216`, `gsm8k_test_173`, `gsm8k_test_183`, `gsm8k_test_244`, `gsm8k_test_482`, `gsm8k_test_694`, `gsm8k_test_712`, `gsm8k_test_739`.

## Result table

| Condition | Semantic correctness | Contract-valid correctness | Final external validity |
|---|---:|---:|---:|
| outlines_json_integer_reasoning_first | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) |
| outlines_json_reasoning_first | 30/49 (61.2%) | 30/49 (61.2%) | 49/49 (100.0%) |
| prompted_json_integer_reasoning_first | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) |
| prompted_json_reasoning_first | 39/49 (79.6%) | 0/49 (0.0%) | 0/49 (0.0%) |
| xgrammar_json_integer_reasoning_first | 37/49 (75.5%) | 37/49 (75.5%) | 49/49 (100.0%) |
| xgrammar_json_reasoning_first | 30/49 (61.2%) | 30/49 (61.2%) | 49/49 (100.0%) |

## Shared-loss repair check

- Outlines integer repaired 7/8 available shared losses: ['gsm8k_test_173', 'gsm8k_test_183', 'gsm8k_test_244', 'gsm8k_test_482', 'gsm8k_test_694', 'gsm8k_test_712', 'gsm8k_test_739'].
- Outlines integer external-invalid rows: none.
- XGrammar integer repaired 8/8 available shared losses: ['gsm8k_test_1216', 'gsm8k_test_173', 'gsm8k_test_183', 'gsm8k_test_244', 'gsm8k_test_482', 'gsm8k_test_694', 'gsm8k_test_712', 'gsm8k_test_739'].
- XGrammar integer external-invalid rows: none.

## Boundary traces

- `gsm8k_test_12`: selected boundary tokens [' ', '1'].
- `gsm8k_test_1216`: selected boundary tokens [' ', '2'].
- `gsm8k_test_173`: selected boundary tokens [' ', '1'].

## Preregistered decision

Use the paired full-set comparisons in the summary to apply the preregistered green, yellow, or red rule.

The report does not generalize beyond the declared model, prompt, schema, greedy decoding, precision, backend versions, and evaluated items.
