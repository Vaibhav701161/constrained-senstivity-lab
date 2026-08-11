---
title: Overview
description: Artifact-backed evaluation of how structured-output contracts change model behavior
hide:
  - toc
---

<section class="csl-hero">
  <div class="csl-hero__grid">
    <div>
      <p class="csl-eyebrow">Structured-output evaluation infrastructure</p>
      <h1>Measure what a contract changes, not only whether it validates.</h1>
      <p class="csl-hero__lede">
        Constrained Sensitivity Lab measures how model-facing schemas alter
        semantic correctness, structural validity, and executable outcomes. Every
        conclusion is tied to paired rows, frozen protocols, source hashes, and
        replayable analysis.
      </p>
      <div class="csl-actions">
        <a class="csl-button csl-button--primary" href="results/">Inspect the final results</a>
        <a class="csl-button csl-button--secondary" href="getting-started/quickstart/">Replay the evidence</a>
        <a class="csl-button csl-button--secondary" href="https://github.com/Vaibhav701161/structtrace">Open StructTrace</a>
      </div>
    </div>
    <aside class="csl-signal" aria-label="Current evidence signal">
      <div class="csl-signal__header">
        <span>Confirmatory gate</span>
        <span class="csl-signal__status">Closed</span>
      </div>
      <pre>model     Llama 3.2 3B
holdout   150 unseen items
control   canonical string
treatment JSON integer

control   92 / 150
treatment 82 / 150
effect    -6.7 pp
CI        [-12.7, -0.7]</pre>
      <p class="csl-signal__foot">The schema correction preserved the negative direction. No output was excluded after launch.</p>
    </aside>
  </div>
</section>

<div class="csl-metrics">
  <dl class="csl-metric"><dt>1,501</dt><dd>property cases for deterministic integer stringification</dd></dl>
  <dl class="csl-metric"><dt>464</dt><dd>rows in the general raw-output replay scope</dd></dl>
  <dl class="csl-metric"><dt>150</dt><dd>repository-unseen items in the confirmatory holdout</dd></dl>
  <dl class="csl-metric"><dt>22 / 22</dt><dd>canonical holdout discordances manually attributed</dd></dl>
</div>

## The problem

<p class="csl-section-intro">
Constrained decoding is commonly evaluated as a formatting mechanism. That is
necessary but incomplete. A grammar changes the set of legal next tokens, and a
schema changes the representation shown to the model. Either can change the answer,
even when the final object is perfectly valid.
</p>

The project separates three claims that are often conflated:

| Claim | Verification method | Current status |
|---|---|---|
| The generated object satisfies its internal schema | Backend and JSON Schema validation | Measured per row |
| The inverse transform preserves the caller contract | Property tests and final external validation | Supported for canonical integer strings |
| The transform preserves or improves model quality | Paired empirical evaluation | Not generally supported |

<div class="csl-decision">
  <strong>Current decision:</strong> the general optimizing-transform thesis is
  closed. The supported product direction is contract-sensitivity measurement,
  backed by conservative compilation and fail-closed schema analysis.
</div>

<figure class="csl-figure">
  <img src="assets/figures/validity-semantics-separation.svg" alt="Structural validity and task correctness separated across baseline and representation studies">
  <figcaption>Structural success and task correctness are measured independently. Arrows connect matched conditions only; task domains are not pooled.</figcaption>
</figure>

## Choose your path

<div class="csl-card-grid csl-card-grid--paths">
  <a class="csl-card csl-card--link" href="getting-started/overview/">
    <span class="csl-card__label">New to the topic</span>
    <h3>Learn the foundations</h3>
    <p>Start with constrained decoding, model-facing contracts, and the difference between valid and correct.</p>
    <span class="csl-card__cta">Start learning</span>
  </a>
  <a class="csl-card csl-card--link" href="results/">
    <span class="csl-card__label">Review the claim</span>
    <h3>Audit the final results</h3>
    <p>Inspect effects, confidence intervals, all paired transitions, and the complete mechanism audit.</p>
    <span class="csl-card__cta">Open results</span>
  </a>
  <a class="csl-card csl-card--link" href="system/">
    <span class="csl-card__label">Build on the work</span>
    <h3>Understand the system</h3>
    <p>Trace ContractIR, typed refusal, runtime parity, inverse transduction, and paired evaluation.</p>
    <span class="csl-card__cta">Inspect architecture</span>
  </a>
  <a class="csl-card csl-card--link" href="reproducibility/">
    <span class="csl-card__label">Verify locally</span>
    <h3>Replay the artifacts</h3>
    <p>Recompute row scores and summaries without a GPU, model download, or hosted service.</p>
    <span class="csl-card__cta">Choose an audit path</span>
  </a>
</div>

## The complete evidence chain

<figure class="csl-figure">
  <img src="assets/figures/cross-family-evidence.svg" alt="Paired effects across corrected Qwen, canonical Llama, and executable decision gates">
  <figcaption>The current forest plot uses the final canonical Llama correction. All intervals and transition counts are generated from frozen machine-readable summaries.</figcaption>
</figure>

<div class="csl-timeline">
  <div class="csl-step">
    <h3>1. Baseline constraint study</h3>
    <p>Schema compliance reached 100%, while recoverable GSM8K accuracy fell 18.4 points against matched prompt-only JSON.</p>
  </div>
  <div class="csl-step">
    <h3>2. Qwen representation alignment</h3>
    <p>A native integer plus deterministic stringification produced a positive scoped estimate after runner correction.</p>
  </div>
  <div class="csl-step">
    <h3>3. Cross-family Llama test</h3>
    <p>The direction reversed on 150 randomly selected unseen items under one shared XGrammar runtime.</p>
  </div>
  <div class="csl-step">
    <h3>4. Canonical correction and executable gate</h3>
    <p>Exact schema equivalence did not rescue the result, and the bounded tool-call pilot found no execution benefit.</p>
  </div>
</div>

[Follow every gate and correction](studies/evidence-overview.md){ .csl-button .csl-button--secondary }

## What the negative result enabled

The supported direction is not an optimizer that silently rewrites schemas. It is a
measurement system that tells an engineer when a valid contract change alters model
behavior.

That product is now implemented as
[StructTrace](https://github.com/Vaibhav701161/structtrace). The lab remains the frozen research
authority; StructTrace provides the reusable paired runner, deterministic evaluation, evidence
replay, recurring regression cases, and release workflow derived from the findings.

[Trace the research-to-product lineage](system/structtrace-productization.md){ .csl-button .csl-button--secondary }

| System capability | Why it exists |
|---|---|
| Static contract analysis | Prove a narrow inverse mapping or refuse the transform |
| Shared paired runtime | Keep model, prompt, template, backend, and decoding aligned |
| Structural and semantic scoring | Expose valid-but-wrong outputs instead of hiding them |
| Executable wrappers | Test whether a valid call actually causes the correct state |
| Transition and uncertainty analysis | Show repairs, regressions, intervals, and discordant cases |
| Artifact replay | Let reviewers recompute results without cloud inference |

<figure class="csl-figure">
  <img src="assets/figures/research-system-architecture.svg" alt="Contract-sensitivity evaluation pipeline">
  <figcaption>The caller contract remains authoritative. Unsupported transforms stop before generation, and empirical quality remains a separate decision gate.</figcaption>
</figure>

## System boundary

The compiler path is intentionally narrow and auditable:

<div class="csl-pipeline">External JSON Schema
        ↓
ContractIR
        ↓
Alignment analysis and typed refusal
        ↓
Internal JSON Schema
        ↓
XGrammar or Outlines
        ↓
Internal object
        ↓
Deterministic inverse transducer
        ↓
Original external-schema validation
        ↓
Caller-facing object and paired metrics</div>

Information must be preserved at every boundary. Unsupported references, ambiguous
unions, or arbitrary regular-expression rewrites fail closed rather than being
silently approximated.

## Explore the project

<div class="csl-card-grid">
  <div class="csl-card">
    <span class="csl-card__label">Learn</span>
    <h3>Constrained decoding</h3>
    <p>Understand token masking, schema enforcement, and why structural validity does not imply correctness.</p>
    <a href="concepts/constrained-decoding/">Read the foundations</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Results</span>
    <h3>Technical dashboard</h3>
    <p>Review accepted effects, validity gaps, transition balance, item maps, and artifact scope.</p>
    <a href="results/">Open the dashboard</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Evidence</span>
    <h3>Paired research record</h3>
    <p>Inspect each model family, dataset, confidence interval, transition matrix, and frozen decision.</p>
    <a href="studies/evidence-overview/">Review the studies</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Methods</span>
    <h3>Cross-study methodology</h3>
    <p>Understand frozen comparison surfaces, denominator policy, paired statistics, and corrections.</p>
    <a href="methods/">Read the methodology</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">System</span>
    <h3>Fail-closed architecture</h3>
    <p>Trace ContractIR, alignment plans, runtime parity, inverse transduction, and validation boundaries.</p>
    <a href="architecture/">Inspect the architecture</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Audit</span>
    <h3>Artifact replay</h3>
    <p>Recompute accepted row scores and paired summaries locally without a model download or GPU.</p>
    <a href="reproducibility/artifact-replay/">Run the replay</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Reference</span>
    <h3>Supported contracts</h3>
    <p>See which schema features are supported, experimental, prototype-only, or explicitly refused.</p>
    <a href="supported-contracts/">Open the support matrix</a>
  </div>
  <div class="csl-card">
    <span class="csl-card__label">Provenance</span>
    <h3>Evidence map</h3>
    <p>Reach protocols, raw JSONL, manifests, canaries, validators, audits, and decision reports.</p>
    <a href="reproducibility/evidence-map/">Trace the artifacts</a>
  </div>
</div>

## Engineering guarantees

- Frozen experiments remain immutable and are never overwritten by later runners.
- Errors, cap hits, and invalid objects remain in the denominator.
- Canary expansion depends on operational integrity, not early semantic success.
- Model and tokenizer revisions, package environments, datasets, and run signatures
  are recorded in manifests.
- Every confirmatory discordance is retained and attributed.
- Negative findings remain public and guide the current architecture.

<div class="csl-callout">
  <p><strong>Audit the conclusion yourself.</strong><br><span class="csl-caption">The lightweight path replays 464 raw-output rows from its declared scopes with no GPU dependency.</span></p>
  <a class="csl-button csl-button--primary" href="getting-started/quickstart/">Open quickstart</a>
</div>
