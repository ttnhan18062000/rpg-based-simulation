---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260413-STRAT-DEPTH-VISIBILITY
artifact_type: plan
tags: [strat, depth, visibility]
---

# Investigation: Strategic Depth & Visibility Hardening

## Overview
The strategic cognition layer is stable but lacks depth in two areas:
1. **Durable narrative**: Turning points and place attachments are not yet durable in the cognition graph.
2. **Contextual reprioritization**: Directive mutations from life events (e.g. near-death) lack thresholds and history-sensitivity.

## Findings
- `ActionSystem.apply_strategic_update` needs idempotency verification.
- `EntityInspector` crashes if some strategic fields are `None`.
- `CognitionGraphExporter` currently skips `TurningPoints`.
- `DirectiveMutationService` has a hardcoded threshold of 0.8 which needs to be verified in practice.

# Implementation Plan: TCK-20260413-STRAT-DEPTH-VISIBILITY

## Goal
Harden transport stability, expand observability, and verify strategic continuity.

## Proposed Changes
1. **ActionSystem**: Audit `apply_strategic_update` for idempotency.
2. **Inspector**: Add smoke tests with `capsys` and fix optional field rendering.
3. **Graph Exporter**: Add nodes/edges for `TurningPoint` and `PlaceAttachment`.
4. **Logic**: Implement `tests/integration/strategy/test_strategic_continuity.py` for thresholded reprioritization.

# Test Plan: TCK-20260413-STRAT-DEPTH-VISIBILITY

## Automated Tests
- `tests/integration/strategy/test_strategic_transport.py`: Multi-record updates, idempotency, routing.
- `tests/ui/test_inspector_strategy_smoke.py`: CapSys based rendering verification.
- `tests/integration/strategy/test_strategic_continuity.py`: Salience thresholding and priority strengthening.
- `pytest tests/integration/strategy/ tests/e2e/strategy/`

## Manual Verification
- CLI inspection of an entity with multiple turning points.
