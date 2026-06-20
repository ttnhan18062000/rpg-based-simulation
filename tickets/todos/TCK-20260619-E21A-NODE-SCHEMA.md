---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21A-NODE-SCHEMA
phase: open
date: 2026-06-20
tags: [resource-ecology, state-schema, event-taxonomy, phase-2]
---

# TCK-20260619-E21A-NODE-SCHEMA

## Title
Epic 2.1A · ResourceNodeState Schema Extension + RESOURCE_RECOVERED Event

## Status
OPEN

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
- Are there any callers of `ResourceNodeState(...)` using positional (non-keyword) args? Check with `grep -rn "ResourceNodeState(" src/ tests/` before adding the field. If so, the new field must be placed after all existing positional args (it is — `regen_rate_per_tick` goes after `cooldown_remaining`).

## Implementation Notes
- `ResourceNodeState` is `frozen=True, slots=True` — the field must be listed in the class body, not set post-init.
- `to_canonical_dict()` currently caches on first call via `_canonical_cache`. Just add `"regen_rate_per_tick": self.regen_rate_per_tick` to the `res` dict before the cache set.
- After this ticket: run `graphify update src/` to keep the graph current.

## Test Summary
```bash
# Quick constructor test
python3 -c "
from src.core.state import ResourceNodeState
n = ResourceNodeState(id=1, kind='IRON', position=(0,0), yields_item='iron_ore', remaining_charges=3, max_charges=5, required_ticks=10, regen_rate_per_tick=2)
assert n.regen_rate_per_tick == 2
d = n.to_canonical_dict()
assert 'regen_rate_per_tick' in d
print('OK')
"
# Event enum
python3 -c "
from src.domains.world_emergence.schema import WorldEventCategory
assert WorldEventCategory.RESOURCE_RECOVERED == 'RESOURCE_RECOVERED'
print('OK')
"
# Existing unit tests still pass
pytest tests/unit/resource/ -x -v -q
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
