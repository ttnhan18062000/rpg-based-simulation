---
status: active
artifact_type: investigation
ticket_id: TCK-20260628-SIMQ-E2-HUB-CORE
---

# Investigation — TCK-20260628-SIMQ-E2-HUB-CORE

## Current Behavior

### E1 Foundation (already built)

`src/simulation_quality/` has:
- `pillars.py` — `PillarId` enum (10 pillars), `PILLAR_METADATA`, `GRADE_THRESHOLDS`
- `score_record.py` — `ScoreRecord(frozen dataclass)`, `ScoringContext(frozen dataclass)`
- `pillar_accumulator.py` — `PillarAccumulator` (thread-safe, `_seen_event_ids` dedup, `window_buffer=deque(maxlen=200)`, `loop_flags`)
- `quality_report.py` — `QualityReport`, `PillarSnapshot`, `QualityReportBuilder`
- `persistence.py` — `QualityPersistence` (non-blocking file write)
- `weights.py` — `ScoringWeights` (Pydantic frozen, loads YAML), `DetectionParams`
- `feed.py` — `QualityFeedAdapter(ABC)`, `InProcessQualityFeed(QualityFeedAdapter)` (DONE), `BrokerQualityFeed` stub (raises `NotImplementedError` in `start()`)

### InProcessQualityFeed (already wired, L38–49 feed.py)

Uses `QueueDrainWorker(queue=queue, quality_fn=hub.on_envelope)`. The `QueueDrainWorker` already handles the `quality_fn` callback in `_run()` (queue.py:L144). So `start()` is implemented correctly — no changes needed.

### BrokerQualityFeed stub (feed.py:L62–85)

Constructor takes `broker_url`, `stream_name`, `consumer_group`. `start()` raises `NotImplementedError`. Full implementation needed in this ticket.

### RedisStreamConsumer (src/observability/stream/consumer.py)

- `__init__(redis_url, stream_name, group_name, consumer_name)`
- `connect() -> bool` — connects + creates consumer group (BUSYGROUP-safe)
- `read_and_process(handler: Callable[[SimulationEvent], None], block_ms: int) -> int`
  - handler receives `SimulationEvent`, NOT `ObservabilityEventEnvelope`
- `close()`
- No background thread — caller must loop

**Key mismatch:** `RedisStreamConsumer.read_and_process` callback receives `SimulationEvent`; `QualityHub.on_envelope` receives `ObservabilityEventEnvelope`. Must convert via `ObservabilityEventEnvelope.from_simulation_event()` in the BrokerQualityFeed callback.

### Config files (all present)

- `config/simulation_quality/scoring_weights.yaml` — AGENCY and COMBAT sections confirmed
- `config/simulation_quality/detection_params.yaml` — time_gates confirmed: `stasis_gate_ticks: 5`, `zero_combat_by_tick: 200`, `early_extinction_before_tick: 10`, `attrition_50pct_by_tick: 100`, `attrition_90pct_by_tick: 200`
- `config/simulation_quality/grade_thresholds.yaml` — S/A/B/C/D defined

## Mechanics/Engine Constraints

- §2 (Coupling law): `src/simulation_quality/` must NOT import from `src/engine/`, `src/domains/`, `src/systems/`. Only `ObservabilityEventEnvelope` from `src/observability/events.py` and `RedisStreamConsumer` from `src/observability/stream/consumer.py` (BrokerQualityFeed only).
- §3.1 (Zero simulation impact): `on_envelope()` is called from drain worker thread, never from `kernel.tick_once()`.
- §3.2: scorer.score() < 0.1ms; report build < 50ms.
- §4.8: No numeric literals in scorer code — all deltas from `self.weights["key"]`, time gates from `self.weights.int_param("key")`.
- §8: SCORER_REGISTRY maps `event_type → list[PillarScorer]`; multiple scorers can share event_type.

## Parity Ledger Overlap

No pre-existing parity entries for `simulation_quality` module (new module). Will add entries in `infrastructure.yaml`.

## Prior Work

- E1-FOUNDATION complete: all data models in place.
- `InProcessQualityFeed.start()` already correctly implemented using `QueueDrainWorker`.

## Risks and Open Questions

1. **population_stasis detection**: "Zero non-DEFER actions population-wide for 20 ticks" — no dedicated event exists. Will detect on `defer_with_reason` events when `context.window_tag_counts[AGENCY].get("action_taken", 0) == 0` and tick > stasis_gate_ticks. Scorer maintains one-time `_pop_stasis_fired` flag to avoid double-scoring.

2. **project_cycle detection**: "Abandons and immediately restarts same project" — requires state (last project type per entity). Scorer maintains `_last_abandoned: dict[int, str]` to track abandoned projects; fires -2 if next `project_started` for same entity has same type.

3. **commitment_complete (+4)**: No `commitment_completed` event in event_types list. Will use `project_completed` with `payload.get("is_commitment", False)` flag.

4. **entropy_reward (+H×2)**: `route_family_first_use` event. H is undefined in context. Will use fixed `weights["entropy_reward"]` per event (contract says "+H×2" but H computation requires full window entropy — deferred to calibration phase).

5. **combat_dormant (-15)**: "Zero combat events by tick 200" — time-gated absence detection. Detected on any combat event after tick 200 if context shows near-zero activity. Scorer maintains `_dormant_fired` flag.

6. **tactical_variety (+1 per unique modifier)**: `combat_damage` with `payload.get("tactical_modifier")`. Scorer maintains `_seen_modifiers: set[str]` to only reward first use of each modifier.

7. **BrokerQualityFeed thread safety**: `start()` must be idempotent; uses `threading.Thread` with `daemon=True`.

## Anti-Drift Hazards

- Do not import domain modules in scorers or hub.
- SCORER_REGISTRY must be an instance attribute built from registered scorer `EVENT_TYPES`, not a hardcoded if/elif chain.
- `on_envelope()` must catch ALL scorer exceptions (not just ValueError).
- Disable check must be at top of `on_envelope()`, not in `__init__`.
