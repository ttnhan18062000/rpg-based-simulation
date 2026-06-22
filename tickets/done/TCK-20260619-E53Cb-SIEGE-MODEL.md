---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Cb-SIEGE-MODEL
phase: done
date: 2026-06-23
tags: [faction, war, siege, state-model, squad-commitment, phase-5]
---

# TCK-20260619-E53Cb-SIEGE-MODEL

## Title
Epic 5.3Cb · Squad Commitment + Siege State Model

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add durable siege state to `RegionState` and implement the `MilitaryConflictPhase` logic for committing faction squads and degrading `service_availability` each tick a siege is active. Defender reinforcement directive also implemented here.

**Requires:** TCK-20260619-E53Ca-CONFLICT-PHASE

## Scope

### Data model additions

**`SiegeState` frozen dataclass** (new, in `src/core/state.py` adjacent to `RegionState`):
```python
@dataclass(frozen=True, slots=True)
class SiegeState:
    attacker_faction_id: str
    defender_faction_id: str
    siege_progress: float   # 0.0 to 1.0; transfer triggers at >= 1.0
    started_tick: int
```

**`RegionState` additions** (fields appended following E52A `population_cohorts` pattern):
- `siege_state: Optional[SiegeState] = None`
- `service_availability: float = 1.0`  (0.0 to 1.0)

**`WorldUpdate` additions** (in `src/core/updates.py`):
- `service_availability_delta: float = 0.0`
- `siege_state_set: Optional[SiegeState] = None`   (None = no change; use `siege_state_clear = True` to remove)
- `siege_state_clear: bool = False`
- `siege_progress_delta: float = 0.0`

**Apply-path** (`src/engine/apply_plan.py`): handle new `WorldUpdate` fields — apply `service_availability_delta` (clamped [0.0, 1.0]), apply `siege_state_set`, clear `siege_state` if `siege_state_clear=True`, accumulate `siege_progress_delta` into `SiegeState.siege_progress`.

### MilitaryConflictPhase logic (extend `src/engine/military_conflict.py`)

**Squad commitment** (each tick when WAR is detected):
- Identify GUARD entities in contested region via `NavigationComponent.region_id`
- Produce `StateUpdate` upserting a `GroupRecord` with `roles = {entity_id: "FACTION_SQUAD"}` for each committed entity
- Limit: up to 5 entities per contested region (deterministic: sort by entity_id, take first 5)

**Siege initiation** (first tick WAR is detected for a region pair with no existing `siege_state`):
- Select contested region: resume existing siege first; then defender territory min; then nearest by centroid distance
- Emit `WorldUpdate(region_id=..., siege_state_set=SiegeState(attacker_faction_id, defender_faction_id, 0.0, current_tick))`

**Siege degradation** (each tick with active WAR):
- Emit `WorldUpdate(region_id=..., service_availability_delta=-0.05, siege_progress_delta=0.05)`
- Defender reinforcement: if ≥ 3 GUARD entities in contested region → emit `WorldUpdate(service_availability_delta=+0.02, siege_progress_delta=-0.02)`

## Out of Scope
- Territory transfer when `siege_progress ≥ 1.0` (E53Cc)
- War exhaustion / military_strength drain (E53Cd)
- Combat resolution between squads

## Acceptance Criteria
- [x] `SiegeState` round-trips via `to_canonical_dict` / `from_dict`
- [x] `RegionState` carries `siege_state` and `service_availability` fields with defaults
- [x] `WorldUpdate` merge correctly accumulates `service_availability_delta` and `siege_progress_delta`
- [x] Apply-path clamps `service_availability` to [0.0, 1.0] and `siege_progress` to [0.0, 1.0]
- [x] `MilitaryConflictPhase` emits `WorldUpdate` with `siege_state_set` on first WAR tick
- [x] Siege degradation emits correct deltas each tick
- [x] Defender reinforcement (≥3 GUARD entities) emits offset WorldUpdate
- [x] GUARD entities in contested region committed to `GroupRecord` with `"FACTION_SQUAD"` role
- [x] 84/84 faction tests pass; 16/16 siege model tests pass

## Related Tickets
- TCK-20260619-E53C-WAR (parent epic)
- TCK-20260619-E53Ca-CONFLICT-PHASE (required)
- TCK-20260619-E53Cc-TERRITORY-TRANSFER (blocked on this)

## Related Docs
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`
- `docs/mechanics/02_combat_laws.md`
- `docs/parity_ledger/faction.yaml` (FAC-008, FAC-009)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/core/state.py` (SiegeState new class, RegionState additions)
- `src/core/updates.py` (WorldUpdate additions, merge())
- `src/engine/apply_plan.py` (siege apply block lines 125-140)
- `src/engine/military_conflict.py` (full siege loop)

## Assumptions / Open Questions
- `owner_faction_id: Optional[int]` mismatch on RegionState vs `FactionState.faction_id: str` — documented, deferred to E53Cc.
- WARRIOR EntityRole does not exist in the codebase (only GUARD=5). Squad commitment uses GUARD only.
- "Adjacent region" resolved via centroid bounding-box distance (deterministic by region_id tiebreaker).

## Implementation Notes
- `siege_state_clear` flag prevents `None` ambiguity in WorldUpdate merge protocol.
- Apply-path replicates same clamping at both service_availability and siege_progress bounds.
- `_FakeState` in `test_military_conflict_phase.py` updated to include `regions={}` and `entities={}` after E53Cb extended execute() to access those fields.

## Test Summary
```
tests/unit/faction/test_siege_model.py          16 passed
tests/unit/faction/test_military_conflict_phase.py   6 passed
tests/unit/faction/                             84 passed total
```

## Files Changed
- `src/core/state.py` — added `SiegeState` dataclass; extended `RegionState` with `siege_state`, `service_availability`, `to_canonical_dict()` update
- `src/core/updates.py` — added `WorldUpdate` siege fields + `merge()` additions
- `src/engine/apply_plan.py` — siege apply block in region loop (lines 125-140)
- `src/engine/military_conflict.py` — full siege loop: `get_war_pairs`, `_find_contested_region`, `_find_guard_entities_in_region`, `execute()`
- `tests/unit/faction/test_siege_model.py` — new (16 tests)
- `tests/unit/faction/test_military_conflict_phase.py` — updated `_FakeState` to include `regions`, `entities`
- `docs/parity_ledger/faction.yaml` — added FAC-008, FAC-009

## Completion Summary
E53Cb is fully implemented. `SiegeState` is a durable frozen dataclass stored on `RegionState`. `WorldUpdate` carries four siege fields; the apply-path mutates them with clamping. `MilitaryConflictPhase.execute()` performs: WAR pair detection → contested region selection → siege initiation (first tick) → per-tick degradation → defender reinforcement → squad GroupRecord commitment. All 84 faction unit tests pass.
