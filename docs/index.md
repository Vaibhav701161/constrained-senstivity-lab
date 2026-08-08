---
title: Contract Sensitivity Lab
description: Artifact-backed evaluation of how structured-output contracts change model behavior
hide:
  - toc
---

<section class="csl-hero">
  <p class="csl-eyebrow">Structured-output evaluation infrastructure</p>
  <h1>Measure what a contract changes, not only whether it validates.</h1>
  <p class="csl-hero__lede">
    Contract Sensitivity Lab is an artifact-backed harness for testing how
    model-facing schemas alter semantic correctness, output validity, and
    executable outcomes. It treats a schema as part of the model input, then
    measures its behavioral effect with paired experiments.
  </p>
  <div class="csl-actions">
    <a class="csl-button csl-button--primary" href="getting-started/quickstart/">Run the evidence replay</a>
    <a class="csl-button csl-button--secondary" href="studies/evidence-overview/">Inspect the results</a>
  </div>
</section>

<div class="csl-metrics">
  <div class="csl-metric"><strong>1,501</strong><span>property cases for deterministic integer stringification</span></div>
  <div class="csl-metric"><strong>464</strong><span>accepted experiment rows replayed by one command</span></div>
  <div class="csl-metric"><strong>2</strong><span>independent model families evaluated</span></div>
  <div class="csl-metric"><strong>0</strong><span>heuristic repairs allowed in scored paths</span></div>
</div>

## The engineering question

Constrained decoding can guarantee that an output belongs to a grammar. That does
not guarantee that the model preserves its semantic ability under that grammar.
Even contract-preserving representation changes can alter the answer a model emits.

This project asks:

> When two representations map to the same caller-facing contract, does choosing
> one of them change correctness or execution success?

The tested transform was intentionally narrow:

<div class="csl-pipeline">External canonical signed string
             ↓ compile
Internal JSON integer
             ↓ constrained generation
Internal object
             ↓ deterministic inverse transducer
Original external object
             ↓ strict validation
Caller-facing result</div>

The inverse transducer is safe for the supported language. The assumption that it
improves model quality by default is not.

## Current decision

<div class="csl-decision">
  <strong>The general optimizer thesis is closed.</strong><br>
  The supported direction is a contract-sensitivity evaluation harness, with a
  fail-closed schema linter and conservative transduction utilities.
</div>

The corrected Qwen study estimated a positive effect. A preregistered Llama
replication reversed it, and an exact canonical-schema correction preserved the
negative direction. A bounded executable tool-call pilot also found no practical
benefit. The negative results are retained as first-class evidence.

| Decision gate | Control | Treatment | Paired effect | Outcome |
|---|---:|---:|---:|---|
| Corrected Qwen2.5 7B, n=49 | 36.7% | 49.0% | +12.2 pp | Scoped positive signal |
| Llama 3.2 3B canonical holdout, n=150 | 61.3% | 54.7% | -6.7 pp | Optimizer thesis closed |
| Llama 3.2 3B executable pilot, n=30 | 86.7% | 80.0% | -6.7 pp | No practical benefit detected |

[Read the complete evidence chain](studies/evidence-overview.md){ .csl-button .csl-button--secondary }

## What the repository provides

<div class="csl-card-grid">
  <div class="csl-card">
    <h3>Paired evaluation runtime</h3>
    <p>Matched prompts, decoding, model revisions, item order, metrics, and failure handling across representations.</p>
    <a href="architecture/">Architecture</a>
  </div>
  <div class="csl-card">
    <h3>Fail-closed contract analysis</h3>
    <p>Explicit support boundaries for canonical numeric strings, aliases, ordering, whitespace, and refused features.</p>
    <a href="supported-contracts/">Supported contracts</a>
  </div>
  <div class="csl-card">
    <h3>Artifact replay</h3>
    <p>Recompute scores and paired summaries from checked-in rows without downloading models or requiring a GPU.</p>
    <a href="reproducibility/artifact-replay/">Reproduce the evidence</a>
  </div>
  <div class="csl-card">
    <h3>Auditable studies</h3>
    <p>Protocols, manifests, raw JSONL, canary gates, hashes, discordance audits, and frozen decisions.</p>
    <a href="reproducibility/evidence-map/">Evidence map</a>
  </div>
</div>

## Start with the evidence, then the implementation

If you are new to constrained decoding, begin with
[Constrained decoding](concepts/constrained-decoding.md) and
[Contract sensitivity](concepts/contract-sensitivity.md). If you are evaluating
the engineering quality of the repository, run the
[lightweight replay](getting-started/quickstart.md) and then inspect the
[canonical correction](studies/canonical-correction.md).
