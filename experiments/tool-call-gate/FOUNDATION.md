# Executable tool-call gate foundation

This directory records the upstream benchmark basis before any tool-call cases are selected or model outputs are viewed. The experiment scope and sample size remain conditional on the frozen second-family replication decision.

## Upstream pin

- Repository: [ShishirPatil/gorilla](https://github.com/ShishirPatil/gorilla)
- BFCL checkpoint: [`f7cf7359b7ac615a0b294831c5ba2bc95ee4a000`](https://github.com/ShishirPatil/gorilla/commit/f7cf7359b7ac615a0b294831c5ba2bc95ee4a000)
- Reproduction package: `bfcl-eval==2025.12.17`
- License: Apache-2.0
- Reference category: BFCL V4 `simple_python`

The official BFCL leaderboard identifies this exact commit and package version as its reproducibility checkpoint. BFCL supports exact run-ID selection, which allows a pinned partial experiment without silently changing the surrounding benchmark.

## Why the gate uses `simple_python`

The practical gate is intentionally limited to single-turn, single-function calls. It excludes multi-turn agents, parallel calls, web search, memory, live APIs, and other sources of failure unrelated to contract representation.

The current BFCL change log records that its legacy executable categories were retired from leaderboard scoring in April 2025. We therefore do not revive those network-dependent categories. Instead, the gate will use pinned BFCL `simple_python` questions, function definitions, and official ground truths as the semantic foundation. Project-owned deterministic wrappers will execute the selected calls without network access or real-world side effects.

This design keeps two layers separate:

1. BFCL supplies realistic tool descriptions, prompts, function selection, argument semantics, IDs, and reference calls.
2. The project supplies deterministic local execution and state assertions needed to test the unchanged external contract after inverse transduction.

## Registered transform boundary

The only planned representation transform is:

```text
external canonical signed integer string
                    <->
internal JSON integer
```

Candidate cases must contain an integer-valued argument with an unambiguous canonical decimal representation. The control exposes that value to the model as a signed numeric string. The treatment exposes it as an integer, then deterministically stringifies it and validates the original external tool schema before execution.

The gate will score tool selection, exact argument semantics, internal-schema validity, reconstructed external-schema validity, execution success, final state, and heuristic-repair count. A model output is never repaired heuristically.

## Scope resolution

The second-family result was frozen as Red. The authorized practical experiment is therefore one bounded pilot rather than the full gate. Its exact eligibility rules, random 30-case primary sample, complete negative sign-stress supplement, execution semantics, metrics, and decision rule are frozen in `protocol.md` before selection or generation.

No later result can expand this pilot retroactively.
