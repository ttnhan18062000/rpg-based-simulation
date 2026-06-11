---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260428-PH10-EXTERNAL-TRUTH
artifact_type: plan
tags: [ph10, external, truth]
---

# Phase 10 Plan: External Truth and Replay Proof

## Goal
Expose authoritative transaction results and conservation metrics to external observers.

## Approach
1. Add `intent_results` to `EntityState`.
2. Update pipeline to record results.
3. Add global metrics for total items/gold.

## Verification
Replay test with rejected transactions.
