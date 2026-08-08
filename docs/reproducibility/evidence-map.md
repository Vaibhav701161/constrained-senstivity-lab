# Evidence map

Every principal claim should resolve to a protocol, raw output, analysis, validation
report, and decision. The links below point to the public GitHub record when the
artifact lives outside the documentation source tree.

## Baseline matrix

| Layer | Record |
|---|---|
| Protocol | [Methodology](../methodology.md) |
| Accepted summaries | [Qwen2.5 7B combined results](https://github.com/Vaibhav701161/constrained-decoding-lab/tree/master/results/qwen2.5-7b/primary/combined) |
| Execution ledger | [Qwen2.5 7B ledger](../run-ledgers/qwen2.5-7b.md) |
| Interpretation | [Research report](../research-report.md) |
| Public cloud record | [Kaggle notebook](https://www.kaggle.com/code/vaibhav7011/constrained-decoding-qwen7b-evaluation) |

## Representation alignment and corrected Qwen replication

| Layer | Record |
|---|---|
| Historical alignment analysis | [Representation-alignment results](../representation-alignment-results.md) |
| Corrected protocol | [Protocol](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/protocol.md) |
| Corrected validation | [Artifact validation](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/artifact-validation.json) |
| Corrected paired result | [Exact summary](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/paired-summary-exact.md) |
| Architecture decision | [Decision report](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/corrected-replication/results/qwen2.5-7b-corrected/decision-report.md) |

## Second-family replication

| Layer | Record |
|---|---|
| Hypothesis | [HYPOTHESIS.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/HYPOTHESIS.md) |
| Protocol | [protocol.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/protocol.md) |
| Dataset manifest | [dataset-manifest.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/dataset-manifest.json) |
| Source manifest | [source-manifest.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/source-manifest.json) |
| Raw results | [results/](https://github.com/Vaibhav701161/constrained-decoding-lab/tree/master/experiments/second-family-replication/results) |
| Artifact validation | [artifact-validation.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/artifact-validation.json) |
| Paired summary | [paired-summary.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/paired-summary.md) |
| Complete audit | [failure-attribution.jsonl](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/failure-attribution.jsonl) |
| Decision | [decision-report.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/second-family-replication/decision-report.md) |

## Canonical schema correction

| Layer | Record |
|---|---|
| Mismatch audit | [mismatch-audit.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/mismatch-audit.json) |
| Preregistered protocol | [protocol.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/protocol.md) |
| Source manifest | [source-manifest.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/source-manifest.json) |
| Raw control | [result JSONL](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/results/xgrammar_json_canonical_integer_string_reasoning_first.jsonl) |
| Artifact validation | [artifact-validation.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/artifact-validation.json) |
| Paired summary | [paired-summary.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/paired-summary.md) |
| Complete audit | [failure-attribution.jsonl](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/failure-attribution.jsonl) |
| Decision | [decision-report.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/canonical-schema-equivalence-correction/decision-report.md) |

## Executable pilot

| Layer | Record |
|---|---|
| Pinned foundation | [FOUNDATION.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/FOUNDATION.md) |
| Protocol | [protocol.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/protocol.md) |
| Raw results | [results/](https://github.com/Vaibhav701161/constrained-decoding-lab/tree/master/experiments/tool-call-gate/results) |
| Artifact validation | [artifact-validation.json](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/artifact-validation.json) |
| Paired summary | [paired-summary.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/paired-summary.md) |
| Discordance audit | [failure-attribution.jsonl](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/failure-attribution.jsonl) |
| Decision | [decision-report.md](https://github.com/Vaibhav701161/constrained-decoding-lab/blob/master/experiments/tool-call-gate/decision-report.md) |

## Integrity controls

- Dataset selection records full excluded-ID sets and hashes.
- Run manifests bind model revision, tokenizer revision, environment, and signature.
- Canary gates check operational integrity without conditioning expansion on quality.
- Errors and cap hits remain in denominators.
- Discordant outcomes are retained and manually categorized.
- Replay recomputes scores from raw rows rather than trusting report totals.
