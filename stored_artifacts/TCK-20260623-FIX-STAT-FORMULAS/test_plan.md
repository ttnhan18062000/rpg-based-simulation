# Test Plan: TCK-20260623-FIX-STAT-FORMULAS

**Date:** 2026-06-23  
**Tier:** standard  

---

## Scope

Verify all 8 failing tests pass after fixes, and that no regressions are introduced in related subsystems.

---

## Fix Scope Mapping

| Fix | Files Changed | Tests to Run |
|---|---|---|
| F1: TaskComponent injection | `tests/unit/core/test_p1_semantic_hardening.py` | That file |
| F2: Fallback seeding mode | `tests/unit/core/test_hardcoded_regression_guard.py` | That file |
| F3: pressure_report budget | `src/engine/replay_manager.py` | Budget gate file + replay integration |
| F4: rng_checkpoint kernel write | `src/engine/kernel.py` | Checkpointer + scenario runtime |
| F5: Shutdown mock fix | `tests/unit/core/test_graceful_shutdown.py` | That file |

---

## Test Execution Plan

### Phase 1: Run the 8 currently-failing tests (must all pass after fixes)

```bash
python3 -m pytest \
  tests/unit/core/test_p1_semantic_hardening.py::test_stamina_drain \
  tests/unit/core/test_hardcoded_regression_guard.py::test_hardcoded_content_regression_guard \
  tests/unit/engine/test_resource_budget_gate.py::TestReplayManagerPressureReport \
  tests/unit/engine/test_scenario_checkpointer.py::test_checkpoint_header_contains_rng_checkpoint \
  tests/unit/engine/test_scenario_checkpointer.py::test_rng_checkpoint_populated_after_tick \
  tests/unit/core/test_graceful_shutdown.py::test_shutdown_timeout_logic \
  -v --tb=short
```

**Acceptance:** All 8 pass.

### Phase 2: Regression check — affected subsystems

```bash
# Combat/legality (TaskComponent fix ripple)
python3 -m pytest tests/unit/core/test_p1_semantic_hardening.py -v --tb=short

# Replay subsystem (pressure_report change ripple)
python3 -m pytest tests/unit/engine/test_resource_budget_gate.py -v --tb=short

# Kernel/checkpointer (rng_checkpoint + shutdown ripple)
python3 -m pytest tests/unit/engine/test_scenario_checkpointer.py tests/unit/core/test_graceful_shutdown.py -v --tb=short

# Stat formula tests — confirm D10 audit assertions still hold
python3 -m pytest tests/unit/core/test_rpg_math.py tests/unit/progression/test_rpg_advancement.py tests/unit/progression/test_leveling.py tests/unit/progression/test_attribute_growth.py -v --tb=short

# Optimization tests (position parity)
python3 -m pytest tests/unit/optimization/ -v --tb=short
```

### Phase 3: Domain-scoped non-slow run

```bash
python3 -m pytest tests/unit/ -q -m "not slow" --tb=line 2>&1 | tail -20
```

**Acceptance:** No new failures beyond pre-existing (integration worldbuilding `test_compiled_world_ticks_stability` is a known pre-existing failure unrelated to this ticket).

### Phase 4: Integration smoke (optional, slow)

```bash
python3 -m pytest tests/integration/ -q --tb=line -m "not slow" 2>&1 | tail -20
```

---

## Test Cases by Fix

### F1: TaskComponent injection (test_stamina_drain)

| Case | Input | Expected |
|---|---|---|
| Normal flow | h1 with `TaskComponent(work_kind="ENTITY_ACT", payload={"action":"ATTACK","target_id":2})` | `attacker_up.stamina_update.current_delta == -5.0` |
| Legality check | Attacker task has `target_id` matching defender | `combat_engaged=True` in relation context |
| Wrong type guard | `TaskUpdate` injected as `.task` | Should not reach production code (test-only concern) |

### F2: Fallback seeding mode (test_hardcoded_content_regression_guard)

| Case | Input | Expected |
|---|---|---|
| Catalog mode | `seed_phase1_content` with `LEGACY_FALLBACK` mode or real catalog | Seeds successfully, no `FallbackRestrictedError` |
| Content guard | Items not in allowlist | Must appear in `catalog_repo` or test fails |
| No new content | Allowlist unchanged | All registered IDs pass the guard |

### F3: pressure_report budget (3 replay budget tests)

| Case | Input | Expected |
|---|---|---|
| Explicit budget | `pressure_report(budget=SubsystemBudget(max_inflight_chunks=5))` | `report.budget == 5.0` |
| None chunks budget | `pressure_report(budget=SubsystemBudget())` (max_inflight_chunks=None) | `report.budget is None`, `pressure_state=="OK"` |
| No budget arg | `pressure_report()` with no arg | Uses `DEFAULT_REPLAY_BUDGET.max_inflight_chunks` (3) as cap, `report.budget == 3.0` |
| Inflight below 80% | 0 inflight, any budget | `pressure_state=="OK"` |
| Inflight at 80-99% | budget via param | `pressure_state=="WARN"` |
| Inflight at 100%+ | budget via param | `pressure_state=="DEGRADED"` |

### F4: rng_checkpoint populated after tick (2 checkpointer tests)

| Case | Input | Expected |
|---|---|---|
| After 1 tick | `ScenarioRuntimeService.step()` called once | `svc._kernel.state.rng_checkpoint is not None` |
| Checkpoint file | Checkpoint saved after 5 ticks | `header["rng_checkpoint"] is not None` |
| RNG restore | Load checkpoint, restore rng | RNG produces same sequence as at checkpoint |
| Determinism | Same seed + same ticks | `rng_checkpoint` is byte-identical across two runs |

### F5: Shutdown mock fix (test_shutdown_timeout_logic)

| Case | Input | Expected |
|---|---|---|
| Mock replay with numeric metrics | `mock_replay.replay_metrics.return_value = {"pending_flushes": 0, ...}` | No `TypeError`, `mock_replay.finalize.assert_called_once_with(timeout_s=0.1)` |
| Zero pending flushes | Numeric 0 | No warning appended, shutdown completes |
| Positive pending flushes | Numeric >0 | Warning appended to report |

---

## Regression Risk Assessment

| Fix | Risk | Rationale |
|---|---|---|
| F1 (test only) | None | Only changes how a test constructs an entity; production path unchanged |
| F2 (test only) | Low | Changes seeding mode in test context; no production path change |
| F3 (production) | Medium | `pressure_report()` now reads different value; verify WARN/DEGRADED thresholds still correct; Governor and kernel (`kernel.py:956`) call `pressure_report()` — ensure default behavior (no budget arg) still uses constructor value as fallback |
| F4 (production) | Medium | Adds RNG snapshot per tick; verify `get_state()` is cheap (read-only) and deterministic; verify `StateUpdate.rng_checkpoint` is not accidentally merged/overwritten |
| F5 (test only) | None | Only adds mock return value configuration |

---

## Pre-existing Failures (not in scope)

- `tests/integration/worldbuilding/test_world_compile_to_state.py::test_compiled_world_ticks_stability` — pydantic ValidationError + thread leak, pre-existing, unrelated to stat formulas or this ticket.

---

## Done Criteria

- All 8 listed failing tests pass
- `tests/unit/core/test_rpg_math.py` still passes (D10 audit stat assertions confirmed correct)
- `tests/unit/progression/test_rpg_advancement.py` still passes (move_cost and equipment stat assertions confirmed correct)
- `tests/unit/optimization/` still passes (89 tests, no position parity regression)
- No new failures in `tests/unit/ -m "not slow"`
