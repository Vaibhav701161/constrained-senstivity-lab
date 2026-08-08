# Canonical schema-equivalence correction summary

The integer treatment is the immutable accepted Llama treatment arm. Both arms are rescored from raw output against the exact canonical external schema.

| Condition | n | Contract-valid correct | Semantic correct | External valid | Internal valid | Errors | Caps | Mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 150 | 61.3% | 61.3% | 100.0% | 100.0% | 0 | 0 | 78.2 |
| treatment | 150 | 54.7% | 54.7% | 99.3% | 99.3% | 0 | 1 | 78.9 |

Treatment-minus-control difference: -6.7% with exact paired bootstrap 95% interval [-12.7%, -0.7%].
Treatment-only wins: 6. Control-only wins: 16. Exact McNemar p: 0.0524788.

Discordant items: 22.
Manual audit complete: true.
