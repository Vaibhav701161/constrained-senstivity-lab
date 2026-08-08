---
title: Orientation
description: Choose a learning, results, architecture, or reproducibility path through the research
---

# Orientation

Constrained Sensitivity Lab is a research engineering repository, not a hosted model
API. Its primary output is evidence about structured-output systems and reusable
infrastructure for producing that evidence.

## Choose your path

=== "I am new to structured outputs"

    Read [Constrained decoding](../concepts/constrained-decoding.md), then
    [Contract sensitivity](../concepts/contract-sensitivity.md). Together they
    explain the problem without assuming prior research experience.

=== "I want the result"

    Start with the [results dashboard](../results/index.md), then follow the
    [evidence overview](../studies/evidence-overview.md). Together they separate the
    positive Qwen estimate, the corrected negative Llama result, and the executable
    pilot.

=== "I want to audit the work"

    Run the [artifact replay](../reproducibility/artifact-replay.md), inspect the
    [evidence map](../reproducibility/evidence-map.md), and compare each report to
    its raw JSONL and source manifest.

=== "I want to extend the system"

    Start with the [system overview](../system/index.md),
    [architecture](../architecture.md), and
    [supported contracts](../supported-contracts.md). Unsupported schema features
    are deliberately refused rather than silently approximated.

## What is stable

- Deterministic integer to canonical-string transduction is supported.
- Original external-schema validation is mandatory after inverse transduction.
- Artifact replay and the lightweight test suite run without model weights or a GPU.
- The checked-in studies have frozen protocols, source manifests, and decision reports.

## What is not claimed

- The transform is not a universal model-quality optimizer.
- The BFCL-based pilot is not an official BFCL leaderboard submission.
- Backend byte parity is implementation evidence, not an independent replication.
- Correct final answers are not treated as proof of faithful reasoning.

!!! info "Repository status"

    The current product direction is measurement infrastructure: identify
    contract-sensitive boundaries, run paired evaluations, and prevent unsupported
    transformations from entering production unnoticed.
