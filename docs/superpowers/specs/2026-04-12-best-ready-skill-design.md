# Design Spec: Hybrid Skill Selection (best_ready_skill)

## Goal
Resolve 7 test failures in the combat unit test suite caused by a signature mismatch in the `best_ready_skill` helper function. The refactor must support isolated unit testing (passing raw `Entity` objects) while preserving full contextual awareness in the live simulation (using `AIContext`).

## Proposed Changes

### 1. `src/ai/states/combat.py`
Refactor `best_ready_skill` to handle a union type for its first argument.

```python
def best_ready_skill(
    ctx: AIContext | Entity, 
    target_enemy: Entity | None = None, 
    dist_override: int | None = None
) -> str | None:
    # 1. Component Extraction
    if isinstance(ctx, Entity):
        actor = ctx
        context = None
    else:
        actor = ctx.actor
        context = ctx

    # 2. Distance Resolution
    if dist_override is not None:
        dist_to_enemy = dist_override
    elif target_enemy:
        dist_to_enemy = actor.spatial.pos.manhattan(target_enemy.spatial.pos)
    else:
        dist_to_enemy = 1

    # 3. Scoring Logic
    # ... stamina/cooldown/range checks ...
    
    # 4. AoE Logic
    if context and radius > 0:
        # Full multi-target counting using context.visible and context.faction_reg
    else:
        hits = 1 # Fallback for isolated unit tests
```

### 2. `tests/unit/combat/test_ranged_combat.py`
Update test calls to use the new keyword argument for distance overrides.
- Change: `best_ready_skill(e, dist_to_enemy=3)`
- To: `best_ready_skill(e, dist_override=3)`

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/combat/test_combat.py` (Verify 5 failures resolved)
- Run `pytest tests/unit/combat/test_ranged_combat.py` (Verify 2 failures resolved)
- Run `pytest tests/integration/ai/` (Verify no regressions in live AI behavior)

### Manual Verification
- None required (logic is covered by regression suite).
