---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E52G-SOVEREIGNTY-EVENTS
phase: done
date: 2026-06-28
tags: [world-evolution, sovereignty, world-event, observability, p3]
---

# TCK-20260628-E52G-SOVEREIGNTY-EVENTS

## Title
Sovereignty boundary shift events — SOVEREIGNTY_SHIFT WorldEvent emitted on ownership change

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Confirm sovereignty boundary shift events fire and are observable via recent_world_events. Added SOVEREIGNTY_SHIFT to WorldEventCategory and wired emission in WorldDynamicsSystem step 2.2.

## Scope
- `WorldEventCategory.SOVEREIGNTY_SHIFT` added to schema.py
- world_dynamics.py step 2.2: collect sovereignty_events when influence crosses ±100 and ownership changes
- world_dynamics.py step 2.2b: flush events into `update.world_events_add`
- 5 tests; WORLD-107 parity entry

## Out of Scope
- Content authoring (no calamity YAML changes needed — sovereignty events now fire from influence threshold)
- Faction war/siege integration (E53 scope)

## Acceptance Criteria
- [x] `SOVEREIGNTY_SHIFT` category in WorldEventCategory
- [x] Event emitted when influence >= 100 and owner not yet HERO_GUILD
- [x] Event emitted when influence <= -100 and owner not yet MONSTER_HORDE
- [x] No event when influence below threshold
- [x] Event payload contains influence and prev_owner
- [x] 5 tests pass; 260 combined world tests pass
- [x] WORLD-107 parity entry added

## Related Tickets
- Parent epic: TCK-20260628-E-WORLD-EVOLUTION
- Predecessor: TCK-20260628-E52F-TRAUMA-MOTIVATION

## Implementation Notes
- `sovereignty_events` list collected per region during step 2.2, flushed in one `update.replace()` at step 2.2b.
- Guard: `new_owner != owner_fid` prevents re-emitting when ownership was already set (idempotent).
- Events enter `recent_world_events` via the apply pipeline's `world_events_add` path (same path used by demographic cycle events E52A).

## Test Summary
5 tests in `tests/unit/world/test_sovereignty_events.py`:
- SOVEREIGNTY_SHIFT enum exists; hero takeover event; monster takeover event
- no event below threshold; payload contains influence value

## Files Changed
- `src/domains/world_emergence/schema.py` — SOVEREIGNTY_SHIFT added to WorldEventCategory
- `src/engine/world_dynamics.py` — step 2.2 sovereignty_events + step 2.2b flush
- `tests/unit/world/test_sovereignty_events.py` — 5 E52G tests (new file)
- `docs/parity_ledger/world_dynamics.yaml` — WORLD-107 added

## Completion Summary
Sovereignty shifts are now observable WorldEvents. The SOVEREIGNTY_SHIFT category is in the schema, emitted on ownership threshold crossing, and flushed to world_events_add where WorldEmergencePhase can aggregate them in subsequent ticks.
