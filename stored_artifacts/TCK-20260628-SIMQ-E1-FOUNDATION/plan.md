---
status: active
ticket_id: TCK-20260628-SIMQ-E1-FOUNDATION
date: 2026-06-29
---

# Plan — TCK-20260628-SIMQ-E1-FOUNDATION
# Core Models & Data Layer for Simulation Quality Scoring

## Ordered Steps

### Step 1 — Config YAML Files (no code, no blockers)

Files:
- `config/simulation_quality/scoring_weights.yaml` — all 10 pillar sections with all rule keys and initial delta values from contract §5
- `config/simulation_quality/grade_thresholds.yaml` — S/A/B/C/D/F boundary values from contract §4.5
- `config/simulation_quality/detection_params.yaml` — loop_threshold (0.70), window_size (200), MAX_WORST_EVENTS (100), stasis_gate_ticks (5), zero_harvest_after_tick (100), plus all time-gate values
- `config/simulation_quality/profiles/default.yaml` — all 10 pillar weights = 1.0
- `config/simulation_quality/profiles/dungeon_crawl.yaml` — COMBAT: 2.0, FACTION: 0.1
- `config/simulation_quality/profiles/urban_political.yaml` — FACTION: 1.5, ECONOMY: 1.5

Scope guard: No Python code changes. Only YAML creation.

### Step 2 — `src/simulation_quality/pillars.py`

- `PillarId` enum: exactly 10 values — COGNITION, AGENCY, COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE
- `PILLAR_METADATA` dict: per pillar — name, description, phase_anchors, d01_tier
- `GRADE_THRESHOLDS: dict[str, float]` — S/A/B/C/D boundaries (pre-calibration estimates, marked with comment); used by QualityReport; never hardcoded elsewhere
- `src/simulation_quality/__init__.py` — empty package init

Scope guard: No imports from src/engine/, src/domains/, src/systems/.

### Step 3 — `src/simulation_quality/score_record.py`

- `ScoreRecord` — frozen dataclass with all fields from contract §4.1: tick, event_id, pillar, delta, reason, event_type, entity_id, region_id, tags (tuple[str, ...])
- `ScoringContext` — frozen dataclass with all fields from contract §4.2: run_id, current_tick, entity_count, pillar_scores (Mapping[PillarId, float]), pillar_event_counts, window_tag_counts

### Step 4 — `src/simulation_quality/weights.py`

- `DetectionParams` — Pydantic v2 BaseModel: loop_threshold (float), window_size (int), max_worst_events (int), time_gates (dict[str, int])
- `ScoringWeights` — Pydantic v2 BaseModel (frozen): pillar_rules (dict[str, dict[str, float]]), grade_thresholds (dict[str, float]), detection (DetectionParams)
- `ScoringWeights.load(weights_path, grade_path, detection_path, profile="default")` classmethod — loads YAML files, applies profile overrides, raises ValidationError on malformed/missing
- `ScoringWeights.__getitem__(key)` — for `w["rule_key"]` access pattern; reads from flat merged dict
- `ScoringWeights.int(key)` — typed int accessor for time-gate values

Scope guard: Raises ValidationError at startup. Never swallow missing keys silently.

### Step 5 — `src/simulation_quality/pillar_accumulator.py`

- `PillarAccumulator` class — per contract §4.3:
  - `raw_score: float`, `event_count: int`, `negative_count: int`
  - `worst_events: list[ScoreRecord]` — capped at MAX_WORST_EVENTS, sorted by abs(delta) desc
  - `window_buffer: deque[ScoreRecord]` — `deque(maxlen=200)` from config
  - `loop_flags: set[str]`
  - `_seen_event_ids: set[str]` — for idempotent dedup (not bounded)
  - `_lock: threading.Lock` — guards all mutable state in `add()`
- `add(record: ScoreRecord) -> None` — locked; drops duplicate event_ids silently; updates all state
- `snapshot() -> dict` — returns immutable view (copies, not references to mutable state)
- `_check_loop_detection()` — checks window_buffer for tags exceeding LOOP_THRESHOLD; adds to loop_flags

### Step 6 — `src/simulation_quality/quality_report.py`

- `PillarSnapshot` — dataclass: pillar_id, raw_score, normalized_score, grade (str), event_count, negative_count, loop_detected (bool), loop_flags (frozenset), worst_events (tuple)
- `QualityReport` — dataclass: run_id, tick_count, overall_score, overall_grade, generated_at (ISO str), pillars (Mapping[str, PillarSnapshot])
- `QualityReportBuilder.build(accumulators, current_tick, run_id, weights)` — class/static method:
  - Computes normalized_score per pillar
  - Assigns grade from ScoringWeights.grade_thresholds (not from constants)
  - Computes overall_score as weighted average using ScoringWeights pillar weights
  - Returns QualityReport
- `QualityReport.to_dict()` — JSON-serializable dict for persistence

### Step 7 — `src/simulation_quality/persistence.py`

- `QualityPersistence` — non-blocking file writer (pattern: EventRecorder):
  - `__init__(run_dir: str)` — opens `quality_scores.jsonl` in append mode; creates `data/runs/{run_id}/` if needed
  - `write(record: ScoreRecord) -> None` — serializes ScoreRecord to JSON, writes + flushes; exceptions caught + logged, never propagated
  - `write_report(report: QualityReport) -> None` — writes `quality_report.json`; atomic write (write to .tmp then rename)
  - `shutdown() -> None` — flushes and closes file handle

### Step 8 — Modify `src/observability/queue.py` (minimal change)

- Add `quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None` to `QueueDrainWorker.__init__()`
- Store as `self.quality_fn = quality_fn`
- In `_run()`, after `stream_publish_fn` call, add:
  ```python
  if self.quality_fn:
      try:
          self.quality_fn(env)
      except Exception:
          self.failure_count += 1
          self.health_status = "DEGRADED"
  ```
- This is the ONLY modification to existing code.

Scope guard: No other changes to queue.py. EventRecorder continues to work unchanged (quality_fn defaults to None).

### Step 9 — `src/simulation_quality/feed.py`

- `QualityFeedMode` enum — INPROCESS, BROKER
- `QualityFeedAdapter` ABC — `start(hub: QualityHub) -> None`, `stop() -> None`, `health() -> dict`
- `InProcessQualityFeed(QualityFeedAdapter)`:
  - `start(hub)` — gets global queue via `get_observability_queue()`; creates a QueueDrainWorker with `quality_fn=hub.on_envelope`; stores as `self._worker`; calls `self._worker.start()`
  - `stop()` — calls `self._worker.stop()`
  - `health()` — returns `{"status": "HEALTHY"/"DEGRADED", "dropped_count": ..., "mode": "inprocess"}`
- `BrokerQualityFeed(QualityFeedAdapter)` — stub implementation for E1 (raises NotImplementedError); E2 wires the full RedisStreamConsumer
- `build_feed_from_env() -> Optional[QualityFeedAdapter]`:
  - Returns None if QUALITY_SCORING_DISABLED=1
  - Returns InProcessQualityFeed if QUALITY_FEED_MODE=inprocess (default)
  - Returns BrokerQualityFeed if QUALITY_FEED_MODE=broker
  - Raises ValueError for unknown values

### Step 10 — Tests

Files to create in `tests/simulation_quality/`:
- `__init__.py`
- `conftest.py` — shared fixtures: `scoring_weights_fixture()` (loads test YAML or creates minimal ScoringWeights), `sample_score_record()`, managed_accumulator
- `test_weights.py` — ScoringWeights load from real config; ValidationError on missing key; ValidationError on wrong type; all 10 pillars present; grade thresholds load correctly
- `test_accumulator.py` — add() updates raw_score; add() with duplicate event_id is no-op (scored once); worst_events never exceeds MAX_WORST_EVENTS; window_buffer capped at maxlen; loop detection fires at >70% threshold; snapshot() returns immutable copy (not reference)
- `test_report.py` — build() assigns correct grade for each boundary value; overall_score computed from weighted average; normalized_score = raw_score / max(1, tick); grade reads from ScoringWeights, not from hardcoded values
- `test_persistence.py` — write() appends JSONL line; write_report() creates quality_report.json; file written to correct path; exception in write() does not propagate
- `test_feed.py` — build_feed_from_env() returns InProcessQualityFeed by default; returns None when QUALITY_SCORING_DISABLED=1; raises ValueError for unknown QUALITY_FEED_MODE; InProcessQualityFeed.start() + stop() do not leak threads

## Scope Guards

- Must NOT import from: `src/engine/`, `src/domains/`, `src/systems/`, any domain module
- Must NOT hardcode any numeric delta, grade threshold, or time-gate value in Python files
- Must NOT modify EventRecorder (queue.py change is the only existing-code modification)
- Must NOT implement QualityHub, BrokerQualityFeed (beyond stub), or any scorer — those are E2–E4

## Dependency Map

```
Step 1 (YAML) → independent
Step 2 (pillars.py) → independent
Step 3 (ScoreRecord, ScoringContext) → depends on Step 2 (PillarId)
Step 4 (ScoringWeights) → depends on Steps 1, 2
Step 5 (PillarAccumulator) → depends on Steps 3, 4
Step 6 (QualityReport) → depends on Steps 2, 3, 4, 5
Step 7 (QualityPersistence) → depends on Steps 3, 6
Step 8 (queue.py modification) → independent
Step 9 (feed.py) → depends on Step 8
Step 10 (tests) → depends on all above
```

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| PillarId has exactly 10 values | Step 2 |
| ScoreRecord frozen, tags is tuple | Step 3 |
| ScoringWeights raises ValidationError on malformed | Step 4 |
| No numeric literals in scorer files | Enforced throughout |
| worst_events never exceeds MAX_WORST_EVENTS | Step 5 |
| window_buffer is deque(maxlen=W) from config | Step 5 |
| PillarAccumulator.add() uses lock | Step 5 |
| Duplicate event_id scored once | Step 5 |
| QualityReport grade from ScoringWeights | Step 6 |
| QualityPersistence writes to correct paths | Step 7 |
| QualityPersistence writes are non-blocking | Step 7 |
| QualityFeedAdapter ABC has correct signatures | Step 9 |
| InProcessQualityFeed registers without modifying existing queue behavior | Step 8, 9 |
| build_feed_from_env() correct behavior | Step 9 |
| Unit tests for all AC items | Step 10 |

## Deviations

- `ScoringWeights._flat_rules` and `_pillar_weights` stored as instance attributes via `object.__setattr__` (required to work around Pydantic v2 frozen model restrictions for post-construction caching)
- `int_param()` method name used instead of `int()` (plan said `w.int("key")`) to avoid shadowing Python built-in; all tests reference `int_param()`
- `quality_report.py` imports `from datetime import timezone` to avoid deprecation of `datetime.utcnow()`
- `InProcessQualityFeed` creates a separate `QueueDrainWorker` on the global queue (does not modify the EventRecorder's worker) — this is the correct interpretation per investigation §3.1 design note
