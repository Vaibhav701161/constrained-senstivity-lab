# Corrected 7B Representation-Alignment Decision

## Decision

The preregistered outcome is **green for scoped continuation**.

The corrected experiment supports continuing the contract-preserving compiler direction for the demonstrated canonical integer-string transform. It does not support production deployment, universal schema expansion, or a claim that the effect generalizes beyond this model and task.

## Evidence integrity

The remote job completed and the outputs passed an independent local validator.

| Check | Result |
| --- | --- |
| Raw generation rows | 200/200 present |
| Unique items per condition | 50/50 |
| Canary operational gate | Passed |
| Full operational gate | Passed |
| Source, runner, manifest, and result hashes | Matched |
| Cross-backend prompt equivalence | Passed within each representation |
| Generation errors | 0 |
| Token-cap hits | 0 |
| Blank outputs | 0 |
| Internal schema failures | 0 |
| External schema failures | 0 |
| XGrammar boundary traces | 3/3 preregistered items |
| Independent validation failures | 0 |
| Independent validation warnings | 0 |

The accepted artifact-validation SHA-256 is `df704538071ffdf1cbb3b6730ef5af4631913e803731f4898ee95cdfaae52646`.

## Primary result

The cleaned analysis excludes only the previously documented contradictory reference `gsm8k_test_454`, leaving 49 paired items.

| Representation | Correct | Contract-valid accuracy | Final external validity | Negative answers |
| --- | ---: | ---: | ---: | ---: |
| Signed numeric string | 18/49 | 36.7% | 49/49 | 2 |
| Internal integer plus deterministic stringification | 24/49 | 49.0% | 49/49 | 0 |

Paired result:

- net improvement: 6 items, or 12.2 percentage points;
- treatment-only wins: 9;
- control-only wins: 3;
- both correct: 15;
- both wrong: 22;
- exact deterministic bootstrap 95% interval: [0.0, 26.5] percentage points;
- exact McNemar p-value: 0.145996.

The point estimate exceeds the preregistered five-point continuation threshold. Every treatment output preserved the original external contract, and wins exceeded losses by three to one.

The result is not conventionally statistically significant at 0.05. The interval touches zero and the exact McNemar p-value is 0.146. The correct interpretation is evidence strong enough for a scoped next stage under the frozen decision rule, not proof of a universal benefit.

## Backend observation

Outlines and XGrammar produced byte-identical raw outputs on all 50 signed-string items and all 50 integer items.

This is unusually useful causal evidence. With equivalent prompts and aligned canonical grammar policies, backend identity did not explain any item-level semantic difference in this run. The model-facing representation did.

It also means the two backend results are not independent statistical replications. They are two implementations that realized the same deterministic token path on this experiment.

## Repaired and broken items

The internal integer treatment repaired nine items:

```text
gsm8k_test_98
gsm8k_test_416
gsm8k_test_712
gsm8k_test_739
gsm8k_test_765
gsm8k_test_1205
gsm8k_test_1232
gsm8k_test_1251
gsm8k_test_1272
```

It broke three previously correct items:

```text
gsm8k_test_506
gsm8k_test_601
gsm8k_test_996
```

The three regressions are different arithmetic or interpretation failures. They do not form an observed systematic lexical cluster, but they are real and remain in the primary denominator.

## Mechanistic interpretation

Both signed-string negative outputs were repaired by the integer treatment:

- `gsm8k_test_712`: `-14` became `14`;
- `gsm8k_test_1205`: `-1` became `4`.

This satisfies the majority-repair component of the registered boundary hypothesis. The broader set of seven additional repairs shows that representation changes can alter earlier reasoning trajectories, not only the final sign token.

The boundary traces refine the hypothesis:

- the integer grammar masks quote and structural-space continuations at the answer boundary;
- it does not mask the minus token;
- the selected first digit remains determined by the model under a different legal token path.

Therefore, the mechanism is not simply "integers prohibit negative answers." JSON integers permit negatives. The supported interpretation is that the model-facing representation changes tokenization and constrained continuation paths, which can alter both reasoning and final answers.

One important counterexample must remain visible. For `gsm8k_test_712`, the integer output's reasoning still computes `-14`, while its final answer is `14`. The final answer is correct under the benchmark metric, but the reasoning is internally inconsistent. We have evidence of improved final-answer fidelity, not improved reasoning faithfulness.

## Effect of correcting the runner

The historical experiment showed a 14.3-point treatment effect. The corrected replication shows 12.2 points, so the direction survives the runner corrections.

Absolute accuracy changed substantially:

| Evidence version | Signed string | Internal integer | Delta |
| --- | ---: | ---: | ---: |
| Historical mixed runner paths | 61.2% | 75.5% | +14.3 points |
| Corrected paired paths | 36.7% | 49.0% | +12.2 points |

The historical and corrected absolute rates must not be pooled. Prompt handling and canonical grammar behavior differ between the runner versions. The corrected run is authoritative for current architecture decisions.

## Why the decision is green but scoped

The registered green requirements were:

1. at least five points of contract-valid recovery;
2. 100 percent final external validity;
3. paired wins exceeding losses;
4. no new systematic semantic failure;
5. evidence consistent with the representation-boundary mechanism.

The corrected run satisfies all five. It also exposes important uncertainty:

- only 49 clean paired items;
- McNemar p-value above 0.05;
- bootstrap interval touching zero;
- absolute treatment accuracy of only 49.0 percent;
- one model and one benchmark;
- one corrected answer with inconsistent reasoning;
- no independent semantic replication across the two backends because their outputs are identical.

Green therefore means "continue the next bounded research stage." It does not mean "the compiler thesis is proven."

## Authorized next step

The evidence authorizes freezing architecture decisions for the demonstrated transform and building only the narrow path supported by the tests:

```text
canonical signed-integer-string external contract
    -> internal JSON integer
    -> constrained generation
    -> deterministic arbitrary-precision stringification
    -> original external-schema validation
```

The evidence does not authorize broad schema support. Before investing in generalization, the next empirical gate should be one of:

1. a second model family on the same paired contract experiment; or
2. an executable tool-call task where exact contract-valid correctness has practical meaning.

If neither replication preserves a useful positive effect, the project should narrow to a schema-risk linter and measurement tool rather than continue as a general compiler.

## Evidence paths

- Independent artifact validation: `artifact-validation.json`
- Exact paired summary: `paired-summary-exact.json`
- Human-readable exact summary: `paired-summary-exact.md`
- Machine decision: `decision.json`
- Raw results and remote manifests: `results/corrected-replication/`
