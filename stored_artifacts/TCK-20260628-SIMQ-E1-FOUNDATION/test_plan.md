---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E1-FOUNDATION
date: 2026-06-29
tags: [simulation-quality, scoring, foundation, test-plan]
---

# Test Plan — TCK-20260628-SIMQ-E1-FOUNDATION
# Core Models & Data Layer for Simulation Quality Scoring

**Contract source:** `docs/simulation_quality/quality_scoring_contract.md` §11  
**Test root:** `tests/simulation_quality/`  
**Date:** 2026-06-29

---

## 1. Regression Surface (Existing Tests That Must Pass)

These existing tests must continue to pass after E1 changes. They exercise code paths modified or adjacent to E1 work.

| Test File | Scope | Why It Matters |
|---|---|---|
| `tests/unit/test_queue_worker_singleton.py` | `QueueDrainWorker` singleton guard (INFRA-179) | E1 adds `quality_fn` param to `QueueDrainWorker.__init__()` — must not break singleton semantics |
| `tests/unit/test_memory_probe.py` | QueueDrainWorker thread counting | Thread leak detection still works after parameter addition |
| `tests/observability/test_events_timeline.py` | ObservabilityEventEnvelope lifecycle | E1 consumes envelopes from the same queue; routing must be stable |
| `tests/observability/test_metrics_export.py` | Observability metrics | Non-regression: quality layer must not affect metric emission |
| `tests/observability/test_websocket_stream_events.py` | Stream publish path | `stream_publish_fn` must still fire; `quality_fn` is additive |
| `tests/integration/scenarios/test_macro_economy.py` | Full kernel + shutdown | `QueueDrainWorker` thread leak check at session end |

### Regression command (run before and after E1 implementation)
```bash
pytest tests/unit/test_queue_worker_singleton.py \
       tests/unit/test_memory_probe.py \
       tests/observability/ \
       -v --tb=short
```

---

## 2. New Tests Required

All new tests go in `tests/simulation_quality/`. Create `tests/simulation_quality/__init__.py`.

### 2.1 ScoringWeights — Load and Validation

**File:** `tests/simulation_quality/test_scoring_weights.py`

| Test | Description | Assert |
|---|---|---|
| `test_load_valid_config` | Load all three YAML files from `config/simulation_quality/`; no exception | ScoringWeights instance; `pillar_rules["AGENCY"]["action_taken"]` is a float |
| `test_missing_required_key_raises_at_startup` | YAML missing a required pillar section | `pytest.raises(ValidationError)` or `pytest.raises(KeyError)` (whichever the chosen validation strategy produces) |
| `test_malformed_value_type_raises_at_startup` | Grade threshold entry is a string instead of float | `pytest.raises(ValidationError)` |
| `test_grade_thresholds_loaded` | `grade_thresholds["S"]` == 2.0; `grade_thresholds["F_threshold"]` or equivalent | Values match contract §4.5 |
| `test_detection_params_loaded` | `detection.loop_threshold` == 0.70; `detection.window_size` == 200; `detection.max_worst_events` == 100 | Values match contract §3.2 / §4.7 |
| `test_profile_override_applied` | Load with `profile="dungeon_crawl"` | COMBAT pillar weight overridden to 2.0; FACTION to 0.1 |
| `test_weights_frozen` | Attempt `weights.pillar_rules["AGENCY"]["action_taken"] = 99.0` | `TypeError` or equivalent (frozen model) |

### 2.2 PillarAccumulator.add() — Core Accumulation

**File:** `tests/simulation_quality/test_pillar_accumulator.py`

#### Normal flow

| Test | Description | Assert |
|---|---|---|
| `test_add_positive_delta_updates_raw_score` | Add a ScoreRecord with delta=+2.0 | `raw_score == 2.0`; `event_count == 1`; `negative_count == 0` |
| `test_add_negative_delta_updates_counts` | Add a ScoreRecord with delta=-3.0 | `raw_score == -3.0`; `negative_count == 1` |
| `test_add_negative_appears_in_worst_events` | Add negative delta | Record appears in `worst_events` |
| `test_add_positive_does_not_appear_in_worst_events` | Add positive delta only | `worst_events` is empty |
| `test_normalized_score_formula` | Add delta=10.0 records; current_tick=5 | `normalized_score == 10.0 / max(1, 5)` |

#### worst_events ceiling

| Test | Description | Assert |
|---|---|---|
| `test_worst_events_ceiling_at_100` | Add 200 negative ScoreRecords | `len(worst_events) == 100` |
| `test_worst_events_contains_largest_abs_delta` | Add mix of −1.0 and −50.0 records beyond cap | worst_events contains the −50.0 records; −1.0 records are evicted |

#### window_buffer overflow

| Test | Description | Assert |
|---|---|---|
| `test_window_buffer_ceiling_at_200` | Add 500 records | `len(window_buffer) == 200` |
| `test_window_buffer_is_sliding` | Add 205 records | First 5 records not in buffer; last 200 are present |

#### Dedup (same event_id scored once)

| Test | Description | Assert |
|---|---|---|
| `test_dedup_same_event_id_is_no_op` | `add(record)` twice with same `event_id` | `event_count == 1`; `raw_score` unchanged after second call |
| `test_dedup_different_event_ids_both_scored` | Two records with distinct `event_id` | `event_count == 2` |
| `test_dedup_does_not_prevent_same_delta_different_id` | Two records, same delta, different `event_id` | `raw_score == 2 * delta` |

#### Thread safety

| Test | Description | Assert |
|---|---|---|
| `test_concurrent_add_no_data_corruption` | 10 threads each calling `add()` 100 times | `event_count == 1000`; `raw_score` equals sum of all deltas (within float tolerance) |

### 2.3 QualityReport.build() — Grade Assignment

**File:** `tests/simulation_quality/test_quality_report.py`

| Test | Description | Assert |
|---|---|---|
| `test_grade_S_above_2` | normalized_score = +2.1 | grade == "S" |
| `test_grade_A_between_0_5_and_2` | normalized_score = +1.0 | grade == "A" |
| `test_grade_B_between_0_and_0_5` | normalized_score = +0.25 | grade == "B" |
| `test_grade_C_between_minus_0_5_and_0` | normalized_score = −0.25 | grade == "C" |
| `test_grade_D_between_minus_1_and_minus_0_5` | normalized_score = −0.75 | grade == "D" |
| `test_grade_F_below_minus_1` | normalized_score = −1.5 | grade == "F" |
| `test_grade_boundary_exact_0_5` | normalized_score exactly = 0.5 | grade == "A" (boundary is inclusive at lower end) |
| `test_overall_score_weighted_average` | Two pillars, weights=[1.0, 2.0], normalized=[1.0, 0.0] | `overall_score == (1.0×1.0 + 0.0×2.0) / 3.0` |
| `test_report_schema_keys` | `QualityReport.build()` on populated accumulators | Output dict has: `run_id`, `tick_count`, `overall_score`, `overall_grade`, `generated_at`, `pillars` |
| `test_pillar_entry_schema` | Single pillar in report | Entry has: `raw_score`, `normalized_score`, `grade`, `event_count`, `negative_count`, `loop_detected`, `loop_flags`, `worst_events` |
| `test_loop_detected_flag` | Accumulator with `loop_flags = {"goal_lock"}` | `loop_detected == True` in report; `loop_flags == ["goal_lock"]` |
| `test_worst_events_top_10_in_report` | Accumulator with 20 worst_events | Report `worst_events` contains top 10 by abs(delta) |

### 2.4 QualityPersistence — File Output

**File:** `tests/simulation_quality/test_quality_persistence.py`

| Test | Description | Assert |
|---|---|---|
| `test_write_creates_jsonl_file` | `QualityPersistence(run_dir=tmpdir)` + `write(record)` | `quality_scores.jsonl` exists in tmpdir |
| `test_write_appends_valid_json_lines` | Write 3 records | File has 3 lines; each parses as valid JSON |
| `test_jsonl_record_fields` | Write one ScoreRecord | JSON line has: `tick`, `event_id`, `pillar`, `delta`, `reason`, `event_type`, `entity_id`, `region_id`, `tags` |
| `test_shutdown_closes_file_handle` | `write()` then `shutdown()` | File handle is closed; subsequent `write()` raises or is no-op |
| `test_write_exception_does_not_propagate` | Patch `_file_handle.write` to raise OSError | No exception raised to caller; error is logged |
| `test_disabled_persistence_writes_nothing` | `QualityPersistence(enabled=False)` + `write(record)` | No file created |

### 2.5 Config Missing-Key Raises at Startup

**File:** `tests/simulation_quality/test_config_validation.py`

| Test | Description | Assert |
|---|---|---|
| `test_missing_grade_thresholds_file_raises` | Pass nonexistent grade_thresholds path to ScoringWeights.load() | Raises `FileNotFoundError` or `ValidationError` |
| `test_missing_detection_params_file_raises` | Pass nonexistent detection_params path | Raises appropriately |
| `test_extra_unknown_keys_in_yaml_handled` | YAML has extra unknown key | Does not silently ignore; behavior defined by Pydantic `extra="forbid"` or `extra="ignore"` (document choice) |
| `test_all_10_pillar_sections_present_in_production_config` | Load production `scoring_weights.yaml` | All 10 pillar IDs from `PillarId` have a corresponding section |

### 2.6 build_feed_from_env() — Mode Selection

**File:** `tests/simulation_quality/test_factory.py`

| Test | Description | Assert |
|---|---|---|
| `test_inprocess_mode_is_default` | `QUALITY_FEED_MODE` unset | Returns `InProcessQualityFeed` |
| `test_explicit_inprocess_mode` | `QUALITY_FEED_MODE=inprocess` | Returns `InProcessQualityFeed` |
| `test_broker_mode_selected` | `QUALITY_FEED_MODE=broker` | Returns `BrokerQualityFeed` |
| `test_disabled_returns_none` | `QUALITY_SCORING_DISABLED=1` | Returns `None` |
| `test_unknown_mode_raises` | `QUALITY_FEED_MODE=unknown_xyz` | Raises `ValueError` with mode name in message |
| `test_broker_env_vars_forwarded` | `QUALITY_BROKER_URL=redis://myhost:6380` + broker mode | `BrokerQualityFeed` constructed with `broker_url="redis://myhost:6380"` |

### 2.7 QueueDrainWorker quality_fn Integration

**File:** `tests/simulation_quality/test_inprocess_feed.py`

| Test | Description | Assert |
|---|---|---|
| `test_quality_fn_called_per_envelope` | Create `QueueDrainWorker(quality_fn=spy_fn)`, push 3 envelopes, wait for drain | `spy_fn` called 3 times with correct envelopes |
| `test_quality_fn_exception_does_not_stop_worker` | `quality_fn` raises on every call; push 5 envelopes | Worker remains alive; `worker.failure_count >= 1`; `worker.health_status == "DEGRADED"` |
| `test_quality_fn_none_is_default` | Create worker with no `quality_fn` | No AttributeError; file/stream callbacks still fire |
| `test_file_and_stream_still_called_with_quality_fn` | All three callbacks set | All three called per envelope (quality_fn does not replace others) |
| `test_inprocess_feed_start_registers_callback` | `InProcessQualityFeed.start(hub)` → push envelope → wait | `hub.on_envelope` called with the envelope |
| `test_inprocess_feed_stop_shuts_down_worker` | `feed.start(hub)` then `feed.stop()` | Worker thread is no longer alive after stop |
| `test_no_worker_thread_leak_after_stop` | Full lifecycle: start → push → stop | No `observability-drain-worker` threads remain (use memory_probe) |

---

## 3. Scoped Pytest Commands

### Run only E1 tests (during development)
```bash
pytest tests/simulation_quality/ -v --tb=short
```

### Run E1 tests excluding slow tests
```bash
pytest tests/simulation_quality/ -m "not slow" -v --tb=short
```

### Run regression guard (observability + E1)
```bash
pytest tests/simulation_quality/ \
       tests/unit/test_queue_worker_singleton.py \
       tests/unit/test_memory_probe.py \
       tests/observability/ \
       -v --tb=short
```

### Run thread safety test explicitly (may be slow)
```bash
pytest tests/simulation_quality/test_pillar_accumulator.py::test_concurrent_add_no_data_corruption \
       -v --tb=long -s
```

### Full domain scope (E1 + observability regression, excluding slow suite)
```bash
pytest tests/simulation_quality/ tests/observability/ tests/unit/test_queue_worker_singleton.py \
       -m "not slow" --tb=short -q
```

---

## 4. Anti-Drift Test Guards

These tests are specifically designed to prevent implementation drift from the contract. They should be stable and fail loud if the contract is violated.

### Guard 1: Grade thresholds are not hardcoded

**File:** `tests/simulation_quality/test_anti_drift.py`

```python
def test_grade_thresholds_come_from_pillars_module():
    """Verify GRADE_THRESHOLDS is defined in pillars.py and QualityReport uses it."""
    from src.simulation_quality.pillars import GRADE_THRESHOLDS
    assert isinstance(GRADE_THRESHOLDS, dict)
    assert set(GRADE_THRESHOLDS.keys()) >= {"S", "A", "B", "C", "D"}
    # Spot check boundary values
    assert GRADE_THRESHOLDS["S"] == 2.0
    assert GRADE_THRESHOLDS["A"] == 0.5
```

### Guard 2: worst_events never exceeds MAX_WORST_EVENTS

```python
def test_worst_events_hard_ceiling():
    """MAX_WORST_EVENTS = 100 is enforced regardless of how many records are added."""
    from src.simulation_quality.accumulator import PillarAccumulator
    from src.simulation_quality.pillars import PillarId
    acc = PillarAccumulator(PillarId.ECONOMY)
    for i in range(500):
        record = make_score_record(event_id=f"e{i}", delta=-float(i+1), pillar=PillarId.ECONOMY)
        acc.add(record)
    assert len(acc.worst_events) == PillarAccumulator.MAX_WORST_EVENTS
    assert len(acc.worst_events) == 100
```

### Guard 3: window_buffer never exceeds WINDOW_SIZE

```python
def test_window_buffer_hard_ceiling():
    """Window deque maxlen=200 enforced by construction."""
    from src.simulation_quality.accumulator import PillarAccumulator
    from src.simulation_quality.pillars import PillarId
    acc = PillarAccumulator(PillarId.AGENCY)
    for i in range(500):
        record = make_score_record(event_id=f"e{i}", delta=1.0, pillar=PillarId.AGENCY)
        acc.add(record)
    assert len(acc.window_buffer) == PillarAccumulator.WINDOW_SIZE
    assert len(acc.window_buffer) == 200
```

### Guard 4: Quality module does not import from engine or domain internals

```python
def test_simulation_quality_has_no_engine_imports():
    """src/simulation_quality/ must not import from src/engine/, src/domains/, or src/systems/."""
    import importlib
    import pkgutil
    import sys

    forbidden_prefixes = ("src.engine", "src.domains", "src.systems")
    import src.simulation_quality as sq_pkg
    for _, modname, _ in pkgutil.walk_packages(sq_pkg.__path__, prefix="src.simulation_quality."):
        mod = importlib.import_module(modname)
        for key in dir(mod):
            # Check sys.modules for transitive imports
        for imported_mod in list(sys.modules.keys()):
            for prefix in forbidden_prefixes:
                assert not imported_mod.startswith(prefix), (
                    f"{modname} transitively imports {imported_mod} which is in forbidden domain {prefix}"
                )
```

### Guard 5: ScoringWeights is frozen (immutable after load)

```python
def test_scoring_weights_frozen():
    """ScoringWeights must be immutable after construction (Pydantic frozen model)."""
    weights = ScoringWeights.load(...)
    with pytest.raises((TypeError, AttributeError)):
        weights.grade_thresholds["S"] = 999.0
```

### Guard 6: QualityPersistence write failure never propagates

```python
def test_persistence_write_failure_is_silent():
    """A write failure must not raise to the caller (same contract as EventRecorder)."""
    with tempfile.TemporaryDirectory() as d:
        p = QualityPersistence(run_dir=d)
        p._file_handle = None  # simulate closed handle
        record = make_score_record(event_id="x1", delta=-1.0, pillar=PillarId.ECONOMY)
        # Must not raise
        p.write(record)
```

### Guard 7: PillarAccumulator.add() is idempotent on duplicate event_id

```python
def test_accumulator_dedup_idempotent():
    """Calling add() twice with the same event_id must produce same state as calling once."""
    acc = PillarAccumulator(PillarId.COMBAT)
    rec = make_score_record(event_id="dupe-id", delta=-5.0, pillar=PillarId.COMBAT)
    acc.add(rec)
    acc.add(rec)  # duplicate
    assert acc.event_count == 1
    assert acc.raw_score == -5.0
    assert len(acc._seen_event_ids) == 1
```

### Guard 8: All 10 PillarId values covered by PILLAR_METADATA

```python
def test_all_10_pillars_have_metadata():
    """PILLAR_METADATA must have an entry for every PillarId value."""
    from src.simulation_quality.pillars import PillarId, PILLAR_METADATA
    for pillar in PillarId:
        assert pillar in PILLAR_METADATA, f"Missing PILLAR_METADATA entry for {pillar}"
```

---

## 5. Fixture Patterns

### ScoreRecord factory fixture

```python
# tests/simulation_quality/conftest.py
import pytest
from src.simulation_quality.models import ScoreRecord
from src.simulation_quality.pillars import PillarId

def make_score_record(
    event_id: str = "test-event-id",
    delta: float = 1.0,
    pillar: PillarId = PillarId.ECONOMY,
    tick: int = 1,
    reason: str = "test",
) -> ScoreRecord:
    return ScoreRecord(
        tick=tick,
        event_id=event_id,
        pillar=pillar,
        delta=delta,
        reason=reason,
        event_type="test_event",
        entity_id=None,
        region_id=None,
        tags=(),
    )

@pytest.fixture
def score_record():
    return make_score_record()

@pytest.fixture
def minimal_weights():
    """Minimal ScoringWeights for unit tests — does not load production YAML."""
    from src.simulation_quality.weights import ScoringWeights
    return ScoringWeights(
        pillar_rules={"ECONOMY": {"harvest_active": 3.0, "zero_harvest": -20.0}},
        grade_thresholds={"S": 2.0, "A": 0.5, "B": 0.0, "C": -0.5, "D": -1.0},
        detection=DetectionParams(loop_threshold=0.70, window_size=200, max_worst_events=100, time_gates={}),
    )
```

### Worker teardown helper

```python
@pytest.fixture
def managed_drain_worker(tmp_queue):
    """Creates a QueueDrainWorker and guarantees stop() in teardown."""
    from src.observability.queue import BoundedObservabilityQueue, QueueDrainWorker
    q = BoundedObservabilityQueue(max_size=100)
    worker = QueueDrainWorker(queue=q)
    worker.start()
    yield worker
    worker.stop()
```

---

## 6. Test File Index

```
tests/simulation_quality/
├── __init__.py
├── conftest.py                          # shared fixtures and make_score_record
├── test_scoring_weights.py              # §2.1
├── test_pillar_accumulator.py           # §2.2
├── test_quality_report.py              # §2.3
├── test_quality_persistence.py          # §2.4
├── test_config_validation.py           # §2.5
├── test_factory.py                     # §2.6
├── test_inprocess_feed.py              # §2.7
└── test_anti_drift.py                  # §4 guards
```
