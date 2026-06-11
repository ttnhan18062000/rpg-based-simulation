---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Updated Observability / Profiling Roadmap

This replaces the previous Phase 19–27 plan.

Main changes:

```text
1. Performance profiling remains first-class.
2. Behavior observability is optional.
3. Heavy behavior processing is async or post-run.
4. Main engine hot path must stay cheap.
5. All observability features must be independently turnable on/off.
6. Observability must never mutate or slow main logic enough to affect behavior.
```

Current implementation already gives a good base:

```text
- ObservabilityMode exists and timeline storage already supports OFF/LIGHT/DEBUG style behavior.
- EventRecorder can be disabled and bounded.
- EventExtractor already produces curated events and uses dirty entity IDs when possible.
- Live publisher has backpressure/drop behavior.
- Redis stream adapter already uses a background daemon publisher thread and degraded mode when Redis is unavailable.
- Metric windows already record runtime metrics such as tick compute time, memory, event count, and governor mode.
- Historical event/metric query APIs and warehouse adapters already exist.
```

So the plan below **extends the current observability stack**, not replaces it.

---

# Phase 19 — Observability Boundary, Feature Flags, and Safety Contract

# Goal

Define the new observability architecture before implementing more behavior analytics.

This phase answers:

```text
What is hot-path?
What is async?
What is post-run?
What is existing?
What is new?
What can be disabled?
What must never affect main logic?
```

---

# Core rule

```text
Simulation correctness must be identical with observability OFF and observability ON.

Only artifacts, metrics, and diagnostics may differ.
```

---

# Target architecture

```text
Main Simulation Process
  ├── authoritative engine logic
  ├── cheap phase profiling
  ├── cheap raw event envelope creation
  ├── cheap counter increment
  └── non-blocking queue / stream publish

Async Worker / Sidecar
  ├── behavior event normalization
  ├── behavior metric aggregation
  ├── behavior timeline update
  ├── optional live behavior stream
  └── artifact / warehouse writing

Post-run Processor
  ├── episode detection
  ├── behavior pattern detection
  ├── scorecard generation
  ├── cohort analysis
  ├── run comparison
  └── insight generation
```

---

# Task 1 — Write observability boundary document

Create:

```text
docs/architecture/observability_behavior_profiling_boundary.md
```

Must define:

```text
runtime profiling
raw simulation event
behavior event
behavior timeline
behavior episode
behavior metric
behavior finding
behavior insight
scorecard
run comparison
```

## Must explicitly say

```text
Runtime profiling is for optimization.
Behavior profiling is for understanding entity behavior.
They are related, but not the same.
```

## Checklist

- [ ] Current event pipeline is preserved.
- [ ] Current entity timeline system is preserved.
- [ ] Current metric window system is preserved.
- [ ] Current warehouse/query APIs are preserved.
- [ ] Current anomaly/understanding pipeline is preserved.
- [ ] Behavior observability is a new semantic layer.
- [ ] Hot-path responsibilities are listed.
- [ ] Async worker responsibilities are listed.
- [ ] Post-run responsibilities are listed.
- [ ] Non-duplication rules are listed.

---

# Task 2 — Define observability feature flags

Add independent flags.

```text
OBS_RUNTIME_PROFILING
OBS_RAW_EVENTS
OBS_LIVE_STREAM
OBS_EVENT_RECORDER
OBS_ENTITY_TIMELINE
OBS_BEHAVIOR_NORMALIZATION
OBS_BEHAVIOR_TIMELINE
OBS_BEHAVIOR_EPISODES
OBS_BEHAVIOR_METRICS
OBS_BEHAVIOR_PATTERNS
OBS_BEHAVIOR_SCORECARDS
OBS_COHORT_ANALYSIS
OBS_RUN_COMPARISON
OBS_INSIGHT_GENERATION
OBS_WAREHOUSE_INGEST
OBS_DASHBOARD_EXPORT
```

## Important

These must be independently controlled.

Example:

```yaml
observability:
  runtime_profiling: true
  raw_events: true
  behavior_normalization: false
  behavior_episodes: false
  scorecards: false
```

This lets you keep performance profiling ON while disabling behavior analytics.

## Checklist

- [ ] Each flag has default.
- [ ] Each flag appears in run manifest.
- [ ] Each flag has OFF behavior.
- [ ] Each flag can be tested independently.
- [ ] Behavior flags do not disable runtime profiling.
- [ ] Runtime profiling can run alone.
- [ ] Full behavior analysis can be disabled without breaking current event APIs.

---

# Task 3 — Define observability modes

Use modes as presets over flags.

```text
OFF
LIGHT
NORMAL
FULL
RESEARCH
DEBUG
```

## Proposed behavior

| Mode       | Runtime profiling | Raw events    | Behavior events | Episodes          | Scorecards        | Insights              |
| ---------- | ----------------- | ------------- | --------------- | ----------------- | ----------------- | --------------------- |
| `OFF`      | optional minimal  | no            | no              | no                | no                | no                    |
| `LIGHT`    | yes               | critical only | no              | no                | no                | no                    |
| `NORMAL`   | yes               | yes           | async optional  | no/live off       | post-run optional | no                    |
| `FULL`     | yes               | yes           | async           | post-run          | post-run          | post-run              |
| `RESEARCH` | yes               | yes           | async           | post-run          | post-run          | post-run + comparison |
| `DEBUG`    | yes               | yes           | yes             | selected entities | selected entities | yes                   |

Current tests already show `EntityTimelineStore` respecting `OFF`, bounded `LIGHT`, and richer `DEBUG`, so this should extend the existing idea instead of replacing it.

## Checklist

- [ ] Modes map to flags.
- [ ] Direct flag override is allowed.
- [ ] Mode appears in manifest.
- [ ] Mode controls artifact volume.
- [ ] Mode controls hot-path work.
- [ ] Mode controls sidecar/post-run work.
- [ ] Mode does not alter main logic decisions.

---

# Task 4 — Add hot-path safety contract

Create:

```text
docs/architecture/observability_hot_path_safety_contract.md
```

## Allowed in hot path

```text
phase timing
small event envelope creation
cheap counter increment
non-blocking queue append
bounded in-memory timeline append
critical hard-law event recording
```

## Forbidden in hot path

```text
episode detection
scorecard generation
cohort analysis
run comparison
insight generation
large JSON serialization
blocking file I/O
blocking network I/O
warehouse insert
historical query
large deepcopy
full entity/world scan for observability
```

## Checklist

- [ ] Safety contract exists.
- [ ] Architecture tests enforce no hot-path imports from heavy analyzers.
- [ ] Hot-path code does not call post-run processors.
- [ ] Hot-path code does not block on stream writer.
- [ ] Hot-path code has drop/degrade behavior.

---

# Task 5 — Architecture tests

```text
tests/architecture/test_phase19_observability_boundaries.py
tests/architecture/test_phase19_hot_path_safety_contract.py
tests/unit/config/test_phase19_observability_feature_flags.py
```

Test cases:

```text
test_runtime_profiling_flag_independent_from_behavior_flags
test_behavior_flags_default_to_disabled_or_async_safe_mode
test_observability_mode_maps_to_expected_flags
test_hot_path_does_not_import_episode_detector
test_hot_path_does_not_import_scorecard_generator
test_hot_path_does_not_import_run_comparison
test_observability_boundaries_doc_exists
```

---

# Completion criteria

Phase 19 is complete when observability has a clear contract:

```text
Main engine may emit cheap facts.
Everything expensive must be async or post-run.
Every observability feature can be turned off.
```

---

# Phase 20 — Runtime Performance Profiling Lane

# Goal

Preserve and improve performance profiling.

This phase answers:

```text
How long does each phase take?
How much overhead does observability add?
Which phase is the bottleneck?
Does behavior observability hurt the tick budget?
```

This is separate from behavior semantics.

---

# Current base

The current engine already collects phase costs and tick compute information into runtime signals, and live snapshots expose runtime values such as `tick_compute_ms`, memory, and `phase_costs_ms`.

---

# Task 1 — Define `PhaseTimingRecord`

```python
@dataclass(frozen=True)
class PhaseTimingRecord:
    run_id: str
    tick: int
    phase_name: str
    duration_ns: int
    entity_count: int = 0
    update_count: int = 0
    event_count: int = 0
    provider_call_count: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    budget_status: str = "OK"
    failed: bool = False
```

## Checklist

- [ ] Records phase duration.
- [ ] Records per-phase counters.
- [ ] Records budget status.
- [ ] Records failure safely.
- [ ] Works when behavior observability is OFF.
- [ ] Does not allocate large objects.
- [ ] Does not write to disk directly.

---

# Task 2 — Implement `PhaseProfiler`

```python
class PhaseProfiler:
    def profile_phase(
        self,
        tick: int,
        phase_name: str,
    ) -> PhaseProfileScope:
        ...
```

Usage:

```python
with profiler.profile_phase(tick, "combat_resolution") as scope:
    result = combat_phase.run(...)
    scope.set_counter("entity_count", len(active_entities))
```

## Checklist

- [ ] Context manager API.
- [ ] Exception-safe.
- [ ] Minimal overhead.
- [ ] Can be disabled.
- [ ] Stores records in memory/buffer.
- [ ] Emits aggregated window metrics.
- [ ] Compatible with current runtime status.

---

# Task 3 — Extend metric windows without breaking old data

Current `MetricWindowRecord` already stores tick timing, memory, alive/active entities, event count, hard-law count, and governor mode in tests.

Add optional fields:

```text
phase_duration_ms_avg_json
phase_duration_ms_p95_json
phase_event_count_json
phase_budget_status_json
observability_overhead_ms_avg
event_emission_ms_avg
event_stream_publish_ms_avg
behavior_queue_push_ms_avg
```

## Checklist

- [ ] Existing metric window JSON still loads.
- [ ] Missing new fields default safely.
- [ ] Warehouse dry-run still works.
- [ ] Metric trend API remains compatible.
- [ ] Grafana current phase profiling remains valid.
- [ ] New fields can power more detailed profiling later.

---

# Task 4 — Add observability overhead profiler

Track:

```text
event_extraction_ms
event_recorder_ms
timeline_record_ms
stream_publish_enqueue_ms
behavior_queue_push_ms
behavior_worker_lag_ms
dropped_event_count
sampled_event_count
```

## Important

This must be reported separately:

```text
simulation phase time != observability overhead time
```

## Checklist

- [ ] Overhead metrics are separate.
- [ ] Can compare observability OFF vs ON.
- [ ] Can detect “observability caused slowdown.”
- [ ] Can trigger degradation.
- [ ] Can be included in run report.

---

# Task 5 — Tests

```text
tests/unit/observability/performance/test_phase20_phase_profiler.py
tests/unit/observability/performance/test_phase20_metric_window_extension.py
tests/integration/observability/test_phase20_phase_timing_integration.py
tests/perf/test_phase20_observability_overhead_budget.py
```

Test cases:

```text
test_phase_profiler_records_phase_duration
test_phase_profiler_records_failed_phase_duration
test_phase_profiler_disabled_has_minimal_behavior
test_metric_window_loads_old_shape
test_metric_window_serializes_phase_duration_json
test_runtime_profiling_works_when_behavior_observability_off
test_observability_overhead_is_reported_separately
```

---

# Completion criteria

Phase 20 is complete when you can answer:

```text
combat_resolution took 4.2 ms
event extraction added 0.1 ms
behavior processing added 0 ms in hot path because it was deferred
```

---

# Phase 21 — Non-Blocking Event Emission Pipeline

# Goal

Make raw event emission safe, bounded, and non-blocking.

This phase answers:

```text
How do we get facts out of the engine without slowing the engine?
```

---

# Current base

`EventExtractor` already creates curated events and uses dirty entity IDs when possible.

`EventRecorder` can be disabled and bounded.

`RedisStreamAdapter` already uses an internal queue and background daemon publisher thread, which is the correct direction for non-blocking stream output.

---

# Task 1 — Define `ObservabilityEventEnvelope`

Do not pass huge objects.

```python
@dataclass(frozen=True)
class ObservabilityEventEnvelope:
    event_id: str
    run_id: str
    tick: int
    entity_id: int | None
    event_type: str
    event_category: str
    severity: str
    source_system: str
    message: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    related_entity_ids: tuple[int, ...] = ()
```

## Checklist

- [ ] Small payload by default.
- [ ] No full `EntityState`.
- [ ] No full `AuthoritativeState`.
- [ ] No large graph payload.
- [ ] Can convert from `SimulationEvent`.
- [ ] Stable JSON serialization.
- [ ] Includes source event ID.

---

# Task 2 — Implement `BoundedObservabilityQueue`

```python
class BoundedObservabilityQueue:
    def try_push(self, event: ObservabilityEventEnvelope) -> PushResult:
        ...
```

Policies:

```text
DROP_LOW_PRIORITY
DROP_OLDEST_LOW_PRIORITY
SUMMARIZE_REPEATED
REJECT_NEW
```

Default:

```text
drop low-priority, never block
```

## Checklist

- [ ] `try_push` never blocks.
- [ ] Queue has max size.
- [ ] Critical events are protected.
- [ ] Low-priority events can be dropped.
- [ ] Dropped counts recorded.
- [ ] Backpressure status exposed.
- [ ] Push order deterministic.
- [ ] No exception escapes into simulation loop.

---

# Task 3 — Integrate queue into event recorder/stream path

Hot path:

```text
EventExtractor
  -> EventRecorder / EventEmitter
  -> BoundedObservabilityQueue
  -> return to simulation
```

Async path:

```text
queue drain
  -> file writer / stream adapter / behavior worker
```

## Checklist

- [ ] Existing `EventRecorder` path still works.
- [ ] Queue can be disabled.
- [ ] Queue can route to in-process writer.
- [ ] Queue can route to Redis stream adapter.
- [ ] Queue failure degrades observability only.
- [ ] No blocking file/network I/O in hot path.

---

# Task 4 — Worker failure isolation

If worker dies:

```text
simulation continues
observability health = DEGRADED
events may be dropped
hard-law/fatal events remain protected if possible
```

## Checklist

- [ ] Worker exception is caught.
- [ ] Failure count recorded.
- [ ] Health state updated.
- [ ] Engine tick does not fail.
- [ ] Recovery/restart possible.

---

# Task 5 — Tests

```text
tests/unit/observability/stream/test_phase21_bounded_observability_queue.py
tests/integration/observability/test_phase21_non_blocking_event_emission.py
tests/integration/observability/test_phase21_worker_failure_isolation.py
tests/perf/test_phase21_event_emission_hot_path_budget.py
```

Test cases:

```text
test_queue_try_push_never_blocks
test_queue_drops_low_priority_when_full
test_queue_keeps_hard_law_event_when_full
test_event_emission_does_not_block_tick_when_queue_full
test_worker_exception_does_not_crash_engine
test_redis_unavailable_degrades_observability_not_simulation
test_event_emission_overhead_under_budget
```

---

# Completion criteria

Phase 21 is complete when:

```text
The engine can emit events safely without waiting for file, Redis, warehouse, behavior analysis, or dashboard consumers.
```

---

# Phase 22 — Async Behavior Normalization Worker

# Goal

Convert raw events into behavior events outside the hot path.

This phase answers:

```text
What did the entity do in semantic terms?
```

But it must not run inside the main tick loop.

---

# Processing location

Default:

```text
async worker or post-run
```

Not default:

```text
inside simulation tick
```

---

# Task 1 — Define `BehaviorEvent`

```python
@dataclass(frozen=True)
class BehaviorEvent:
    run_id: str
    tick: int
    entity_id: int | None
    behavior_category: str
    behavior_family: str
    subject: str | None = None
    target_id: str | int | None = None
    source_event_ids: tuple[str, ...] = ()
    route_family: str | None = None
    action_type: str | None = None
    outcome: str | None = None
    reason: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
```

Categories:

```text
movement
combat
recovery
preparation
progression
information_seeking
resource_gathering
trade
crafting
quest
cooperation
avoidance
failure_response
world_response
idle_or_defer
unknown_behavior
```

---

# Task 2 — Implement `BehaviorEventNormalizer`

```python
class BehaviorEventNormalizer:
    def normalize_event(
        self,
        event: SimulationEvent | ObservabilityEventEnvelope,
        context: BehaviorNormalizationContext,
    ) -> tuple[BehaviorEvent, ...]:
        ...
```

Mapping examples:

| Raw event            | Behavior event                   |
| -------------------- | -------------------------------- |
| MovementEvent        | `movement/travel`                |
| CombatDamageEvent    | `combat/engage`                  |
| CombatKillEvent      | `combat/kill_or_defeat`          |
| QuestEvent           | `quest/progress`                 |
| GoldTransactionEvent | `trade/buy_sell_or_reward`       |
| project blocked      | `failure_response/blocked_route` |
| rest/sleep/eat       | `recovery/recover`               |

## Checklist

- [ ] Normalization is deterministic.
- [ ] Unknown events are skipped or mapped explicitly.
- [ ] Links source event IDs.
- [ ] Does not mutate raw event.
- [ ] Does not require full world state.
- [ ] Can run from stream consumer.
- [ ] Can run post-run from `simulation_events.jsonl`.
- [ ] Can be disabled by flag.

---

# Task 3 — Implement `BehaviorWorker`

Inputs:

```text
Redis stream
in-process queue
simulation_events.jsonl post-run
```

Outputs:

```text
behavior_events.jsonl
optional behavior metric stream
worker health
```

## Checklist

- [ ] Worker can run as sidecar.
- [ ] Worker can run post-run.
- [ ] Worker can resume from stream offset/checkpoint.
- [ ] Worker has bounded memory.
- [ ] Worker failure does not affect engine.
- [ ] Worker records lag/backlog.
- [ ] Worker can be disabled.

---

# Task 4 — Tests

```text
tests/unit/observability/behavior/test_phase22_behavior_event_model.py
tests/unit/observability/behavior/test_phase22_behavior_event_normalizer.py
tests/integration/observability/test_phase22_behavior_worker_from_jsonl.py
tests/integration/observability/test_phase22_behavior_worker_from_stream.py
```

Test cases:

```text
test_behavior_event_links_source_event_id
test_movement_event_maps_to_movement_behavior
test_combat_event_maps_to_combat_behavior
test_quest_event_maps_to_quest_behavior
test_trade_event_maps_to_trade_behavior
test_unknown_event_policy_is_deterministic
test_behavior_worker_can_process_jsonl_post_run
test_behavior_worker_failure_does_not_affect_engine
```

---

# Completion criteria

Phase 22 is complete when raw simulation events can become semantic behavior events without adding heavy work to the simulation tick.

---

# Phase 23 — Behavior Timeline and Episode Reconstruction

# Goal

Build readable entity behavior histories.

This phase answers:

```text
What did entity 12 do across the simulation?
What episodes did it go through?
Where did it fail, recover, adapt, or get stuck?
```

Default execution:

```text
post-run
```

Optional execution:

```text
async worker for selected entities only
```

---

# Current base

Current entity timelines are already bounded and support mode-based behavior; they record events for main and related entity IDs.

This phase adds a **semantic behavior timeline**, not a duplicate raw event timeline.

---

# Task 1 — Define `EntityBehaviorTimeline`

```python
@dataclass(frozen=True)
class EntityBehaviorTimeline:
    run_id: str
    entity_id: int
    events: tuple[BehaviorEvent, ...]
    dropped_count: int = 0
    start_tick: int | None = None
    end_tick: int | None = None
```

Runtime store optional:

```python
class BehaviorTimelineStore:
    def record(self, event: BehaviorEvent) -> None: ...
    def get_entity_timeline(self, entity_id: int) -> tuple[BehaviorEvent, ...]: ...
```

## Checklist

- [ ] Separate from raw `EntityTimelineStore`.
- [ ] Bounded.
- [ ] Tracks dropped count.
- [ ] Can export selected entities.
- [ ] Can be generated post-run.
- [ ] Can be disabled.

---

# Task 2 — Define `BehaviorEpisode`

```python
@dataclass(frozen=True)
class BehaviorEpisode:
    episode_id: str
    run_id: str
    entity_id: int
    episode_type: str
    start_tick: int
    end_tick: int | None
    trigger: str | None
    steps: tuple[str, ...]
    outcome: str
    source_behavior_event_ids: tuple[str, ...]
    summary: str
```

Episode types:

```text
combat_episode
recovery_episode
information_episode
crafting_episode
quest_episode
cooperation_episode
failure_response_episode
progression_episode
exploration_episode
resource_gathering_episode
```

---

# Task 3 — Implement `EpisodeDetector`

Run post-run by default.

```python
class EpisodeDetector:
    def detect(
        self,
        timeline: EntityBehaviorTimeline,
    ) -> tuple[BehaviorEpisode, ...]:
        ...
```

## Rules

```text
quest_accept + quest_progress + quest_complete = quest episode
combat_start + combat_result = combat episode
failure + route_changed = failure-response episode
info_query + info_learned = information episode
gather + craft + equip = crafting/progression episode
```

## Checklist

- [ ] Does not require exact sequence.
- [ ] Can leave open episodes.
- [ ] Can mark stuck/abandoned episodes.
- [ ] Deterministic IDs.
- [ ] Links source behavior event IDs.
- [ ] Runs post-run by default.
- [ ] Live mode restricted to selected entities.

---

# Task 4 — Artifacts

Write:

```text
behavior_timelines.json
behavior_episodes.jsonl
```

## Checklist

- [ ] Schema versioned.
- [ ] Missing files allowed.
- [ ] Large timelines compactable.
- [ ] Entity IDs indexed.
- [ ] Tick ranges indexed.
- [ ] Does not affect `simulation_events.jsonl`.

---

# Task 5 — Tests

```text
tests/unit/observability/behavior/test_phase23_behavior_timeline_store.py
tests/unit/observability/behavior/test_phase23_behavior_episode_model.py
tests/unit/observability/behavior/test_phase23_episode_detector.py
tests/integration/observability/test_phase23_behavior_timeline_episode_artifacts.py
```

Test cases:

```text
test_behavior_timeline_store_is_bounded
test_behavior_timeline_tracks_dropped_count
test_information_events_form_information_episode
test_combat_events_form_combat_episode
test_crafting_events_form_progression_episode
test_failure_then_route_change_forms_failure_response_episode
test_episode_artifacts_are_written_post_run
test_episode_detector_not_called_from_engine_tick
```

---

# Completion criteria

Phase 23 is complete when one entity can be inspected as:

```text
raw events -> behavior events -> behavior episodes
```

without running episode detection in the main simulation tick.

---

# Phase 24 — Semantic Behavior Metrics

# Goal

Add counters that explain behavior, separate from runtime metrics.

This phase answers:

```text
How often did entities fight, retreat, recover, seek information, convert rewards, cooperate, fail, or adapt?
```

---

# Rule

```text
Runtime MetricWindowRecord remains runtime/performance-focused.
BehaviorMetricWindow is semantic-behavior-focused.
```

Do not mix them.

---

# Task 1 — Define `BehaviorMetricWindow`

```python
@dataclass(frozen=True)
class BehaviorMetricWindow:
    run_id: str
    window_start_tick: int
    window_end_tick: int
    behavior_counts: Mapping[str, int]
    route_family_counts: Mapping[str, int]
    episode_counts: Mapping[str, int]
    episode_outcomes: Mapping[str, int]
    failure_counts: Mapping[str, int]
    adaptation_counts: Mapping[str, int]
    entity_activity_counts: Mapping[str, int]
```

---

# Task 2 — Implement `BehaviorMetricsAggregator`

```python
class BehaviorMetricsAggregator:
    def aggregate(
        self,
        behavior_events: Sequence[BehaviorEvent],
        episodes: Sequence[BehaviorEpisode],
        window: TickWindow,
    ) -> BehaviorMetricWindow:
        ...
```

Counters:

```text
behavior_events_total{category,family}
route_selected_total{route_family}
route_changed_total{from,to}
episode_started_total{episode_type}
episode_completed_total{episode_type,outcome}
action_failed_total{reason}
project_blocked_total{blocker_type}
retreat_total
information_sought_total
reward_converted_total
cooperation_attempted_total
```

---

# Task 3 — Add behavior quality counter slots

Support counters produced later by detectors:

```text
repeated_failure_loop_total
route_switch_after_failure_total
successful_adaptation_total
unsafe_engagement_total
retreat_when_low_hp_total
information_sought_for_unknown_total
hidden_knowledge_suspected_total
stagnant_entity_total
```

---

# Task 4 — Store behavior metrics separately

Artifact:

```text
behavior_metric_windows.jsonl
```

Optional warehouse table:

```text
behavior_metric_windows
```

## Checklist

- [ ] Does not modify current `metric_windows`.
- [ ] Can join by `run_id` and tick window.
- [ ] Missing behavior metrics allowed.
- [ ] Old runs still load.
- [ ] Behavior metrics can be generated post-run.
- [ ] Behavior metrics can be generated by sidecar worker if enabled.

---

# Task 5 — Tests

```text
tests/unit/observability/behavior/test_phase24_behavior_metric_window.py
tests/unit/observability/behavior/test_phase24_behavior_metrics_aggregator.py
tests/integration/observability/test_phase24_behavior_metric_artifacts.py
tests/unit/observability/warehouse/test_phase24_behavior_metric_ingestion.py
```

Test cases:

```text
test_behavior_counts_aggregate_by_category_and_family
test_route_family_counts_aggregate
test_episode_outcomes_aggregate
test_behavior_metrics_do_not_modify_runtime_metric_windows
test_old_run_without_behavior_metrics_still_loads
test_behavior_metric_window_artifact_written
```

---

# Completion criteria

Phase 24 is complete when you can report:

```text
runtime:
  combat phase p95 = 4.8 ms

behavior:
  combat episodes = 37
  retreats = 9
  repeated failure loops = 2
```

as separate lanes.

---

# Phase 25 — Pattern Detectors and Behavior Insights

# Goal

Detect behavior problems and behavior improvements.

This phase answers:

```text
What meaningful behavior pattern happened?
Was it good, bad, or suspicious?
```

Run location:

```text
post-run by default
```

Do not run these detectors in the tick loop.

---

# Existing base

The current observability system already has post-run rule/pipeline concepts that load run artifacts, events, metric windows, and produce reports.

So behavior detectors should plug into the existing post-run understanding/reporting path.

---

# Task 1 — Define `BehaviorFinding`

```python
@dataclass(frozen=True)
class BehaviorFinding:
    finding_id: str
    finding_type: str
    severity: str
    summary: str
    affected_entities: tuple[int, ...]
    tick_range: tuple[int, int] | None
    evidence_event_ids: tuple[str, ...]
    evidence_episode_ids: tuple[str, ...]
    suggested_systems: tuple[str, ...]
    recommendation: str
```

Finding types:

```text
repeated_failure_loop
hidden_knowledge_suspicion
route_convergence
over_cautious_collapse
unsafe_engagement_pattern
no_adaptation_after_failure
behavior_noise_without_impact
successful_adaptation
route_diversity_improved
```

---

# Task 2 — Implement detectors

```text
RepeatedFailureLoopDetector
BehaviorChangeProofDetector
HiddenKnowledgeSuspicionDetector
RouteConvergenceDetector
StagnationDetector
UnsafeEngagementDetector
NoImpactCognitionDetector
```

## Checklist

- [ ] Use behavior events/episodes/metrics.
- [ ] Evidence IDs included.
- [ ] Deterministic.
- [ ] Missing artifacts skip gracefully.
- [ ] No hidden world truth unless explicitly available as debug evidence.
- [ ] No main-engine dependency.
- [ ] Post-run only by default.

---

# Task 3 — Implement `BehaviorInsightGenerator`

Example insight:

```text
Cautious entities are over-deferring.

Evidence:
- 72% of cautious cohort episodes ended with defer.
- progression rate is low.
- repeated recovery episodes occurred without new injury.

Suggested inspection:
- caution bias
- safe route generation
- recovery readiness thresholds
```

## Checklist

- [ ] Rule-based first.
- [ ] Evidence-backed.
- [ ] Bounded language.
- [ ] Links to findings.
- [ ] Links to affected entities.
- [ ] Does not duplicate story generation.
- [ ] Can be added to existing run report.

---

# Task 4 — Extend post-run analysis pipeline

Inputs:

```text
behavior_events
behavior_episodes
behavior_metric_windows
```

Outputs:

```text
behavior_findings.jsonl
behavior_insights.json
behavior_section in run_report.md
```

## Checklist

- [ ] Existing analyzers still run.
- [ ] Behavior analysis skipped if artifacts missing.
- [ ] Behavior findings appear in report.
- [ ] Behavior insights appear in report.
- [ ] No required live dependency.

---

# Task 5 — Tests

```text
tests/unit/observability/behavior/test_phase25_behavior_pattern_detectors.py
tests/unit/observability/behavior/test_phase25_behavior_insight_generator.py
tests/integration/observability/test_phase25_postrun_behavior_analysis.py
```

Test cases:

```text
test_repeated_failure_loop_detected
test_behavior_change_proof_detected
test_hidden_knowledge_suspicion_detected
test_route_convergence_detected
test_stagnation_detected
test_behavior_insight_contains_evidence_and_recommendation
test_behavior_analysis_skips_when_artifacts_missing
test_behavior_analysis_never_runs_inside_tick
```

---

# Completion criteria

Phase 25 is complete when post-run analysis can say:

```text
Entities repeated blocked crafting route because missing-material blocker did not trigger information-seeking.
```

not only:

```text
Quest stalled.
```

---

# Phase 26 — Behavior Scorecards, Cohort Analysis, and Run Comparison

# Goal

Prove whether an enrichment feature changed behavior and whether the cost was acceptable.

This phase answers:

```text
Did the new cognition/aspect feature improve behavior?
Which cohorts changed?
What runtime overhead did it add?
```

Run location:

```text
post-run only
```

---

# Task 1 — Define entity behavior scorecard

```python
@dataclass(frozen=True)
class EntityBehaviorScorecard:
    run_id: str
    entity_id: int
    ticks_observed: int
    route_families_used: Mapping[str, int]
    behavior_categories_used: Mapping[str, int]
    episodes_started: int
    episodes_completed: int
    episodes_failed: int
    repeated_failure_count: int
    adaptation_proof_count: int
    stagnation_score: float
    progression_score: float
    cooperation_score: float
    information_usage_score: float
    behavior_diversity_score: float
    verdict: str
```

---

# Task 2 — Define run behavior scorecard

```python
@dataclass(frozen=True)
class RunBehaviorScorecard:
    run_id: str
    entity_count: int
    route_diversity_score: float
    action_entropy: float
    episode_success_rate: float
    stagnation_ratio: float
    repeated_failure_loop_count: int
    adaptation_proof_count: int
    hidden_knowledge_suspicion_count: int
    cognition_impact_score: float | None
    observability_overhead_ms_avg: float | None
    runtime_cost_delta_percent: float | None
    verdict: str
```

---

# Task 3 — Implement cohort analyzer

Cohorts:

```text
class
trait
level band
starting region
feature exposure
lost combat before
heard rumor
used information
has causal memory
```

Metrics:

```text
route distribution
episode success rate
survival/progression
failure loops
adaptation proofs
information usage
cooperation usage
runtime cost per cohort if available
```

---

# Task 4 — Implement run comparison

Compare:

```text
baseline
feature OFF
feature SHADOW
feature ON
full cognition stack
```

Comparison dimensions:

```text
route diversity
action distribution
episode outcomes
stagnation ratio
repeated failure loops
adaptation proofs
survival/failure/recovery trends
runtime overhead
observability overhead
```

## Important verdict rule

Do not claim improvement if only event volume increased.

Example bad:

```text
more cognition events -> feature helped
```

Correct:

```text
more cognition events + fewer repeated failures + more adaptation proofs + acceptable runtime cost -> feature likely helped
```

---

# Task 5 — Artifacts

```text
entity_behavior_scorecards.jsonl
run_behavior_scorecard.json
cohort_behavior_report.json
run_behavior_comparison.json
```

---

# Task 6 — Tests

```text
tests/unit/observability/behavior/test_phase26_entity_behavior_scorecard.py
tests/unit/observability/behavior/test_phase26_run_behavior_scorecard.py
tests/unit/observability/behavior/test_phase26_cohort_analyzer.py
tests/unit/observability/behavior/test_phase26_run_behavior_comparison.py
tests/integration/observability/test_phase26_behavior_scorecard_artifacts.py
```

Test cases:

```text
test_entity_scorecard_counts_route_families
test_entity_scorecard_detects_stagnation
test_run_scorecard_computes_route_diversity
test_cohort_analyzer_groups_by_trait
test_run_comparison_reports_behavior_delta
test_run_comparison_reports_performance_delta
test_comparison_does_not_claim_improvement_when_only_event_volume_increased
```

---

# Completion criteria

Phase 26 is complete when you can answer:

```text
The new feature reduced repeated failure loops by 40%, increased route diversity, and added 3% runtime overhead.
```

---

# Phase 27 — Storage, Query API, and Dashboard Integration

# Goal

Expose behavior observability through the current data examination stack.

Do not create a separate isolated tool unless necessary.

---

# Current base

Current APIs already support run/event/anomaly/entity timeline/metric trend querying in tests.

The current UI already has historical search and entity timeline querying.

Warehouse adapters already query events, anomalies, metric windows, and violations.

---

# Task 1 — Extend artifact repository

Add artifact paths:

```text
behavior_events
behavior_timelines
behavior_episodes
behavior_metric_windows
entity_behavior_scorecards
run_behavior_scorecard
behavior_findings
behavior_insights
cohort_behavior_report
run_behavior_comparison
```

## Checklist

- [ ] Schema versioned.
- [ ] Missing behavior artifacts allowed.
- [ ] Existing run manifests still load.
- [ ] Compact workflow can include behavior files.
- [ ] Register workflow can include behavior files.
- [ ] No existing artifact path is renamed.

---

# Task 2 — Extend warehouse schema

Optional tables:

```text
behavior_events
behavior_episodes
behavior_metric_windows
entity_behavior_scorecards
run_behavior_scorecards
behavior_findings
behavior_insights
cohort_reports
behavior_comparisons
```

## Checklist

- [ ] Local adapter supports dry-run.
- [ ] ClickHouse adapter supports optional tables.
- [ ] Null adapter no-op remains no-op.
- [ ] Old runs ingest without behavior tables.
- [ ] Queries are paginated.
- [ ] Missing tables degrade gracefully.

---

# Task 3 — Add query APIs

Endpoints:

```text
GET /api/v1/behavior/events
GET /api/v1/behavior/entities/{entity_id}/timeline
GET /api/v1/behavior/entities/{entity_id}/episodes
GET /api/v1/behavior/runs/{run_id}/scorecard
GET /api/v1/behavior/runs/{run_id}/insights
GET /api/v1/behavior/runs/{run_id}/cohorts
GET /api/v1/behavior/compare
```

## Checklist

- [ ] Uses existing API style.
- [ ] Sanitizes identifiers like existing routes.
- [ ] Supports run_id/entity_id/tick range/category filters.
- [ ] Returns empty data when behavior artifacts missing.
- [ ] Does not expose raw file paths.
- [ ] Does not require behavior observability to be enabled for old runs.

---

# Task 4 — Add dashboard panels

Add to current dashboard style:

```text
Behavior Overview
Route Family Distribution
Episode Outcomes
Stagnation / Repeated Failure
Adaptation Proofs
Cohort Comparison
Behavior vs Performance Cost
Top Behavior Insights
```

Keep existing panels:

```text
phase profiling
tick rate
memory
health
event logs
raw event search
```

Current dashboard already has simulation pulse, economy, tactical, admin/performance, logs, and raw event stream sections, so behavior panels should be added beside those, not replace them.

---

# Task 5 — Tests

```text
tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py
tests/unit/observability/warehouse/test_phase27_behavior_warehouse_schema.py
tests/api/test_phase27_behavior_query_api.py
tests/integration/observability/test_phase27_behavior_dataset_builder.py
```

Test cases:

```text
test_behavior_artifact_paths_resolve
test_old_run_without_behavior_artifacts_still_loads
test_behavior_event_query_filters_by_entity_and_category
test_behavior_timeline_query_returns_ordered_events
test_behavior_scorecard_api_returns_empty_for_missing_artifact
test_dataset_builder_includes_behavior_tables_when_present
```

---

# Completion criteria

Phase 27 is complete when behavior data is accessible through:

```text
artifacts
warehouse
API
dashboard
reports
```

without replacing current observability.

---

# Phase 28 — Observability Budget, Sampling, Degradation, and Rollout Gate

# Goal

Guarantee observability does not harm the engine.

This phase answers:

```text
Can observability safely lose detail instead of slowing or breaking simulation?
```

---

# Task 1 — Define `ObservabilityBudgetProfile`

```python
@dataclass(frozen=True)
class ObservabilityBudgetProfile:
    max_hot_path_overhead_percent: float
    max_event_emit_ns_per_event: int
    max_raw_events_per_tick: int
    max_behavior_events_per_tick: int
    max_event_queue_size: int
    max_timeline_events_per_entity: int
    max_open_episodes_per_entity: int
    max_live_publish_ms_per_tick: float
    max_postrun_analysis_seconds: float
```

---

# Task 2 — Define sampling policy

```text
always keep hard-law violations
always keep fatal errors
always keep selected debug entities
always keep explicit research markers
sample low-severity repeated events
summarize repeated behavior
drop low-priority events under pressure
```

## Checklist

- [ ] Critical events are never dropped.
- [ ] Low-priority events can be dropped.
- [ ] Dropped count recorded.
- [ ] Summarized count recorded.
- [ ] Sampling deterministic.
- [ ] Sampling policy appears in manifest.

---

# Task 3 — Define degradation levels

```text
NORMAL
CONSTRAINED
DEGRADED
CRITICAL_OBS_ONLY
```

## NORMAL

```text
configured observability runs
```

## CONSTRAINED

```text
sample low-priority events
disable live episode processing
keep runtime profiling
```

## DEGRADED

```text
raw critical events only
behavior timeline disabled
behavior worker optional
keep phase timing
```

## CRITICAL_OBS_ONLY

```text
hard-law events
fatal errors
minimal phase timing
```

Current live status already exposes governor/health-style state, so this should reuse that model rather than invent a separate status type.

---

# Task 4 — Add rollout gate

Create:

```text
scripts/behavior_observability_rollout_gate.py
```

Checks:

```text
observability OFF and ON produce same authoritative hash
runtime profiling works with behavior features OFF
queue full does not block tick
worker failure does not crash engine
post-run analysis can be deferred
behavior artifacts are optional
overhead under budget
critical events not dropped
```

---

# Task 5 — Tests

```text
tests/unit/observability/budget/test_phase28_observability_budget_profile.py
tests/unit/observability/budget/test_phase28_sampling_policy.py
tests/integration/observability/test_phase28_observability_degradation.py
tests/integration/observability/test_phase28_observability_determinism.py
tests/perf/test_phase28_behavior_observability_overhead.py
tests/certification/test_phase28_behavior_observability_rollout_gate.py
```

Test cases:

```text
test_critical_event_is_never_dropped
test_low_priority_events_are_sampled_under_pressure
test_sampling_is_deterministic
test_queue_full_does_not_block_tick
test_worker_failure_degrades_observability_not_engine
test_observability_off_and_full_have_same_authoritative_hash
test_runtime_profiling_works_when_behavior_flags_off
test_postrun_processing_can_be_deferred
test_rollout_gate_rejects_excessive_observability_overhead
```

---

# Completion criteria

Phase 28 is complete when:

```text
Observability can be turned on for research,
turned off for production,
degraded under pressure,
and never changes simulation correctness.
```

---

# Updated final roadmap

| Phase | Name                               | Hot path?           | Main purpose                          |
| ----: | ---------------------------------- | ------------------- | ------------------------------------- |
|    19 | Boundary / flags / safety contract | light only          | Define ownership and turnability      |
|    20 | Runtime performance profiling      | yes, cheap          | Preserve phase/tick optimization data |
|    21 | Non-blocking event emission        | yes, cheap          | Emit facts safely                     |
|    22 | Async behavior normalization       | no by default       | Convert raw events to behavior events |
|    23 | Timelines / episodes               | post-run by default | Reconstruct entity behavior           |
|    24 | Semantic behavior metrics          | async/post-run      | Count behavior meaningfully           |
|    25 | Pattern detectors / insights       | post-run            | Find behavior problems/improvements   |
|    26 | Scorecards / cohorts / comparison  | post-run            | Prove feature impact and cost         |
|    27 | Storage / API / dashboard          | mostly outside tick | Expose behavior data                  |
|    28 | Budget / sampling / rollout gate   | light guard         | Keep observability safe               |

---

# Final architecture after update

```text
Simulation Tick
  ├── authoritative logic
  ├── PhaseProfiler
  ├── EventExtractor
  ├── BoundedObservabilityQueue.try_push()
  └── continue immediately

Async / Sidecar
  ├── drain queue / stream
  ├── write raw events
  ├── normalize BehaviorEvent
  ├── aggregate lightweight behavior metrics
  └── persist artifacts / warehouse

Post-run
  ├── build timelines
  ├── detect episodes
  ├── detect patterns
  ├── generate scorecards
  ├── compare runs
  └── generate insights
```

---

# Implementation priority

Do this order:

```text
1. Phase 19 — boundary, flags, hot-path contract
2. Phase 20 — runtime profiling extension
3. Phase 21 — non-blocking event emission
4. Phase 28 initial guard — queue full, worker failure, OFF/ON determinism
5. Phase 22 — async behavior normalization
6. Phase 24 — behavior metrics
7. Phase 23 — post-run timelines and episodes
8. Phase 25 — behavior findings and insights
9. Phase 26 — scorecards, cohorts, comparison
10. Phase 27 — API/dashboard/warehouse
11. Phase 28 full rollout gate
```

Reason:

```text
First make observability safe.
Then make it cheap.
Then make it useful.
Then expose it.
Then certify it.
```

---

# Non-negotiable rule

```text
Observability can drop detail.
Observability can defer work.
Observability can degrade itself.
Observability can be disabled.

But observability must not slow, block, mutate, or change the main simulation logic.
```
