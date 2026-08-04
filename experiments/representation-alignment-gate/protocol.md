# Representation-Alignment Gate Protocol

## Question

Does a native JSON integer as the hard-constrained, model-facing answer
representation recover the semantic losses observed with a signed numeric string,
while deterministic stringification restores validity under the original external
contract?

## Status and scope

This protocol is confirmatory for the representation comparison once the targeted
screen passes. It does not establish that the observed sign cluster is a universal
property of constrained decoding, Qwen models, Outlines, or XGrammar.

## Frozen baseline

The accepted baseline is referenced, never rewritten or rerun:

| Treatment | Frozen artifact |
|---|---|
| Prompt-only signed numeric string | `results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/prompted_json_reasoning_first.jsonl` |
| Outlines signed numeric string | `results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/outlines_json_reasoning_first.jsonl` |
| XGrammar signed numeric string | `results/qwen2.5-7b/primary/reasoning-first/results/qwen2.5-7b-smoke/xgrammar_json_reasoning_first.jsonl` |

The baseline model, item order, data hash, chat template, greedy decoding, token
budget, FP32 precision, and canonical XGrammar whitespace policy are retained.

## New model-facing conditions

All integer conditions use reasoning before answer and the internal schema in
[`schemas/internal-integer.schema.json`](schemas/internal-integer.schema.json).

1. `prompted_json_integer_reasoning_first`
2. `outlines_json_integer_reasoning_first`
3. `xgrammar_json_integer_reasoning_first`

The prompt text is identical across these three conditions. Relative to the frozen
signed-string JSON prompt, the intended difference is only the declared internal
answer representation and its symbolic template. The integer template renders
`"answer": <integer>` rather than a quoted placeholder.

The optional `unsigned_numeric_string_diagnostic` condition is restricted to the
targeted, known-positive suite. It is a diagnostic intervention, not an externally
contract-equivalent production condition because the original contract permits
negative numbers.

## Transduction and validation

For every internal-integer output:

1. Parse the complete internal JSON object.
2. Require that `answer` is an actual JSON integer, excluding booleans.
3. Convert it to a canonical base-10 string with arbitrary-precision Python integer
   semantics.
4. Rebuild the external object with the original field names and order.
5. Validate the rebuilt object against
   `external-signed-numeric-string.schema.json`.
6. Mark `contract_valid_correct` true only when final external validation and
   representation-independent semantic scoring are both true.

No LLM, heuristic repair, rounding, sign removal, leading-zero padding, or lossy
coercion is permitted.

## Data and exclusion rule

The full confirmation uses the deterministic 50-item GSM8K subset with SHA-256
`3639f2f6def0f50e02086bc91e6f4a45567c85aa9b0f498224cb9421400d812a`.
The known contradictory reference `gsm8k_test_454` remains in raw output and is the
only item excluded from the cleaned, paired analysis. No new exclusions are allowed.

The targeted suite is mechanically derived from frozen raw results. It contains the
union of constrained losses, deterministic matched controls, and deterministic
shared failures. It supports debugging and trace collection only. It cannot replace
the frozen confirmation set.

## Metrics

Primary metric:

- Contract-valid accuracy after external transduction on the cleaned 49-item set.

Secondary metrics:

- Recoverable semantic accuracy.
- Internal-schema validity.
- Final external-schema validity.
- Negative-answer rate.
- Completion, error, and token-cap rate.
- Paired wins, losses, bootstrap interval, and exact McNemar test against the frozen
  constrained signed-string baseline.
- Repaired and newly broken item IDs.
- Latency and generated-token differences.

## Targeted-screen progression rule

Proceed to full confirmation only when at least one constrained integer backend:

- repairs at least five of the eight shared baseline losses on the targeted suite;
- produces externally valid transduced output for every completed targeted row; and
- has compact boundary traces consistent with the representation hypothesis.

If the targeted screen fails, preserve the result and record the failed mechanism.
Do not run a broad matrix or add unrelated transforms merely to search for a gain.

## Full-confirmation decision rule

Green, continue the compiler:

- at least five percentage points of recovery over the matching frozen constrained
  baseline;
- a majority of shared sign-loss items repaired;
- 100% final external validity; and
- no new systematic semantic failure.

Yellow, narrow the scope:

- a real but sub-five-point gain or a mechanism limited to a narrow, declared schema
  domain.

Red, stop the compiler build:

- no safe transform recovers fidelity, or traces contradict the representation
  explanation and no second localized mechanism survives.

## Allowed changes before launch

Allowed debugging changes are limited to defects that violate this protocol, such as
incorrect schema construction, transduction, scoring, provenance capture, or backend
integration. Every such change must be documented before rerunning the affected
stage.

Prompt wording, data selection, primary metrics, success thresholds, precision,
model, decoding policy, or external contract may not be tuned after observing
targeted outcomes. Any necessary change creates a new exploratory protocol.
