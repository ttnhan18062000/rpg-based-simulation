---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21A-NODE-SCHEMA
phase: done
date: 2026-06-20
tags: [resource-ecology, state-schema, event-taxonomy, phase-2]
---

# TCK-20260619-E21A-NODE-SCHEMA

## Title
Epic 2.1A · ResourceNodeState Schema Extension + RESOURCE_RECOVERED Event

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ResourceNodeState` lacks `regen_rate_per_tick` — the per-tick charge replenishment rate needed by E21B's regen loop. `WorldEventCategory` lacks `RESOURCE_RECOVERED` — the counterpart to `RESOURCE_DEPLETED`. This ticket adds both with zero behavior change (no logic, only schema).

**Blocks:** TCK-20260619-E21B-REGEN-SERVICE

## Scope

### 1. Add `regen_rate_per_tick` to `ResourceNodeState` — `src/core/state.py:L808`

```python
@dataclass(frozen=True, slots=True)
class ResourceNodeState:
    ...
    respawn_cooldown: int = 100
    cooldown_remaining: int = 0
    regen_rate_per_tick: int = 0   # NEW: charges regenerated per ecology tick (0 = no regen)
```

- Default `0` preserves all existing behavior (no regen by default)
- Add to `to_canonical_dict()` (currently ends at `cooldown_remaining`)
- No changes to callers needed (keyword arg with default)

### 2. Add `RESOURCE_RECOVERED` to `WorldEventCategory` — `src/domains/world_emergence/schema.py:L12`

```python
class WorldEventCategory(str, Enum):
    ...
    RESOURCE_DEPLETED = "RESOURCE_DEPLETED"
    RESOURCE_RECOVERED = "RESOURCE_RECOVERED"   # NEW
```

That's the complete scope. No other changes.

## Out of Scope
- Any regen logic (E21B)
- Emitting events (E21B)
- Consumer changes (E21D)

## Acceptance Criteria
- `ResourceNodeState(id=1, kind="IRON", position=(0,0), yields_item="iron_ore", remaining_charges=3, max_charges=5, required_ticks=10, regen_rate_per_tick=2)` constructs without error
- `ResourceNodeState(...).to_canonical_dict()` includes `"regen_rate_per_tick": 2`
- `WorldEventCategory.RESOURCE_RECOVERED` is accessible and `== "RESOURCE_RECOVERED"`
- All existing `ResourceNodeState` constructors in the codebase still work (default=0 absorbs them)

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (parent epic)
- TCK-20260619-E21B-REGEN-SERVICE (blocked on this)

## Related Docs
- `docs/mechanics/03_economic_laws.md` § 3 (update to mention regen_rate_per_tick after E21B adds logic)
- `docs/parity_ledger/town_resource.yaml` (update after E21B/D)

## Related Code Areas
- `src/core/state.py:L808` (ResourceNodeState)
- `src/domains/world_emergence/schema.py:L12` (WorldEventCategory)

## Assumptions / Open Questions
- All callers use keyword args — verified via grep before adding field. Default=0 is safe.

## Implementation Notes
- `ResourceNodeState` is `frozen=True, slots=True` — the field was listed in the class body after `cooldown_remaining`, before `_canonical_cache`.
- `to_canonical_dict()` caches on first call via `_canonical_cache`. Added `"regen_rate_per_tick": self.regen_rate_per_tick` to the `res` dict before the cache set.
- `RESOURCE_RECOVERED = "RESOURCE_RECOVERED"` added to `WorldEventCategory` after `RESOURCE_DEPLETED`.
- 4 new AC-mapped tests added to `tests/unit/resource/test_resource_contract.py`.
- No parity ledger update required — schema-only, default=0, no behavior change.
- No docs update required — `docs/mechanics/03_economic_laws.md` update deferred to E21B per ticket scope.

## Test Summary
All 4 new AC tests pass. 16 pre-existing failures in the scoped suite are unrelated to this ticket (verified before/after comparison). Net: 326 tests pass (4 new added).

```bash
pytest tests/unit/resource/test_resource_contract.py -k "regen_rate or resource_recovered" -v
# 4 passed
```

## Files Changed
- `src/core/state.py` — added `regen_rate_per_tick: int = 0` field to `ResourceNodeState`; added `"regen_rate_per_tick"` to `to_canonical_dict()`
- `src/domains/world_emergence/schema.py` — added `RESOURCE_RECOVERED = "RESOURCE_RECOVERED"` to `WorldEventCategory`
- `tests/unit/resource/test_resource_contract.py` — added 4 new AC-mapped tests

## Completion Summary
Added `regen_rate_per_tick: int = 0` to `ResourceNodeState` (class body + `to_canonical_dict()`) and `RESOURCE_RECOVERED` to `WorldEventCategory`, unblocking E21B's regen service with zero behavior change. All 4 acceptance criteria verified by new tests.
