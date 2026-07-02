---
ticket_id: TCK-20260630-SIMQ-WIRE-KERNEL
phase: test_plan
date: 2026-06-30
---

# Test Plan: Wire SimQ quality_fn into Kernel Event Pipeline

## Regression Surface

The following test suites must continue to pass without modification (except for the
two feed tests noted under "Tests Requiring Update"):

```
pytest tests/observability/ -x
pytest tests/simulation_quality/ -x
```

Key tests within the regression surface:

| File | Critical tests | What they guard |
|---|---|---|
| `tests/simulation_quality/test_quality_hub_integration.py` | All classes | Hub routing, accumulation, persistence, error isolation, disable mechanism |
| `tests/simulation_quality/test_feed.py` | `test_build_feed_*` × 5, `test_broker_*` × 2 | `build_feed_from_env()` contract, BrokerQualityFeed behavior |
| `tests/observability/` | Full suite | `BoundedObservabilityQueue`, `QueueDrainWorker`, `EventRecorder` behavior |
| `tests/certification/test_event_observability_parity.py` | `test_state_hash_parity_across_observability_modes` | Observability must not mutate authoritative state hash — critical regression guard |

### Tests requiring update (not regression failures — intentional contract change)

These two tests in `tests/simulation_quality/test_feed.py` test behavior that is
being deliberately changed by this ticket:

1. `test_inprocess_feed_start_stop_no_thread_leak` (line 55-62)
   - Currently asserts `feed._worker is not None` and `feed._worker.is_alive()`
   - After refactor: `InProcessQualityFeed` has no `_worker` attribute
   - **Update**: assert `feed._hub is not None` after `start(hub)`, and confirm no
     new daemon thread was started (`threading.active_count()` delta = 0)

2. `test_inprocess_feed_health_reports_status` (line 65-74)
   - Currently reads health status from `self._worker.health_status`
   - After refactor: status is returned as a fixed string from hub reference check
   - **Update**: assert `health["status"] == "HEALTHY"` when hub is registered, and
     `health["status"] == "STOPPED"` when hub is None (existing
     `test_inprocess_feed_health_when_stopped` at line 77 still passes as-is if
     `_hub` is initialized to `None`)

---

## New Tests Required

### 1. Unit: EventRecorder passes quality_fn to its QueueDrainWorker

**File:** `tests/observability/test_event_recorder_quality_fn.py`
(or add to existing `tests/observability/test_event_recorder.py` if it exists)

**Purpose:** Verify that `EventRecorder.__init__` stores the provided callable and
passes it through to the `QueueDrainWorker`, and that the worker calls it when
draining envelopes.

```python
"""tests/observability/test_event_recorder_quality_fn.py"""
from __future__ import annotations
import time
from unittest.mock import MagicMock
from src.observability.event_recorder import EventRecorder
from src.observability.events import SimulationEvent


def _make_event(tick: int = 1) -> SimulationEvent:
    return SimulationEvent(
        event_id="test-evt-001",
        run_id="test-run",
        tick=tick,
        entity_id=1,
        event_type="action_executed",
        event_category="strategy",
        severity="INFO",
        source_system="test",
        message="test event",
        payload={},
        related_entity_ids=[],
    )


def test_event_recorder_passes_quality_fn_to_worker():
    """quality_fn kwarg is stored on the underlying QueueDrainWorker."""
    mock_fn = MagicMock()
    recorder = EventRecorder(enabled=True, quality_fn=mock_fn)
    assert recorder._worker.quality_fn is mock_fn
    recorder.shutdown()


def test_event_recorder_quality_fn_none_by_default():
    """quality_fn defaults to None — no quality callback wired without explicit arg."""
    recorder = EventRecorder(enabled=True)
    assert recorder._worker.quality_fn is None
    recorder.shutdown()


def test_event_recorder_quality_fn_called_on_drain():
    """quality_fn is called for each envelope drained from the private queue."""
    received = []
    recorder = EventRecorder(enabled=True, quality_fn=lambda env: received.append(env))
    recorder.record(_make_event(tick=1))
    recorder.record(_make_event(tick=2))
    # Allow background drain worker time to process
    deadline = time.monotonic() + 2.0
    while len(received) < 2 and time.monotonic() < deadline:
        time.sleep(0.02)
    recorder.shutdown()
    assert len(received) == 2, f"Expected 2 quality_fn calls, got {len(received)}"


def test_event_recorder_quality_fn_exception_does_not_crash_worker():
    """An exception in quality_fn must not stop the drain worker."""
    call_count = [0]

    def boom(env):
        call_count[0] += 1
        raise RuntimeError("intentional quality_fn error")

    recorder = EventRecorder(enabled=True, quality_fn=boom)
    recorder.record(_make_event(tick=1))
    recorder.record(_make_event(tick=2))
    deadline = time.monotonic() + 2.0
    while call_count[0] < 2 and time.monotonic() < deadline:
        time.sleep(0.02)
    assert recorder._worker.is_alive(), "Worker must survive quality_fn exceptions"
    recorder.shutdown()


def test_event_recorder_quality_fn_disabled_recorder_skips():
    """When enabled=False, no envelopes reach quality_fn (recorder is off)."""
    received = []
    recorder = EventRecorder(enabled=False, quality_fn=lambda env: received.append(env))
    recorder.record(_make_event(tick=1))
    time.sleep(0.1)
    recorder.shutdown()
    assert received == [], "quality_fn must not be called when recorder is disabled"
```

**Scoped run:**
```
pytest tests/observability/test_event_recorder_quality_fn.py -v
```

---

### 2. Unit: InProcessQualityFeed.start() does NOT create a second QueueDrainWorker

**File:** Update `tests/simulation_quality/test_feed.py` — replace the two
thread-assumption tests and add explicit no-worker-creation assertions.

**Purpose:** Verify that after the refactor, `InProcessQualityFeed.start()` is a
lifecycle-only call that stores the hub reference but creates no background thread.

```python
# Add to tests/simulation_quality/test_feed.py (replacing / updating affected tests)

import threading


def test_inprocess_feed_start_does_not_create_worker_thread():
    """After refactor: InProcessQualityFeed.start() must NOT spawn a QueueDrainWorker."""
    hub = _MockHub()
    feed = InProcessQualityFeed()
    threads_before = threading.active_count()
    feed.start(hub)
    threads_after = threading.active_count()
    # No new thread should have been created
    assert threads_after == threads_before, (
        f"InProcessQualityFeed.start() must not start a thread: "
        f"before={threads_before}, after={threads_after}"
    )
    feed.stop()


def test_inprocess_feed_start_registers_hub_reference():
    """After refactor: start() stores hub; stop() clears it."""
    hub = _MockHub()
    feed = InProcessQualityFeed()
    feed.start(hub)
    assert feed._hub is hub
    feed.stop()
    assert feed._hub is None


def test_inprocess_feed_health_healthy_when_hub_registered():
    """health() reports HEALTHY after start(), STOPPED before start()."""
    hub = _MockHub()
    feed = InProcessQualityFeed()
    assert feed.health()["status"] == "STOPPED"
    feed.start(hub)
    assert feed.health()["status"] == "HEALTHY"
    assert feed.health()["mode"] == "inprocess"
    feed.stop()
    assert feed.health()["status"] == "STOPPED"


def test_inprocess_feed_has_no_worker_attribute_after_refactor():
    """Confirm _worker is no longer present on InProcessQualityFeed."""
    feed = InProcessQualityFeed()
    assert not hasattr(feed, "_worker"), (
        "InProcessQualityFeed must not have a _worker attribute after refactor"
    )
```

**Scoped run:**
```
pytest tests/simulation_quality/test_feed.py -v
```

---

### 3. Integration: 20-tick sandbox_world run with InProcessQualityFeed active

**File:** `tests/simulation_quality/test_kernel_simq_integration.py` (new file)

**Purpose:** End-to-end proof that the kernel wiring produces non-zero quality scores.
Drives the Kernel directly with a minimal WorldSpec (not `sandbox_world` YAML to avoid
world-repo dependency in CI), runs 20 ticks, then reads the `QualityReport` from
`self._quality_hub` and asserts `tick_count > 0` and AGENCY `event_count > 0`.

Note: The acceptance criteria says "20-tick sandbox_world run" but the integration
test pattern in this codebase constructs the world via `WorldCompiler.compile(spec)`
from a `WorldSpec` dict, not by loading `data/worlds/sandbox_world/world.yaml`.
The test below uses a minimal embedded spec with entities that will emit AGENCY
events (`action_executed`). This avoids file-system dependency and is consistent with
`tests/integration/scenarios/test_entity_differentiation.py`.

```python
"""tests/simulation_quality/test_kernel_simq_integration.py

Integration test: kernel SimQ wiring produces non-zero quality scores in a live run.
Ticket: TCK-20260630-SIMQ-WIRE-KERNEL
"""
from __future__ import annotations
import os
import time
import pytest

from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec
from src.observability.config import ObservabilityConfig, ObservabilityMode


TICKS = 20
SEED = 42


def _build_simq_test_spec() -> WorldSpec:
    """Minimal world with entities that will emit AGENCY events within 20 ticks."""
    raw_spec = {
        "schema_version": "worldspec.v1",
        "world_id": "simq_wire_test",
        "name": "SimQ Wire Test World",
        "topology": {
            "width": 32,
            "height": 32,
            "coordinate_system": "grid",
        },
        "regions": [
            {
                "id": "arena",
                "type": "wilderness",
                "bounds": [0, 0, 32, 32],
                "terrain": "GRASS",
                "sovereignty": "neutral",
            }
        ],
        "entities": [
            {
                "id": f"hero_{i}",
                "type": "hero",
                "class": "warrior",
                "location": {"region": "arena", "x": i * 4, "y": 0},
            }
            for i in range(4)
        ] + [
            {
                "id": "monster_0",
                "type": "monster",
                "class": "beast",
                "location": {"region": "arena", "x": 16, "y": 16},
            }
        ],
    }
    return WorldSpec.model_validate(raw_spec)


@pytest.fixture
def simq_kernel(tmp_path):
    """Build a Kernel with SimQ enabled (QUALITY_SCORING_DISABLED unset)."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
    # Ensure SimQ is enabled
    os.environ.pop("QUALITY_SCORING_DISABLED", None)
    os.environ.pop("QUALITY_FEED_MODE", None)  # use default inprocess

    spec = _build_simq_test_spec()
    state, _report = WorldCompiler.compile(spec, seed=SEED)
    rng = DeterministicRNG(SEED)
    profile = RuntimeProfile(
        name="simq-wire-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=0,  # local sequential
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0,
    )
    kernel = Kernel(profile, state, rng, run_id="simq-wire-test-run")
    yield kernel
    kernel.shutdown()
    ObservabilityConfig.set_override_mode(None)


def test_simq_wiring_produces_nonzero_tick_count(simq_kernel):
    """After 20 ticks, QualityHub.tick_count must be > 0."""
    for _ in range(TICKS):
        simq_kernel.tick_once()

    # Allow drain worker to process remaining queue items
    time.sleep(0.2)

    hub = simq_kernel._quality_hub
    assert hub is not None, (
        "Kernel._quality_hub must not be None when QUALITY_SCORING_DISABLED is unset"
    )
    report = hub.get_quality_report()
    assert report.tick_count > 0, (
        f"Expected tick_count > 0 after {TICKS} ticks; got {report.tick_count}. "
        "SimQ is not receiving events — check quality_fn wiring in Kernel.__init__."
    )


def test_simq_wiring_agency_pillar_receives_events(simq_kernel):
    """After 20 ticks, AGENCY pillar event_count must be > 0."""
    for _ in range(TICKS):
        simq_kernel.tick_once()

    time.sleep(0.2)

    hub = simq_kernel._quality_hub
    assert hub is not None
    report = hub.get_quality_report()
    agency = report.pillars.get("AGENCY")
    assert agency is not None, "AGENCY pillar missing from quality report"
    assert agency.event_count > 0, (
        f"AGENCY pillar event_count=0 after {TICKS} ticks. "
        "action_executed / route_selected events are not reaching the hub."
    )


def test_simq_disabled_produces_no_hub(tmp_path, monkeypatch):
    """When QUALITY_SCORING_DISABLED=1, Kernel._quality_hub must be None."""
    monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)

    spec = _build_simq_test_spec()
    state, _ = WorldCompiler.compile(spec, seed=SEED)
    rng = DeterministicRNG(SEED)
    profile = RuntimeProfile(
        name="simq-disabled-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=100.0,
    )
    kernel = Kernel(profile, state, rng, run_id="simq-disabled-test-run")
    try:
        for _ in range(5):
            kernel.tick_once()
        assert kernel._quality_hub is None, (
            "Kernel._quality_hub must be None when QUALITY_SCORING_DISABLED=1"
        )
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)


def test_only_one_drain_worker_exists_during_run(simq_kernel):
    """Exactly one QueueDrainWorker must exist on EventRecorder's private queue.
    
    Verifies G3 fix: InProcessQualityFeed no longer creates a competing worker.
    """
    import threading

    # Count threads named "observability-drain-worker" before and during run
    def _drain_worker_count() -> int:
        return sum(
            1 for t in threading.enumerate()
            if t.name == "observability-drain-worker"
        )

    for _ in range(5):
        simq_kernel.tick_once()

    count = _drain_worker_count()
    assert count == 1, (
        f"Expected exactly 1 observability-drain-worker thread, found {count}. "
        "InProcessQualityFeed may still be creating a competing QueueDrainWorker."
    )
```

**Scoped run:**
```
pytest tests/simulation_quality/test_kernel_simq_integration.py -v
```

---

## Scoped Pytest Commands

### Fast (unit only, no slow marker):
```bash
pytest tests/observability/ tests/simulation_quality/ -x -m "not slow"
```

### With new unit tests only:
```bash
pytest tests/observability/test_event_recorder_quality_fn.py \
       tests/simulation_quality/test_feed.py \
       -v
```

### Full integration (includes sandbox_world kernel run):
```bash
pytest tests/simulation_quality/test_kernel_simq_integration.py -v
```

### Full regression sweep for this ticket:
```bash
pytest tests/observability/ tests/simulation_quality/ \
       tests/certification/test_event_observability_parity.py \
       -x -m "not slow" -v
```

### Acceptance criteria verification (all 6 criteria):
```bash
# AC1, AC2, AC3, AC4 together:
pytest tests/simulation_quality/test_kernel_simq_integration.py \
       tests/observability/ \
       tests/simulation_quality/ \
       -x -m "not slow" -v

# AC4 alone:
pytest tests/observability/ -x -v

# AC5 alone:
pytest tests/simulation_quality/ -x -m "not slow" -v
```

---

## Anti-Drift Guards

### AG-1 — State hash parity must not regress

`tests/certification/test_event_observability_parity.py::test_state_hash_parity_across_observability_modes`
must pass. Any change to how `EventRecorder` or `QueueDrainWorker` processes events
must not alter the authoritative state hash. The `quality_fn` callback is read-only
— it must never write to `AuthoritativeState`. If this test fails after the change,
the fix has contaminated the authoritative pipeline.

### AG-2 — quality_fn exception guard in QueueDrainWorker must not be removed

`test_event_recorder_quality_fn_exception_does_not_crash_worker` (new test above)
guards this. If `queue.py:144-149` exception handling is ever loosened, this test
catches it.

### AG-3 — InProcessQualityFeed must not regain a _worker

`test_inprocess_feed_has_no_worker_attribute_after_refactor` (new test above) uses
`hasattr` to explicitly assert no `_worker` exists. If a future refactor accidentally
re-introduces a competing worker, this test fails.

### AG-4 — build_feed_from_env() return contract must not change

`tests/simulation_quality/test_feed.py::test_build_feed_returns_inprocess_by_default`
and `test_build_feed_returns_none_when_disabled` guard the public API. The refactored
`InProcessQualityFeed` must still be returned by `build_feed_from_env()` in the
default case — only its `start()` behavior changes internally.

### AG-5 — Observability mode OFF must produce no hub, no scorers, no cost

`test_simq_disabled_produces_no_hub` (integration test above) covers
`QUALITY_SCORING_DISABLED=1`. A complementary check should be added for
`ObservabilityMode.OFF` — when observability is fully off, the entire SimQ block
is skipped. This can be added as a parametrized variant of the disabled test.

### AG-6 — Exactly one drain worker thread during run

`test_only_one_drain_worker_exists_during_run` (integration test above) guards
the G3 fix. If `InProcessQualityFeed` ever re-acquires a worker thread, the
thread-count assertion catches it immediately.
