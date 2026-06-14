---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-BUDGET-GATE
date: 2026-06-14
---

# TCK-20260614-RESOURCE-BUDGET-GATE — Implementation Plan

---

## Scope Guards (What NOT to Touch)

- Do NOT modify `CacheBudgetPolicy` or `ArtifactBudgetRegistry` — these are orthogonal.
- Do NOT wire governor degradation decisions — `pressure_report()` is advisory output only.
- Do NOT touch the kernel tick hot path with `pressure_report()` calls.
- Do NOT change `CanonicalStateHasher.get_hash()` static method signature or hash logic — bit-identical output is mandatory.
- Do NOT embed `SubsystemBudget` defaults inside subsystem constructors; all defaults live in `optimization_profiles.py`.
- Do NOT introduce `src/engine/resource_budget.py` — placement decision is `src/config/optimization_profiles.py` (per investigation §Best File Placement).
- Do NOT replace `max_events` in `EventRecorder` — `budget.max_queue_items` is an independent check, not a replacement.
- Do NOT call `get_stats()` inside `ReplayManager.pressure_report()`.
- Do NOT add a lock to `_chunks_persisted` reads — it is advisory, plain `int` is sufficient (document this explicitly in a comment).
- Do NOT implement dashboard display or governor integration (later tickets: TCK-20260614-RESOURCE-DASHBOARD, governor epic).
- Do NOT modify `DEBUG_REFERENCE` profile's existing non-budget fields.

---

## Step 1 — Add `SubsystemBudget` and `SubsystemPressureReport` dataclasses

**File**: `src/config/optimization_profiles.py`

**What**: Insert two new `frozen=True, slots=True` dataclasses above `OptimizationProfile`.

`SubsystemBudget` fields (all optional with `None` default = unlimited):
- `subsystem: str`
- `max_artifact_mb: float | None = None`
- `max_pending_flushes: int | None = None`
- `max_queue_items: int | None = None`
- `max_tracked_entities: int | None = None`
- `max_full_hashes_per_100_ticks: int | None = None`
- `max_inflight_chunks: int | None = None`
- `max_hot_path_loads: int | None = None`

`SubsystemPressureReport` fields:
- `subsystem: str`
- `current_usage: int`
- `budget: int | None`
- `pressure_state: str`  — one of `"OK"`, `"WARN"`, `"DEGRADED"`
- `degradation_action: str | None`

**Extend `OptimizationProfile`**: add `subsystem_budgets: dict[str, SubsystemBudget] = field(default_factory=dict)`. Because `OptimizationProfile` is `frozen=True, slots=True`, the new field must be appended after all existing fields with a default.

**Acceptance criteria mapped**: "SubsystemBudget and SubsystemPressureReport dataclasses exist"

**Depends on**: nothing — this is the foundation for all subsequent steps.

---

## Step 2 — Define default `SubsystemBudget` instances and wire into profiles

**File**: `src/config/optimization_profiles.py`

**What**: Define module-level default budget constants for all 7 required subsystems, then pass them via `subsystem_budgets=` when constructing `DEFAULT_PROFILE` and `DEBUG_REFERENCE`. All other named profiles (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`) receive the same default budgets as `DEFAULT_PROFILE` unless there is a specific reason to override (there is none in this ticket's scope — leave them with the same defaults for now, passed explicitly so the profiles are self-documenting).

**Default budget values** (reasonable non-None for every non-DEBUG profile):
- `certification`: `max_artifact_mb=50.0`
- `replay`: `max_inflight_chunks=10`
- `observability`: `max_queue_items=5000`
- `cognition`: `max_tracked_entities=500`
- `hashing`: `max_full_hashes_per_100_ticks=10`
- `worker`: `max_pending_flushes=20`
- `content`: `max_hot_path_loads=100`

**`DEBUG_REFERENCE`**: All 7 subsystems must be present, each with all fields `None` (unlimited). This preserves the parity baseline and satisfies the AC guard test.

**Acceptance criteria mapped**: "Default budgets defined for all 7 subsystems"; "DEBUG_REFERENCE profile is unaffected (its budgets are set to None = unlimited)"

**Depends on**: Step 1 (dataclasses must exist before instances can be constructed).

---

## Step 3 — Add `_chunks_persisted` counter to `ReplayManager` and expose `pressure_report()`

**File**: `src/engine/replay_manager.py`

**What**:

1. Add `budget: SubsystemBudget | None = None` parameter to `ReplayManager.__init__()`. Store as `self._budget = budget`.

2. Add `self._chunks_persisted: int = 0` to `__init__()` (after executor setup). Add a comment: `# Advisory only — plain int, no lock needed; slight race is acceptable for pressure signal.`

3. In `_execute_persistence()`, after the `with self._manifest_lock:` block that appends to `self._manifest["chunks"]`, add `self._chunks_persisted += 1` outside the lock (after the block closes). This ensures the increment happens only on success, and the advisory read in `pressure_report()` needs no lock.

4. Add method `pressure_report() -> SubsystemPressureReport`:
   - Compute `inflight = self._current_chunk_id - self._chunks_persisted` (lock-free, advisory snapshot).
   - If `self._budget is None` or `self._budget.max_inflight_chunks is None`: return `SubsystemPressureReport(subsystem="replay", current_usage=inflight, budget=None, pressure_state="OK", degradation_action=None)`.
   - `cap = self._budget.max_inflight_chunks`
   - `state = "OK"` if `inflight < cap * 0.8` else `"WARN"` if `inflight < cap` else `"DEGRADED"`.
   - `action = "downgrade_richness" if state == "WARN" else "disable_capture" if state == "DEGRADED" else None` (advisory strings per replay_contract.md).
   - Return `SubsystemPressureReport(subsystem="replay", current_usage=inflight, budget=cap, pressure_state=state, degradation_action=action)`.

**Import**: Add `from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport` at the top of `replay_manager.py`.

**Acceptance criteria mapped**: "ReplayManager exposes pressure_report() — at minimum reports chunk count vs. budget"

**Depends on**: Step 1 (types), Step 2 (budget instances available for construction in tests).

---

## Step 4 — Add `BudgetedCanonicalHasher` to `src/engine/checkpoint.py`

**File**: `src/engine/checkpoint.py`

**What**: Add a new instance class `BudgetedCanonicalHasher` below the existing `CanonicalStateHasher` static class. Do NOT modify `CanonicalStateHasher` itself.

`BudgetedCanonicalHasher.__init__(self, budget: SubsystemBudget)`:
- `self._budget = budget`
- `self._call_count: int = 0`
- `self._window_start_tick: int = 0`
- `self._last_known_hash: str | None = None`

`BudgetedCanonicalHasher.get_hash(self, state: AuthoritativeState, current_tick: int) -> str`:
1. **Window reset**: if `current_tick - self._window_start_tick >= 100`: `self._call_count = 0`; `self._window_start_tick = current_tick`.
2. **Budget check**: if `self._budget.max_full_hashes_per_100_ticks is not None` and `self._call_count >= self._budget.max_full_hashes_per_100_ticks`:
   - Log a WARNING: `"BudgetedCanonicalHasher: rate limit reached (%d calls in window); returning stale hash"`.
   - Return `self._last_known_hash` (may be `None` on first call; caller must handle — document this).
3. **Normal path**: increment `self._call_count`, delegate to `CanonicalStateHasher.get_hash(state)`, store result in `self._last_known_hash`, return it.

`BudgetedCanonicalHasher.pressure_report(self) -> SubsystemPressureReport`:
- If `self._budget.max_full_hashes_per_100_ticks is None`: return OK with `budget=None`.
- `cap = self._budget.max_full_hashes_per_100_ticks`
- `state = "OK"` if `self._call_count <= cap` else `"WARN"`.  (WARN when count exceeds budget, per AC.)
- `action = "returning_stale_hash"` if `state == "WARN"` else `None`.  (Must contain "stale" — required by test_plan anti-drift guard #5.)
- Return `SubsystemPressureReport(subsystem="hashing", current_usage=self._call_count, budget=cap, pressure_state=state, degradation_action=action)`.

**Import**: Add `from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport` at the top of `checkpoint.py`.

**Acceptance criteria mapped**: "CanonicalStateHasher tracks full-hash call count per 100-tick window; pressure_report() reports WARN when over budget"

**Depends on**: Step 1 (types). Does NOT depend on Steps 2 or 3.

---

## Step 5 — Wire `SubsystemBudget` into `EventRecorder` and add `pressure_report()`

**File**: `src/observability/event_recorder.py`

**What**:

1. Add `budget: SubsystemBudget | None = None` parameter to `EventRecorder.__init__()` after `enabled`. Store as `self._budget = budget`. Do NOT change the existing `max_events` behavior.

2. Add method `pressure_report(self) -> SubsystemPressureReport`:
   - `queue_size = self.queue.get_size()`
   - If `self._budget is None` or `self._budget.max_queue_items is None`: return `SubsystemPressureReport(subsystem="observability", current_usage=queue_size, budget=None, pressure_state="OK", degradation_action=None)`.
   - `cap = self._budget.max_queue_items`
   - `ratio = queue_size / cap` (guard against `cap == 0` with a `max(cap, 1)` floor).
   - `state = "OK"` if `ratio < 0.8` else `"WARN"` if `ratio < 1.0` else `"DEGRADED"`.
   - `action = "drop_low_severity" if state == "WARN" else "drop_all_non_critical" if state == "DEGRADED" else None`.
   - Return `SubsystemPressureReport(subsystem="observability", current_usage=queue_size, budget=cap, pressure_state=state, degradation_action=action)`.

3. The `record()` method body is NOT changed — the budget check at enqueue (AC wording) is satisfied by `pressure_report()` being callable at enqueue time; the AC does not require modifying `record()` to call `pressure_report()` internally. `pressure_report()` is a read-only advisory query, per the advisory model (Implementation Notes: "non-blocking and read-only").

**Import**: Add `from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport` at the top of `event_recorder.py`.

**Acceptance criteria mapped**: "EventRecorder checks max_queue_items against queue size at enqueue; returns pressure_report() with WARN when above 80%, DEGRADED at 100%"

**Depends on**: Step 1 (types). Does NOT depend on Steps 2, 3, or 4.

---

## Step 6 — Write new unit tests

**File**: `tests/unit/engine/test_resource_budget_gate.py` (new file)

**What**: Implement all tests defined in `test_plan.md`, in order:

1. `test_subsystem_budget_defaults_are_sane` — imports `DEFAULT_PROFILE`, `DEBUG_REFERENCE`; checks all 7 keys present; checks non-None in defaults; checks all-None in DEBUG_REFERENCE.
2. `test_event_recorder_reports_ok_below_warn_threshold` — 7 items at cap=10 → OK.
3. `test_event_recorder_reports_warn_at_80pct_capacity` — 8 items at cap=10 → WARN.
4. `test_event_recorder_reports_degraded_at_full_capacity` — 5 items at cap=5 → DEGRADED.
5. `test_subsystem_budget_none_fields_mean_unlimited` — `max_queue_items=None` → always OK.
6. `test_canonical_hasher_ok_within_budget` — 3 calls, cap=5 → OK.
7. `test_canonical_hasher_reports_warn_over_budget` — 4 calls, cap=3 → WARN; `degradation_action` contains "stale".
8. `test_canonical_hasher_window_resets_after_100_ticks` — exhaust in tick 0, call at tick 100 → OK with `current_usage==1`.
9. `test_replay_manager_pressure_report_ok` — fresh manager with `max_inflight_chunks=5` → report exists, `subsystem=="replay"`, `budget==5`.

Each test follows the exact structure in `test_plan.md`. Tests must be fast (< 100ms), use `unittest.mock.patch` for hash delegation, and not touch real disk I/O beyond what `tmp_path` provides.

**Acceptance criteria mapped**: "Tests: pressure_report returns correct state at varying usage levels for each wired subsystem"

**Depends on**: Steps 1–5 (all types and methods must exist for tests to import and run).

---

## Step 7 — Add parity ledger entries INFRA-194, INFRA-195, INFRA-196

**File**: `docs/parity_ledger/infrastructure.yaml`

**What**: Append three new entries at the bottom of the file (after INFRA-193):

```yaml
- id: INFRA-194
  text: >
    EventRecorder.pressure_report() returns pressure_state=WARN when queue occupancy
    is >= 80% of max_queue_items, and DEGRADED at >= 100%. Returns OK when below 80%.
    None budget yields OK unconditionally.
  status: verified
  priority: P1
  v2_evidence: src/observability/event_recorder.py::EventRecorder.pressure_report
  test_path: tests/unit/engine/test_resource_budget_gate.py::test_event_recorder_reports_warn_at_80pct_capacity
  divergence_note: null

- id: INFRA-195
  text: >
    ReplayManager.pressure_report() reports inflight chunk count vs. max_inflight_chunks
    budget. The method is non-blocking, lock-free, and advisory-only. The degradation_action
    string is consumed by the Governor; ReplayManager does not execute it.
  status: verified
  priority: P1
  v2_evidence: src/engine/replay_manager.py::ReplayManager.pressure_report
  test_path: tests/unit/engine/test_resource_budget_gate.py::test_replay_manager_pressure_report_ok
  divergence_note: null

- id: INFRA-196
  text: >
    BudgetedCanonicalHasher tracks full-hash call count per 100-tick window.
    pressure_report() returns WARN when call count exceeds max_full_hashes_per_100_ticks.
    Over-budget calls return the last known hash (stale); degradation_action contains
    "returning_stale_hash" to make the degraded return value self-documenting.
    The underlying CanonicalStateHasher static class is unchanged (INFRA-119 through INFRA-130 unaffected).
  status: verified
  priority: P1
  v2_evidence: src/engine/checkpoint.py::BudgetedCanonicalHasher
  test_path: tests/unit/engine/test_resource_budget_gate.py::test_canonical_hasher_reports_warn_over_budget
  divergence_note: null
```

**Acceptance criteria mapped**: Parity ledger remains current; INFRA-173 spirit satisfied for new subsystems.

**Depends on**: Step 6 (test paths must exist before entries are marked `verified`).

---

## Dependency Map

```
Step 1 (SubsystemBudget/SubsystemPressureReport types)
  └─► Step 2 (profile defaults)
  └─► Step 3 (ReplayManager.pressure_report)    ← independent of Steps 4, 5
  └─► Step 4 (BudgetedCanonicalHasher)           ← independent of Steps 3, 5
  └─► Step 5 (EventRecorder.pressure_report)     ← independent of Steps 3, 4
        Steps 2, 3, 4, 5 all complete
          └─► Step 6 (new unit tests)
                Step 6 complete (test paths exist)
                  └─► Step 7 (parity ledger entries)
```

Steps 3, 4, and 5 are fully independent of each other and may be implemented in any order or in parallel after Step 1.

---

## Files Changed Per Step

| Step | Files |
|------|-------|
| 1 | `src/config/optimization_profiles.py` |
| 2 | `src/config/optimization_profiles.py` |
| 3 | `src/engine/replay_manager.py` |
| 4 | `src/engine/checkpoint.py` |
| 5 | `src/observability/event_recorder.py` |
| 6 | `tests/unit/engine/test_resource_budget_gate.py` (new) |
| 7 | `docs/parity_ledger/infrastructure.yaml` |

---

## Acceptance Criteria Traceability

| Acceptance Criterion | Covered By |
|---|---|
| `SubsystemBudget` and `SubsystemPressureReport` dataclasses exist | Step 1 |
| Default budgets defined for all 7 subsystems | Step 2 |
| `DEBUG_REFERENCE` profile has all-`None` subsystem budgets | Step 2 |
| `EventRecorder.pressure_report()` returns WARN ≥80%, DEGRADED at 100% | Step 5, verified by Step 6 |
| `ReplayManager.pressure_report()` reports chunk count vs. budget | Step 3, verified by Step 6 |
| `CanonicalStateHasher` rate-tracked; `pressure_report()` WARN over budget | Step 4, verified by Step 6 |
| Tests: correct pressure state at varying usage levels | Step 6 |
| `DEBUG_REFERENCE` profile unaffected | Step 2 + Step 6 (`test_subsystem_budget_defaults_are_sane`) |
| Parity ledger updated | Step 7 |

---

## Regression Test Commands

After Step 6, run in order:

```bash
# Primary: new tests
pytest tests/unit/engine/test_resource_budget_gate.py -v

# Regression: existing affected unit tests
pytest tests/unit/observability/test_event_recorder.py \
       tests/unit/kernel/test_replay_pressure.py \
       tests/unit/kernel/test_replay_chunk_rotation.py \
       tests/unit/kernel/test_replay_contract.py \
       tests/unit/kernel/test_replay_overflow.py \
       tests/unit/kernel/test_replay_shutdown_budget.py \
       tests/unit/engine/ tests/unit/core/ -v

# Hash/determinism integrity (must not regress)
pytest tests/integration/kernel/test_checkpoint_reproducibility.py \
       tests/integration/kernel/test_determinism_suite.py -v

# Final gate
pytest -m "not slow" -v
```
