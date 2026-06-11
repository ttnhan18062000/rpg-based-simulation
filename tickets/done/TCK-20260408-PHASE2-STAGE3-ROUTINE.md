---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260408-PHASE2-STAGE3-ROUTINE
phase: done
date: 2026-04-08
tags: [phase2, stage3, routine]
---

# Ticket: TCK-20260408-PHASE2-STAGE3-ROUTINE
Title: Phase 2 Stage 3: Routine and Biological Needs Simulation
Status: INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the biological needs (sleep, hunger) and daily routine simulation for entities. This is part of the Phase 2 Macro-Interest and Behavioral Realism design shift, designated as Stage 3.

## Scope
- Authoritative biological decay (sleep debt, hunger increase).
- Action implementation for `SLEEP` and `EAT`.
- AI utility scoring for biological goals.
- Time-of-day biases for routines (circadian rhythm).
- UI exposure of biological stats.

## Out of Scope
- Household economics.
- Complex regional consequence systems.
- Advanced disease or stamina-specific fatigue (beyond basic sleep debt).

## Acceptance Criteria
- [x] Entities accumulate sleep debt and hunger over time.
- [x] Entities propose `SLEEP` or `EAT` actions when needs are critical.
- [x] Sleep debt and hunger decrease when the corresponding action is applied.
- [x] Routine states are visible in the entity inspection API/UI.
- [x] Integration tests verify the biological loop.

## Related Tickets
- TCK-20260407-PHASE2-SOCIAL (Done)

## Related Stored Artifacts
- stored_artifacts/social_propagation_plan/ (Reference for AOA patterns)

## Open Questions or Assumptions
- Assumption: 1 hour = 10 ticks (240 ticks per day).
- Question: Should hunger result in damage if it reaches 1.0? (Wait for design feedback or implement as non-fatal first).

## Current Status
- [x] Context Scan
- [/] Planning
- [ ] Implementation
- [ ] Verification
