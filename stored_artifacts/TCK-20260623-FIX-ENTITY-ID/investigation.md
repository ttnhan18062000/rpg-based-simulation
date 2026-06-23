---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-ENTITY-ID
artifact_type: investigation
tags: [pipeline, entity_updates, faction_awareness, state_update, KeyError]
---

# Investigation — TCK-20260623-FIX-ENTITY-ID

## Summary

All `KeyError: 1` failures and the `assert 1 in {}` failure share a single root cause: three pipeline phases in `src/engine/pipeline.py` unconditionally replace the accumulated `StateUpdate` with a fresh one that ignores the incoming `u` parameter, wiping `entity_updates`, `building_updates`, and all other carried state.

---

## Entity ID Type (Production)

`AuthoritativeState.entities: Dict[int, EntityState]` — keys are `int`.  
`StateUpdate.entity_updates: Dict[int, EntityUpdate]` — keys are `int`.  
`EntityUpdate.entity_id: int`.

All test fixtures use integer keys (`{1: e1}`, `{2: entity}`) matching the production type. **There is no type mismatch.**

---

## Root Cause: Pipeline Phases That Ignore `u` and Return Fresh `StateUpdate`

### The `run_phase` contract

`run_phase` in `AuthoritativeApplyPipeline.refine` does:

```python
phase_upd = phase_fn(upd)
return phase_upd
```

It replaces the accumulated `update` with whatever `phase_fn(upd)` returns. If the phase function ignores `u` and constructs a fresh `StateUpdate(...)`, all fields not explicitly set revert to their dataclass defaults — including `entity_updates={}` and `building_updates={}`.

### The three offending phases

All three run unconditionally (no `feature_flag` argument), are wired into the pipeline between lines 179–223 of `src/engine/pipeline.py`, and their lambdas each **ignore `u`**:

**1. `faction_awareness` (line 179–182)**

```python
update = run_phase(
    "faction_awareness", update,
    lambda u: _SU_fa(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events)),
)
```

Returns `StateUpdate(faction_updates=...)`. `entity_updates`, `building_updates`, and all other fields are `{}` / `[]` default. This is the first wipe — confirmed by instrumentation: entity 1 present before, absent after.

**2. `diplomatic_transitions` (line 209–211)**

```python
update = run_phase(
    "diplomatic_transitions", update,
    lambda u: _SU_dt(faction_updates=_diplo_updates, world_events_add=_diplo_world_events),
)
```

Same pattern. Returns a fresh `StateUpdate` ignoring `u`.

**3. `military_conflict` (line 219–221)**

```python
update = run_phase(
    "military_conflict", update,
    lambda u: MilitaryConflictPhase.execute(state),
)
```

`MilitaryConflictPhase.execute(state)` ignores `u` entirely and returns its own fresh `StateUpdate`. Same wipe.

### Execution order and failure mapping

Pipeline execution order relevant to failures:

1. Line 96: compaction (entity 1 survives, resource_transfers intact)
2. Line 135–136: trust_boundary, actor_validity (entity 1 survives)
3. Line 152: `information_belief` (ENABLE_BELIEF_ASSIMILATION=ON in belief test → produces entity_updates={1: ...})
4. **Line 179: `faction_awareness` — WIPES entity_updates={} and building_updates={}**
5. **Line 209: `diplomatic_transitions` — WIPES again**
6. **Line 219: `military_conflict` — WIPES again**
7. Line 255–263: dirty refresh, interaction, building_sabotage (entity_updates already empty, building_updates already empty)
8. Line 290–299: Phase 6 dirty refresh, quest_rewards, shop, paid_information, resource_transactions

**resource_transactions** (line 299) sees `entity_updates={}` — nothing to process. Returns empty.

### Per-test failure mapping

| Test | What gets wiped | Symptom |
|---|---|---|
| `test_negative_case_depleted_node` (e5.py:123) | `entity_updates={1: EntityUpdate(resource_transfers=[intent])}` wiped at faction_awareness | `refined.entity_updates[1]` → `KeyError: 1` |
| `test_belief_assimilation_persists_facts` (fused_loop.py:208) | belief phase produces `entity_updates={1: ...}` at line 152, then faction_awareness wipes it at line 179 | `assert 1 in refined.entity_updates` → `assert 1 in {}` |
| `test_building_sabotage` (recovery_gaps.py:99) | `building_updates={1: BuildingUpdate(...)}` produced at line 263 — but wait, building_sabotage runs AFTER faction_awareness. Let me clarify: trust_boundary at line 204 resets `building_updates={}`. Building_sabotage at line 263 repopulates `building_updates={1: ...}`. Then no further wipe occurs for building_updates after line 263. | **See note below** |
| `test_hardening_e5.py:240, 251, 219` | Same as line 123 — entity_updates wiped before resource_transactions | `KeyError: 1` on `refined.entity_updates[1]` |

**Note on `test_building_sabotage`**: The sabotage system (line 263) runs after the faction wipes, so it should repopulate `building_updates`. However, `building_sabotage` iterates `update.entity_updates` (sabotage.py line 27) — and by line 263, `entity_updates` is already `{}` (wiped by faction_awareness at line 179). Therefore no entity triggers the SABOTAGE branch, and `building_updates` is never populated. The `KeyError` on `refined.building_updates[1]` is a **downstream consequence** of entity_updates being empty.

---

## The Fix

The three `run_phase` lambdas must merge their output into the incoming `u` rather than replace it. The pattern is:

```python
# Wrong (current): ignores u, returns fresh StateUpdate
lambda u: StateUpdate(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events))

# Correct: merge result into u
lambda u: u.merge(StateUpdate(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events)))
```

`StateUpdate.merge` is already implemented (src/core/updates.py lines 966-1088) and correctly merges all fields including `entity_updates`, `building_updates`, `faction_updates`, and `world_events_add`.

### Exact fix locations in `src/engine/pipeline.py`

**Fix 1 — `faction_awareness` (lines 179–182):**

```python
# Before:
update = run_phase(
    "faction_awareness", update,
    lambda u: _SU_fa(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events)),
)

# After:
update = run_phase(
    "faction_awareness", update,
    lambda u: u.merge(_SU_fa(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events))),
)
```

**Fix 2 — `diplomatic_transitions` (lines 209–211):**

```python
# Before:
lambda u: _SU_dt(faction_updates=_diplo_updates, world_events_add=_diplo_world_events),

# After:
lambda u: u.merge(_SU_dt(faction_updates=_diplo_updates, world_events_add=_diplo_world_events)),
```

**Fix 3 — `military_conflict` (lines 219–221):**

```python
# Before:
lambda u: MilitaryConflictPhase.execute(state),

# After:
lambda u: u.merge(MilitaryConflictPhase.execute(state)),
```

---

## Verification Approach

`StateUpdate.merge` is already tested and accumulates rather than replaces. After these fixes:

- `faction_updates` and `world_events_add` are merged (additive)
- `entity_updates` from prior phases (resource_transfers, belief assimilation results) are preserved
- `building_updates` from sabotage are preserved (now possible since entity_updates are not empty when sabotage runs)
- No data loss from any phase that appends to rather than replaces the update

---

## Files to Change

- `src/engine/pipeline.py` — lines 179–182, 209–211, 219–221: add `u.merge(...)` wrapper

## Files NOT Changed

- Tests — they are correctly constructed; the bug is in production pipeline code
- `src/core/updates.py` — `StateUpdate.merge` already works correctly
- `src/engine/compactor.py`, `src/engine/economy.py`, `src/engine/sabotage.py` — all correct
