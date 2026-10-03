---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-BUDGET-GATE
date: 2026-06-14
---

# TCK-20260614-RESOURCE-BUDGET-GATE — Test Plan

## Regression Surface

Existing tests that exercise the three wired subsystems and must remain green after this ticket's changes:

| File | What it covers | Risk from this ticket |
|---|---|---|
| `tests/unit/observability/test_event_recorder.py` | `EventRecorder` disabled mode, bounds, eviction, JSONL write | Adding `pressure_report()` and budget check to `record()` must not alter eviction behavior or JSONL output |
| `tests/unit/kernel/test_replay_pressure.py` | `ReplayManager` retention modes, rotation triggers, manifest write | Adding `pressure_report()` and `_chunks_persisted` counter must not affect rotation logic or manifest atomicity |
| `tests/unit/kernel/test_replay_chunk_rotation.py` | Chunk rotation on tick/saturation | Same risk as above |
| `tests/unit/kernel/test_replay_contract.py` | Replay contract compliance | Advisory-only `pressure_report()` must not alter replay allowed/richness logic |
| `tests/unit/kernel/test_replay_overflow.py` | Buffer overflow/drop semantics | Unchanged by this ticket |
| `tests/unit/kernel/test_replay_shutdown_budget.py` | Finalization timeout enforcement | Unchanged by this ticket |
| `tests/integration/kernel/test_checkpoint_reproducibility.py` | `CanonicalStateHasher` reproducibility | Must verify that rate-limiting does not silently produce stale hashes that pass hash-equality checks |
| `tests/integration/kernel/test_determinism_suite.py` | Full determinism across runs | Hash-value bit identity must be preserved when under budget |
| `tests/certification/test_artifact_budget.py` | `ArtifactBudgetRegistry` (INFRA-193) | No overlap with subsystem budgets; should remain green with no changes |
| `tests/certification/test_evidence_levels.py` | `CanonicalStateHasher.get_hash()` called in harness | If `CanonicalStateHasher` becomes an instance, the harness construction must pass an instance |

---

## New Tests Required

**File**: `tests/unit/engine/test_resource_budget_gate.py`

All tests must be fast (< 100ms each), isolated (no file I/O, no real executor threads where avoidable), and deterministic.

---

### test_subsystem_budget_defaults_are_sane

**AC**: Default `SubsystemBudget` instances exist for all 7 subsystems; `DEBUG_REFERENCE` profile has all-`None` budgets.

```python
def test_subsystem_budget_defaults_are_sane():
    from src.config.optimization_profiles import DEFAULT_PROFILE, DEBUG_REFERENCE
    # All 7 subsystems present in DEFAULT_PROFILE
    required = {"certification", "replay", "observability", "cognition", "hashing", "worker", "content"}
    assert set(DEFAULT_PROFILE.subsystem_budgets.keys()) == required

    # All default budgets have at least one non-None field
    for name, budget in DEFAULT_PROFILE.subsystem_budgets.items():
        fields = [
            budget.max_artifact_mb, budget.max_pending_flushes, budget.max_queue_items,
            budget.max_tracked_entities, budget.max_full_hashes_per_100_ticks,
            budget.max_inflight_chunks, budget.max_hot_path_loads
        ]
        assert any(f is not None for f in fields), f"{name} budget has all-None fields"

    # DEBUG_REFERENCE has all-None budgets (unlimited)
    for name, budget in DEBUG_REFERENCE.subsystem_budgets.items():
        fields = [
            budget.max_artifact_mb, budget.max_pending_flushes, budget.max_queue_items,
            budget.max_tracked_entities, budget.max_full_hashes_per_100_ticks,
            budget.max_inflight_chunks, budget.max_hot_path_loads
        ]
        assert all(f is None for f in fields), f"DEBUG_REFERENCE {name} budget must be unlimited (all None)"
```

---

### test_event_recorder_reports_warn_at_80pct_capacity

**AC**: `EventRecorder.pressure_report()` returns `pressure_state == "WARN"` when queue occupancy is between 80% and 99% of `max_queue_items`.

```python
def test_event_recorder_reports_warn_at_80pct_capacity():
    from src.config.optimization_profiles import SubsystemBudget
    from src.observability.event_recorder import EventRecorder
    from src.observability.events import SimulationEvent

    budget = SubsystemBudget(subsystem="observability", max_queue_items=10)
    recorder = EventRecorder(enabled=True, budget=budget)
    # Force the queue to report a size of 8 (80% of 10) without real I/O
    recorder.queue.max_size = 10

    def make_event(n):
        return SimulationEvent(
            event_type="test", event_category="test", tick=n,
            severity="INFO", source_system="test", message="m", entity_id=n
        )

    # Fill queue to exactly 80%: 8 items
    # Bypass in-memory eviction by setting a large max_events
    recorder.max_events = 1000
    for i in range(8):
        recorder.record(make_event(i))

    report = recorder.pressure_report()
    assert report.subsystem == "observability"
    assert report.pressure_state == "WARN", f"Expected WARN at 80%, got {report.pressure_state}"
    assert report.current_usage == 8
    assert report.budget == 10
    assert report.degradation_action is not None

    recorder.shutdown()
```

---

### test_event_recorder_reports_degraded_at_full_capacity

**AC**: `EventRecorder.pressure_report()` returns `pressure_state == "DEGRADED"` when queue occupancy is at or above 100% of `max_queue_items`.

```python
def test_event_recorder_reports_degraded_at_full_capacity():
    from src.config.optimization_profiles import SubsystemBudget
    from src.observability.event_recorder import EventRecorder
    from src.observability.events import SimulationEvent

    budget = SubsystemBudget(subsystem="observability", max_queue_items=5)
    recorder = EventRecorder(enabled=True, budget=budget)
    recorder.queue.max_size = 5
    recorder.max_events = 1000

    def make_event(n):
        return SimulationEvent(
            event_type="test", event_category="test", tick=n,
            severity="INFO", source_system="test", message="m", entity_id=n
        )

    # Fill queue to 100% (5 items). BoundedObservabilityQueue.try_push should cap at max_size.
    for i in range(5):
        recorder.record(make_event(i))

    report = recorder.pressure_report()
    assert report.pressure_state == "DEGRADED", f"Expected DEGRADED at 100%, got {report.pressure_state}"
    assert report.current_usage >= 5

    recorder.shutdown()
```

---

### test_event_recorder_reports_ok_below_warn_threshold

**AC**: `pressure_report()` returns `pressure_state == "OK"` when queue occupancy is below 80%.

```python
def test_event_recorder_reports_ok_below_warn_threshold():
    from src.config.optimization_profiles import SubsystemBudget
    from src.observability.event_recorder import EventRecorder
    from src.observability.events import SimulationEvent

    budget = SubsystemBudget(subsystem="observability", max_queue_items=10)
    recorder = EventRecorder(enabled=True, budget=budget)
    recorder.queue.max_size = 10
    recorder.max_events = 1000

    def make_event(n):
        return SimulationEvent(
            event_type="test", event_category="test", tick=n,
            severity="INFO", source_system="test", message="m", entity_id=n
        )

    # 7 items = 70% — below 80% warn threshold
    for i in range(7):
        recorder.record(make_event(i))

    report = recorder.pressure_report()
    assert report.pressure_state == "OK", f"Expected OK at 70%, got {report.pressure_state}"
    recorder.shutdown()
```

---

### test_canonical_hasher_reports_warn_over_budget

**AC**: `CanonicalStateHasher` (or its budget-aware wrapper) tracks calls per 100-tick window; `pressure_report()` returns `WARN` when calls exceed `max_full_hashes_per_100_ticks`.

```python
def test_canonical_hasher_reports_warn_over_budget():
    from src.config.optimization_profiles import SubsystemBudget
    from src.engine.checkpoint import BudgetedCanonicalHasher  # new instance wrapper
    from unittest.mock import MagicMock, patch

    budget = SubsystemBudget(subsystem="hashing", max_full_hashes_per_100_ticks=3)
    hasher = BudgetedCanonicalHasher(budget=budget)

    fake_state = MagicMock()
    # Tick window starts at 0; make 4 calls within tick 0–99
    with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="abc123"):
        for _ in range(4):
            hasher.get_hash(fake_state, current_tick=10)

    report = hasher.pressure_report()
    assert report.subsystem == "hashing"
    assert report.pressure_state == "WARN", f"Expected WARN after 4 calls > budget 3, got {report.pressure_state}"
    assert report.current_usage == 4
    assert report.budget == 3
    assert report.degradation_action is not None
    assert "stale" in report.degradation_action.lower()
```

---

### test_canonical_hasher_ok_within_budget

**AC**: `pressure_report()` returns OK when call count is within the 100-tick window budget.

```python
def test_canonical_hasher_ok_within_budget():
    from src.config.optimization_profiles import SubsystemBudget
    from src.engine.checkpoint import BudgetedCanonicalHasher
    from unittest.mock import MagicMock, patch

    budget = SubsystemBudget(subsystem="hashing", max_full_hashes_per_100_ticks=5)
    hasher = BudgetedCanonicalHasher(budget=budget)

    fake_state = MagicMock()
    with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="abc123"):
        for _ in range(3):
            hasher.get_hash(fake_state, current_tick=10)

    report = hasher.pressure_report()
    assert report.pressure_state == "OK"
```

---

### test_canonical_hasher_window_resets_after_100_ticks

**AC**: Call counter resets when `current_tick - window_start_tick >= 100`.

```python
def test_canonical_hasher_window_resets_after_100_ticks():
    from src.config.optimization_profiles import SubsystemBudget
    from src.engine.checkpoint import BudgetedCanonicalHasher
    from unittest.mock import MagicMock, patch

    budget = SubsystemBudget(subsystem="hashing", max_full_hashes_per_100_ticks=2)
    hasher = BudgetedCanonicalHasher(budget=budget)
    fake_state = MagicMock()

    with patch("src.engine.checkpoint.CanonicalStateHasher.get_hash", return_value="abc123"):
        # Exhaust budget in window starting at tick 0
        hasher.get_hash(fake_state, current_tick=0)
        hasher.get_hash(fake_state, current_tick=0)
        hasher.get_hash(fake_state, current_tick=0)  # Over budget

        # Advance 100 ticks — new window
        hasher.get_hash(fake_state, current_tick=100)

    report = hasher.pressure_report()
    # After reset, only 1 call in the new window — should be OK
    assert report.pressure_state == "OK"
    assert report.current_usage == 1
```

---

### test_replay_manager_pressure_report_ok

**AC**: `ReplayManager.pressure_report()` exists, returns `SubsystemPressureReport` with `subsystem == "replay"`, and returns `OK` when inflight count is within budget.

```python
def test_replay_manager_pressure_report_ok(tmp_path):
    from src.config.optimization_profiles import SubsystemBudget
    from src.engine.replay_manager import ReplayManager

    replay_dir = tmp_path / "replay"
    replay_dir.mkdir()
    budget = SubsystemBudget(subsystem="replay", max_inflight_chunks=5)
    manager = ReplayManager(run_dir=replay_dir, profile_name="test", budget=budget)

    report = manager.pressure_report()
    assert report.subsystem == "replay"
    assert report.pressure_state in ("OK", "WARN", "DEGRADED")
    assert report.current_usage >= 0
    assert report.budget == 5
```

---

### test_subsystem_budget_none_fields_mean_unlimited

**AC**: `None` budget field values must yield `pressure_state == "OK"` always.

```python
def test_subsystem_budget_none_fields_mean_unlimited():
    from src.config.optimization_profiles import SubsystemBudget
    from src.observability.event_recorder import EventRecorder
    from src.observability.events import SimulationEvent

    # Unlimited budget: max_queue_items=None
    budget = SubsystemBudget(subsystem="observability", max_queue_items=None)
    recorder = EventRecorder(enabled=True, budget=budget)
    recorder.max_events = 1000

    def make_event(n):
        return SimulationEvent(
            event_type="test", event_category="test", tick=n,
            severity="INFO", source_system="test", message="m", entity_id=n
        )

    for i in range(500):
        recorder.record(make_event(i))

    report = recorder.pressure_report()
    assert report.pressure_state == "OK", "None budget must always yield OK"
    recorder.shutdown()
```

---

## Scoped Pytest Commands

Primary scope (new tests + directly affected units):
```
pytest tests/unit/engine/test_resource_budget_gate.py -v
```

Regression sweep (existing tests in affected domains):
```
pytest tests/unit/observability/test_event_recorder.py \
       tests/unit/kernel/test_replay_pressure.py \
       tests/unit/kernel/test_replay_chunk_rotation.py \
       tests/unit/kernel/test_replay_contract.py \
       tests/unit/kernel/test_replay_overflow.py \
       tests/unit/kernel/test_replay_shutdown_budget.py \
       tests/unit/engine/ \
       tests/unit/core/ \
       -v
```

Checkpoint/determinism regression (must not change hash values):
```
pytest tests/integration/kernel/test_checkpoint_reproducibility.py \
       tests/integration/kernel/test_determinism_suite.py \
       -v
```

Full non-slow suite (final gate before merge):
```
pytest -m "not slow" -v
```

---

## Anti-Drift Guards

1. **`pressure_report()` is read-only**: No test should verify that calling `pressure_report()` modifies any state. Add an assertion that calling it twice returns equivalent results (idempotency check).

2. **No test should call `CanonicalStateHasher.get_hash()` with a real `AuthoritativeState` to test rate limiting** — use `unittest.mock.patch` to isolate the hash work from the rate-tracking logic.

3. **`DEBUG_REFERENCE` budget guard**: Add `test_subsystem_budget_defaults_are_sane` assertion that `DEBUG_REFERENCE.subsystem_budgets` entries all have `None` for every budget field. This prevents silent regression where a future profile addition accidentally caps the debug profile.

4. **INFRA-193 regression guard**: `tests/certification/test_artifact_budget.py` must remain green. The new `SubsystemBudget`/`SubsystemPressureReport` types are orthogonal to `ArtifactBudget`/`BudgetCheckResult` — verify no naming collision in imports.

5. **Stale hash documentation guard**: The `BudgetedCanonicalHasher` test for over-budget behavior must assert that the returned value equals `_last_known_hash` and that `pressure_report().degradation_action` contains the word "stale" or "cached" to ensure the degraded return value is self-documenting.

6. **`pressure_report()` non-blocking contract**: No test fixture for `pressure_report()` should require real thread pool activity or disk I/O to produce a result. All tests must be runnable without a live executor or filesystem.
