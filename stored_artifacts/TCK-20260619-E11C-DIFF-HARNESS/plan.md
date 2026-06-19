---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260619-E11C-DIFF-HARNESS
artifact_type: plan
tags: [entity-differentiation, test-harness, behavioral-quality, integration, phase-1]
---

# Plan — TCK-20260619-E11C-DIFF-HARNESS
# E11-C · Build 400-tick differentiation test harness

---

## Scope Guard

This ticket is **harness-only**. No changes to:
- Scoring weights (`src/ai/goals/scorers.py`)
- Bravery coefficient calibration (reserved for E11D)
- Feature flag defaults (`src/domains/optimization/feature_flags.py`)
- Any `src/` file except as needed for import correctness

All work is confined to:
- `tests/integration/scenarios/test_entity_differentiation.py` (new file — the only deliverable)

---

## Dependency Map

```
E11A-HERO-AUTHORING  ──►  E11C-DIFF-HARNESS  ──►  E11D-SCORING-CAL
E11B-OBS-SNAPSHOT    ──►  (soft: personality already on entity.identity.personality)

Internal step order:
  Step 1  (WorldSpec helper)
    └──►  Step 2  (test_no_identical_personality_vectors_at_spawn)
    └──►  Step 3  (profile + kernel helpers)
              └──►  Step 4  (tick loop + histogram)
                        └──►  Step 5  (quartile assertion)
                                  └──►  Step 6  (marks + smoke run)
```

External prerequisites verified before starting implementation:
- E11A complete: HERO entities with distinct bravery values exist in compiled world
- `ENABLE_COMBAT_ENGAGEMENT` feature flag exists in `src/domains/optimization/feature_flags.py`
- `GoalKind.COMBAT_ENGAGE` enum value is `"combat_engage"` (confirmed: `src/core/strategic.py:111`)
- `pytest.ini` markers `slow`, `integration` already registered (confirmed: `pytest.ini` lines 64–75)
- `WorldCompiler.compile(spec, seed)` returns `(AuthoritativeState, report)` (confirmed: `tests/integration/worldbuilding/test_world_compile_to_state.py`)
- Kernel N-tick loop pattern confirmed from `tests/integration/kernel/test_long_run_determinism.py`

---

## Ordered Steps

### Step 1 — Create file skeleton and `_build_differentiation_spec()` helper

**File:** `tests/integration/scenarios/test_entity_differentiation.py` (new)

**What:**
- Create the file with module-level imports and the `_build_differentiation_spec()` function.
- The function returns a `WorldSpec` compiled from an inline `worldspec.v1` dict with:
  - 8 heroes (`role: hero`, `faction: heroes`, `spawn_region: arena`)
  - 4 monsters (`role: monster`, `faction: monsters`, `spawn_region: arena`)
  - Both groups spawn in the same `arena` region (bounds `[0, 0, 32, 32]`) to guarantee hostile proximity from tick 0
  - A second `village` region to satisfy any topology minimum requirements
- Do NOT use `sandbox_world` — it has only 3 heroes, too few for quartile calculation.

**Imports block:**
```python
import pytest
from collections import defaultdict
from dataclasses import replace

from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec
from src.core.strategic import GoalKind
```

**Scope guard:** No `src/` imports modified. No scorer imports. No calibration code.

**Verifiable independently:** `python3 -c "from tests.integration.scenarios.test_entity_differentiation import _build_differentiation_spec; print(_build_differentiation_spec())"` must not raise.

**AC mapped:** Precondition for AC-1 (harness runs without errors) and AC-2 (test_no_identical passes).

---

### Step 2 — Implement `test_no_identical_personality_vectors_at_spawn`

**File:** `tests/integration/scenarios/test_entity_differentiation.py`

**What:**
- Add `test_no_identical_personality_vectors_at_spawn()` decorated with `@pytest.mark.integration`.
- Steps inside:
  1. Call `_build_differentiation_spec()` → `WorldCompiler.compile(spec, seed=42)` → `(state, report)`.
  2. Iterate `state.entities.values()`.
  3. Build tuple `(p.greed, p.bravery, p.sociability, p.industry)` from `entity.identity.personality`.
  4. Assert each tuple is unique using a `set`; fail with entity ID and duplicate tuple on collision.
- Mark: `@pytest.mark.integration` only (no `slow` — compile + tick-0 check is fast).

**Scope guard:** Read-only access to `state.entities`; no mutations; no scorer code.

**Verifiable independently:**
```bash
pytest tests/integration/scenarios/test_entity_differentiation.py::test_no_identical_personality_vectors_at_spawn -v
```
Must pass (strict pass — not xfail).

**AC mapped:** AC-1 (`test_no_identical_personality_vectors_at_spawn` passes with current seeding).

---

### Step 3 — Add `_test_profile()` helper

**File:** `tests/integration/scenarios/test_entity_differentiation.py`

**What:**
- Add module-level `_test_profile()` function returning a `RuntimeProfile` for the 400-tick run:
  - `name="differentiation-test"`, `hardware_class=HardwareClass.CLASS_B`
  - `max_ram_mb=512`, `max_cpu_percent=100.0`, `max_worker_count=1`
  - `max_queue_depth=500`, `max_replay_buffer_kb=0`
  - `max_observability_budget_percent=0.0` (no observability overhead)
  - `max_tick_budget_ms=200.0`
- Add module-level constants: `TICKS = 400`, `SEED = 42`.

**Scope guard:** Pure configuration helper; no src modifications.

**Verifiable independently:** Function returns a `RuntimeProfile` instance without error.

**AC mapped:** Precondition for Step 4.

---

### Step 4 — Implement tick loop with per-entity route histogram

**File:** `tests/integration/scenarios/test_entity_differentiation.py`

**What:**
- Add the body of `test_bravery_quartile_combat_rate_2x()` up to (and including) the histogram collection loop.
- Steps:
  1. Compile world: `spec = _build_differentiation_spec()` → `WorldCompiler.compile(spec, seed=SEED)` → `(initial_state, report)`.
  2. Enable feature flags via `replace()`:
     ```python
     initial_state = replace(
         initial_state,
         feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON", "ENABLE_ADVENTURE_ROUTING": "ON"}
     )
     ```
  3. Construct `project_kind_history: dict[int, list[str | None]] = defaultdict(list)`.
  4. Construct `Kernel(_test_profile(), initial_state, DeterministicRNG(SEED), flags={"no_replay": True})`.
  5. Run loop: `for _ in range(TICKS): kernel.tick_once()` then sample `kernel.state`:
     - For each `(eid, ent)` in `kernel.state.entities.items()`:
       - Read `cur_proj_id = ent.strategic.current_project_id`
       - If set and present in `ent.strategic.projects`: append `kind.value` (or `str(kind)`)
       - Else: append `None`
  6. Capture `final_state = kernel.state` after loop.

**Critical constraint:** Sample `kernel.state` inside the loop (not after). `current_project_id` reflects the live tick choice; scanning `projects` dict post-hoc would conflate multi-tick project durations.

**Scope guard:** No scoring code; no feature flag defaults changed. Read-only state access.

**Verifiable independently:** The loop completes 400 iterations without exception; `project_kind_history` is non-empty.

**AC mapped:** Precondition for Step 5 (data required for quartile assertion).

---

### Step 5 — Implement quartile computation and 2× assertion

**File:** `tests/integration/scenarios/test_entity_differentiation.py`

**What:**
- Complete `test_bravery_quartile_combat_rate_2x()` with the assertion block.
- Steps after histogram collection:
  1. Filter `final_state.entities.values()` to `ent.kind.lower() == "hero"` and `ent.combat.alive`.
  2. Assert `len(hero_entities) >= 4` (guard against E11A prerequisite failure).
  3. Sort `hero_entities` by `e.identity.personality.bravery` ascending.
  4. Compute `q_size = max(1, n // 4)`.
  5. `bottom_quartile = hero_entities[:q_size]`, `top_quartile = hero_entities[n - q_size:]`.
  6. Define `combat_engage_rate(entity_list)`:
     - Sum ticks in `project_kind_history[ent.id]` equal to `GoalKind.COMBAT_ENGAGE.value`
     - Divide by `max(1, total_ticks)` (guard against zero-length histories)
  7. Assert `bottom_rate > 0` (diagnostic gate — clarifies flag or proximity issue if it fails).
  8. Assert `top_rate >= 2.0 * bottom_rate`.
- Add `@pytest.mark.xfail(strict=False, reason="Calibration pending TCK-20260619-E11D-SCORING-CAL")`.
- Add `@pytest.mark.slow` and `@pytest.mark.integration`.

**Scope guard:** Computation only; no scoring logic; no src mutations.

**Verifiable independently:**
```bash
pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v
```
Must complete without import errors or runtime crashes. Result is xfail or xpass — either is acceptable pre-E11D.

**AC mapped:** AC-2 (`test_bravery_quartile_combat_rate_2x` is xfail until E11D; does not error). AC-3 (harness runs in `pytest tests/integration/scenarios/` without errors).

---

### Step 6 — Smoke run and final verification

**File:** No new files. Read-only verification step.

**What:**
- Run the strict-pass test alone to confirm no import errors or unexpected failures:
  ```bash
  pytest tests/integration/scenarios/test_entity_differentiation.py::test_no_identical_personality_vectors_at_spawn -v
  ```
- Run the full file to confirm xfail mark is correctly applied and no crash occurs:
  ```bash
  pytest tests/integration/scenarios/test_entity_differentiation.py -v
  ```
- Run the broader scenarios suite to confirm no regressions:
  ```bash
  pytest tests/integration/scenarios/ -v -m "not extra_slow" --tb=short
  ```
- Confirm markers are already registered in `pytest.ini` (`slow`, `integration` — confirmed present at lines 64–75).

**Scope guard:** Read-only verification. If a marker is missing from `pytest.ini`, add it there (not in a conftest) — but this is not expected to be needed.

**AC mapped:** All three ACs (AC-1, AC-2, AC-3) verified by execution.

---

## Acceptance Criteria → Step Mapping

| AC | Description | Step |
|---|---|---|
| AC-1 | `test_no_identical_personality_vectors_at_spawn` passes (strict) | Steps 1, 2, 6 |
| AC-2 | `test_bravery_quartile_combat_rate_2x` is xfail, not crash | Steps 1, 3, 4, 5, 6 |
| AC-3 | Harness runs in `pytest tests/integration/scenarios/` without errors | Steps 1–6 |

---

## Files Changed

| File | Action | Scope |
|---|---|---|
| `tests/integration/scenarios/test_entity_differentiation.py` | Create (new) | All test logic |
| `pytest.ini` | No change expected (markers already registered) | — |
| Any `src/` file | No changes | Harness-only scope guard |

---

## Deviations from Plan

None. All 6 steps executed exactly as specified:
- Step 1: Skeleton and `_build_differentiation_spec()` created with inline 8-hero + 4-monster worldspec.v1 dict, both groups in `arena` region (bounds [0,0,32,32]).
- Step 2: `test_no_identical_personality_vectors_at_spawn` passes strictly (0.46s).
- Step 3: `_test_profile()` and `TICKS = 400`, `SEED = 42` constants added as specified.
- Step 4: Tick loop with per-entity `current_project_id → projects[id].kind` sampling inside loop.
- Step 5: Quartile assertion with `xfail(strict=False)`, `@pytest.mark.slow`, `@pytest.mark.integration`.
- Step 6: All smoke runs pass. `test_bravery_quartile_combat_rate_2x` is correctly xfail (pre-E11D). 112 non-slow scenarios tests pass with no regressions.

Minor implementation notes:
- Hero detection uses `ent.kind.lower() == "hero"` (confirmed from compiler.py line 317: `kind=pop_spec.role.lower()`).
- `feature_flags` dict uses string values `"ON"`; pipeline.py reads these and applies via `FeatureFlagManager`.
- `EntityRole` import not needed in final file (hero detection via `ent.kind` string, not enum comparison).

---

## Anti-Drift Reminders (enforced in implementation)

1. **Do not use `transaction_trace`** for route histogram — it contains economic transfer strings, not goal-selection events.
2. **Do not use `entity_timeline_store`** — LIGHT mode retains only 20 events; 400 ticks × N entities overflows it.
3. **Do not scan `projects` dict post-hoc** — only `current_project_id → projects[id].kind` reflects per-tick choice.
4. **Do not use `sandbox_world`** — only 3 heroes; quartile math breaks with n < 4.
5. **Do not enable `audit_mode`** — it accumulates unbounded `transaction_trace`, degrading performance with no benefit.
6. **Do not change scoring weights** — calibration is E11D, not E11C.
