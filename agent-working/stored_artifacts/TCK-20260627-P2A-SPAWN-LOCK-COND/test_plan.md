# Test Plan — TCK-20260627-P2A-SPAWN-LOCK-COND

## Regression Surface (existing tests that must pass)

| Test File | Why it matters |
|---|---|
| `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` | Contains `test_filters_out_locked_projects` — lock still works when threat is NOT resolved |
| `tests/unit/strategic/test_project_continuity.py` | `test_project_lock` — `evaluate_project_switch` lock check must not break |
| `tests/unit/strategic/test_goal_hysteresis.py` | Hysteresis and detour resumption must survive |
| `tests/unit/strategic/test_interruption_resistance.py` | Retention margin logic must be unaffected |

## New Tests Required (per AC)

### Test 1 — Early lock release when threat resolved
**File**: `tests/unit/systems/test_spawn_lock_condition.py` (new)

**Scenario**: Entity has HP=100%, max_hp=100 (hp_ratio=1.0), active project with `lock_until_tick=100`, tick=5, no hostiles in state. Expect: entity is NOT skipped by `AdventureDecisionPhase.apply()`, i.e., `update.entity_updates` is non-empty or the lock-check path is bypassed.

### Test 2 — Lock maintained when HP is low
**Scenario**: Entity has HP=50%, max_hp=100 (hp_ratio=0.5), active project with `lock_until_tick=100`, tick=5, no hostiles. Expect: entity IS skipped (lock held — HP not above 0.8 threshold).

### Test 3 — Lock maintained when hostile is present
**Scenario**: Entity HP=100%, max_hp=100, active project with `lock_until_tick=100`, tick=5, hostile entity (MONSTER_HORDE faction, alive) within radius=10.0. Expect: entity IS skipped (lock held — hostile present).

### Test 4 — Lock maintained when both HP low AND hostile present
**Scenario**: HP=40%, hostile present. Expect: entity IS skipped.

### Test 5 — Lock expires normally (time-based release)
**Scenario**: Entity HP=50%, hostile present, `lock_until_tick=10`, tick=11. Expect: entity is NOT skipped (lock expired by time — existing behavior unchanged).

## Scoped Pytest Commands

```bash
# Primary: new unit tests for the conditional
pytest tests/unit/systems/test_spawn_lock_condition.py -v

# Regression: adventure phase integration
pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -v

# Regression: strategic lock and continuity
pytest tests/unit/strategic/test_project_continuity.py tests/unit/strategic/test_goal_hysteresis.py tests/unit/strategic/test_interruption_resistance.py -v

# Combined scoped run
pytest tests/unit/systems/test_spawn_lock_condition.py tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py tests/unit/strategic/test_project_continuity.py tests/unit/strategic/test_goal_hysteresis.py -v
```

## Anti-Drift Test Guards

- Test 1 must assert that the entity update IS produced (routing proceeds after early release).
- Test 2 and 3 must assert `not update.entity_updates` (lock held).
- `test_filters_out_locked_projects` must pass unchanged — it uses HP=100 but also has hostiles in state? Actually it uses HP=100/max_hp=100. Check: if hp_ratio > 0.8 AND no hostiles → the lock would be released even in the existing test. This must be verified carefully.
  → If the existing test has no hostiles and hp_ratio=1.0, the early release will trigger and the test assertion (`assert not update.entity_updates`) may break.
  → The existing test must be updated to either add a hostile entity or lower HP to trigger the "threat not resolved" condition, so the lock still holds.
