---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Cb-SIEGE-MODEL
phase: open
date: 2026-06-22
tags: [faction, war, siege, state-model, squad-commitment, phase-5]
---

# TCK-20260619-E53Cb-SIEGE-MODEL

## Title
Epic 5.3Cb · Squad Commitment + Siege State Model

## Status
OPEN

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

**Squad commitment** (runs once when WAR is detected for a region pair, or each tick to refresh):
- For each active WAR faction pair, identify GUARD + WARRIOR entities whose `NavigationComponent.region_id` is adjacent to or within a contested region
- Produce `StateUpdate` upserting a `GroupRecord` with `roles = {entity_id: "FACTION_SQUAD"}` for each committed entity
- Limit: up to 5 entities per faction per contested region (deterministic: sort by entity_id, take first 5)

**Siege initiation** (first tick WAR is detected for a region pair with no existing `siege_state`):
- Select the contested region (attacker's nearest non-owned region adjacent to their territory)
- Emit `WorldUpdate(region_id=..., siege_state_set=SiegeState(attacker_faction_id, defender_faction_id, 0.0, current_tick))`

**Siege degradation** (each tick with active `siege_state`):
- Attacker side: emit `WorldUpdate(region_id=..., service_availability_delta=-0.05, siege_progress_delta=0.05)`
- Defender side: emit `FactionDirective(kind="REINFORCE", target_region_id=...)` so defender entities score reinforcement routes higher (via E53Ac scoring)
- Defender reinforcement effect: if defender has ≥ 3 squad entities in the contested region, emit `WorldUpdate(region_id=..., service_availability_delta=+0.02, siege_progress_delta=-0.02)` to partially offset attacker's progress

## Out of Scope
- Territory transfer when `siege_progress ≥ 1.0` (E53Cc)
- War exhaustion / military_strength drain (E53Cd)
- Combat resolution between squads — this is handled by the existing combat pipeline; `MilitaryConflictPhase` only governs siege-level state, not individual engagements

## Acceptance Criteria
- `SiegeState` round-trips via `to_canonical_dict` / `from_dict`
- `RegionState` serializes `siege_state` and `service_availability` correctly
- `WorldUpdate` merge correctly accumulates `service_availability_delta` and `siege_progress_delta`
- Apply-path clamps `service_availability` to [0.0, 1.0]
- Unit test `test_siege_state_initiates_on_war` passes: given a WAR pair, `MilitaryConflictPhase` emits a `WorldUpdate` that sets `siege_state`
- Unit test `test_siege_degrades_service_availability` passes: after N ticks, `service_availability` decreases by `0.05 * N` (no defender reinforcement)
- Unit test `test_defender_reinforcement_offsets_siege_progress` passes: with ≥ 3 defender entities in region, net `siege_progress_delta = 0.05 - 0.02 = 0.03`
- Unit test `test_squad_commitment_group_record` passes: GUARD + WARRIOR entities near contested region are added to a `GroupRecord` with `"FACTION_SQUAD"` role

## Related Tickets
- TCK-20260619-E53C-WAR (parent epic)
- TCK-20260619-E53Ca-CONFLICT-PHASE (required)
- TCK-20260619-E53Cc-TERRITORY-TRANSFER (blocked on this)

## Related Docs
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md` (Decision 2: SiegeState as sub-record; Decision 3: service_availability; Decision 5: squad commitment)
- `docs/mechanics/02_combat_laws.md` (standard damage formula — do NOT special-case siege combat)
- `src/core/state.py:L208` (RegionState reference)
- `src/core/updates.py:L747` (WorldUpdate reference)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/core/state.py` (SiegeState new class, RegionState additions)
- `src/core/updates.py` (WorldUpdate additions)
- `src/engine/apply_plan.py` (apply siege fields)
- `src/engine/military_conflict.py` (extend with siege logic)

## Assumptions / Open Questions
- `SiegeState.attacker_faction_id` is `str` (catalog ID), consistent with `FactionState.faction_id: str`. The `owner_faction_id: Optional[int]` mismatch on `RegionState` must be resolved in E53Ca's investigation; this ticket should not proceed until that resolution is documented.
- "Adjacent region" lookup: use existing `AuthoritativeState.regions` bounds intersection or a static adjacency map. If no adjacency utility exists, implement a simple bounding-box distance check (sorted deterministically by region_id for tiebreaking).

## Implementation Notes
- `SiegeState` is durable (survives across ticks) — it must have `to_canonical_dict` and `from_dict`.
- `siege_state_clear` flag on `WorldUpdate` (not `siege_state_set=None`) is needed because `None` is the "no-op" sentinel for optional fields in the merge protocol.
- Apply-path must handle the case where `siege_progress_delta` would push `siege_progress > 1.0` — clamp at 1.0 and leave the transfer to E53Cc.

## Test Summary
```bash
pytest tests/unit/faction/test_siege_model.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
