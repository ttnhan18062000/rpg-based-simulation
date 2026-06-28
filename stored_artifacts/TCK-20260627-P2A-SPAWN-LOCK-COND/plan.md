# Plan — TCK-20260627-P2A-SPAWN-LOCK-COND

## Summary
Add a threat-resolution early-release condition to the strategic project lock check in `adventure/phase.py`, and enforce a 50-tick cap on all lock assignments. Update the existing regression test whose HP/hostile setup conflicts with the new condition.

## Ordered Steps

### Step 1 — Modify `src/domains/adventure/phase.py` (Primary Fix)
**File**: `src/domains/adventure/phase.py`, around line 67

Replace the bare `continue` when `tick < active_proj.lock_until_tick` with a two-condition early-release check:
- Compute `hp_ratio = hero.combat.hp / max(1, hero.combat.max_hp)`
- Query `SpatialQueryService.nearby_entities(state, hero.navigation.position, radius=10.0)`
- `has_hostile = any(alive entity with different faction in nearby_ids excluding self)`
- `threat_resolved = hp_ratio > 0.8 and not has_hostile`
- Only `continue` (skip the entity) if `not threat_resolved`

Import `SpatialQueryService` at the top of the file (or inline local import if avoiding circular deps).

**What NOT to change**: `engine/tactical.py:59` lock check — that is for immediate task continuity during combat, not adventure routing.

**Dependency**: None — this is the primary change.
**Verifies AC**: #2 (threat-resolution check), #3 (events begin early).

### Step 2 — Cap lock assignments at 50 ticks
**Files**:
- `src/domains/adventure/mapper.py:101`: Change `tick + 10` to `min(tick + 50, tick + 10)` — adds explicit cap intent (no behavior change since 10 < 50)
- `src/systems/strategic_systems/intelligence.py:1340`: Same pattern `min(current_tick + 50, current_tick + 10)`
- `src/systems/strategic_systems/intelligence.py:1266`: Same `min(current_tick + 50, current_tick + 20)`

**Dependency**: Independent of Step 1.
**Verifies AC**: #1 (cap at current_tick + 50).

### Step 3 — Update existing regression test
**File**: `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`

In `test_filters_out_locked_projects`:
- Change `CombatComponent(hp=100, max_hp=100, ...)` → `CombatComponent(hp=40, max_hp=100, ...)` (hp_ratio=0.4, below 0.8 threshold).
- This preserves test semantics: entity is locked because threat is still active (low HP), not because the lock timer hasn't expired.

**Dependency**: Must follow Step 1 (otherwise existing test still passes on its own).

### Step 4 — Add new unit tests
**File**: `tests/unit/systems/test_spawn_lock_condition.py` (new)

Add 5 tests (see test_plan.md for details):
1. HP=100%, no hostiles → lock released early (entity processed)
2. HP=50%, no hostiles → lock held (entity skipped)
3. HP=100%, hostile present → lock held
4. HP=40%, hostile present → lock held
5. Lock expired by tick (tick > lock_until_tick), HP=50%, hostile present → lock released (time-based)

Use `AdventureDecisionPhase.apply()` with minimal `AuthoritativeState` and `V2EntityBuilder`.

**Dependency**: Depends on Step 1.

### Step 5 — Update parity ledger
**File**: `docs/parity_ledger/strategic_cognition.yaml`

Add new entry: `spawn_lock_conditional_release` with:
- `status: verified`
- `v2_evidence: src/domains/adventure/phase.py` (new condition)
- `test_path: tests/unit/systems/test_spawn_lock_condition.py`

**Dependency**: Follows Step 4.

## Explicit Scope Guards (what NOT to touch)
- `src/engine/tactical.py` — different lock check for combat task continuity, not in scope
- `src/ai/goals/scorers.py` — goal thresholds (0.5 for COMBAT_RETREAT, 0.9 for RECOVER) must NOT change
- `src/systems/social_systems/contracts.py:180` — contract lock (tick + 50) is already at cap, no change needed
- `src/engine/apply.py` — the authoritative state applicator; no lock logic here to touch

## Dependency Map
- Step 2 is independent of Step 1
- Step 3 depends on Step 1
- Step 4 depends on Step 1
- Step 5 depends on Step 4

## Acceptance Criteria Mapped to Steps
| AC | Steps |
|---|---|
| lock_until_tick cap at current_tick + 50 | Step 2 |
| Threat-resolution check (HP > 80%, no hostile) releases lock early | Step 1 |
| Behavioral events begin before tick 50 | Step 1 (unit tests verify, integration via test_plan scenario) |
| Regression: spawn and combat tests pass | Step 3 + existing test suite |

## Deviations
(None yet — fill in if implementation differs from plan)
