# Contract Alignment Architecture

## Purpose

The system preserves a caller's external JSON contract while allowing a model to
generate through a narrower, explicitly justified internal representation. It is a
contract compiler and validation boundary, not a grammar engine and not a semantic
repair system.

The original external schema remains authoritative. Every transformation must have
a deterministic inverse, an explicit applicability proof, versioned provenance, and
a fail-closed path. Unsupported constructs are recorded and refused rather than
silently weakened.

## Canonical pipeline

```text
External JSON Schema
        |
        v
ContractIR
        |
        v
Alignment analysis
        |
        v
AlignmentPlan
        |
        v
Internal JSON Schema
        |
        v
XGrammar / Outlines
        |
        v
Internal object
        |
        v
Deterministic inverse transducer
        |
        v
Original external-schema validation
        |
        v
Caller-facing object
```

## Boundary guarantees

| Boundary | Information preserved | Permitted change | Fail-closed condition |
|---|---|---|---|
| External schema to `ContractIR` | Declared types, properties, required fields, property order, additional-property policy, supported scalar constraints, schema dialect, and unsupported-keyword locations | Canonical ordering and serialization only | Malformed schema, unknown required property, ambiguous type, unsupported keyword, reference, or invalid pattern |
| `ContractIR` to alignment analysis | Stable schema hash, field paths, lexical representation, and unsupported-construct record | Candidate transform discovery | No transform is proposed when applicability cannot be proven from the schema and explicit policy |
| Alignment analysis to `AlignmentPlan` | External schema hash, transform order, transform versions, backend requirements, transducer version, provenance, and refusal reasons | A model-facing representation may be selected | A plan with any refusal reason is non-executable |
| `AlignmentPlan` to internal schema | All fields required for deterministic external reconstruction | Proven schema rewrites, internal-only bounded fields, aliases, and generation order | Transform collision, narrowing without an explicit assertion, incomplete order mapping, or unsupported composition |
| Internal schema to grammar backend | Internal property order, types, required fields, compact whitespace policy, and backend options | Backend-specific compiled grammar representation | Grammar compilation failure or a backend that cannot honor plan requirements |
| Grammar backend to internal object | One model call, frozen prompt, frozen chat template, model revision, tokenizer revision, and decoding configuration | Tokens may differ only because the registered representation differs | Generation exception, empty output, token cap, invalid JSON, invalid internal schema, or manifest mismatch |
| Internal object to inverse transducer | Generated sign, magnitude, field values, and all externally visible semantics | Exact inverse operations such as integer to canonical base-10 string and alias restoration | Missing field, wrong runtime type, boolean-as-integer, collision, invalid scratch value, or ambiguous inverse |
| Inverse transducer to external validation | Reconstructed caller-facing names, types, order, and values | Canonical serialization only | Any violation of the original external schema |
| External validation to caller | Only the validated caller-facing object | None | No partially transformed or invalid object is returned |

## Execution invariants

1. The external schema is never replaced as the final authority.
2. A plan is deterministic, canonically serializable, hashable, and replayable.
3. Transform order is explicit and validated.
4. Reverse transduction uses no model, heuristic repair, rounding, sign inference,
   parser recovery, or fallback coercion.
5. A value is returned only after validation against the original external schema.
6. Generation errors, token-cap hits, invalid objects, and transduction failures are
   recorded as failures. They are not silently retried into a different condition.
7. Backend and environment configuration are part of experimental provenance.
8. Accepted artifacts are immutable. Corrections create new evidence layers.

## Current demonstrated path

The empirically demonstrated transform is narrow:

```text
external answer: canonical signed integer string
        |
        v
internal answer: JSON integer
        |
        v
constrained generation
        |
        v
arbitrary-precision base-10 stringification
        |
        v
validation against the original signed-string schema
```

For example, an internal integer `-12` becomes the external string `"-12"`. The
transducer does not change the sign or magnitude. Values such as booleans, floats,
numeric strings, exponent notation, leading-plus notation, and unsupported lexical
languages are refused unless a separate proven transform explicitly supports them.

## Runtime separation

The canonical experiment runtime has one generation path. Representation is data,
not a separate runner:

```text
representation = signed-numeric-string | integer
```

Model loading, tokenizer loading, chat-template application, XGrammar compilation,
decoding, visible-token counting, latency measurement, error handling, manifests,
row writing, and resume validation are shared. Only the model-facing answer schema,
the symbolic prompt placeholder, and integer inverse transduction may differ.

## Non-goals

- Reimplementing XGrammar, Outlines, or another grammar execution engine.
- Repairing mathematically incorrect answers.
- Claiming that a contract-valid answer has faithful reasoning.
- Supporting arbitrary JSON Schema through silent approximation.
- Selecting transforms from observed benchmark wins.
- Treating two byte-identical backend outputs as independent semantic replications.

## Evidence policy

Architecture expansion requires a preregistered empirical gate. Unit tests establish
determinism and contract safety; they do not establish model-quality benefit. A new
transform remains prototype or experimental until a matched task shows practical
value without violating the external contract.
