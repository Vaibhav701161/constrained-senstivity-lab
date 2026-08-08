# Bounded executable tool-call pilot hypothesis

## Status

This hypothesis is frozen after the second-family replication produced its preregistered Red outcome and before any pilot model output is generated.

## Question

On pinned BFCL single-turn, single-function cases, does replacing a model-facing canonical signed integer string with a native JSON integer improve the probability that the model emits an externally valid call with exact argument semantics that executes to the correct deterministic state?

## Control

The model emits the externally required canonical integer strings directly.

## Treatment

The model emits native JSON integers. A deterministic inverse transducer reconstructs canonical integer strings and validates the unchanged external tool contract before execution.

## Primary hypothesis

On the random 30-case primary sample, treatment executable-contract success is at least five percentage points higher than control, treatment-only wins exceed control-only wins, external validity is 100%, and no coherent regression cluster appears.

## Null and adverse outcomes

An effect at or below zero, control-only wins equal to or greater than treatment-only wins, lower external validity, or a coherent new failure mode is a Red practical result.

## Scope

This is the single bounded practical pilot authorized by the Red second-family result. It is not an official BFCL leaderboard submission and cannot justify broad compiler claims by itself.
