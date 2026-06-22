---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Aa-FACTION-STATE
phase: open
date: 2026-06-22
tags: [faction, faction-state, authoritative-state, core-model, phase-5]
---

# TCK-20260619-E53Aa-FACTION-STATE

## Title
Epic 5.3Aa · FactionState Durable Model + AuthoritativeState Field

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add `FactionState` as a V2 frozen-dataclass durable model in `src/core/state.py` and register it in `AuthoritativeState.factions`. Also add the companion `FactionUpdate` typed mutation record in `src/core/updates.py` so later tickets can express faction mutations through the authoritative path. Build fresh — do NOT reference `docs/systems/grand_strategy.md`.

## Scope

**FactionState** (in `src/core/state.py`, adjacent to `GroupRecord` ~line 514):
```python
@dataclass(frozen=True, slots=True)
class FactionState:
    faction_id: str
    territory: Tuple[str, ...] = ()           # region_ids controlled
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0

    def to_canonical_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, d: dict) -> "FactionState": ...
```

**AuthoritativeState** — add field:
```python
factions: Dict[str, FactionState] = field(default_factory=dict)
```
Place after `groups` field. Must not disturb existing `slots=True` / cache fields.

**FactionUpdate** (in `src/core/updates.py`):
```python
@dataclass(frozen=True, slots=True)
class FactionUpdate:
    faction_id: str
    tension_delta: float = 0.0
    military_strength_set: Optional[float] = None
    territory_add: Tuple[str, ...] = ()
    territory_remove: Tuple[str, ...] = ()
    resources_delta: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations_set: Dict[str, str] = field(default_factory=dict)
    active_doctrines_set: Optional[Tuple[str, ...]] = None

    def is_noop(self) -> bool: ...
```

**StateUpdate** — add field:
```python
faction_updates: list[FactionUpdate] = field(default_factory=list)
```
Update `StateUpdate.merge()` to merge faction_updates lists.

**Apply path** — add faction update application in `src/engine/apply_plan.py` (or `apply.py`) to apply `FactionUpdate` objects to `AuthoritativeState.factions`, following the same pattern as existing typed update application (e.g. `RegionState` updates).

## Out of Scope
- FactionDecisionPhase (E53Ab)
- Directive propagation (E53Ac)
- Tension update from events (E53Ad)
- Diplomatic relations logic (E53B)

## Acceptance Criteria
- `FactionState` is constructible, frozen, and serializes/deserializes via `to_canonical_dict()` / `from_dict()` round-trip
- `AuthoritativeState(tick=0, seed=0)` instantiates with `factions={}` without error
- `FactionUpdate` applies correctly: `tension_delta` accumulates, `territory_add/remove` merge correctly, `military_strength_set` overwrites
- Existing `AuthoritativeState` tests continue to pass (no regressions)
- `test_faction_state_serialization_round_trip` passes
- `test_authoritative_state_has_factions_field` passes
- `test_faction_update_apply_tension_delta` passes

## Related Tickets
- TCK-20260619-E53A-FACTION-AGENT (parent epic)
- TCK-20260619-E53Ab-DECISION-PHASE (depends on this)
- TCK-20260619-E53Ac-DIRECTIVE-PROP (depends on this)
- TCK-20260619-E53Ad-TENSION-UPDATE (depends on this)

## Related Docs
- `docs/engine/authoritative_mutation_pipeline_contract.md` (mutation rules and apply-path law)
- `docs/core/state.md` (immutability law)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/core/state.py` (~L514, GroupRecord vicinity; ~L1003 AuthoritativeState)
- `src/core/updates.py` (add FactionUpdate; update StateUpdate)
- `src/engine/apply_plan.py` or `src/engine/apply.py` (apply faction updates)
- `tests/unit/faction/test_faction_state.py` (new file)

## Assumptions / Open Questions
- `FactionState` uses string `faction_id` (catalog-registered) — consistent with region/resource-node keying; the existing `Faction(IntEnum)` on entities is a separate numeric tag and must NOT be replaced.
- `resources: Dict[str, int]` keys are resource type strings (e.g. "gold", "iron") — follow existing resource naming conventions in catalog.
- `diplomatic_relations: Dict[str, str]` maps faction_id → relation_label (e.g. "allied", "hostile", "neutral") — labels to be formalized in E53B; for now accept any string.

## Implementation Notes
- `AuthoritativeState` uses `slots=True` — new field must have a default; place it before the `_readonly_cache` and other private cache fields.
- Follow the exact pattern used by E52A for `RegionState.population_cohorts`: add field, update `to_canonical_dict`, update `apply_plan.py`.
- `StateUpdate.merge()` must handle `faction_updates` list concatenation; verify `is_noop()` is updated accordingly.

## Test Summary
```bash
pytest tests/unit/faction/ -x -v
pytest tests/unit/core/test_state.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
