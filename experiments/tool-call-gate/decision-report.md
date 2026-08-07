# Bounded executable tool-call pilot decision report

## Decision

**Red: the practical tool-call pilot did not support the optimizing transform.**

On the preregistered random 30-case primary sample, replacing caller-facing
canonical integer strings with model-facing JSON integers reduced executable
contract success from 26/30 (86.7%) to 24/30 (80.0%). The paired difference was
-6.7 percentage points, with an exact paired bootstrap 95% interval of
[-20.0, 6.7] points. There was 1 treatment-only win and 3 control-only wins;
the exact two-sided McNemar p-value was 0.625.

The treatment retained 100% internal-schema validity, reconstructed external
validity, dispatch success, and execution acceptance. Its failures were semantic:
the model supplied the wrong arguments in six primary cases, compared with four
for the control. The representation change therefore preserved the contract
boundary but did not preserve or improve call meaning.

This satisfies two independent preregistered Red conditions:

1. the primary paired effect was negative; and
2. control-only wins exceeded treatment-only wins.

The optimizing-compiler thesis is closed under the current evidence. The supported
product direction is now a schema-risk linter, measurement harness, and
contract-sensitivity analyzer. The project must not claim that native-integer
alignment generally improves tool-call correctness.

## Practical question

Does replacing a model-facing canonical integer string with a native JSON integer,
followed by deterministic stringification and validation against the unchanged
caller contract, increase the probability that a model emits a valid call that
executes with exactly correct arguments and state?

The test used realistic function-call cases and official acceptable argument values
from the pinned BFCL V4 `simple_python` files. It did not run the original BFCL
functions. Project-owned, deterministic, side-effect-free wrappers tested strict
contract reconstruction, dispatch, typed arguments, execution acceptance, and
post-execution state.

## Frozen design

| Component | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Model and tokenizer revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Constrained backend | XGrammar 0.2.3 |
| Decoding | Greedy, seed 0, FP32, 192 maximum new tokens |
| Compute | Modal L4 with `device_map="auto"` |
| Reference source | BFCL V4 `simple_python` at Gorilla commit `f7cf7359b7ac615a0b294831c5ba2bc95ee4a000` |
| BFCL package reference | `bfcl-eval==2025.12.17` |
| Primary set | 30 uniformly sampled eligible cases, seed 20260817 |
| Sign-stress set | All 3 eligible cases with a negative required integer reference |
| Control | Model emits caller-facing canonical integer strings |
| Treatment | Model emits native integers, then deterministic inverse transduction |
| Primary outcome | Paired executable-contract success on the random 30-case set |
| Post-launch exclusions | None |

The exact selected dataset SHA-256 is
`8590c3b1a13173dbb6a31d7b3496dad419e93bcc1b1d10352c67629b0cd1804d`.
The preparation manifest records 194 eligible cases from 400 upstream cases, every
selected ID, every eligibility reason, the source hashes, the seed, and the absence
of overlap between primary and stress cases.

## Operational integrity

The three-case canary passed all 20 frozen operational checks before expansion.
Semantic outcomes were not inspected for the expansion decision. The same resumable
files then continued to the complete 33 cases per condition.

Across all 66 generations:

- all expected rows were present exactly once and in identical paired order;
- the Llama chat template was applied exactly once;
- one frozen model revision and tokenizer revision were used;
- paired environments, source bindings, dataset hashes, and decoding settings
  matched;
- there were zero generation exceptions and zero token-cap hits;
- whole-response JSON, internal schema, and reconstructed external schema validity
  were 66/66;
- deterministic dispatch and execution acceptance were 66/66;
- there were zero transduction failures and zero heuristic repairs; and
- all invalid, wrong, or inconsistent outcomes remained in their assigned
  denominators.

The machine-readable validator reported no failures. The control result SHA-256 is
`3643e30a577aa6fcba1158435b94af863d53403665368d690ae88e81fba41f68`;
the treatment result SHA-256 is
`1a610c66a3cccd7e6120baa23bcef5f0523f5ba39fa6eb5a5bb84d4f24946638`.

## Primary result

| Metric | String control | Integer treatment |
|---|---:|---:|
| Assigned calls | 30 | 30 |
| Executable-contract success | 26 (86.7%) | 24 (80.0%) |
| Correct tool selection | 30 (100.0%) | 30 (100.0%) |
| Whole-response valid JSON | 30 (100.0%) | 30 (100.0%) |
| Internal-schema valid | 30 (100.0%) | 30 (100.0%) |
| Reconstructed external-schema valid | 30 (100.0%) | 30 (100.0%) |
| Exact argument semantics | 26 (86.7%) | 24 (80.0%) |
| Execution accepted | 30 (100.0%) | 30 (100.0%) |
| Correct post-execution state | 26 (86.7%) | 24 (80.0%) |
| Errors | 0 | 0 |
| Token-cap hits | 0 | 0 |
| Heuristic repairs | 0 | 0 |
| Mean visible generated tokens | 26.3 | 26.5 |
| Median visible generated tokens | 26 | 26 |
| Mean latency, descriptive only | 1824.4 ms | 1805.9 ms |

Primary paired transition matrix:

| | Treatment correct | Treatment incorrect |
|---|---:|---:|
| Control correct | 23 | 3 |
| Control incorrect | 1 | 3 |

The interval crosses zero, so this small pilot does not establish statistically
detectable harm. Statistical uncertainty does not make the result Yellow under the
frozen gate: a zero or negative primary estimate, or losses greater than or equal to
wins, was explicitly sufficient for Red.

## Separate negative-sign stress result

The three-case sign-stress subset improved from 1/3 (33.3%) to 2/3 (66.7%). Its
paired interval was [0.0, 100.0] points, with 1 treatment-only win, no control-only
wins, and exact McNemar p = 1.0.

This result is descriptive, extremely underpowered, and was preregistered as
separate from the primary estimate. More importantly, the sole repaired case did
not repair a sign: both conditions emitted the exact correct coefficients `3`,
`-11`, and `-4`. The success changed because the treatment emitted `root_type="all"`
instead of the control's `root_type="real"`. The stress result therefore does not
provide direct evidence that native integers fixed a signed lexical boundary.

It cannot rescue the negative random primary result.

## Complete discordance audit

Every one of the five discordant calls was manually inspected against its user
request, schema, pinned acceptable BFCL arguments, decoded arguments, execution
state, and raw outputs.

| ID | Subset | Direction | Audit finding |
|---|---|---|---|
| `simple_python_202` | Primary | Treatment-only win | `usage_duration=3` was correct in both. The non-integer `energy_type` changed from incorrect `solar` to accepted `renewable`. |
| `simple_python_40` | Primary | Control-only win | Required integers remained correct. Optional permeability changed from the pinned value to a more precise but non-accepted value. |
| `simple_python_365` | Primary | Control-only win | Requested input quantity changed from `2` to `16`, apparently substituting the conversion result for the function input. |
| `simple_python_399` | Primary | Control-only win | Minimum rating changed from the pinned `4` to `5`, strengthening and therefore altering the requested threshold. |
| `simple_python_5` | Sign stress | Treatment-only win | Signed coefficients were identical and correct. Non-integer `root_type` changed from incorrect `real` to accepted `all`. |

Category totals were 2 argument-semantic corrections and 3 argument-semantic
regressions. There were no tool-selection changes, direct integer lexical-boundary
repairs, validation failures, transduction failures, execution failures,
truncations, or parser issues among the discordants.

The two corrections and one regression occurred in fields that were not transformed
between integer string and native integer. This shows that a small schema change can
perturb the entire generated call, not only the transformed field. The two remaining
regressions directly changed transformed integer arguments. The observed mechanism
is broader contract sensitivity, not reliable removal of lexical friction.

## Predeclared gate evaluation

| Green requirement | Result |
|---|---|
| At least +5 points on the primary sample | Failed: -6.7 points |
| Treatment-only wins exceed control-only wins | Failed: 1 versus 3 |
| Treatment external validity is 100% | Passed: 30/30 |
| Treatment execution success is not lower | Passed: both 30/30 |
| No coherent regression cluster | Failed: three semantic regressions, including two transformed integer fields |

The result is Red. It is not Green because three requirements failed. It is not
Yellow because the primary estimate was negative and losses exceeded wins, both of
which were explicit Red conditions. The positive secondary stress estimate is too
small, non-confirmatory, and mechanistically unrelated to sign repair.

## Combined evidence across the program

The accepted Qwen2.5-7B corrected experiment remains a real but narrow observation:
native-integer generation improved contract-valid GSM8K correctness by an estimated
12.2 points on its cleaned 49-item set, with a paired interval touching zero.

The independent Llama 3.2 3B GSM8K replication then moved in the opposite direction:
-6.7 points on 150 unseen items, 5 treatment wins versus 15 losses, with a paired
interval fully below zero. The same negative direction appeared on the 49-item
bridge set at -2.0 points.

This bounded executable pilot also moved in the wrong primary direction: -6.7
points, 1 win versus 3 losses. It confirmed that the transducer and validation
boundary can operate perfectly, but it did not convert that engineering correctness
into better call semantics.

The evidence pattern is therefore:

```text
Qwen GSM8K corrected result:        positive, uncertain, model-specific
Llama unseen GSM8K replication:     negative, interval below zero
Llama executable BFCL-based pilot:  negative, small and uncertain
                                    |
                                    v
General optimizing transform:       not supported
Measurement and risk analysis:      supported direction
```

## What was learned

1. **Contract preservation is necessary but not sufficient.** The treatment achieved
   perfect schema reconstruction and execution acceptance while reducing exact call
   correctness.
2. **Schema representation is a semantic intervention.** It changed values in both
   transformed and untouched fields.
3. **A local gain did not generalize.** The earlier Qwen result was not reproduced by
   either the Llama math replication or this practical pilot.
4. **Failure accounting prevented a false claim.** Pooling the three sign-stress
   cases with the primary sample would have made the total look less negative, but
   the protocol forbade that analysis.
5. **The infrastructure remains useful.** Frozen manifests, resumable paired runs,
   deterministic transducers, fail-closed validation, exact artifact hashes,
   per-component scoring, and discordance audits form a credible way to measure
   contract sensitivity before deployment.

## Product decision

Broad optimizer expansion stops here. No prompt search, model search, schema-feature
expansion, or broad company/recruiter campaign is authorized by these results.

The project continues as an evidence-oriented system with three functions:

1. **Schema-risk linter:** statically identifies model-facing contract features that
   may create fragile token or representation boundaries, while refusing transforms
   that lack a proof of preservation.
2. **Contract-sensitivity analyzer:** runs paired, frozen-schema interventions and
   reports wins, regressions, validity, uncertainty, and mechanism attribution.
3. **Measurement harness:** preserves dataset identity, prompts, environments,
   failures, execution traces, manifests, and exact replay evidence across structured
   output backends.

The existing integer-to-string transducer remains supported as a deterministic
contract-preserving utility. It is not promoted as a default quality optimization.
Future transforms must earn task-level support independently by model family,
contract, and workload. A linter may recommend measurement, but it must not promise
improvement from the current evidence.

## Scope and limitations

- This is a bounded 30-case primary pilot, not a full BFCL leaderboard evaluation.
- The external numeric-string contract is a project-defined adaptation of pinned
  BFCL cases. It is not the unmodified BFCL tool contract.
- The deterministic wrappers test boundary validation, dispatch, exact arguments,
  and state recording. They do not reproduce original business logic.
- Only one Llama model, XGrammar, greedy decoding, one prompt, and one transform were
  tested.
- The primary sample contained no negative required integer references. The separate
  sign-stress set contained only three cases.
- Latency is descriptive because the conditions ran sequentially and cloud timing
  is not controlled tightly enough for a performance claim.
- The negative point estimate is uncertain at this sample size. The Red decision
  follows the preregistered directional gate, not a claim of statistically proven
  harm in tool calling generally.

## Reproducibility and cost

- Primary generations: 60.
- Separate stress generations: 6.
- Total pilot generations: 66.
- Post-launch exclusions: 0.
- Generation retries for semantic failures: 0.
- Artifact validation failures: 0.
- Manually audited discordants: 5/5.
- Modal metered monthly usage after this pilot: approximately $1.58.
- Modal billed cost: $0.00.
- Remaining credit before the frozen $3 reserve: approximately $25.42.

Canonical artifacts:

- [Frozen protocol](protocol.md)
- [Pinned source foundation](FOUNDATION.md)
- [Source manifest](source-manifest.json)
- [Dataset manifest](dataset-manifest.json)
- [Operational canary gate](canary-gate.json)
- [Artifact validation](artifact-validation.json)
- [Machine-readable paired summary](paired-summary.json)
- [Readable paired summary](paired-summary.md)
- [Complete discordance audit](failure-attribution.jsonl)
- [Raw paired results](results)
- [Environment and run manifests](manifests)

This report freezes the practical gate. No alternative prompt or selective rerun is
used to reinterpret the result.
