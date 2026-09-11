---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E52F-TRAUMA-MOTIVATION
phase: done
date: 2026-06-28
tags: [world-evolution, trauma, motivation, concern, p3]
---

# TCK-20260628-E52F-TRAUMA-MOTIVATION

## Title
Trauma→motivation feedback: direct regional trauma_score → DANGER ConcernState injection

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Validate and fix trauma→entity motivation feedback. The previous path (trauma → hazard_level → DANGER concern) required ~3500 ticks. E52F adds a direct path: regional trauma_score > 0.5 immediately injects a DANGER ConcernState into entity.strategic.concerns, satisfying the <100-tick requirement.

## Scope
- `TraumaRegionConcernBridge.inject_concerns()` in `src/domains/world_emergence/services.py`
- Step 2.3 wiring in `src/engine/world_dynamics.py`
- `TRAUMA_CONCERN_THRESHOLD=0.5`, `URGENCY_SCALE=50.0`
- 9 tests; WORLD-106 parity entry

## Out of Scope
- Removing the existing hazard_level → concern path (EventInterpreter.interpret_regional_danger)
- Sovereignty boundary validation (E52G)

## Acceptance Criteria
- [x] Entity in region with trauma_score > 0.5 receives DANGER ConcernState on same tick
- [x] Urgency = min(1.0, trauma_score / 50.0)
- [x] Dead/inactive entities excluded
- [x] Entity without region_id excluded
- [x] 9 tests pass; 255 world+emergence tests pass
- [x] WORLD-106 parity ledger entry added

## Related Tickets
- Parent epic: TCK-20260628-E-WORLD-EVOLUTION
- Predecessor: TCK-20260628-E52E-SEASONAL-PROPAGATION
- Successor: TCK-20260628-E52G-SOVEREIGNTY-EVENTS

## Implementation Notes
- Uses `StrategicUpdate.concerns_add_or_update` — the authoritative path for concern injection.
- Concern id is deterministic: `"regional_trauma_{region_id}"`. Overwrites each tick (idempotent).
- Wired in step 2.3 after ownership/calamity progression but before cadence-gated section.
- Existing hazard_level → concern path (interpret_regional_danger, fires at hazard > 0.7) is kept as the high-hazard escalation signal; the new path gives faster feedback for moderate trauma.

## Test Summary
9 tests in `tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py`:
- no regions/empty; below threshold (exactly at); above threshold; urgency scaling; urgency cap
- dead entity excluded; no region_id excluded; safe vs unsafe regions; concern within 1 tick

## Files Changed
- `src/domains/world_emergence/services.py` — TraumaRegionConcernBridge class + Dict/StrategicUpdate imports
- `src/engine/world_dynamics.py` — step 2.3 trauma concern injection
- `tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py` — 9 E52F tests (new)
- `docs/parity_ledger/world_dynamics.yaml` — WORLD-106 added

## Completion Summary
Direct trauma→entity motivation path implemented. Any entity in a region with 1+ deaths (trauma > 0.5) now gets a DANGER ConcernState on the same tick, closing the <100-tick feedback loop.
