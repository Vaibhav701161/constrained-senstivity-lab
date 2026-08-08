# Canonical schema-equivalence correction hypothesis

## Correction question

When the control language is exactly the compiler-supported canonical signed-integer
string language, does the frozen Llama integer treatment still fail to improve
contract-valid GSM8K correctness?

## Discovered mismatch

The accepted second-family control used a broad numeric-string grammar that permits
decimals, fractions, comma grouping, and leading zeros. The compiler prototype only
accepts canonical signed-integer strings. The experiment therefore changed both
representation and accepted value language.

This mismatch was discovered after the second-family and tool-call decisions were
frozen. It does not invalidate those observed rows, but it narrows what they can say
about the exact compiler-supported transform.

## Fixed comparison

```text
control:    ^-?(?:0|[1-9][0-9]*)$
treatment:  JSON integer followed by exact base-10 stringification
```

The treatment is the already frozen 150-item Llama integer arm. It will not be
regenerated. Exactly one new 150-item canonical-string control arm is authorized.

## Claim discipline

A negative corrected effect closes the exact optimizer thesis under the tested
model and workload. An approximately neutral effect still rejects default automatic
optimization. A positive corrected effect does not establish replication because
the correction was designed after discovering the mismatch; it would require a
fresh preregistered holdout before any positive cross-family claim.
