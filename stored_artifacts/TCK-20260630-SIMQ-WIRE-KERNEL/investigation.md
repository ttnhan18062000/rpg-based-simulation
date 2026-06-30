---
ticket_id: TCK-20260630-SIMQ-WIRE-KERNEL
phase: investigation
date: 2026-06-30
---

# Investigation: Wire SimQ quality_fn into Kernel Event Pipeline

## Current Behavior (file:line refs for each gap)

### Gap G1 — quality_fn slot exists but is never populated at kernel init

`QueueDrainWorker.__init__` at `src/observability/queue.py:92-104` accepts a
`quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None` parameter
and calls it inside `_run()` at line 144 with a try/except guard identical to the
`file_write_fn` and `stream_publish_fn` guards.

`EventRecorder.__init__` at `src/observability/event_recorder.py:99-103` constructs
its `QueueDrainWorker` passing only `file_write_fn` and `stream_publish_fn` — the
`quality_fn` argument is absent:

```python
# event_recorder.py:99-103  (current — missing quality_fn)
self._worker = QueueDrainWorker(
    queue=self.queue,
    file_write_fn=self._write_envelope_to_file,
    stream_publish_fn=self._publish_envelope_to_stream
)
```

`Kernel.__init__` at `src/engine/kernel.py:226-230` constructs `EventRecorder` with
no `quality_fn` parameter (parameter does not yet exist on EventRecorder):

```python
# kernel.py:226-230  (current — no quality_fn path)
self._event_recorder = EventRecorder(
    run_dir=run_dir_str,
    max_events=5000,
    enabled=(obs_mode != ObservabilityMode.OFF)
)
```

Result: `hub.on_envelope()` is never in the drain worker's call chain. Every envelope
reaches `file_write_fn` / `stream_publish_fn` and is then discarded with no quality
scoring. `tick_count` and all pillar `event_count` values stay 0.

### Gap G3 — InProcessQualityFeed creates a competing second QueueDrainWorker

`InProcessQualityFeed.start()` at `src/simulation_quality/feed.py:39-45` creates
a brand-new `QueueDrainWorker` on the **same** global `BoundedObservabilityQueue`
singleton returned by `get_observability_queue()`:

```python
# feed.py:39-45  (current — competing consumer)
def start(self, hub: Any) -> None:
    queue = get_observability_queue()
    self._worker = QueueDrainWorker(
        queue=queue,
        quality_fn=hub.on_envelope,
    )
    self._worker.start()
```

`EventRecorder` creates its own private `BoundedObservabilityQueue` at
`event_recorder.py:98` (`self.queue = BoundedObservabilityQueue(...)`). This is a
**different queue object** from the global singleton. `EventRecorder.record()` at
line 221 pushes envelopes into `self.queue` (the private one). The global queue
accessed by `get_observability_queue()` is never written to during a simulation run.

Therefore `InProcessQualityFeed`'s worker drains a permanently-empty global queue.
No race condition actually occurs — the feed's worker simply never sees any events
because the events live in `EventRecorder.queue` (private), not
`get_observability_queue()` (global singleton). This is a more fundamental disconnect
than the race described in D20; both queues exist simultaneously but only the private
one receives events.

### Confirmed source: EventRecorder uses a private queue, not the global singleton

`event_recorder.py:98`:
```python
self.queue = BoundedObservabilityQueue(max_size=self.max_events)
```

This is allocated fresh in `EventRecorder.__init__`. The module-level `_global_queue`
at `queue.py:157` is only accessed via `get_observability_queue()` and is never
touched by `EventRecorder`. The two queue objects are independent.

---

## How the Fix Threads Through the Three Files

### Step 1 — Add `quality_fn` parameter to `EventRecorder.__init__`

File: `src/observability/event_recorder.py`

Add `quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None` to
`EventRecorder.__init__` signature. Store it and pass it to `QueueDrainWorker`:

```python
# After fix: event_recorder.py ~line 59 (new param) and ~line 99-104 (pass-through)
def __init__(
    self,
    run_dir: Optional[str] = None,
    max_events: int = 5000,
    enabled: bool = True,
    budget: SubsystemBudget | None = None,
    quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
) -> None:
    ...
    self._worker = QueueDrainWorker(
        queue=self.queue,
        file_write_fn=self._write_envelope_to_file,
        stream_publish_fn=self._publish_envelope_to_stream,
        quality_fn=quality_fn,
    )
```

The `Callable` import is already present in `event_recorder.py` (line 6 imports
`from typing import Any, Dict, List, Optional`; `Callable` must be added).
`ObservabilityEventEnvelope` import is already done at line 96 inside `__init__`
via a local `from` import — the type hint in the signature will need it at module
level or kept as a string annotation.

### Step 2 — Add `_quality_hub` and `_quality_feed` slots; wire in `Kernel.__init__`

File: `src/engine/kernel.py`

Add `"_quality_hub"` and `"_quality_feed"` to `__slots__` at line 40-50.

In `Kernel.__init__`, insert the hub/feed construction **before** `EventRecorder` is
constructed (currently line 226). Required construction order:

```python
# kernel.py — insert after obs_mode resolved (~line 217), before EventRecorder (~line 226)

from src.simulation_quality.feed import build_feed_from_env
from src.simulation_quality.quality_hub import QualityHub

self._quality_hub = None
self._quality_feed = None
_quality_fn = None

if obs_mode != ObservabilityMode.OFF:
    _feed = build_feed_from_env()
    if _feed is not None:
        from src.simulation_quality.scorers.agency import AgencyScorer
        # ... all 10 scorers ...
        from src.simulation_quality.weights import ScoringWeights
        from src.simulation_quality.persistence import QualityPersistence
        _weights = ScoringWeights.load()
        _scorers = [AgencyScorer(_weights), ...]
        _persistence = QualityPersistence(run_dir_str or "data/runs")
        self._quality_hub = QualityHub(_scorers, _weights, _persistence, run_id=self._run_id)
        self._quality_feed = _feed
        _quality_fn = self._quality_hub.on_envelope

self._event_recorder = EventRecorder(
    run_dir=run_dir_str,
    max_events=5000,
    enabled=(obs_mode != ObservabilityMode.OFF),
    quality_fn=_quality_fn,
)
```

The `_quality_feed` variable is retained as a lifecycle handle so `shutdown()` can
call `self._quality_feed.stop()` and `self._quality_hub.get_quality_report()` for
final persistence. Null-guard all access (`if self._quality_hub`).

**Note on scorer construction:** The ticket scope says to build all 10 scorers. The
existing test fixture in `test_quality_hub_integration.py` imports scorers individually
(`AgencyScorer`, `CombatScorer`). The implementation should import all scorers from
`src.simulation_quality.scorers.*` — check existing scorer module list at
`src/simulation_quality/scorers/` to confirm the 10 class names.

### Step 3 — Refactor `InProcessQualityFeed` to lifecycle-only

File: `src/simulation_quality/feed.py`

`InProcessQualityFeed` must no longer create a `QueueDrainWorker`. Its `start(hub)`
method becomes a lifecycle registrar only — it stores the hub reference for
`health()` and `stop()` reporting. The `QueueDrainWorker` import at line 8 can be
removed from this file if no longer used.

```python
# After fix: feed.py InProcessQualityFeed
class InProcessQualityFeed(QualityFeedAdapter):
    """Lifecycle manager for in-process quality scoring via EventRecorder's worker."""

    def __init__(self) -> None:
        self._hub: Optional[Any] = None

    def start(self, hub: Any) -> None:
        # quality_fn is wired into EventRecorder's QueueDrainWorker at kernel init.
        # This method only registers the hub reference for health/stop reporting.
        self._hub = hub

    def stop(self) -> None:
        self._hub = None

    def health(self) -> dict[str, Any]:
        if self._hub is None:
            return {"status": "STOPPED", "dropped_count": 0, "mode": "inprocess"}
        return {"status": "HEALTHY", "dropped_count": 0, "mode": "inprocess"}
```

The `BrokerQualityFeed` class is untouched — it creates its own Redis consumer thread
on a separate stream and is not affected by this change.

`build_feed_from_env()` return signature is unchanged.

---

## Mechanics / Architecture Constraints

### No quality layer importing engine

`src/simulation_quality/` must not import from `src/engine/`. The current structure
already respects this: `QualityHub` and the scorers import only from
`src/observability/events.py` and `src/simulation_quality/`. The fix preserves this:
`Kernel` imports from `src/simulation_quality/`, not the reverse.

### quality_fn is a Callable, not a hub reference

`EventRecorder` and `QueueDrainWorker` accept a `Callable`, not a `QualityHub`
object. This keeps the observability layer decoupled from the quality layer — it
treats quality scoring as just another drain callback, identical in structure to
`file_write_fn` and `stream_publish_fn`.

### EventRecorder's private queue is the authoritative event sink

`EventRecorder.queue` (private `BoundedObservabilityQueue`, created at
`event_recorder.py:98`) is the only queue that receives simulation envelopes
during a run. The global queue singleton (`get_observability_queue()` in `queue.py`)
is a separate object that currently receives no events in the kernel path.
`InProcessQualityFeed` must not reference the global queue at all after this fix.

### Optional path must be strictly zero-overhead when disabled

`QUALITY_SCORING_DISABLED=1` → `build_feed_from_env()` returns `None` → `_quality_fn`
stays `None` → `QueueDrainWorker` skips the `if self.quality_fn:` branch at
`queue.py:144`. No hub is constructed, no scorers loaded. Simulation behavior is
bit-identical to today.

### Kernel `__slots__` must be updated

`Kernel` uses `__slots__` (line 40). Adding `_quality_hub` and `_quality_feed`
without declaring them in `__slots__` will raise `AttributeError` at runtime.

### Shutdown path

`Kernel.shutdown()` at line 904 must be extended to call
`self._quality_feed.stop()` (if not None) and optionally write the final quality
report via `self._quality_hub.get_quality_report()`. The `QualityPersistence` object
already handles write-through on every `on_envelope()` call, so the shutdown write
is a best-effort final flush only.

---

## Parity Ledger Overlap

### `infrastructure.yaml` entries directly affected by this ticket

| ID | Text (summary) | Current status | Action required |
|---|---|---|---|
| INFRA-232 | `QueueDrainWorker.quality_fn` is called per-envelope; safe when `None` | `verified` | No change — behavior already correct, now exercised by kernel path |
| INFRA-233 | `QUALITY_SCORING_DISABLED=1` → `build_feed_from_env()` returns `None` | `verified` | No change — disabled path unchanged |
| INFRA-236 | `QualityHub.on_envelope()` routes to scorers; disabled short-circuits | `verified` | No change — hub behavior unchanged |

### New parity ledger entry required

A new entry `INFRA-249` (or next available) must be added to `infrastructure.yaml`
for the kernel wiring itself:

```yaml
- id: INFRA-249
  text: >
    Kernel.__init__ constructs QualityHub and passes hub.on_envelope as quality_fn
    to EventRecorder's QueueDrainWorker when QUALITY_SCORING_DISABLED is unset.
    InProcessQualityFeed.start() is a lifecycle-only registrar — it does not create
    a second QueueDrainWorker. (TCK-20260630-SIMQ-WIRE-KERNEL)
  status: verified    # after implementation
  priority: P1
  test_path: tests/simulation_quality/test_kernel_simq_integration.py
```

### `SIMQ-CALIBRATED-001` entry (line 3079+)

This entry covers the full event translation and emission layer as `verified`. It is
unaffected by this ticket — the translation mappings in `quality_hub.py` and the
emission hooks in `event_extractor.py` are not changed. The entry's `status` stays
`verified`.

---

## Risks and Open Questions

### R1 — Scorer construction cost at kernel init

Building all 10 scorers and loading `ScoringWeights` from YAML adds startup work to
`Kernel.__init__`. On a CLASS_A/B hardware profile this is negligible (one YAML
read, 10 small object allocations). On a CLASS_C profile with tight startup budgets
it should be profiled. Mitigation: the entire block is inside `if obs_mode !=
ObservabilityMode.OFF`, so it is skipped in pure headless/OFF mode.

### R2 — `run_dir_str` may be None when artifact_repo is absent

`QualityPersistence` is constructed with `run_dir_str or "data/runs"`. If `run_dir_str`
is `None` (no artifact repo, no replay dir), persistence writes fall back to
`data/runs/`. This matches the existing `EventRecorder` fallback. Confirm
`QualityPersistence.__init__` handles a bare base dir correctly (creates subdirs).

### R3 — `InProcessQualityFeed` test `test_inprocess_feed_start_stop_no_thread_leak` will break

This test at `tests/simulation_quality/test_feed.py:55-62` currently asserts
`feed._worker is not None` and `feed._worker.is_alive()` after `start()`. After
the refactor `_worker` is removed from `InProcessQualityFeed` entirely. This test
**must be updated** as part of this ticket — the new assertion should confirm that
no worker thread is started (verify via `threading.active_count()` delta or
simply that `feed._hub is not None`).

### R4 — `test_inprocess_feed_health_reports_status` assumes worker-based health

`tests/simulation_quality/test_feed.py:65-74` reads `feed.health()["status"]` which
currently comes from `self._worker.health_status`. After refactor the status becomes
a fixed string. This test must be updated to assert `status == "HEALTHY"` when the
hub is registered.

### R5 — `INFRA-232` parity test path references a non-existent test

`infrastructure.yaml:INFRA-232.test_path` references
`tests/simulation_quality/test_feed.py::test_inprocess_feed_quality_fn_called`
which does not currently exist in `test_feed.py`. This is a pre-existing parity
ledger gap — the test path should be corrected when the new tests are added.

### Open Question OQ-1 — Should Kernel expose `_quality_hub` as a public property?

The server-side wiring ticket (TCK-20260630-SIMQ-WIRE-SERVER) calls
`set_quality_hub(hub)` from `src/api/dependencies.py`. If the kernel constructs the
hub, the server needs to retrieve it post-construction. Two options:
- Kernel exposes a `quality_hub` property (read-only)
- Kernel passes `hub` to the server manager directly after construction

This decision is out of scope for this ticket (G2 is TCK-20260630-SIMQ-WIRE-SERVER)
but the implementation should ensure `self._quality_hub` is accessible for that
ticket's use.

---

## Anti-Drift Hazards

### H1 — quality_fn exception guard must not leak to simulation loop

`QueueDrainWorker._run()` at `queue.py:144-149` already wraps `quality_fn(env)` in
`try/except Exception`. If this guard is ever removed or narrowed, a scorer exception
will propagate into the drain thread and crash the background worker, silently
stopping all quality scoring with no engine-visible error. The test suite must assert
that a scorer exception does not propagate (existing `test_scorer_exception_does_not_propagate`
in `test_quality_hub_integration.py` covers the hub level; the drain-worker level
guard is covered by INFRA-232).

### H2 — EventRecorder `shutdown()` does not call quality_fn on final flush

`EventRecorder.shutdown()` at line 299-320 stops the worker then does a final
synchronous flush of remaining queue items calling only `_write_envelope_to_file`
and `_publish_envelope_to_stream`. The `quality_fn` is **not called** on the final
flush (lines 308-310). This means events queued between the last drain cycle and
shutdown are scored by file/stream but not by SimQ. This is an acceptable design
trade-off for the current ticket (the flush is a best-effort tail) but should be
noted for a future improvement. The integration test should use `time.sleep` or
flush assertions to avoid flakiness from this gap.

### H3 — Disabling quality must not silently downgrade to partial scoring

If `build_feed_from_env()` returns `None` (disabled) but `_quality_fn` is
accidentally set to a non-None value, or vice versa, the system enters a
partially-wired state. The implementation must use a single `_feed is not None`
gate to control both hub construction and `_quality_fn` assignment.

### H4 — Two `BoundedObservabilityQueue` objects must not merge

The global queue (`get_observability_queue()`) and the `EventRecorder`'s private
queue must remain separate. Nothing in this ticket should wire the private queue
into the global singleton or vice versa. `InProcessQualityFeed` after refactor must
not call `get_observability_queue()` at all.

### H5 — Kernel `__slots__` incompleteness causes silent AttributeError

If `_quality_hub` or `_quality_feed` are assigned in `__init__` without being in
`__slots__`, Python raises `AttributeError: '_quality_hub' object has no attribute`
at the assignment line. This is caught immediately in tests but could be missed if
tests don't exercise the enabled path. The slots update must be verified explicitly.
