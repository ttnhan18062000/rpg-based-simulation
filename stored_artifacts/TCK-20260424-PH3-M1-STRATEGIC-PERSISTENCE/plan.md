---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260424-PH3-M1-STRATEGIC-PERSISTENCE
artifact_type: plan
tags: [ph3, m1, strategic, persistence]
---

# Strategic Objective Persistence Plan

## Goal
Implement deterministic project lifecycle management in `StrategicIntelligenceSystem`.

## Proposed Changes
- Add `project_lock_until` and status tracking to `StrategicComponent`.
- Update `StrategicIntelligenceSystem.evaluate_strategic_intent` to handle suspension/resumption.
- Fix `DeterministicScheduler` to exclude inactive entities.

## Verification
- Create `tests/parity/test_strategic_persistence.py`.
- Run parity tests to confirm project survival across combat ticks.
