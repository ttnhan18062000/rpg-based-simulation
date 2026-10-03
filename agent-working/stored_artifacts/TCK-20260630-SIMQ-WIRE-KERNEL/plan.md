---
ticket_id: TCK-20260630-SIMQ-WIRE-KERNEL
phase: plan
date: 2026-06-30
---

# Plan: Wire SimQ quality_fn into Kernel Event Pipeline

## Context

Root cause (from investigation): `EventRecorder.__init__` (event_recorder.py:99-103)
constructs `QueueDrainWorker` without `quality_fn`. `InProcessQualityFeed.start()`
creates a second `QueueDrainWorker` on the global queue singleton — an object that
never receives any events because all events flow through `EventRecorder.queue`
(a private `BoundedObservabilityQueue`, event_recorder.py:98). Fix touches 3 source
files and updates 1 test file.

Config paths resolved from file system:
- `config/simulation_quality/scoring_weights.yaml`
- `config/simulation_quality/grade_thresholds.yaml`
- `config/simulation_quality/detection_params.yaml`
- Profile dir: `config/simulation_quality/profiles/`

`ScoringWeights.load` signature requires positional args:
`load(weights_path, grade_path, detection_path, profile="default")`

`QualityPersistence.__init__` takes a bare `run_dir: str` — no None-safety built in.
OQ-3 is resolved by passing `run_dir_str or "data/runs"` at the call site in Kernel.

INFRA-249 in `docs/parity_ledger/infrastructure.yaml` (line 3053) already exists but
describes the server-side write path, not the kernel wiring. It must be updated to
reflect the kernel wiring behavior that this ticket adds.

`src/simulation_quality/scorers/__init__.py` exports only `PillarScorer` — no
`ALL_SCORERS` list. Plan adds one (Step 1).

10 scorer classes (one per file):
- `agency.py` → `AgencyScorer`
- `cognition.py` → `CognitionScorer`
- `combat.py` → `CombatScorer`
- `economy.py` → `EconomyScorer`
- `faction.py` → `FactionScorer`
- `information.py` → `InformationScorer`
- `narrative.py` → `NarrativeScorer`
- `progression.py` → `ProgressionScorer`
- `social.py` → `SocialScorer`
- `world_dynamics.py` → `WorldDynamicsScorer`

---

## Ordered Steps

---

### Step 1 — Add `ALL_SCORERS` factory to `scorers/__init__.py`

**Purpose:** Provide a single authoritative import point for all scorer instances so
Kernel (Step 3) does not hardcode 10 individual imports.

**File:** `src/simulation_quality/scorers/__init__.py`

**Current content (lines 1-3):**
```python
from src.simulation_quality.scorers.base import PillarScorer

__all__ = ["PillarScorer"]
```

**Change:** Append an `ALL_SCORERS` factory function that constructs all 10 scorer
instances given a `ScoringWeights` object. Use a function (not a module-level list)
to avoid instantiation at import time.

```python
from src.simulation_quality.scorers.base import PillarScorer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.simulation_quality.weights import ScoringWeights

__all__ = ["PillarScorer", "build_all_scorers"]


def build_all_scorers(weights: "ScoringWeights") -> list[PillarScorer]:
    """Construct one instance of every PillarScorer. Import lazily to avoid cycles."""
    from src.simulation_quality.scorers.agency import AgencyScorer
    from src.simulation_quality.scorers.cognition import CognitionScorer
    from src.simulation_quality.scorers.combat import CombatScorer
    from src.simulation_quality.scorers.economy import EconomyScorer
    from src.simulation_quality.scorers.faction import FactionScorer
    from src.simulation_quality.scorers.information import InformationScorer
    from src.simulation_quality.scorers.narrative import NarrativeScorer
    from src.simulation_quality.scorers.progression import ProgressionScorer
    from src.simulation_quality.scorers.social import SocialScorer
    from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer

    return [
        AgencyScorer(weights),
        CognitionScorer(weights),
        CombatScorer(weights),
        EconomyScorer(weights),
        FactionScorer(weights),
        InformationScorer(weights),
        NarrativeScorer(weights),
        ProgressionScorer(weights),
        SocialScorer(weights),
        WorldDynamicsScorer(weights),
    ]
```

**What NOT to touch:**
- `base.py` — unchanged
- Any individual scorer file — unchanged
- Existing `__all__` entry for `PillarScorer` — preserved

**Dependencies:** None. This step is standalone.

---

### Step 2 — Add `quality_fn` parameter to `EventRecorder.__init__`

**File:** `src/observability/event_recorder.py`

**Gap:** G1. `QueueDrainWorker` (queue.py:97) already has a `quality_fn` slot;
`EventRecorder` never populates it.

**Change A — Add `Callable` to typing import (line 6):**

Current:
```python
from typing import Any, Dict, List, Optional
```
After:
```python
from typing import Any, Callable, Dict, List, Optional
```

**Change B — Add `quality_fn` parameter to `__init__` signature (line 58-64):**

Current signature ends at:
```python
    def __init__(
        self,
        run_dir: Optional[str] = None,
        max_events: int = 5000,
        enabled: bool = True,
        budget: SubsystemBudget | None = None,
    ) -> None:
```

After:
```python
    def __init__(
        self,
        run_dir: Optional[str] = None,
        max_events: int = 5000,
        enabled: bool = True,
        budget: SubsystemBudget | None = None,
        quality_fn: Optional[Callable] = None,
    ) -> None:
```

Note: The type annotation for `quality_fn` uses `Optional[Callable]` (bare, no
subscript) to avoid the `ObservabilityEventEnvelope` forward-reference complexity
at module level. The slot in `QueueDrainWorker` is identically typed.

**Change C — Store and pass to `QueueDrainWorker` (lines 99-103):**

Current:
```python
        self._worker = QueueDrainWorker(
            queue=self.queue,
            file_write_fn=self._write_envelope_to_file,
            stream_publish_fn=self._publish_envelope_to_stream
        )
```

After:
```python
        self._quality_fn = quality_fn
        self._worker = QueueDrainWorker(
            queue=self.queue,
            file_write_fn=self._write_envelope_to_file,
            stream_publish_fn=self._publish_envelope_to_stream,
            quality_fn=quality_fn,
        )
```

**What NOT to touch:**
- `_write_envelope_to_file`, `_publish_envelope_to_stream`, `record()`, `shutdown()` — all unchanged
- `ObservabilityController`, `ObservabilityMode` — unchanged
- The `QueueDrainWorker._run()` quality_fn guard at queue.py:144-149 — already correct, not touched

**Dependencies:** None. This step is standalone (queue.py already supports quality_fn).

---

### Step 3 — Wire QualityHub into `Kernel.__init__`

**File:** `src/engine/kernel.py`

**Gap:** G1 (kernel side). Kernel builds `EventRecorder` at line 226 without the hub.

#### 3a — Add `_quality_hub` and `_quality_feed` to `__slots__` (lines 40-50)

Current `__slots__` tuple last line:
```python
        "_workers_started", "_last_shutdown_report",
```

After (append two slots to the same tuple):
```python
        "_workers_started", "_last_shutdown_report",
        "_quality_hub", "_quality_feed",
```

**Why critical:** Kernel uses `__slots__`. Assigning `self._quality_hub` without
declaring it raises `AttributeError` at runtime (investigation H5).

#### 3b — Insert hub construction block before `EventRecorder` (between lines 224 and 226)

Insert after `run_dir_str` is resolved (line 224) and before `EventRecorder` is
constructed (line 226). Full insertion block:

```python
        # --- SimQ hub construction (TCK-20260630-SIMQ-WIRE-KERNEL) ---
        import os as _os
        self._quality_hub = None
        self._quality_feed = None
        _quality_fn = None

        _simq_enabled = obs_mode != ObservabilityMode.OFF
        if _simq_enabled:
            try:
                from src.simulation_quality.feed import build_feed_from_env
                _feed = build_feed_from_env()
                if _feed is not None:
                    from src.simulation_quality.weights import ScoringWeights
                    from src.simulation_quality.persistence import QualityPersistence
                    from src.simulation_quality.quality_hub import QualityHub
                    from src.simulation_quality.scorers import build_all_scorers

                    _base = _os.path.abspath(".")
                    _weights_path = _os.path.join(_base, "config/simulation_quality/scoring_weights.yaml")
                    _grade_path = _os.path.join(_base, "config/simulation_quality/grade_thresholds.yaml")
                    _detection_path = _os.path.join(_base, "config/simulation_quality/detection_params.yaml")

                    _weights = ScoringWeights.load(
                        weights_path=_weights_path,
                        grade_path=_grade_path,
                        detection_path=_detection_path,
                        profile="default",
                    )
                    _persistence_dir = run_dir_str or "data/runs"
                    _persistence = QualityPersistence(_persistence_dir)
                    _scorers = build_all_scorers(_weights)
                    self._quality_hub = QualityHub(
                        scorers=_scorers,
                        weights=_weights,
                        persistence=_persistence,
                        run_id=self._run_id,
                    )
                    self._quality_feed = _feed
                    _quality_fn = self._quality_hub.on_envelope
                    self._quality_feed.start(self._quality_hub)
            except Exception as _simq_err:
                logger.warning(
                    "SimQ hub construction failed (non-fatal, quality scoring disabled): %s",
                    _simq_err,
                )
                self._quality_hub = None
                self._quality_feed = None
                _quality_fn = None
        # --- end SimQ hub construction ---
```

#### 3c — Pass `quality_fn` to `EventRecorder` (line 226-230)

Current:
```python
        self._event_recorder = EventRecorder(
            run_dir=run_dir_str,
            max_events=5000,
            enabled=(obs_mode != ObservabilityMode.OFF)
        )
```

After:
```python
        self._event_recorder = EventRecorder(
            run_dir=run_dir_str,
            max_events=5000,
            enabled=(obs_mode != ObservabilityMode.OFF),
            quality_fn=_quality_fn,
        )
```

#### 3d — Add `quality_hub` read-only property (OQ-1)

Add after `__slots__` / `__init__` block, before `validate()`. This allows
TCK-20260630-SIMQ-WIRE-SERVER to retrieve the hub post-construction without
accessing a private attribute directly:

```python
    @property
    def quality_hub(self):
        """Read-only access to the QualityHub instance (None if SimQ is disabled)."""
        return self._quality_hub
```

#### 3e — Extend `shutdown()` to stop quality feed and write final report

In `shutdown()` at line 904, after `_event_recorder.shutdown()` (line 913), insert:

```python
        if hasattr(self, "_quality_feed") and self._quality_feed is not None:
            try:
                self._quality_feed.stop()
            except Exception:
                logger.warning("InProcessQualityFeed.stop() failed during shutdown (non-fatal)")

        if hasattr(self, "_quality_hub") and self._quality_hub is not None:
            try:
                report = self._quality_hub.get_quality_report()
                if hasattr(self._quality_hub, "_persistence") and self._quality_hub._persistence:
                    self._quality_hub._persistence.write_report(report)
                    self._quality_hub._persistence.shutdown()
            except Exception:
                logger.warning("QualityHub final report write failed during shutdown (non-fatal)")
```

**What NOT to touch:**
- `validate()` — unchanged
- All other Kernel phases/methods — unchanged
- `ObservabilityMode` enum — already imported at line 116, no re-import needed
- `import os` — already present at line 222 (`import os`) inside the `if self._artifact_repo` block; the new block uses `import os as _os` to be self-contained within the conditional scope

**Dependencies:** Requires Step 1 (`build_all_scorers`) and Step 2 (`quality_fn` param on `EventRecorder`).

---

### Step 4 — Refactor `InProcessQualityFeed` to lifecycle-only

**File:** `src/simulation_quality/feed.py`

**Gap:** G3. `InProcessQualityFeed.start()` currently creates a competing
`QueueDrainWorker` on the global queue — an object that never receives events
(investigation confirmed this is a permanent disconnect, not a race).

**Change A — Remove `QueueDrainWorker` and `get_observability_queue` from import (line 8):**

Current:
```python
from src.observability.queue import QueueDrainWorker, get_observability_queue
```

After:
```python
# QueueDrainWorker and get_observability_queue intentionally removed:
# InProcessQualityFeed is now a lifecycle-only registrar; quality_fn is wired
# into EventRecorder's worker at Kernel.__init__ (TCK-20260630-SIMQ-WIRE-KERNEL).
```

If `QueueDrainWorker` or `get_observability_queue` are needed elsewhere in the
file (they are not — only `InProcessQualityFeed` used them), leave the import.
Check: `BrokerQualityFeed` does not import from `queue.py`. Safe to remove entirely.

**Change B — Rewrite `InProcessQualityFeed` class body:**

Current (lines 33-60):
```python
class InProcessQualityFeed(QualityFeedAdapter):
    """Delivers envelopes to QualityHub via a dedicated QueueDrainWorker on the global queue."""

    def __init__(self) -> None:
        self._worker: Optional[QueueDrainWorker] = None

    def start(self, hub: Any) -> None:
        queue = get_observability_queue()
        self._worker = QueueDrainWorker(
            queue=queue,
            quality_fn=hub.on_envelope,
        )
        self._worker.start()

    def stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def health(self) -> dict[str, Any]:
        if self._worker is None:
            return {"status": "STOPPED", "dropped_count": 0, "mode": "inprocess"}
        status = self._worker.health_status
        return {
            "status": status,
            "dropped_count": self._worker.failure_count,
            "mode": "inprocess",
        }
```

After:
```python
class InProcessQualityFeed(QualityFeedAdapter):
    """Lifecycle registrar for in-process quality scoring.

    quality_fn is wired into EventRecorder's QueueDrainWorker at Kernel.__init__.
    This class exists only to provide a consistent start()/stop()/health() interface
    for the lifecycle manager — it does not own a QueueDrainWorker.
    (TCK-20260630-SIMQ-WIRE-KERNEL)
    """

    def __init__(self) -> None:
        self._hub: Optional[Any] = None

    def start(self, hub: Any) -> None:
        # quality_fn already wired into EventRecorder's worker at kernel init.
        # Only store hub reference for health() and stop() reporting.
        self._hub = hub

    def stop(self) -> None:
        self._hub = None

    def health(self) -> dict[str, Any]:
        if self._hub is None:
            return {"status": "STOPPED", "dropped_count": 0, "mode": "inprocess"}
        return {"status": "HEALTHY", "dropped_count": 0, "mode": "inprocess"}
```

**Change C — Remove `threading` import (line 3) if it is only used by `InProcessQualityFeed`:**

Check: `threading` is used at line 3 (`import threading`) and line 75 in
`BrokerQualityFeed` (`self._thread: Optional[threading.Thread]`). It is also used
at line 115. Do NOT remove `threading` — it is still required by `BrokerQualityFeed`.

**What NOT to touch:**
- `BrokerQualityFeed` — entirely unchanged
- `build_feed_from_env()` — unchanged (return type and behavior identical)
- `QualityFeedAdapter` ABC — unchanged
- `QualityFeedMode` enum — unchanged

**Note on `Optional` import:** `Optional` is used in `BrokerQualityFeed`
(`self._thread: Optional[threading.Thread]`, `self._consumer: Optional[Any]`)
so the `Optional` import from `typing` must stay.

**Dependencies:** Requires Step 3 to be correct (hub already `start()`ed before
`InProcessQualityFeed.start()` is called — Step 3b calls `self._quality_feed.start(hub)`
after hub is constructed).

---

### Step 5 — Update broken pre-existing tests and add new tests

#### 5a — Update `tests/simulation_quality/test_feed.py`

Two tests assert `_worker` internals that no longer exist after Step 4:

**Test 1** — `test_inprocess_feed_start_stop_no_thread_leak` (approximately line 55-62):
Replace assertion `feed._worker is not None` and `feed._worker.is_alive()` with:
```python
import threading
threads_before = threading.active_count()
feed.start(mock_hub)
threads_after = threading.active_count()
assert threads_after == threads_before, "InProcessQualityFeed.start() must not start a thread"
assert feed._hub is mock_hub
feed.stop()
assert feed._hub is None
```

**Test 2** — `test_inprocess_feed_health_reports_status` (approximately line 65-74):
Replace worker-based health status assertion with:
```python
feed.start(mock_hub)
h = feed.health()
assert h["status"] == "HEALTHY"
assert h["mode"] == "inprocess"
feed.stop()
assert feed.health()["status"] == "STOPPED"
```

Also update `test_inprocess_feed_health_when_stopped` (approximately line 77) if
it checks `_worker` — replace with `_hub is None` check.

**Exact location:** Read `tests/simulation_quality/test_feed.py` lines 50-90 during
implementation to find the exact line numbers before editing.

#### 5b — New file: `tests/observability/test_event_recorder_quality_fn.py`

Create new file (does not exist; existing `test_event_recorder.py` may exist — check
and add to it if it does, or create new file if not). 4 tests as specified in
`test_plan.md`:
1. `test_event_recorder_passes_quality_fn_to_worker` — asserts `recorder._worker.quality_fn is mock_fn`
2. `test_event_recorder_quality_fn_none_by_default` — asserts `recorder._worker.quality_fn is None`
3. `test_event_recorder_quality_fn_called_on_drain` — end-to-end drain with 2 events
4. `test_event_recorder_quality_fn_exception_does_not_crash_worker` — exception isolation

Full test content is in `test_plan.md` §"New Tests Required / 1."

#### 5c — New file: `tests/simulation_quality/test_kernel_simq_integration.py`

Create new file. 4 tests as specified in `test_plan.md`:
1. `test_simq_wiring_produces_nonzero_tick_count` — 20 ticks → `report.tick_count > 0`
2. `test_simq_wiring_agency_pillar_receives_events` — AGENCY `event_count > 0`
3. `test_simq_disabled_produces_no_hub` — `QUALITY_SCORING_DISABLED=1` → `_quality_hub is None`
4. `test_only_one_drain_worker_exists_during_run` — thread-count check for single drain worker

Full test content is in `test_plan.md` §"New Tests Required / 3."

**Note on fixture:** `ObservabilityConfig.set_override_mode` is called in the
fixture — verify this method exists on `ObservabilityConfig` before writing the
integration test; if not, use `monkeypatch.setenv("OBSERVABILITY_MODE", "DEBUG")`
as fallback.

**What NOT to touch:**
- `tests/simulation_quality/test_quality_hub_integration.py` — no changes needed
- `tests/observability/` other files — no changes needed
- Any test for `BrokerQualityFeed`, `build_feed_from_env`, `ScoringWeights` — unchanged

**Dependencies:** Requires Steps 2, 3, 4 complete.

---

### Step 6 — Update parity ledger

**File:** `docs/parity_ledger/infrastructure.yaml`

#### 6a — Update INFRA-249 (line 3053)

INFRA-249 currently describes the **server-side** quality_report write in
`api/server.py`. After this ticket, that entry is no longer the only wiring point —
the kernel now owns hub construction and the primary event path. Update INFRA-249 to
cover kernel wiring (the more fundamental behavior), and ensure it points to the new
integration test.

**Current INFRA-249 text (line 3053-3064):**
```yaml
- id: INFRA-249
  text: "quality_report.json written at server shutdown in api/server.py lifespan
    teardown, immediately before manager.stop(). Uses get_quality_hub()+get_quality_persistence()
    injected via src/api/dependencies.py. Failure is WARNING-logged only (never crashes shutdown)."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/api/server.py (lifespan teardown, lines ~44-52)
  proof_type: null
  test_path: tests/simulation_quality/test_api_routes.py
  divergence_note: null
  support_boundary: null
```

**After (replace entire entry):**
```yaml
- id: INFRA-249
  text: >
    Kernel.__init__ constructs QualityHub and passes hub.on_envelope as quality_fn
    to EventRecorder's QueueDrainWorker when obs_mode != OFF and
    QUALITY_SCORING_DISABLED is unset. InProcessQualityFeed.start() is a
    lifecycle-only registrar — it does not create a second QueueDrainWorker.
    quality_report.json written at Kernel.shutdown() via QualityPersistence.write_report().
    (TCK-20260630-SIMQ-WIRE-KERNEL)
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/engine/kernel.py (SimQ hub construction block in __init__) +
    src/simulation_quality/feed.py::InProcessQualityFeed (lifecycle-only after refactor)
  proof_type: null
  test_path: tests/simulation_quality/test_kernel_simq_integration.py::test_simq_wiring_produces_nonzero_tick_count
  divergence_note: null
  support_boundary: null
```

#### 6b — Fix INFRA-232 `test_path` (line 2828)

Current `test_path` references `test_inprocess_feed_quality_fn_called` which does
not exist (investigation R5). After Step 5b creates
`test_event_recorder_quality_fn.py`, update INFRA-232:

Current:
```yaml
  test_path: tests/simulation_quality/test_feed.py::test_inprocess_feed_start_stop,test_inprocess_feed_quality_fn_called
```

After:
```yaml
  test_path: tests/observability/test_event_recorder_quality_fn.py::test_event_recorder_quality_fn_called_on_drain
```

**What NOT to touch:**
- INFRA-233, INFRA-234, INFRA-235, INFRA-236, INFRA-250, SIMQ-CALIBRATED-001 — unchanged
- Server-side API wiring (TCK-20260630-SIMQ-WIRE-SERVER) will add its own ledger entry

**Dependencies:** Requires Steps 2, 4, 5 complete (test files must exist for test_path
to be valid).

---

## Scope Guards

The following are explicitly out of scope and must not be touched:

| Area | Why |
|---|---|
| `src/api/` routes/server/dependencies | TCK-20260630-SIMQ-WIRE-SERVER |
| `BrokerQualityFeed` | Not involved in G1/G3 |
| `src/observability/queue.py` | Already correct; `quality_fn` slot exists |
| Grade thresholds / calibration | TCK-20260630-SIMQ-RECALIBRATE |
| Engine feedback (quality → decisions) | Future work |
| `src/simulation_quality/quality_hub.py` | No changes needed |
| Individual scorer files | No changes needed |
| `QueueDrainWorker._run()` exception guards | Already correct |

---

## Dependency Graph

```
Step 1 (scorers/__init__.py)  ←── no deps
Step 2 (event_recorder.py)    ←── no deps
Step 3 (kernel.py)            ←── Step 1, Step 2
Step 4 (feed.py)              ←── Step 3 (hub constructed before feed.start())
Step 5 (tests)                ←── Steps 2, 3, 4
Step 6 (parity ledger)        ←── Step 5 (test paths must exist)
```

Steps 1 and 2 can be done in parallel. Steps 3 and 4 must follow 1+2.
Step 5 must follow 3+4. Step 6 must follow 5.

---

## Risk Notes

| Risk | Mitigation |
|---|---|
| R2: `run_dir_str` may be None | Resolved by `run_dir_str or "data/runs"` in Step 3b |
| R3/R4: pre-existing feed tests break | Covered by Step 5a updates |
| H5: `__slots__` incomplete | Step 3a explicitly declares both new slots |
| H2: final flush does not call quality_fn | Noted; acceptable trade-off for tail events |
| Config files absent in CI | Step 3b wraps entire block in try/except; hub stays None gracefully |
| `ObservabilityConfig.set_override_mode` may not exist | Step 5c notes fallback to monkeypatch.setenv |
