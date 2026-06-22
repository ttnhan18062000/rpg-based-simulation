---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Aa-FACTION-STATE
phase: done
date: 2026-06-22
tags: [faction, faction-state, authoritative-state, core-model, phase-5]
---

# TCK-20260619-E53Aa-FACTION-STATE

## Title
Epic 5.3Aa · FactionState Durable Model + AuthoritativeState Field

## Status
DONE

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

### Completed Implementation (2026-06-22)

**Step 1 — FactionState** (`src/core/state.py`): Added `FactionState` frozen dataclass with `slots=True` after `GroupRecord.to_canonical_dict()`. Includes `to_canonical_dict()` with sorted dicts and `object.__setattr__` cache bypass, and `from_dict()` with `tuple()` coercion for territory and active_doctrines.

**Step 2 — AuthoritativeState.factions** (`src/core/state.py`): Added `factions: Dict[str, "FactionState"] = field(default_factory=dict)` after `information_providers`. Updated `to_readonly()` to wrap `factions` with `ReadOnlyDict`.

**Step 3 — FactionUpdate** (`src/core/updates.py`): Added `FactionUpdate` frozen dataclass before `StateUpdate` with `is_noop()` checking all 7 semantic fields. Added `Tuple` to the typing imports.

**Step 4 — StateUpdate.faction_updates** (`src/core/updates.py`): Added `faction_updates: List[FactionUpdate]` field. Updated `is_noop()` to check `not self.faction_updates`. Updated `merge_many()`: init `new_faction_updates`, extend with noop-filtered entries from each other, pass in `replace()` call.

**Step 5 — apply.py** (`src/engine/apply.py`): Added `FactionState` to top-level imports. Added faction update resolution block before `AuthoritativeState(...)` constructor, using `getattr` guard for replay safety. Applied: tension clamped to [0.0, 1.0], territory set-union/difference, resources accumulated, relations overwritten, doctrines replaced. Passed `factions=new_factions` explicitly to the constructor.

**Step 6 — Tests** (`tests/unit/faction/`): Created `__init__.py` and `test_faction_state.py` with 10 tests. All 10 pass; all 13 regression tests pass.

## Test Summary
```bash
pytest tests/unit/faction/ -x -v
pytest tests/unit/core/test_state.py -x -v
```

## Files Changed
- `src/core/state.py` — Added `FactionState` dataclass; added `factions` field to `AuthoritativeState`; updated `to_readonly()`
- `src/core/updates.py` — Added `Tuple` import; added `FactionUpdate` dataclass; added `faction_updates` field to `StateUpdate`; updated `is_noop()` and `merge_many()`
- `src/engine/apply.py` — Added `FactionState` import; added faction update resolution block; added `factions=new_factions` to `AuthoritativeState()` constructor
- `tests/unit/faction/__init__.py` — New (empty)
- `tests/unit/faction/test_faction_state.py` — New, 10 tests
- `docs/parity_ledger/faction.yaml` — New; parity entries FAC-001 and FAC-002
- `docs/parity_ledger/substrate.yaml` — Updated with faction state reference

## Completion Summary
FactionState frozen dataclass added to state.py (after GroupRecord); factions: Dict[str, FactionState] field on AuthoritativeState with ReadOnlyDict wrapping in to_readonly(); FactionUpdate frozen dataclass in updates.py with is_noop(); faction_updates added to StateUpdate with merge_many() noop filtering; apply.py computes new_factions from FactionUpdate list and passes factions=new_factions to AuthoritativeState constructor; 10 new tests in tests/unit/faction/; parity entries FAC-001 and FAC-002 created in docs/parity_ledger/faction.yaml.
