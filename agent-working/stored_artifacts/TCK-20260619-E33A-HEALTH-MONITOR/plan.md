---
ticket_id: TCK-20260619-E33A-HEALTH-MONITOR
phase: plan
date: 2026-06-21
---

# Plan: EconomyHealthMonitor + Metrics

## Scope Guards (What NOT to touch)

- Do NOT add a new `TickPhase` enum value — `src/engine/phases.py` is FROZEN.
- Do NOT store `EconomyHealthSnapshot` in `AuthoritativeState` — it is transient observability only.
- Do NOT modify `src/observability/warehouse/models.py` — that file's `MetricWindowRecord` is a separate DB schema layer; the canonical record is in `src/observability/reporting/metric_recorder.py`.
- Do NOT scan `e.inventory.items` for `gold_coin` stacks — use `e.inventory.gold` (the authoritative scalar field on `InventoryComponent`).
- Do NOT use `e.is_alive` — the correct liveness path is `e.combat.alive`.
- Do NOT wire into the GOVERNANCE sub-phase of the `AuthoritativeApplyPipeline` (RESOLUTION territory). The monitor is read-only observability, not a resolution action.
- Do NOT write a new output file — reuse `metric_windows.jsonl` via the existing `MetricWindowRecorder` pipeline.
- Do NOT break the `MetricWindowAccumulator` flush cycle — new fields must be additive optional fields with defaults.
- Do NOT implement `transaction_velocity` or `avg_price_index` data sourcing — both are explicit TODOs per ticket scope; stub at `0.0` and `{}` respectively.

---

## Dependency Map

```
Step 1 (EconomyHealthMonitor + EconomyHealthSnapshot — pure module, no imports from steps 2–4)
  └─► Step 2a (extend MetricWindowRecord with optional economy fields)
        └─► Step 2b (extend MetricWindowAccumulator to accept + store snapshot)
              └─► Step 2c (extend MetricWindowAccumulator.flush() to emit economy fields)
                    └─► Step 2d (call EconomyHealthMonitor.sample() in kernel, pass snapshot to record_tick)
Step 1 ──────────────────────────────────────────────────────────────────────────► Step 3 (unit tests — imports Step 1 only)
Step 2a + 2b + 2c + 2d ──────────────────────────────────────────────────────────► Step 3 TC-09 (integration test)
Steps 1–3 ───────────────────────────────────────────────────────────────────────► Step 4 (parity ledger — docs only)
```

---

## Step 1 — Create `src/economy/health_monitor.py`

**Purpose:** Implement `EconomyHealthSnapshot` (typed Pydantic model) and `EconomyHealthMonitor` (pure read-only sampler). No integration wiring here — purely the computation module.

**File to create:** `src/economy/health_monitor.py`

**Specification:**

```python
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from src.core.state import AuthoritativeState


class EconomyHealthSnapshot(BaseModel):
    """Transient read-only economy health sample for one window boundary."""
    tick: int
    gini_coefficient: float
    transaction_velocity: float   # TODO E33A: count trades in window
    avg_price_index: dict         # TODO E33A: per-commodity prices


class EconomyHealthMonitor:
    WINDOW_SIZE: int = 100        # ticks per sampling window

    @staticmethod
    def sample(state: AuthoritativeState, tick: int) -> Optional[EconomyHealthSnapshot]:
        """Sample economy health at window boundaries. Returns None otherwise."""
        if tick % EconomyHealthMonitor.WINDOW_SIZE != 0:
            return None
        entity_gold: list[float] = [
            float(e.inventory.gold)
            for e in state.entities.values()
            if e.combat.alive
        ]
        return EconomyHealthSnapshot(
            tick=tick,
            gini_coefficient=EconomyHealthMonitor._gini(entity_gold),
            transaction_velocity=0.0,   # TODO E33A: count trades in window
            avg_price_index={},         # TODO E33A: per-commodity prices
        )

    @staticmethod
    def _gini(values: list[float]) -> float:
        """Standard discrete Gini coefficient (sorted 1-indexed formula)."""
        if not values or sum(values) == 0:
            return 0.0
        n = len(values)
        s = sorted(values)
        cum = sum((i + 1) * v for i, v in enumerate(s))
        return (2 * cum) / (n * sum(s)) - (n + 1) / n
```

**Key corrections from ticket pseudocode:**
- `e.inventory.gold` replaces the `gold_coin` item-stack scan
- `e.combat.alive` replaces the non-existent `e.is_alive`
- Return type annotated as `Optional[EconomyHealthSnapshot]`

**Verification:** `EconomyHealthMonitor._gini([1, 2, 3, 4])` must return `0.25` (manual check: cum = 1+4+9+16 = 30; G = 60/40 − 5/4 = 1.5 − 1.25 = 0.25).

**AC coverage:** Enables TC-01 through TC-08; is the prerequisite for TC-09.

---

## Step 2 — Wire snapshot into the `MetricWindowRecord` pipeline

This is a four-part atomic block: all four sub-steps must land together or the pipeline is broken between them. They touch three files.

### Step 2a — Extend `MetricWindowRecord` with optional economy health fields

**File:** `src/observability/reporting/metric_recorder.py`, `MetricWindowRecord` class (lines 10–48)

Add after the `behavior_queue_push_ms_avg` field (line 48):

```python
    # Economy health extension (E33A)
    economy_gini_coefficient: Optional[float] = None
    economy_transaction_velocity: Optional[float] = None
    economy_avg_price_index_json: Optional[str] = None  # JSON-encoded dict
```

All three fields are `Optional` with `None` defaults — strictly additive, no existing `flush()` call breaks.

**Verification:** `MetricWindowRecord(run_id="x", window_start_tick=0, window_end_tick=100, ticks_observed=100, alive_entities_avg=0.0, active_entities_avg=0.0, gold_total_avg=0.0, tick_compute_ms_avg=0.0, tick_compute_ms_p95=0.0, memory_rss_bytes_avg=0.0, memory_rss_bytes_max=0.0, hard_law_violation_count=0, event_count=0, anomaly_candidate_count=0)` must still construct without error (no required fields added).

### Step 2b — Extend `MetricWindowAccumulator` to accept and store a snapshot

**File:** `src/observability/reporting/metric_recorder.py`, `MetricWindowAccumulator` class

Add instance variable in `__init__` (line 55 area):

```python
        self._economy_snapshot: Optional["EconomyHealthSnapshot"] = None
```

Add a new method after `record_tick`:

```python
    def record_economy_snapshot(self, snapshot: "EconomyHealthSnapshot") -> None:
        """Store the most recent economy health snapshot (one per window boundary)."""
        self._economy_snapshot = snapshot
```

**Why store only the most recent:** `sample()` only fires on `tick % 100 == 0`. Within a 100-tick accumulation window there is exactly one snapshot — the one at the window boundary tick that also triggers `_flush_window`. Storing the last is correct.

### Step 2c — Emit economy fields in `MetricWindowAccumulator.flush()`

**File:** `src/observability/reporting/metric_recorder.py`, `flush()` method (line 215 area)

Add before the `return MetricWindowRecord(...)` call:

```python
        import json as _json
        eco_gini = None
        eco_velocity = None
        eco_price_json = None
        if self._economy_snapshot is not None:
            eco_gini = self._economy_snapshot.gini_coefficient
            eco_velocity = self._economy_snapshot.transaction_velocity
            eco_price_json = _json.dumps(self._economy_snapshot.avg_price_index)
```

Add to the `MetricWindowRecord(...)` constructor call (after `behavior_queue_push_ms_avg=...`):

```python
            economy_gini_coefficient=eco_gini,
            economy_transaction_velocity=eco_velocity,
            economy_avg_price_index_json=eco_price_json,
```

**Verification:** A flush with no snapshot attached produces `None` for all three fields. A flush with a snapshot attached serialises correctly.

### Step 2d — Call `EconomyHealthMonitor.sample()` in kernel and pass snapshot to `record_tick`

**File:** `src/engine/kernel.py`, lines 381–400 (the `if self._metric_recorder:` block)

The current block:
```python
        if self._metric_recorder:
            try:
                from src.engine.metrics import MetricsService
                world_metrics = MetricsService.extract_metrics(self._state)
            except Exception:
                logger.exception("Failed to extract WorldMetrics")
                world_metrics = None

            signals = self._status.signal_history[-1] if self._status.signal_history else None
            event_count = getattr(self, "_current_tick_event_count", 0)
            violation_count = getattr(self, "_current_tick_violation_count", 0)

            self._metric_recorder.record_tick(
                tick=self._state.tick,
                world_metrics=world_metrics,
                ...
            )
```

Extend to:
```python
        if self._metric_recorder:
            try:
                from src.engine.metrics import MetricsService
                world_metrics = MetricsService.extract_metrics(self._state)
            except Exception:
                logger.exception("Failed to extract WorldMetrics")
                world_metrics = None

            # Economy health snapshot (E33A) — read-only, fires every WINDOW_SIZE ticks
            try:
                from src.economy.health_monitor import EconomyHealthMonitor
                economy_snapshot = EconomyHealthMonitor.sample(self._state, self._state.tick)
                if economy_snapshot is not None:
                    self._metric_recorder._accumulator.record_economy_snapshot(economy_snapshot)
            except Exception:
                logger.exception("Failed to sample EconomyHealthMonitor")

            signals = self._status.signal_history[-1] if self._status.signal_history else None
            event_count = getattr(self, "_current_tick_event_count", 0)
            violation_count = getattr(self, "_current_tick_violation_count", 0)

            self._metric_recorder.record_tick(
                tick=self._state.tick,
                world_metrics=world_metrics,
                ...
            )
```

**Why call before `record_tick` rather than after:** `record_tick` checks `ticks_observed >= window_size` and calls `_flush_window` which resets the accumulator. The snapshot must be stored in the accumulator before `flush()` is triggered, so `record_economy_snapshot` must be called before `record_tick`.

**Why access `_accumulator` directly:** `MetricWindowRecorder` does not expose a public economy snapshot method. Adding one to `MetricWindowRecorder` (a thin public wrapper calling through to `_accumulator`) is cleaner; implement as a one-liner public method `record_economy_snapshot(snapshot)` on `MetricWindowRecorder` that delegates to `self._accumulator.record_economy_snapshot(snapshot)`, and call `self._metric_recorder.record_economy_snapshot(economy_snapshot)` from the kernel.

**Scope guard:** The `try/except` wrapper ensures any failure in the monitor (e.g., missing attribute on an entity) is logged and swallowed — never blocks a tick.

**AC coverage:** Step 2 unlocks TC-09 (2000-tick integration test). The `metric_windows.jsonl` lines will contain `economy_gini_coefficient`, `economy_transaction_velocity`, `economy_avg_price_index_json` at every window boundary (every 100 ticks → ≥20 entries in 2000 ticks).

---

## Step 3 — Write `tests/unit/economy/test_economy_health_monitor.py`

**Files to create:**
- `tests/unit/economy/__init__.py` (empty — directory does not exist yet)
- `tests/unit/economy/test_economy_health_monitor.py`

**Test cases to implement (per test_plan.md):**

| ID | Name | What it pins |
|---|---|---|
| TC-01 | `test_gini_coefficient_computed_correctly` | Formula correctness for 3 known distributions |
| TC-02 | `test_gini_edge_cases` | Empty list, all-zero, single entity, large uniform |
| TC-03 | `test_sample_returns_none_off_window` | `None` for ticks 1, 50, 99, 101, 150 |
| TC-04 | `test_sample_returns_snapshot_on_window_boundary` | Non-None for ticks 100, 200, 500, 1000 |
| TC-05 | `test_sample_reads_inventory_gold_not_items` | `inventory.gold` is the wealth source (anti-drift guard) |
| TC-06 | `test_sample_excludes_dead_entities` | `combat.alive == False` entities excluded from Gini |
| TC-07 | `test_snapshot_fields_present` | `gini_coefficient` in [0,1], `transaction_velocity: float`, `avg_price_index: dict` |
| TC-08 | `test_snapshot_is_not_mutating_state` | `state.fingerprint()` unchanged before/after sample |
| TC-09 | `test_metric_windows_produced_in_2000_tick_run` | Integration: ≥20 entries with economy fields in `metric_windows.jsonl` — mark `@pytest.mark.slow` |

**Fixtures required:**

- `minimal_state`: An `AuthoritativeState` with ≥1 alive entity, `inventory.gold=10`. Build via the project's existing state factory or construct a minimal mock.
- `state_with_entities`: 3 entities — entity_a (`gold=100`, no gold_coin items), entity_b (`gold=0`, has `ItemStack("gold_coin", 50)`), entity_c (`gold=200`). All alive.
- `state_with_mixed_alive`: 3 entities — two alive (`gold=100`, `gold=200`), one dead (`combat.alive=False`, `gold=999`).
- `standard_kernel_factory`: Existing kernel factory from integration test infrastructure (check `tests/conftest.py` or `tests_v2/conftest.py` for the canonical fixture name before implementing).

**Key computed values (pre-verified for test assertions):**

- `_gini([10, 10, 10, 10])` → `0.0` (perfect equality)
- `_gini([0, 0, 0, 100])` → `0.75` (perfect inequality, n=4: (n-1)/n)
- `_gini([1, 2, 3, 4])` → `0.25` (cum=30, G=60/40−5/4=0.25)
- TC-05 wealth vector `[0, 100, 200]` (sorted) → Gini = 4/9 ≈ 0.4444 (cum=1×0+2×100+3×200=800, G=1600/900−4/3=16/9−12/9=4/9)
- TC-06 wealth vector `[100, 200]` → Gini = 1/6 ≈ 0.1667 (cum=100+400=500, G=1000/600−3/2=5/3−3/2=1/6)

**Scoped run to verify step:**
```bash
pytest tests/unit/economy/test_economy_health_monitor.py -x -v -m "not slow"
```

**AC coverage:** TC-01 is the named AC test; all remaining TCs are required coverage per test_plan.md.

---

## Step 4 — Add parity ledger entry TOWN-177

**File:** `docs/parity_ledger/town_resource.yaml`

Append after the last entry (currently TOWN-176, line 1864):

```yaml
- id: TOWN-177
  text: >
    EconomyHealthMonitor samples gold distribution read-only once per WINDOW_SIZE
    ticks and writes EconomyHealthSnapshot (gini_coefficient, transaction_velocity,
    avg_price_index) into metric_windows.jsonl economy fields without mutating
    AuthoritativeState.
  status: verified
  priority: P1
  v2_evidence: >
    src/economy/health_monitor.py — EconomyHealthMonitor.sample() reads
    e.inventory.gold and e.combat.alive; never writes to state; result passed via
    MetricWindowRecorder into metric_windows.jsonl
  test_path: tests/unit/economy/test_economy_health_monitor.py::test_gini_coefficient_computed_correctly
  divergence_note: null
```

Note: Set `status: verified` (not `missing`) at write time — implementation is complete before this step executes.

**Verification:** `grep -c "TOWN-177" docs/parity_ledger/town_resource.yaml` returns `1`.

---

## Acceptance Criteria → Step Mapping

| AC | Step | Test |
|---|---|---|
| 2000-tick run produces `metric_windows.jsonl` with ≥20 entries | Step 2 (pipeline wiring) | TC-09 |
| Each entry has `gini_coefficient` field | Steps 1 + 2a + 2c | TC-09 field check |
| Each entry has `transaction_velocity` field | Steps 1 + 2a + 2c | TC-09 field check |
| Each entry has `avg_price_index` field | Steps 1 + 2a + 2c | TC-09 field check |
| `test_gini_coefficient_computed_correctly` passes | Step 1 (formula) | TC-01 |

---

## Regression Guard

Run before and after implementation:
```bash
pytest tests_v2/test_deterministic_baseline.py tests_v2/replay/ tests/rpg/test_resource_conservation_v2.py -x -v --tb=short -m "not slow"
```

Critical guards:
- `test_full_tick_determinism` — monitor must not perturb state hash
- `test_subsystem_order_documentation` — no new `TickPhase` value
- Replay tests — monitor is observability-only, no replay output change

---

## Deviations from Plan

None. All steps followed exactly as specified. One note on step 2c: the plan draft showed `import json as _json` but the implementation instruction said to use the existing `json` import — existing `import json` at line 219 of `flush()` was used directly, no alias added (per CRITICAL ARCHITECTURE CONSTRAINTS).

---

## Files Changed Summary

| File | Action | Step |
|---|---|---|
| `src/economy/health_monitor.py` | CREATE | 1 |
| `src/observability/reporting/metric_recorder.py` | MODIFY (3 locations: MetricWindowRecord, MetricWindowAccumulator, flush) | 2a, 2b, 2c |
| `src/engine/kernel.py` | MODIFY (1 location: metric recorder block ~L381) | 2d |
| `tests/unit/economy/__init__.py` | CREATE (empty) | 3 |
| `tests/unit/economy/test_economy_health_monitor.py` | CREATE | 3 |
| `docs/parity_ledger/town_resource.yaml` | MODIFY (append TOWN-177) | 4 |
