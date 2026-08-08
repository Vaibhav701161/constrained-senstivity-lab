# Bounded executable tool-call pilot protocol

## Freeze boundary

This protocol is frozen before case selection is materialized and before model generation. Candidate eligibility, selection seeds, prompts, schemas, decoding, scoring, execution, denominators, and decision rules are fixed here.

The second-family replication was Red. Therefore, this experiment uses the bounded pilot path rather than the full practical gate.

## Fixed sources

| Component | Frozen value |
|---|---|
| BFCL repository | `ShishirPatil/gorilla` |
| BFCL commit | `f7cf7359b7ac615a0b294831c5ba2bc95ee4a000` |
| BFCL package reference | `bfcl-eval==2025.12.17` |
| BFCL category | `BFCL_v4_simple_python` |
| Question source SHA-256 | `82dd63ba502eb2520c6b5d1d9a5c4b590e03ff261565175561f6228a367d1991` |
| Ground-truth source SHA-256 | `90cd5bc653690ee8e459b5b3f3fc9458606f7f3fcbf795bb51b7dc581f8c86dc` |

The pinned source files supply realistic prompts, function descriptions, parameter definitions, tool names, item IDs, and official acceptable argument values. Project-owned wrappers add deterministic local execution without network calls or real-world side effects.

## Model and decoding

| Setting | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Backend | XGrammar 0.2.3 |
| Decoding | Greedy, `do_sample=False` |
| Seed | 0 |
| Dtype | FP32 |
| Placement | `device_map="auto"` on Modal L4 |
| Maximum new tokens | 192 |
| Chat template | Llama template applied exactly once |

The software environment remains the pinned project environment. No prompt, model, package, or decoding search is permitted after launch.

## Candidate eligibility

A BFCL case is eligible only when all of the following are true:

1. it is in pinned `BFCL_v4_simple_python`;
2. it exposes exactly one function;
3. the function has an object-like parameter schema;
4. at least one required parameter has BFCL type `integer`;
5. the pinned ground truth contains exactly one call for that function;
6. every required integer parameter has at least one integer-valued acceptable reference; and
7. the case and ground truth can be normalized without guessing or repairing data.

Eligibility is computed mechanically in BFCL source order. No model output is involved.

## Frozen selection

The primary pilot contains 30 cases selected uniformly without replacement from the complete eligible pool with Python MT19937 seed `20260817`.

Because signed-boundary cases are rare in BFCL, a separate mechanism stress set contains every eligible case whose required integer reference includes a negative value. A stress case already selected by the random primary sample is not duplicated. Stress results are reported separately and are never pooled into the primary effect.

The selection script records:

- the complete eligible ID list;
- the complete ineligible-reason counts;
- the 30 primary IDs in BFCL source order;
- the negative sign-stress IDs in BFCL source order;
- source hashes, seed, algorithm, and dataset hash; and
- overlap and uniqueness checks.

## External contract and internal representation

Each case has one caller-facing schema:

```json
{
  "name": "the_exact_bfcl_function_name",
  "arguments": {
    "integer_parameter": "-12"
  }
}
```

All BFCL integer parameter types are mapped to canonical decimal strings in the external schema:

```text
^-?(0|[1-9][0-9]*)$
```

Other supported primitive and array parameter types retain their BFCL meaning. Object-like BFCL type `dict` is normalized to JSON Schema type `object`. Unsupported or ambiguous schema constructs fail closed during preparation.

The treatment-facing schema differs only in mapping those canonical integer-string fields back to native JSON `integer` fields. The function name, property names, descriptions, required fields, property order, additional-property policy, prompt text outside the rendered schema, and output envelope remain identical.

The inverse transducer recursively stringifies only the registered integer fields. It performs no clipping, rounding, coercion from model-produced strings, key insertion, aliasing, or heuristic repair. The reconstructed call must validate against the unchanged external schema before execution.

## Prompt

The model receives:

1. the original BFCL user request;
2. the single BFCL function name and description;
3. the complete model-facing call schema; and
4. an instruction to return only one JSON call object with no markdown or extra text.

The serialized model-facing schema is the only prompt difference between control and treatment. Llama's chat template is applied exactly once.

## Deterministic execution

No original BFCL function is called and no external service is contacted. A project-owned deterministic wrapper:

1. dispatches only the exact registered function name;
2. validates the reconstructed caller-facing object;
3. strictly parses registered canonical integer strings;
4. records the normalized call in an isolated in-memory state;
5. computes a deterministic receipt digest; and
6. compares the resulting state with states allowed by the pinned BFCL ground truth.

This tests contract reconstruction, dispatch, exact arguments, executable acceptance, and post-execution state. It does not claim to reproduce the original function's business logic.

## Row-level metrics

Every row records:

- exact tool selection;
- whole-response JSON validity;
- internal-schema validity;
- inverse-transduction success;
- reconstructed external-schema validity;
- exact BFCL argument semantics;
- deterministic execution success;
- correct post-execution state;
- executable-contract success;
- heuristic-repair count, fixed at zero;
- errors and token-cap hits;
- generated tokens; and
- latency, marked descriptive only.

`executable_contract_success` requires every correctness and validity component above to pass. A structurally valid but semantically wrong call can execute, but it does not count as successful.

## Error handling and denominator

Generation exceptions, token-cap hits, invalid JSON, invalid internal objects, transduction failures, external-schema failures, wrong tools, wrong arguments, execution failures, and incorrect post-execution states remain in the assigned denominator and count as failures.

There are no post-launch exclusions. Dataset defects found after output inspection remain in the denominator. There are no retries, output recovery, regex extraction, default insertion, or heuristic repairs.

## Operational canary

The first three primary cases run under both representations. Expansion checks only:

- identical IDs and order;
- no duplicate rows;
- exactly one chat-template application;
- nonempty outputs;
- no generation exceptions;
- no token-cap hits;
- internal-schema validity;
- treatment transduction and external validity;
- one model and tokenizer revision;
- one package and GPU environment; and
- matching dataset and source hashes.

Semantic correctness and which representation wins cannot be used to decide expansion. The same files resume from three rows to the full selected dataset.

## Analysis

The 30-case random primary sample and sign-stress set are reported separately.

Primary paired metrics:

- control and treatment executable-contract success;
- treatment-only and control-only wins;
- paired percentage-point difference;
- exact McNemar test;
- exact paired bootstrap interval; and
- all component validity and execution rates.

Every discordant primary or stress case is manually inspected. Categories are:

- integer lexical-boundary change;
- tool-selection change;
- argument-semantic correction;
- argument-semantic regression;
- transduction or validation failure;
- execution or state failure;
- truncation;
- other.

## Decision gate

This bounded pilot is too small to establish a general product claim. Its gate decides whether the practical direction remains plausible.

### Green practical signal

All must hold on the random 30-case primary sample:

1. treatment improves executable-contract success by at least 5 percentage points;
2. treatment-only wins exceed control-only wins;
3. treatment external validity is 100%;
4. treatment execution success is not lower than control; and
5. no coherent regression cluster appears.

### Yellow

The estimate is positive but below five points, uncertainty crosses zero, or stress and primary behavior disagree without a coherent treatment regression. The project remains a measurement and analysis system; broad compiler expansion is not authorized.

### Red

Any of the following is sufficient:

- the primary difference is zero or negative;
- control-only wins equal or exceed treatment-only wins;
- treatment external validity or execution success is lower;
- the treatment produces a coherent new failure mode.

If Red, the optimizing-compiler thesis is closed for the current evidence. The supported product direction becomes a schema-risk linter, measurement harness, and contract-sensitivity analyzer.

## Required artifacts

```text
experiments/tool-call-gate/
|-- HYPOTHESIS.md
|-- protocol.md
|-- source-manifest.json
|-- dataset-manifest.json
|-- canary-gate.json
|-- artifact-validation.json
|-- paired-summary.json
|-- paired-summary.md
|-- failure-attribution.jsonl
|-- decision-report.md
|-- manifests/
`-- results/
```
