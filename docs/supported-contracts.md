# Supported Contracts and Refusal Policy

## Status definitions

- **Supported**: implemented, property-tested, and backed by accepted task evidence.
- **Supported policy**: an enforced backend policy with operational evidence.
- **Prototype**: implemented and unit-tested, but not independently validated for
  model quality.
- **Experimental**: safety behavior exists, but practical benefit is unproven.
- **Refused**: intentionally non-executable because preservation has not been proven.

## Current matrix

| Feature | Current status | Evidence |
|---|---|---|
| Canonical signed integer string | Supported | Corrected Qwen2.5-7B experiment, exact transducer tests, and adversarial lexical tests |
| Integer to canonical string transduction | Supported | 1,501 property cases, boolean rejection, arbitrary-precision cases, and original-schema validation |
| Final validation against original schema | Supported | Transducer tests, compiler acceptance probes, and 200-row corrected replication |
| Stable contract IR and hashing | Prototype | Canonical serialization, round-trip, unsupported-keyword, and stable-hash tests |
| Deterministic alignment plans | Prototype | Serialization, transform-order, backend-requirement, refusal, and replay tests |
| Field ordering | Prototype | Strong Qwen experimental motivation and unit-tested buffered restoration; no independent quality validation |
| Key aliases | Prototype | Bijective forward and inverse mapping tests; no empirical quality validation |
| Scratch field | Experimental | Collision, bound, deletion, and policy tests; no model-quality validation |
| Canonical whitespace | Supported policy | Historical backend stall evidence and pinned real-backend grammar tests |
| Bounded whitespace | Prototype | Backend option generation tested; not used in accepted task evidence |
| Arbitrary whitespace | Refused for accepted experiments | Adds unbounded legal paths and is outside the canonical experimental language |
| `$ref` | Refused | Local, recursive, and remote reference preservation is not implemented |
| Unions such as `oneOf`, `anyOf`, and multi-type arrays | Refused | Branch semantics and invertibility are not currently proven |
| Arbitrary regex transformation | Refused | Unsafe without a proven language equivalence or explicit narrowing assertion |
| Schema-valued `additionalProperties` | Refused | Initial IR supports only boolean additional-property policy |
| Heuristic numeric coercion | Refused | Would change lexical semantics and conceal contract failures |
| Float to integer conversion | Refused | Rounding and precision semantics are not contract-preserving by default |
| Sign repair or magnitude repair | Refused | The compiler must preserve generated semantics rather than infer an intended answer |
| Model-based output repair | Refused | Adds a second semantic model call and breaks exact provenance |
| Streaming field-order restoration | Refused | Reordering requires explicit buffering under the current plan |

## Supported canonical integer-string language

The accepted transform requires an external field with JSON type `string` and a
pattern equivalent to the project's canonical signed-integer language:

```regex
^-?(?:0|[1-9][0-9]*)$
```

Accepted examples include:

```text
"0"
"17"
"-17"
"123456789012345678901234567890"
```

Examples refused by the canonical transform include:

```text
"+17"
"017"
"17.0"
"1.7e1"
"1,000"
"17/1"
```

Refusal does not mean these contracts are invalid. It means the current compiler
does not claim a semantics-preserving mapping for their lexical languages.

## Promotion rule

No feature changes status merely because a test can be written or a backend can
compile it. Promotion requires:

1. a precise external contract;
2. an applicability rule;
3. a deterministic inverse;
4. final validation against the unchanged external schema;
5. adversarial and property testing;
6. a preregistered task-level evaluation;
7. preserved failures and explicit limitations.

Rows remain red until their evidence exists. Support is not added merely to make the
table look broader.
