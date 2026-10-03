# Investigation: TCK-20260623-FIX-STAT-FORMULAS

**Date:** 2026-06-23  
**Phase timestamp:** 2026-06-23T23:48:36Z  
**Investigator:** agent  

---

## Summary

The D10 audit reported ~7 stat-recalculation failures with patterns like `assert 8==23` and `assert 9.5==11.9`. Investigation found those **specific tests pass cleanly** — the formulas in `src/progression/leveling.py` and `src/engine/rpg_depth.py` are correct and match test expectations.

The actual 8 failing tests fall into four distinct root-cause buckets, none of which involve a changed stat formula. The D10 audit assertions (`8 vs 23`, `9.5 vs 11.9`, `(10.0,10.0) vs (10.0,11.0)`) were likely captured from a different branch state or mis-attributed during the audit.

---

## Actual Failing Tests (8 total)

### Bucket 1: Wrong object type injected into entity.task (1 failure)

**Test:** `tests/unit/core/test_p1_semantic_hardening.py::test_stamina_drain`

**Error:**
```
AttributeError: 'TaskUpdate' object has no attribute 'payload'
  src/engine/legality.py:231
    if attacker.task.payload.get("target_id") == target.id ...
```

**Root cause:** The test patches the entity's `.task` field with a `TaskUpdate` object (line 258: `h1 = replace(h1, task=task_upd)`). `TaskUpdate` has `payload_set`, not `payload`. The live entity's `.task` field is a `TaskComponent` (defined in `src/core/state.py:382`) which has `.payload`. The production code at `legality.py:231` correctly calls `.task.payload.get(...)` — it expects a `TaskComponent`.

**Fix location:** `tests/unit/core/test_p1_semantic_hardening.py:257-258`  
**Fix type:** Test bug — replace `TaskUpdate` injection with a `TaskComponent` carrying the payload dict.

```python
# WRONG (current):
task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=payload)
h1 = replace(h1, task=task_upd)

# CORRECT:
from src.core.state import TaskComponent
h1 = replace(h1, task=TaskComponent(work_kind="ENTITY_ACT", payload=payload))
```

---

### Bucket 2: Fallback seeding blocked by mode guard (1 failure)

**Test:** `tests/unit/core/test_hardcoded_regression_guard.py::test_hardcoded_content_regression_guard`

**Error:**
```
FallbackRestrictedError: [mode=catalog_with_compatibility] Fallback to hardcoded content is 
restricted in this mode.
  src/core/registries.py:640
```

**Root cause:** `seed_phase1_content(catalog_repo=None, required=False)` hits the branch at `registries.py:637-640` that checks `_FORBIDDEN_FALLBACK_MODES`. The current runtime mode is `catalog_with_compatibility` (in `_FORBIDDEN_FALLBACK_MODES = frozenset({"catalog_strict", "catalog_with_compatibility"})`), so the fallback raises `FallbackRestrictedError` even when `required=False`.

The test intent is to verify no new hardcoded content was sneaked in. With the current mode architecture, the test must pass a real `CatalogRepository` to `seed_phase1_content` instead of passing `None`. Alternatively, the test should temporarily set the runtime mode to a non-forbidden mode (e.g. `LEGACY_FALLBACK`) before calling the seed function.

**Fix location:** `tests/unit/core/test_hardcoded_regression_guard.py:48`  
**Fix type:** Test bug — the test must either use a catalog repo or set mode to `LEGACY_FALLBACK` for this call.

---

### Bucket 3: ReplayManager.pressure_report() ignores injected budget (3 failures)

**Tests:**
- `test_resource_budget_gate.py::TestReplayManagerPressureReport::test_replay_pressure_report_exists` — expects `budget=5.0`, gets `2.0`
- `test_replay_pressure_report_none_budget` — expects `budget=None`, gets `2.0`
- `test_replay_pressure_report_default_budget_used_when_none_passed` — expects `budget=3.0` (DEFAULT_REPLAY_BUDGET.max_inflight_chunks), gets `2.0`

**Root cause:** `ReplayManager.pressure_report(budget: SubsystemBudget | None = None)` at `src/engine/replay_manager.py:319` **ignores the `budget` parameter entirely**. It always reads `self._max_pending_flushes` (set at construction time, default=2) as the budget cap. The tests construct `ReplayManager` with no `max_inflight_chunks` override (so `_max_pending_flushes=2`) and then pass a `SubsystemBudget` at call time expecting it to take precedence — but the method never uses it.

The `_make_replay_manager` helper at test line 67 constructs `ReplayManager(...)` with default `max_pending_flushes=2`, then returns `(mgr, SubsystemBudget(subsystem="replay", max_inflight_chunks=max_inflight_chunks))`. The test passes the budget to `mgr.pressure_report(budget=budget)` and expects the method to use `budget.max_inflight_chunks` as the cap — but the method reads `self._max_pending_flushes` instead.

**Fix location:** `src/engine/replay_manager.py:319-353`  
**Fix type:** Production bug — `pressure_report()` must honor the `budget` parameter when provided.

```python
def pressure_report(self, budget: SubsystemBudget | None = None) -> SubsystemPressureReport:
    with self._inflight_lock:
        inflight = self._inflight_count
    # Use injected budget's max_inflight_chunks if provided, fall back to constructor value
    if budget is not None and budget.max_inflight_chunks is not None:
        max_f = budget.max_inflight_chunks
    else:
        max_f = self._max_pending_flushes
    budget_val = float(max_f) if max_f and max_f > 0 else None
    if not max_f or max_f <= 0:
        return SubsystemPressureReport(
            subsystem="replay",
            current_usage=float(inflight),
            budget=None,
            pressure_state="OK",
            degradation_action=None,
        )
    ...
```

---

### Bucket 4: rng_checkpoint never written during kernel tick (2 failures)

**Tests:**
- `test_scenario_checkpointer.py::test_checkpoint_header_contains_rng_checkpoint` — `header["rng_checkpoint"] is not None` fails
- `test_scenario_checkpointer.py::test_rng_checkpoint_populated_after_tick` — `state.rng_checkpoint is not None` fails

**Root cause:** `AuthoritativeState.rng_checkpoint` (defined at `src/core/state.py:1134`) starts as `None` and is updated via `ApplyPath.apply_generation` from `StateUpdate.rng_checkpoint` (see `src/engine/apply.py:287`). However, **no kernel phase ever sets `StateUpdate.rng_checkpoint`**.

In `_phase_advancement` (`kernel.py:637-668`), the `StateUpdate` passed to `ApplyPath.apply_generation` comes from `_phase_resolution`'s `refined_update` — which never includes `rng_checkpoint`. The kernel has access to `self._rng` (a `DeterministicRNG` with `get_state()` at `src/platform/rng.py:40`) but never snapshots it into the update.

**Fix location:** `src/engine/kernel.py` — `_phase_resolution` or `_phase_advancement`  
**Fix type:** Production bug — must snapshot `self._rng.get_state()` into the `StateUpdate.rng_checkpoint` before calling `ApplyPath.apply_generation`.

```python
# In _phase_advancement, before apply_generation:
update = replace(update, rng_checkpoint=self._rng.get_state())
```

---

### Bucket 5: Kernel.shutdown() — MagicMock vs int comparison (1 failure)

**Test:** `tests/unit/core/test_graceful_shutdown.py::test_shutdown_timeout_logic`

**Error:**
```
TypeError: '>' not supported between instances of 'MagicMock' and 'int'
  src/engine/kernel.py:889
    if report.pending_replay_flushes > 0:
```

**Root cause:** The test mocks `replay` with a bare `MagicMock()`. When `kernel.shutdown()` calls `self._replay.replay_metrics()`, it gets a `MagicMock` return value. Then `rm.get("pending_replay_flushes", ...)` on a `MagicMock` also returns a `MagicMock`. Assigning that `MagicMock` to `report.pending_replay_flushes` and then comparing `> 0` raises `TypeError`.

The `ShutdownReport` likely has `pending_replay_flushes` typed as `int`. The test needs to configure the mock's `replay_metrics()` return value.

**Fix location:** `tests/unit/core/test_graceful_shutdown.py:44-48`  
**Fix type:** Test bug — configure mock to return a numeric-compatible value.

```python
mock_replay = MagicMock()
mock_replay.replay_metrics.return_value = {"pending_flushes": 0, "pending_replay_flushes": 0}
```

---

## D10 Audit Assertions — Reconciliation

| D10 Claim | Test File | Status |
|---|---|---|
| `assert 8==23` stat recalculation | `test_rpg_math.py::test_stat_recalculation` | **PASSES** — formula is correct (DEF=5+vit*0.3=8 base; +15 gear=23) |
| `assert 9.5==11.9` equipment stat | `test_rpg_advancement.py::test_equipment_stat_injection_move_cost` | **PASSES** — move_cost 9.5 base, 11.9 with iron_plate |
| `assert (10.0,10.0)==(10.0,11.0)` position | `tests/unit/optimization/` | **ALL PASS** — 89 optimization tests pass |

The D10 audit failure count of ~7 matches the 8 actual failures found, but the specific assertion patterns were from a different branch or test run state.

---

## Fix Recommendation Summary

| # | Failure | Fix Where | Fix Type |
|---|---|---|---|
| 1 | `test_stamina_drain` | Test: `test_p1_semantic_hardening.py:257-258` | Test bug: use `TaskComponent` not `TaskUpdate` |
| 2 | `test_hardcoded_content_regression_guard` | Test: `test_hardcoded_regression_guard.py:48` | Test bug: pass catalog_repo or set mode to LEGACY_FALLBACK |
| 3 | `test_replay_pressure_report_exists` | Production: `replay_manager.py:319-353` | Production bug: honor `budget` param in `pressure_report()` |
| 4 | `test_replay_pressure_report_none_budget` | Production: `replay_manager.py:319-353` | Production bug: same |
| 5 | `test_replay_pressure_report_default_budget_used_when_none_passed` | Production: `replay_manager.py:319-353` | Production bug: same |
| 6 | `test_checkpoint_header_contains_rng_checkpoint` | Production: `kernel.py` `_phase_advancement` | Production bug: snapshot rng into StateUpdate |
| 7 | `test_rng_checkpoint_populated_after_tick` | Production: `kernel.py` `_phase_advancement` | Production bug: same |
| 8 | `test_shutdown_timeout_logic` | Test: `test_graceful_shutdown.py:44` | Test bug: configure mock return value |

**3 production bugs, 4 test bugs (1 test covers 2 production bugs in bucket 4).**

---

## Files Relevant to Fixes

- `src/engine/legality.py:231` — accesses `.task.payload` (correct; test passes wrong type)
- `src/core/state.py:382` — `TaskComponent` definition with `.payload: Dict`
- `src/core/updates.py:202` — `TaskUpdate` definition with `.payload_set`
- `src/engine/replay_manager.py:319-353` — `pressure_report()` ignores budget param
- `src/engine/kernel.py:637-654` — `_phase_advancement` never sets `rng_checkpoint`
- `src/platform/rng.py:40` — `DeterministicRNG.get_state()` for snapshot
- `src/core/updates.py:899` — `StateUpdate.rng_checkpoint` field
- `src/core/modes.py:7` — `_FORBIDDEN_FALLBACK_MODES` blocks fallback seeding
- `src/engine/kernel.py:886-889` — `shutdown()` calls `report.pending_replay_flushes > 0` on potentially un-typed value
