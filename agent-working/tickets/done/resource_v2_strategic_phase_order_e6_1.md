---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: resource_v2_strategic_phase_order_e6_1
phase: done
date: unknown
tags: [resource_v2_strategic_phase_order_e6_1]
---

# TCK-20260503-STRATEGIC-PHASE-REALIGNMENT

## Title
Aligning Strategic Cognition with Tactical Execution (Phase Order)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Reduce the 1-tick latency between strategic redirection and tactical execution.

## Scope
- Re-evaluate the `AuthoritativePhaseSequence`.
- Move `StrategicIntelligenceSystem` and `StrategicRedirectionSystem` earlier in the `refine` pipeline (before Movement/Combat).
- Ensure strategic updates influence the *current* tick's tactical choices.

## Acceptance Criteria
- [ ] An entity that triggers a "Retreat" redirection in Tick N must be able to perform a "Retreat" move in Tick N.

## Related Code Areas
- src/engine/pipeline.py
- src/engine/phases.py
