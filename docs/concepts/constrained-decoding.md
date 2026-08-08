# Constrained decoding

## The basic idea

A language model normally chooses its next token from the entire vocabulary.
Constrained decoding removes choices that would make the final output violate a
formal language such as JSON, a regular expression, or a JSON Schema.

Suppose a caller requires:

```json
{"answer": "-12"}
```

A prompt can ask the model to follow that format, but the model can still emit an
unquoted number, omit the key, or add prose. A constrained decoder converts the
contract into token-level rules and prevents structurally illegal continuations.

## Prompting and enforcement are different

| Mechanism | What it does | What it cannot guarantee |
|---|---|---|
| Prompt instruction | Describes the desired format in natural language | Structural compliance |
| Output parser | Interprets text after generation | That malformed output was never produced |
| Constrained decoder | Masks illegal token continuations during generation | Semantic correctness |
| External validator | Checks the completed object against the caller contract | That the answer is correct |

The distinction matters because syntactic success can hide semantic regressions.
In the baseline 7B study, constrained backends reached 100% schema compliance while
recoverable mathematical accuracy fell by 18.4 percentage points against the
matched prompt-only condition.

## Why constraints can change meaning

Constraints do more than clean up a response after generation. At every step they
change the probability distribution by removing tokens. They can also change:

- which representation the model sees in the prompt;
- which field must be produced first;
- whether a sign, quote, or delimiter is legal at a decision boundary;
- how much reasoning can appear before a required value;
- which continuations remain reachable.

That is why the project measures paired semantic outcomes instead of reporting only
JSON validity.

## Backends used here

The studies use Outlines and XGrammar as structured-generation implementations.
When their matched outputs are byte-identical, that supports implementation parity
for the tested subset. It does not create two independent model replications because
both backends constrain the same underlying model and prompt.

## Continue learning

Read [Contract sensitivity](contract-sensitivity.md) for the central measurement
problem, then inspect the [Qwen baseline](../studies/qwen-baseline.md).
