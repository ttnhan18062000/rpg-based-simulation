---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E1-FOUNDATION
date: 2026-06-29
tags: [simulation-quality, scoring, foundation, investigation]
---

# Investigation — TCK-20260628-SIMQ-E1-FOUNDATION
# Core Models & Data Layer for Simulation Quality Scoring

**Contract source:** `docs/simulation_quality/quality_scoring_contract.md`
**Date:** 2026-06-29

---

## 1. Current Behavior (What Exists / What Doesn't)

### What exists

| Component | Location | Status |
|---|---|---|
| `ObservabilityEventEnvelope` | `src/observability/events.py` | Exists — frozen dataclass; is the input type for QualityHub |
| `BoundedObservabilityQueue` | `src/observability/queue.py` | Exists — `drain()`, `try_push()`, thread-safe |
| `QueueDrainWorker` | `src/observability/queue.py` | Exists — calls `file_write_fn` and `stream_publish_fn` per envelope; **no quality callback slot** |
| `EventRecorder` | `src/observability/event_recorder.py` | Exists — reference pattern for non-blocking file writes (file opened in `__init__`, written in `_write_envelope_to_file`, closed in `shutdown()`) |
| `RedisStreamConsumer` | `src/observability/stream/consumer.py` | Exists (M36) — usable by `BrokerQualityFeed` without modification |
| `config/observability/` | `config/observability/` | Exists — empty directory; shows the config layout pattern |
| Pydantic | `requirements.txt` | `pydantic==2.12.5`, `pydantic_core==2.41.5` — V2 API must be used |
| Test thread guard | `tests/conftest.py` | Session-scoped `QueueDrainWorker` thread leak detector — all new tests creating workers must call `shutdown()` |

### What does not exist (must be created by this ticket)

| Component | Path | Purpose |
|---|---|---|
| `src/simulation_quality/__init__.py` | — | New module package |
| `src/simulation_quality/pillars.py` | — | `PillarId` enum, `PILLAR_METADATA`, `GRADE_THRESHOLDS` constants |
| `src/simulation_quality/models.py` | — | `ScoreRecord`, `ScoringContext`, `QualityProfile` dataclasses |
| `src/simulation_quality/accumulator.py` | — | `PillarAccumulator` (thread-safe, dedup, window, worst_events) |
| `src/simulation_quality/weights.py` | — | `ScoringWeights` Pydantic v2 BaseModel |
| `src/simulation_quality/report.py` | — | `QualityReport.build()` |
| `src/simulation_quality/persistence.py` | — | `QualityPersistence` (non-blocking JSONL writer) |
| `src/simulation_quality/feed.py` | — | `QualityFeedAdapter` ABC, `InProcessQualityFeed`, `BrokerQualityFeed` |
| `src/simulation_quality/factory.py` | — | `build_feed_from_env()` factory |
| `config/simulation_quality/scoring_weights.yaml` | — | Per-pillar delta magnitudes |
| `config/simulation_quality/grade_thresholds.yaml` | — | S/A/B/C/D/F boundary values |
| `config/simulation_quality/detection_params.yaml` | — | Loop threshold (0.70), window size (200), MAX_WORST_EVENTS (100), time-gate ticks |
| `config/simulation_quality/profiles/default.yaml` | — | All pillar weights = 1.0 |
| `config/simulation_quality/profiles/dungeon_crawl.yaml` | — | COMBAT: 2.0, FACTION: 0.1, etc. |
| `config/simulation_quality/profiles/urban_political.yaml` | — | FACTION: 1.5, ECONOMY: 1.5, etc. |
| `tests/simulation_quality/` | — | Entire test directory; no tests exist yet |

---

## 2. Mechanics / Engine Constraints (from Contract §3, §4, §8)

### §3.1 — Zero Simulation Impact (hard constraint)
- `QualityHub.on_envelope()` must never be called from inside `kernel.tick_once()`.
- In INPROCESS mode: called from the `QueueDrainWorker` background thread (after drain).
- In BROKER mode: called from `BrokerQualityFeed`'s consumer thread.
- Dropped score records are logged at WARNING level but must never raise an exception.

### §3.2 — Overhead Budget (hard constraint, tested in E6)
- `scorer.score()`: < 0.1 ms per event
- `QualityReport.build()`: < 50 ms
- `worst_events` list: max 100 records per pillar (`MAX_WORST_EVENTS = 100`)
- `window_buffer`: max 200 records per pillar (`deque(maxlen=200)`)
- `quality_scores.jsonl`: streamed to disk; never held in memory

### §3.3 — Disable Mechanism
- `QUALITY_SCORING_DISABLED=1` env var bypasses everything.
- When disabled: no QualityHub instantiated, no files written, REST returns `{"enabled": false}`.

### §3.4 — Dual Feed Mode
- `QUALITY_FEED_MODE=inprocess` (default) or `QUALITY_FEED_MODE=broker`.
- `QualityHub` and scorers are **identical** in both modes — only delivery mechanism changes.
- BROKER mode needs: `QUALITY_BROKER_URL`, `QUALITY_STREAM_NAME`, `QUALITY_CONSUMER_GROUP`.

### §4.4 — Normalized Score Formula
```
normalized_score = raw_score / max(1, current_tick)
```

### §4.5 — Grade Thresholds (named constants in `pillars.py`, not hardcoded in scorers)
| Grade | Range |
|---|---|
| S | > +2.0 |
| A | +0.5 to +2.0 |
| B | 0.0 to +0.5 |
| C | −0.5 to 0.0 |
| D | −1.0 to −0.5 |
| F | < −1.0 |

### §4.7 — Loop Detection
- Window size W = 200 (deque maxlen).
- Loop fires when: `tag_frequency(tag, window) / window_size > LOOP_THRESHOLD` (0.70 default).
- Loop flags are diagnostic only — no extra score penalty.

### §4.8 — Data-Driven Scoring
- All delta magnitudes, grade thresholds, and time-gate tick values live in YAML config files.
- Scorer Python code must contain **zero numeric literals** for these values.
- `ScoringWeights` is a Pydantic model — invalid YAML raises `ValidationError` at startup.

### §8.2 — Persistence Pattern
- `quality_scores.jsonl`: one JSONL line per `ScoreRecord`, appended during run; same pattern as `EventRecorder`.
- `quality_report.json`: written at run end by `QualityReport.build()`.
- Both files in `data/runs/{run_id}/`.

---

## 3. Critical Design Decisions

### 3.1 InProcessQualityFeed — Queue Integration

**Problem:** `QueueDrainWorker.__init__()` currently accepts only `file_write_fn` and `stream_publish_fn`. There is no quality callback slot.

**Decision:** Add an optional `quality_fn` parameter to `QueueDrainWorker.__init__()`:

```python
def __init__(
    self,
    queue: BoundedObservabilityQueue,
    file_write_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
    stream_publish_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
    quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
    interval_sec: float = 0.01
) -> None:
```

And call it in `_run()` after `stream_publish_fn`:

```python
if self.quality_fn:
    try:
        self.quality_fn(env)
    except Exception:
        self.failure_count += 1
        self.health_status = "DEGRADED"
```

**Rationale:** Minimal, non-breaking change. `EventRecorder` continues to pass `quality_fn=None` (default). `InProcessQualityFeed.start()` creates a new `QueueDrainWorker` with `quality_fn=hub.on_envelope`. This keeps quality scoring fully decoupled from the simulation path.

**Alternative considered:** A list of extra callbacks. Rejected — single `quality_fn` is sufficient; the list approach adds complexity without benefit at this stage.

**Impact on existing code:** `EventRecorder` instantiates `QueueDrainWorker` at line 99–103. Since `quality_fn` is optional with default `None`, no change to `EventRecorder` is required for this ticket. `InProcessQualityFeed` will instantiate its own `QueueDrainWorker` (or modify an existing one) when `start()` is called.

### 3.2 ScoringWeights — Pydantic v2 BaseModel

Uses Pydantic v2 (`pydantic==2.12.5`). Must use v2 API (`model_validator`, `model_fields`, not `@validator`).

`ScoringWeights` loads all three YAML files at construction:

```python
class ScoringWeights(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Per-pillar rule deltas: {PillarId.value: {rule_key: float}}
    pillar_rules: dict[str, dict[str, float]]
    grade_thresholds: dict[str, float]
    detection: DetectionParams

    @classmethod
    def load(cls, weights_path: str, grade_path: str, detection_path: str, profile: str = "default") -> "ScoringWeights":
        ...  # loads YAML files, merges profile overrides
```

`ValidationError` at startup (not silently at score time) is the contract requirement.

Scorers access weights via: `self.weights.pillar_rules["AGENCY"]["action_taken"]`
Integer time-gate values via: `int(self.weights.detection.time_gates["stasis_gate_ticks"])`

### 3.3 PillarAccumulator — Thread Safety

`PillarAccumulator.add()` is called from the drain worker thread. It must use `threading.Lock`.

```python
class PillarAccumulator:
    MAX_WORST_EVENTS: ClassVar[int] = 100
    WINDOW_SIZE: ClassVar[int] = 200

    def __init__(self, pillar_id: PillarId) -> None:
        self.pillar_id = pillar_id
        self.raw_score: float = 0.0
        self.event_count: int = 0
        self.negative_count: int = 0
        self.worst_events: list[ScoreRecord] = []
        self.window_buffer: deque[ScoreRecord] = deque(maxlen=self.WINDOW_SIZE)
        self.loop_flags: set[str] = set()
        self._seen_event_ids: set[str] = set()  # dedup for broker at-least-once
        self._lock = threading.Lock()

    def add(self, record: ScoreRecord) -> None:
        with self._lock:
            if record.event_id in self._seen_event_ids:
                return  # idempotent: broker at-least-once safe
            self._seen_event_ids.add(record.event_id)
            self.raw_score += record.delta
            self.event_count += 1
            if record.delta < 0:
                self.negative_count += 1
                # maintain worst_events sorted by abs(delta) descending, capped at MAX_WORST_EVENTS
                self.worst_events.append(record)
                self.worst_events.sort(key=lambda r: abs(r.delta), reverse=True)
                if len(self.worst_events) > self.MAX_WORST_EVENTS:
                    self.worst_events.pop()
            self.window_buffer.append(record)
            self._check_loop_detection()
```

### 3.4 QualityPersistence — Non-Blocking File Write

Pattern: same as `EventRecorder._write_envelope_to_file()`:
- File handle opened in `__init__()` (append mode, UTF-8)
- Each call to `write(record)` serializes to JSON and calls `file_handle.write(...) + flush()`
- File handle closed in `shutdown()`
- All exceptions caught and logged; never propagated

Since `write()` is called from the drain worker thread (same thread as `hub.on_envelope()`), the write is effectively single-threaded — no additional locking needed on the file handle.

### 3.5 build_feed_from_env() — Factory

```python
def build_feed_from_env() -> Optional[QualityFeedAdapter]:
    if os.environ.get("QUALITY_SCORING_DISABLED") == "1":
        return None
    mode = os.environ.get("QUALITY_FEED_MODE", "inprocess").lower()
    if mode == "inprocess":
        return InProcessQualityFeed()
    elif mode == "broker":
        return BrokerQualityFeed(
            broker_url=os.environ.get("QUALITY_BROKER_URL", "redis://localhost:6379"),
            stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events"),
            consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
        )
    else:
        raise ValueError(f"Unknown QUALITY_FEED_MODE: {mode!r}")
```

---

## 4. Parity Ledger Overlap

### infrastructure.yaml entries affected

| Entry | Text (summary) | Action Required |
|---|---|---|
| INFRA-179 | Only one QueueDrainWorker drains the global observability queue at a time. | `InProcessQualityFeed` creates its own worker against its own queue reference — must not break the singleton guard. Verify the singleton guard in `get_or_start_global_worker()` is not bypassed. |

### New entries required (add to infrastructure.yaml after E1 lands)

| Proposed ID | Text |
|---|---|
| INFRA-190 | `QueueDrainWorker.quality_fn` is called per-envelope after `file_write_fn` and `stream_publish_fn`; exceptions are caught and do not propagate. |
| INFRA-191 | `QUALITY_SCORING_DISABLED=1` prevents any `QualityHub` instantiation and leaves simulation behavior bit-identical. |
| INFRA-192 | `ScoringWeights` raises `ValidationError` at startup if any required key is missing or malformed. |
| INFRA-193 | `PillarAccumulator.add()` is idempotent for duplicate `event_id` values (broker at-least-once safe). |

---

## 5. Prior Work

- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative design reference for this entire module (2026-06-28)
- `docs/plans/sim_quality_scoring_module.md` — the investigation source document referenced in the contract
- `TCK-20260628-SIMQ-EPIC` (parent epic) — tracks child tickets E1–E7
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/` — prior investigation artifacts

No prior implementation of `src/simulation_quality/` exists. No migration or compatibility concern with existing code.

---

## 6. Risks and Open Questions

### Risk: QueueDrainWorker thread leak in tests
**Severity:** High (detected at session close by conftest.py)
**Mitigation:** Every test that creates a `QueueDrainWorker` must call `stop()` in teardown. `InProcessQualityFeed.stop()` must call `self._worker.stop()`. Tests should use `try/finally` or pytest fixtures with `yield` + cleanup.

### Risk: Pydantic v2 API usage
**Severity:** Medium
**Mitigation:** Use `model_config = ConfigDict(frozen=True)`, `@model_validator(mode="before")`, `model_fields`, `Field(...)` — not the v1 `@validator` or `class Config`. Confirm with: `from pydantic import BaseModel, ConfigDict, model_validator, Field`.

### Risk: worst_events sort performance at MAX_WORST_EVENTS boundary
**Severity:** Low
**Mitigation:** The sort is over at most 101 elements (insert then truncate). Python's Timsort is O(n log n) but stable and fast for small n. Acceptable for < 0.1 ms budget per call. If profiling in E6 shows pressure, switch to `heapq.nlargest`.

### Risk: scoring_weights.yaml is not validated at the granularity of individual pillar sections
**Severity:** Medium
**Detail:** Pydantic validates the top-level schema. Missing keys within a pillar section (e.g., a scorer calls `self.weights["AGENCY"]["missing_key"]`) would KeyError at score time, not startup. 
**Mitigation:** `ScoringWeights` must enumerate all required keys for each pillar as typed fields (or as a known-keys validator). Alternatively, scorers use `.get(key, 0.0)` with a logged warning — but this violates the "raises at startup" contract. **Recommended:** use a known-key validator per pillar section in Pydantic, or define required key lists in `pillars.py` and validate against them in `ScoringWeights.__init__`.

### Risk: InProcessQualityFeed worker vs. EventRecorder worker — two workers draining the same queue
**Severity:** High
**Detail:** `EventRecorder` creates its own `QueueDrainWorker` at line 99–103. If `InProcessQualityFeed` also creates a `QueueDrainWorker` on the **same queue**, two workers would race to drain envelopes. Each envelope would only be seen by one of them.
**Resolution (from contract §3.4):** `InProcessQualityFeed.start()` registers a `quality_fn` **on the existing `QueueDrainWorker`** — it does NOT create a second worker. Concretely: the `EventRecorder`'s `_worker` instance needs to have its `quality_fn` set before `start()`. This means either:
  (a) `EventRecorder` accepts a `quality_fn` constructor arg and passes it to `QueueDrainWorker` (cleanest), or
  (b) `InProcessQualityFeed` receives a reference to the existing `QueueDrainWorker` and sets `worker.quality_fn = hub.on_envelope` at feed start time.
  Option (b) has a race window between `worker.start()` and `quality_fn` assignment. **Recommended:** option (a) — pass `quality_fn` at construction so the attribute is set before the thread starts.

### Open Question: Should `InProcessQualityFeed.start()` operate on the global worker or a per-recorder worker?
**Context:** The contract says "registers a drain callback on `BoundedObservabilityQueue`." The EventRecorder uses a per-instance queue and worker. The global worker (`get_or_start_global_worker`) uses the global queue.
**Working assumption:** In a simulation run, a single `EventRecorder` is active. `InProcessQualityFeed` receives a reference to that recorder's `_worker` and sets `quality_fn`. If multiple recorders exist, each would need its own feed. This should be clarified before E2 begins.

---

## 7. Anti-Drift Hazards

| Hazard | Where it manifests | Guard |
|---|---|---|
| Numeric literals in scorer code | `src/simulation_quality/scorers/*.py` | Code review gate; add a lint rule or test that imports all scorers and asserts `quality_fn` uses `self.weights[...]` not float literals. |
| Grade thresholds hardcoded outside `pillars.py` | Any file comparing `normalized_score` to a float | Single source of truth: `GRADE_THRESHOLDS` dict in `pillars.py`; assert in test that grade assignment reads from this dict. |
| `worst_events` exceeding 100 entries | `PillarAccumulator.worst_events` | `MAX_WORST_EVENTS = 100` class variable; assertion test after 10,000 events. |
| `window_buffer` exceeding 200 entries | `PillarAccumulator.window_buffer` | `deque(maxlen=200)` enforces at construction; test after 10,000 events. |
| Quality scoring blocking simulation tick | Any path from `kernel.tick_once()` to `QualityHub.on_envelope()` | Architecture test: assert the call chain never reaches `on_envelope` from `tick_once`. |
| `ScoringWeights` missing-key swallowed silently | Scorer calling `self.weights[pillar][missing_key]` | Startup validation test: load production config → no KeyError; malformed config → ValidationError. |
| QueueDrainWorker thread leak in test suite | Test creates worker without stopping | conftest.py session guard; fixture pattern with `yield` + `worker.stop()` in teardown. |
| Duplicate event_id scored twice in broker mode | `PillarAccumulator.add()` called with same envelope | `_seen_event_ids` dedup set; test that add() with duplicate is a no-op. |
