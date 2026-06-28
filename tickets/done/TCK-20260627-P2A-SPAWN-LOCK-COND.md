---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2A-SPAWN-LOCK-COND
phase: done
date: 2026-06-27
tags: [p2, spawn-lock, lock-until-tick, conditional, activation-delay, project-state]
---

# TCK-20260627-P2A-SPAWN-LOCK-COND

## Title
Make `lock_until_tick` conditional on threat resolution, add 50-tick cap

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Initial spawn projects lock entities via `lock_until_tick` for ~200 ticks post-combat, regardless of whether the triggering threat is still active. 20% of a standard 1,000-tick run is enforced dead time. Entities whose threats resolve earlier (HP restored, enemies dead) remain locked until the fixed tick, wasting behavioral capacity. Source: D06 F2.

## Scope
- Find where `lock_until_tick` is assigned for initial spawn projects (likely in `src/engine/apply.py` or `ProjectState` initialization).
- Make the lock conditional: release when triggering threat is resolved (entity HP > 80%, no active hostile in vicinity) OR when a 50-tick cap is reached.
- Add cap: `lock_until_tick = min(current_tick + 50, existing_lock_tick)`.
- Verify: in a D06-style 1,000-tick run, behavioral activity begins before tick 50.

## Out of Scope
- Changing the rejection backoff mechanism (P1-A).
- Changes to spawn rate (P2-B).

## Acceptance Criteria
- [ ] `lock_until_tick` assignment is conditional: cap at `current_tick + 50`.
- [ ] Threat-resolution check releases the lock early when entity HP > 80% and no hostile entity is in vicinity.
- [ ] Behavioral events begin before tick 50 in a 1,000-tick run with seed 42.
- [ ] Regression: existing spawn and combat tests pass.

## Related Tickets
- TCK-20260627-P1A-REJECTION-BACKOFF (complementary — both reduce dead-time in early ticks)
- TCK-20260627-P2B-SPAWN-CADENCE (spawn population health — do after this)

## Related Docs
- `docs/audits/D06_longrun_health.md` F2
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-AUDIT-D06/`

## Related Code Areas
- `src/engine/apply.py` (likely where `lock_until_tick` is set)
- `src/core/state.py` (`ProjectState` — if lock is stored here)
- `src/worldassembly/entity_spawner.py` (initial spawn context)

## Assumptions / Open Questions
- "Hostile in vicinity" is defined by the existing spatial query capability (`WorldIndexService` via `Kernel`).
- HP threshold 80% is a starting point — calibrate if needed.

## Implementation Notes
- Root cause: no single 200-tick lock exists; the D06 dead window is caused by cascading
  10-tick relocks as COMBAT_RETREAT/RECOVER goal keeps scoring high while HP is low.
- Added `_threat_resolved(hero, state)` helper in `adventure/phase.py` (pure read-only):
  returns True when `hp_ratio > 0.8` AND no alive entity of a different faction is within
  radius=10.0 (via `SpatialQueryService.nearby_entities`).
- Lock check at `phase.py` changed: `if tick < lock AND not _threat_resolved(hero, state): continue`.
- Cap via `min(tick + N, tick + 50)` at all lock assignment sites in `mapper.py` and
  `intelligence.py` (lines 1266, 1340). No behavior change (originals < 50) but documents
  the enforcement boundary.
- Updated existing regression test to use hp=40 (threat-active HP) so the lock remains
  enforced under the new conditional (test still verifies lock-while-threatened behavior).
- `engine/tactical.py:59` lock check NOT changed — that path governs combat task continuity.

## Test Summary
- Unit: entity with resolved threat (HP=100%, no hostiles) has lock released before cap.
- Integration: 1,000-tick run shows behavioral events before tick 50.

## Files Changed
- `src/domains/adventure/phase.py` — added `_threat_resolved()` helper and conditional lock check
- `src/domains/adventure/mapper.py` — cap lock at min(tick+10, tick+50)
- `src/systems/strategic_systems/intelligence.py` — cap detour and goal-scored project locks
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — updated HP to 40 for lock-active scenario
- `tests/unit/systems/test_spawn_lock_condition.py` — new: 6 targeted tests for conditional lock
- `docs/parity_ledger/strategic_cognition.yaml` — added STRAT-236

## Completion Summary
Investigation found no single 200-tick hardcoded lock; the D06 dead window (ticks 101–200) was caused by cascading 10-tick relocks as COMBAT_RETREAT/RECOVER goal kept scoring high while entity HP remained low. Primary fix: added `_threat_resolved(hero, state)` to `adventure/phase.py` that returns True when `hp_ratio > 0.8` AND no alive hostile entity of a different faction is within 10 units via `SpatialQueryService`. The lock check now reads `if tick < lock_until_tick and not _threat_resolved(hero, state): continue`, releasing the lock as soon as the threat resolves instead of waiting for the timer to cascade to ~200. Secondary: all lock assignment sites capped at `min(N, tick+50)` as an explicit enforcement boundary. Existing regression test updated to use hp=40 to keep its lock-while-threatened semantics. 6 new unit tests added covering early-release and lock-held conditions. All 19 tests pass. Parity ledger entry STRAT-236 added.
