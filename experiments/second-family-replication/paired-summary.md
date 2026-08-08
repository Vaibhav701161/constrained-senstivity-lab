# Second-family paired summary

Generation errors, token-cap hits, invalid objects, and transduction failures remain in every denominator.
Latency is descriptive and is not an inferential endpoint.

## Fresh set

| Condition | n | Contract-valid correct | Semantic correct | External valid | Internal valid | Errors | Cap hits | Mean tokens | Mean latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 150 | 61.3% | 61.3% | 100.0% | 100.0% | 0 | 0 | 79.2 | 4698.2 |
| treatment | 150 | 54.7% | 54.7% | 99.3% | 99.3% | 0 | 1 | 78.9 | 4727.3 |

Primary paired difference: -6.7% with exact paired bootstrap 95% interval [-12.7%, -1.3%].
Treatment-only wins: 5. Control-only wins: 15. Exact McNemar p: 0.0413895.

## Bridge set

| Condition | n | Contract-valid correct | Semantic correct | External valid | Internal valid | Errors | Cap hits | Mean tokens | Mean latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 49 | 42.9% | 42.9% | 100.0% | 100.0% | 0 | 0 | 77.6 | 4733.7 |
| treatment | 49 | 40.8% | 40.8% | 100.0% | 100.0% | 0 | 0 | 77.8 | 4529.8 |

Primary paired difference: -2.0% with exact paired bootstrap 95% interval [-10.2%, 6.1%].
Treatment-only wins: 2. Control-only wins: 3. Exact McNemar p: 1.

## Discordant-item audit

Total discordant items requiring manual attribution: 25.
Manual audit complete: true.
