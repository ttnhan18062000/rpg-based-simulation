---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, scoring, pillars, architecture, contract, major-feature]
---

# Simulation Quality Scoring — Contract & Design Reference

**Module path:** `src/simulation_quality/`  
**Ticket:** TCK-20260628-SIMQ-EPIC (epic) — child tickets listed in §13  
**Investigation source:** `docs/plans/sim_quality_scoring_module.md`  
**Last updated:** 2026-06-28

**See also:** `docs/simulation_quality/extension_points.md` — a single map of every axis this
system can be extended along (world breadth/depth, event vocabulary, pillar/scenario registry,
tuning config, temporal depth, feed mode, anchor granularity, the engine-correctness bridge),
each with current real numbers and the extension mechanism.

---

## 1. Purpose & Scope

The engine produces simulation output every tick. No automated system currently answers
the question: *is this a good run?* — subsystem by subsystem, in real time, with a
drill-down path when something is wrong.

This module scores **simulation health**: whether each subsystem is alive, balanced, and
producing emergent output. It does not score correctness (that is `hard_law_monitor`),
performance (that is `perf_baseline_policy.md`), or content quality (human judgment).

**Three goals:**

1. **Automated quality visibility** — a developer can run any scenario and immediately
   see which subsystems are healthy and which are degenerate, without manually auditing
   events.

2. **Regression detection** — grade thresholds catch when a code change silently kills
   a subsystem (e.g., a refactor disables the economy loop without a test catching it).

3. **Balance and tuning support** — concrete signal per pillar replaces manual
   observation when calibrating world configs, spawn rates, faction balance, etc.

**What this module is NOT:**

| System | Why it's different |
|---|---|
| `RunBehaviorScorecard` (`src/observability/behavior/`) | Post-run episode aggregates; behavioral diversity metrics; not per-subsystem or incremental |
| `CampaignScorecardEvaluator` (`src/domains/campaigns/`) | Binary pass/fail semantic verdict from arc types; not graduated health |
| `AnalyzerQualityReporter` (`src/observability/understanding/quality/`) | Measures the analyzer's own accuracy (false positive rates); not simulation health |
| `hard_law_monitor` | Correctness: binary contract violation detection; a run can pass all hard laws and score F on Economy |
| Audit dimensions D01–D19 | Manual, human-authored, one-time findings; this module automates the same question per run |

---

## 2. Architectural Position

```
┌─────────────────────────────────────────────────────────────────┐
│                      Simulation Loop                            │
│  Kernel.tick_once()                                             │
│  → pipeline.py:refine()           (PP-01 … PP-37)              │
│  → world_dynamics.py:resolve()    (WD-01 … WD-15)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ emits SimulationEvent
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Observability Layer                           │
│  EventBus → ObservabilityEventEnvelope                          │
│  → BoundedObservabilityQueue → QueueDrainWorker                 │
│  → simulation_events.jsonl  │  replay chunks  │  telemetry bridge  │
└──────────┬──────────────────────────────────┬────────────────────┘
           │ INPROCESS mode                   │ BROKER mode
           │ drain callback                   │ RedisStreamConsumer
           ▼                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    QualityFeedAdapter (ABC)                      │
│   InProcessQualityFeed          BrokerQualityFeed                │
│   (drain worker thread)         (separate process / thread)      │
└───────────────────────────┬──────────────────────────────────────┘
                            │ ObservabilityEventEnvelope
                            ▼ [non-blocking in both modes]
┌─────────────────────────────────────────────────────────────────┐
│             Simulation Quality Layer  [THIS MODULE]             │
│                                                                 │
│   QualityHub  (feed-mode-agnostic)                              │
│   ├── ScoringWeights (loaded from config/simulation_quality/)  │
│   ├── SCORER_REGISTRY: {event_type → [PillarScorer]}           │
│   ├── 10 × PillarScorer.score(envelope, context, weights)      │
│   ├── 10 × PillarAccumulator (raw_score, window, worst_events) │
│   │        + event_id deduplication (broker at-least-once safe) │
│   ├── Persistence → quality_scores.jsonl                        │
│   └── QualityReport.build() → quality_report.json              │
│                                                                 │
│   Read-only query API (current run + post-run)                  │
│   GET /api/v1/quality/*                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ read-only signals (future, §12)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Analysis / Post-Run Layer (existing)               │
│  RunBehaviorScorecard  │  CampaignScorecard  │  audit tooling   │
└─────────────────────────────────────────────────────────────────┘
```

**Coupling law:** `src/simulation_quality/` must never import from `src/engine/`,
`src/domains/`, `src/systems/`, or any domain-internal module. The only permitted
inputs are `ObservabilityEventEnvelope` from `src/observability/events.py` and
the `ScoringContext` type defined within this module. Domain internals are invisible.

---

## 3. Performance Contract

This section is non-negotiable. Every implementation decision must respect these
constraints. Violations block merge.

### 3.1 Zero Simulation Impact

The simulation loop must never block, wait, or slow down for quality scoring — in either feed mode.

- **INPROCESS mode:** `QualityHub.on_envelope()` is called from the `BoundedObservabilityQueue`
  drain worker thread — not from inside `kernel.tick_once()`. The simulation produces events
  and moves on.
- **BROKER mode:** `QualityHub.on_envelope()` is called from the `BrokerQualityFeed` consumer
  thread or subprocess. The simulation has zero awareness of the quality layer.
- In both modes, if scoring is slower than the event production rate, score records are
  dropped. **Dropped records are logged at WARNING level but never cause an exception.**

### 3.2 Overhead Budget

| Metric | Limit | Enforcement |
|---|---|---|
| CPU overhead per drain event | < 0.1 ms per event in `scorer.score()` | Performance test in E6 |
| Memory: worst_events list | Max 100 records per pillar | `PillarAccumulator.MAX_WORST_EVENTS = 100` |
| Memory: window buffer | Max W=200 records per pillar | `deque(maxlen=200)` |
| Memory: quality_scores.jsonl | Streamed to disk; not held in memory | Persistence layer §8 |
| quality_report.json build time | < 50 ms for full report | Regression test in E6 |

### 3.3 Disable Mechanism

Set `QUALITY_SCORING_DISABLED=1` environment variable to bypass the `QualityHub`
entirely. When disabled:
- No `QualityHub` is instantiated
- No `quality_scores.jsonl` is written
- REST endpoints return `{"enabled": false, "message": "QUALITY_SCORING_DISABLED=1"}`
- Simulation behavior is bit-identical to a run without the module present

This is the production safety valve. Scoring is never a prerequisite for the simulation.

### 3.4 Dual Feed Mode

The module supports two feed modes selected at startup. The `QualityHub` and all scorers
are identical in both modes — only the event delivery mechanism changes.

#### Mode selection

Set `QUALITY_FEED_MODE` environment variable (default: `inprocess`):

| Value | Class | Delivery mechanism |
|---|---|---|
| `inprocess` | `InProcessQualityFeed` | Drain callback in `BoundedObservabilityQueue` worker thread |
| `broker` | `BrokerQualityFeed` | `RedisStreamConsumer` — separate thread or subprocess |

Additional env vars for broker mode:

| Variable | Default | Purpose |
|---|---|---|
| `QUALITY_BROKER_URL` | `ObservabilityConfig.get_redis_url()` (`redis://localhost:6379/0` when no `SIM_REDIS_URL`/`RPG_REDIS_URL` override) | Redis connection URL |
| `QUALITY_STREAM_NAME` | `ObservabilityConfig.get_stream_name()` (`simulation:events` when no `SIM_STREAM_NAME`/`RPG_STREAM_NAME` override) | Redis stream key to consume from |
| `QUALITY_CONSUMER_GROUP` | `quality_scoring` | Consumer group name |

#### `QualityFeedAdapter` interface

```python
class QualityFeedAdapter(ABC):
    def start(self, hub: QualityHub) -> None: ...  # begin delivering envelopes to hub.on_envelope()
    def stop(self) -> None: ...                    # graceful shutdown
    def health(self) -> dict: ...                  # status, lag, dropped_count
```

`InProcessQualityFeed.start()` stores the `QualityHub` reference for health/stop reporting;
the actual envelope delivery is wired by the kernel injecting `quality_fn=hub.on_envelope`
into `EventRecorder`'s `QueueDrainWorker` at kernel init time (`kernel.py`).
`BrokerQualityFeed.start()` instantiates a `RedisStreamConsumer` (from `src/observability/stream/consumer.py`)
and calls `hub.on_envelope()` from its callback. No other code changes — `RedisStreamConsumer`
is already built (M36).

#### Idempotency (broker at-least-once delivery)

Redis Streams delivers at-least-once on consumer group retry. `PillarAccumulator.add()`
tracks a `_seen_event_ids: set[str]` and silently drops duplicate `event_id` values.
This is a no-op cost in INPROCESS mode (no duplicates possible) and required correctness
in BROKER mode.

#### Separate process (BROKER mode)

`BrokerQualityFeed` can run the `RedisStreamConsumer` in a dedicated subprocess via
`src/simulation_quality/worker.py`. This fully isolates quality scoring memory and CPU
from the simulation process. The subprocess connects to Redis independently; the
simulation process has no reference to it.

```
[simulation process]           [quality worker process]
  engine + observability  →  Redis Stream  →  BrokerQualityFeed
                                               → QualityHub
                                               → quality_scores.jsonl
                                               → quality_report.json
                                               → GET /api/v1/quality/*
```

The REST API in BROKER mode is served from the worker process on a configurable port
(`QUALITY_WORKER_PORT`, default: `8082`).

---

## 4. Score Model

### 4.1 ScoreRecord

The atomic unit of scoring. Immutable, typed, serializable.

```python
@dataclass(frozen=True)
class ScoreRecord:
    tick: int               # simulation tick when the source event occurred
    event_id: str           # links back to ObservabilityEventEnvelope.event_id
    pillar: PillarId        # which pillar scored this event
    delta: float            # positive = healthy signal; negative = degenerate signal
    reason: str             # human-readable explanation (not stored state — traceability only)
    event_type: str         # original event_type for cross-reference with simulation_events.jsonl
    entity_id: int | None   # source entity if applicable
    region_id: str | None   # source region if applicable
    tags: tuple[str, ...]   # diagnostic tags e.g. ("stagnation", "zero_harvest", "loop_detected")
```

### 4.2 ScoringContext

Read-only context passed to every `scorer.score()` call. Scorers must not mutate it.

```python
@dataclass(frozen=True)
class ScoringContext:
    run_id: str
    current_tick: int
    entity_count: int                         # live entity count at last tick
    pillar_scores: Mapping[PillarId, float]   # read-only snapshot of accumulated raw scores
    pillar_event_counts: Mapping[PillarId, int]
    window_tag_counts: Mapping[PillarId, Mapping[str, int]]  # tag frequency in current window
```

Scorers may use `context.current_tick` to apply time-gated penalties (e.g., "zero
harvesting is only penalized after tick 100").

### 4.3 PillarAccumulator State

Per pillar, maintained by `QualityHub`:

```
raw_score:           float        — running sum of all deltas
event_count:         int          — total scored events
negative_count:      int          — events with delta < 0
last_event_tick:     int          — tick of the most recent scored event (0 if no events)
worst_events:        list[ScoreRecord]  — top MAX_WORST_EVENTS by abs(delta), negative only
window_buffer:       deque[ScoreRecord] — sliding window (maxlen=W=200)
loop_flags:          set[str]     — active loop detection tags
```

`last_event_tick` is updated on every non-duplicate `add()` call as
`self.last_event_tick = max(self.last_event_tick, record.tick)`. It is exposed via
`snapshot()` and used only at report-build time. It never affects loop detection or
simulation behavior.

### 4.4 Normalized Score

```python
floor_tick      = max(1, current_tick // 4)
effective_denom = max(floor_tick, last_event_tick)  if last_event_tick > 0
                  else current_tick
normalized_score = raw_score / effective_denom

# last_event_tick: tick of the most recent scored event for this pillar
#                  (tracked by PillarAccumulator; 0 if no events ever fired)
# floor_tick:      25% of run duration — prevents S-grade inflation from
#                  initialization-burst pillars (e.g., AGENCY events all at tick 1)
# Falls back to current_tick only for pillars with zero scored events (raw_score always 0.0)
```

This is the value used for grade assignment and cross-run comparison.
Raw score is retained for full transparency.

**Rationale (TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY):** The original formula divided by
`current_tick`, which caused grade decay for pillars whose events completed early in the
run (H2 artifact: same 127.0 COMBAT raw_score earned A at 200t but B at 401t). The fix
caps the denominator at `last_event_tick` so idle post-event ticks do not dilute the
grade. The floor (`current_tick // 4`) prevents the inverse pathology: pillars with
initialization bursts at tick 1 would otherwise receive S grades (40/1 = 40.0 >> S
threshold of 2.0). Example: AGENCY fires all events at tick 1 in simq_routing_test;
floor=100 at 401t produces norm=40/100=0.40 → B, which is the correct pre-fix grade
and appropriate for initialization-burst behavior. The floor value of 4 (25% of run
duration) is architectural — it represents the minimum activity window required to
sustain a meaningful grade. Any change to this divisor must update both this section
and `src/simulation_quality/quality_report.py` simultaneously.

### 4.5 Health Grades

| Grade | Normalized Score Range | Meaning |
|---|---|---|
| **S** | > +2.0 | Exceptional — subsystem producing rich, diverse output well above baseline |
| **A** | +0.5 to +2.0 | Healthy — subsystem functioning as designed |
| **B** | 0.0 to +0.5 | Adequate — subsystem active but limited output |
| **C** | −0.5 to 0.0 | Concerning — subsystem underperforming; investigate |
| **D** | −1.0 to −0.5 | Degraded — significant degenerate signals present |
| **F** | < −1.0 | Degenerate — subsystem broken, absent, or in permanent failure mode |

**Threshold calibration status (2026-06-30 — re-calibrated, TCK-20260630-SIMQ-RECALIBRATE):**
Thresholds are validated against real simulation data and loaded from
`config/simulation_quality/grade_thresholds.yaml`. They **must not be hardcoded inline**
in any scorer or accumulator.

Re-calibration ran `tools/calibrate_simq.py` across 3 seeds (42, 137, 999) × 200 ticks
on `sandbox_world` (10 entities) with the kernel wiring fix from TCK-20260630-SIMQ-WIRE-KERNEL
in place. Observed normalized scores:

| Pillar | Events (range) | Norm score (range) | Grade |
|---|---|---|---|
| COMBAT | 2–13 | +0.04 → +0.46 | B |
| NARRATIVE | 16–22 | +1.08 → +1.40 | A |
| PROGRESSION | 0–4 | 0.00 → +0.21 | B/C |
| Others (7 pillars) | 0 | 0.00 | C |

AGENCY, COGNITION, ECONOMY, FACTION, INFORMATION, SOCIAL, WORLD pillars produce zero
signal on `sandbox_world` because P0-A (`ENABLE_ADVENTURE_ROUTING`) defaults OFF. Per-pillar
threshold tuning for these pillars is deferred to the post-P0-A calibration pass.

Threshold values (S: 2.0, A: 0.5, B: 0.0, C: −0.5, D: −1.0) are validated — NARRATIVE
correctly grades A, COMBAT correctly grades B. No changes were required from the initial
estimates.

### 4.6 Overall Quality Score

```
overall_score = sum(pillar_normalized_score × pillar_weight for each pillar)
              / sum(all weights)
```

Default weight = 1.0 for all pillars. Weights are configurable via `QualityProfile`
(scenario-specific). A combat-focused world scenario can double the Combat pillar weight.

### 4.7 Loop and Stagnation Detection

Each `PillarAccumulator` maintains a sliding window (default: 200 scored events). Loop detection fires when:

```
tag_frequency(tag, window) / window_size > LOOP_THRESHOLD   (default: 0.70)
```

When a loop is detected for a tag:
- The tag is added to `loop_flags` for that pillar
- Subsequent `ScoreRecord` entries for that pillar include the tag `"loop_detected:{tag}"`
- The `QualityReport` marks the pillar with `loop_detected: true`
- An alert appears in `GET /api/v1/quality/alerts`

Loop detection does **not** add an extra score penalty — the underlying negative deltas
already drive the score down. Loop flags are purely diagnostic.

**Important:** The window counts **scored events**, not ticks. At typical 200-tick event densities
(47–287 scored events observed across sandbox_world and dungeon_crawl), the window rarely fills —
meaning loop detection remains dormant in most calibration runs. This is expected and correct;
loop flags are a real-time signal for long running sessions, not a short-run calibration metric.

**CLI sweep tooling:** `tools/calibrate_simq.py` accepts `--window-size INT` and
`--loop-threshold FLOAT` to override these values for a single run without mutating
`detection_params.yaml`. These flags are intended for diagnostic sweeps only.

**Confirmed values (TCK-20260701-SIMQ-LOOP-WINDOW-TUNE, 2026-07-02):**
Sweep across window_size ∈ {100, 150, 200, 300} on sandbox_world (47 events/200t) and
dungeon_crawl (287 events/200t) at seed 42 showed zero grade change across all window sizes.
Decision: **200/0.70 confirmed correct, no change.** The low event density means the window
never fills in 200-tick runs; the threshold is irrelevant until event volume is substantially
higher (≥ window_size events per pillar per run).

### 4.8 Data-Driven Scoring Weights

**Scoring deltas, grade thresholds, and time-gate values are stored in config files —
not hardcoded in scorer Python code.** This is required so that calibration (E7-CALIBRATE)
is a config-file edit, not a code change, and so that scenario profiles can override
weights without touching scorer logic.

#### What lives in data files

```
config/simulation_quality/
├── scoring_weights.yaml     # per-pillar, per-rule delta magnitudes
├── grade_thresholds.yaml    # normalized score boundaries for S/A/B/C/D/F
├── detection_params.yaml    # loop detection threshold (0.70), window size (200),
│                            # time-gate tick values, MAX_WORST_EVENTS, etc.
└── profiles/
    ├── default.yaml         # pillar weight overrides = all 1.0
    ├── dungeon_crawl.yaml   # COMBAT: 2.0, FACTION: 0.1, etc.
    └── urban_political.yaml # FACTION: 1.5, ECONOMY: 1.5, etc.
```

Example `scoring_weights.yaml` excerpt:
```yaml
AGENCY:
  action_taken: +1.0
  route_novelty: +3.0
  commitment_complete: +4.0
  defer_idle: -1.0
  stasis_per_tick: -3.0          # applied per tick beyond N=5 threshold
  rejection_cascade: -5.0
  rejection_cascade_sustained: -15.0
  project_cycle: -2.0
  population_stasis: -25.0

ECONOMY:
  harvest_active: +3.0
  crafting_active: +4.0
  trade_active: +3.0
  gold_flow: +1.0
  scarcity_active: +1.0
  ecology_cycling: +2.0          # note: ecology_cycle event also scored in WORLD
  conservation_valid: +1.0
  zero_harvest_after_tick: -20.0
  zero_crafting_after_tick: -15.0
  conservation_violated: -50.0
  # ...
```

Example `grade_thresholds.yaml`:
```yaml
S: 2.0
A: 0.5
B: 0.0
C: -0.5
D: -1.0
# F: anything below D threshold
```

#### What stays in code

Scorer Python files contain only **logic** — conditions, branching, tag assignment,
context checks. They never contain numeric literals for deltas, thresholds, or
time-gate tick values:

```python
class AgencyScorer(PillarScorer):
    def __init__(self, weights):
        ...
        self._entity_defer_streak: dict[int, int] = {}
        self._entity_stasis_fired: dict[int, bool] = {}

    def score(self, envelope, context):
        w = self.weights  # injected ScoringWeights at construction
        entity_id = envelope.entity_id

        if envelope.event_type == "action_executed":
            self._entity_defer_streak.pop(entity_id, None)
            self._entity_stasis_fired.pop(entity_id, None)
            return ScoreRecord(delta=w["action_taken"], tags=("action_taken",), ...)

        if envelope.event_type == "defer_with_reason":
            gate = w.int("stasis_gate_ticks")
            cap = w.int("stasis_extra_ticks_cap")
            streak = self._entity_defer_streak.get(entity_id, 0) + 1
            self._entity_defer_streak[entity_id] = streak

            delta = w["defer_idle"]
            tags = ["defer_idle"]
            if streak > gate:
                tags.append("stasis_N")
                extra = streak - gate
                # Fire only once the streak has actually reached the full cap threshold
                # (extra >= cap) -- NOT at the first post-gate tick (extra == 1), which
                # would always yield capped_extra=1 regardless of `cap`.
                if not self._entity_stasis_fired.get(entity_id, False) and extra >= cap:
                    delta += w["stasis_per_tick"] * min(extra, cap)
                    self._entity_stasis_fired[entity_id] = True
            return ScoreRecord(delta=delta, tags=tuple(tags), ...)
```

`_entity_defer_streak`/`_entity_stasis_fired` are per-entity instance state (not part of the
shared `ScoringContext`/`window_tag_counts`) — they track a true per-entity consecutive-defer
streak, mirroring the scorer's existing `_last_abandoned` per-entity pattern. The streak resets
whenever the entity takes `action_executed`, `route_selected`, `route_family_first_use`, or
`project_completed` (any real non-defer routing outcome). The population-wide `population_stasis`
one-shot check (zero `action_taken` for anyone in the shared window) is a separate mechanism and
still reads `context.window_tag_counts` — it is unaffected by this per-entity streak.

#### Injection pattern

`QualityHub` loads `ScoringWeights` from the active profile at construction and injects
it into every scorer:

```python
weights = ScoringWeights.load("config/simulation_quality/scoring_weights.yaml",
                               profile="default")
scorers = [AgencyScorer(weights), CombatScorer(weights), ...]
hub = QualityHub(scorers, weights)
```

`ScoringWeights` is a Pydantic model. Invalid YAML raises at load time, not silently at
score time: a missing top-level `detection_params.yaml` key raises a bare `KeyError`
(e.g. `raw_detection["loop_threshold"]`); a non-numeric rule value raises a bare
`ValueError` from the `float(v)` conversion. Neither path currently raises
`pydantic.ValidationError` — `ScoringWeights.load()` validates by direct dict access and
explicit `float()`/`int()` conversion before constructing the pydantic model, not via
pydantic's own field validation (corrected here from an earlier, inaccurate description;
see `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`, INFRA-234).

#### Pillar-scoped weight resolution (`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`)

Weight lookup is pillar-scoped, not a single shared namespace. `ScoringWeights.for_pillar
(pillar_id)` returns a `PillarWeightsView` that reads only from that pillar's own
`pillar_rules` section; `PillarScorer.__init__` resolves `self.weights =
weights.for_pillar(self.PILLAR_ID)` once at construction (each of the 10 scorer
subclasses declares its own `PILLAR_ID` class attribute). A scorer's `self.weights["key"]`
call sites keep their existing bare-string syntax, but now resolve to that scorer's own
pillar's declared value — never another pillar's, even if a rule key name is reused
across two pillar sections. `PillarWeightsView` forwards `int_param()`/`pillar_weight()`
to the parent `ScoringWeights` unchanged.

A rule key declared in more than one pillar section (7 keys exist today — see §7.3) is
*ambiguous* at the top level: `ScoringWeights.__getitem__` (bare `weights["key"]`, outside
any scorer) raises `KeyError` for these keys, directing the caller to
`ScoringWeights.for_pillar(pillar_id)["key"]` instead of risking a silent cross-pillar
collision. Non-colliding keys are unaffected and keep resolving via bare `weights["key"]`
exactly as before.

#### Calibration workflow (E7-CALIBRATE)

1. Run baseline scenarios → collect `quality_report.json`
2. Edit `scoring_weights.yaml` and `grade_thresholds.yaml`
3. Re-run — no code change, no redeploy
4. Commit updated config files as calibration artifacts
5. Regenerate `grade_anchors.json` for regression tests

---

## 5. The 10 Pillars

### Pillar Metadata

| ID | Name | Primary Domain | Phase Anchors | D01 Tier |
|---|---|---|---|---|
| `COGNITION` | Cognition | Entity brain, belief, self-model | PP-03, PP-04, PP-30 | Tier 1 (23/25) |
| `AGENCY` | Agency & Action | Adventure routing, action execution | PP-12, PP-13–15, PP-30 | Tier 1 (24/25) |
| `COMBAT` | Combat | Entity-level engagement, lifecycle | PP-16, PP-31, PP-33 | Tier 2 (17/25) |
| `FACTION` | Faction & Military | Diplomacy, military conflict, territory | PP-08–11, PP-23 | Tier 2 (20/25) |
| `ECONOMY` | Economy | Resource loop, crafting, trade, ecology | PP-07, PP-21, PP-24–27, WD-05, WD-10 | Tier 1 (22/25) |
| `PROGRESSION` | Progression | XP, levels, skills, trait expression | PP-24, PP-28, PP-29, PP-31 | Tier 2 (19/25) |
| `SOCIAL` | Social | Cooperation, contracts, groups, reputation | PP-05, PP-34, PP-35, PP-36 | Tier 2 (16/25) |
| `INFORMATION` | Information & Belief | Knowledge asymmetry, paid info, leads | PP-04, PP-26, PP-30 | Tier 2 (18/25) |
| `WORLD` | World Dynamics | Ecology, calamity, spawn, trauma, demographics | PP-20, PP-22, WD-01–15 | Tier 1 (22/25) |
| `NARRATIVE` | Narrative | Quests, chronicle, world emergence, scenario | PP-23, PP-24, PP-33 | Tier 2 (10/25 partial) |

**Coverage note (`TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES`):** a real event type existing in
`src/observability/event_extractor.py` but absent from a pillar's own "Event types scored" list
below is not automatically an unaudited gap — check
`docs/simulation_quality/event_type_coverage.md` §5 "Unscored Intentional" first. As of this
ticket, 14 real event types are deliberately unscored with a documented reason there
(`attribute_changed`, `belief_contradiction`, `biological_state_changed`,
`entity_faction_changed`, `entity_role_changed`, `equipment_durability_changed`, `item_equipped`,
`item_unequipped`, `recipe_learned`, `scar_gained`, `skill_cooldown_started`, `stamina_changed`,
`wound_healed`, `wound_sustained`) — this table intentionally does not duplicate that doc's own
per-event reasoning, to keep a single source of truth.

---

### COGNITION

**Question:** Are entities using imperfect, subjective knowledge to make divergent
decisions — or are they behaving as effectively omniscient agents with flat distributions?

**Pipeline:** PP-03 (`self_model`), PP-04 (`information_belief`), PP-30 (`strategic_intelligence`)

**Event types scored:** `belief_updated`, `lead_certainty_changed`, `strategic_goal_changed`,
`self_model_updated`, `decision_divergence_detected`, `knowledge_default_fallback`

| Signal | Delta | Tag |
|---|---|---|
| Belief updated from event (entity changes known state) | +2 | `belief_active` |
| Two entities in same region diverge on route choice due to belief difference | +5 | `subjective_divergence` |
| Lead certainty increased from new information | +1 | `knowledge_sharpening` |
| Strategic goal changed by re-scoring (not by external event) | +3 | `cognition_replan` |
| Entity makes decision on zero knowledge (default fallback path fired) | −2 | `zero_knowledge_decision` |
| Lead certainty decayed to zero without replacement on active lead | −3 | `knowledge_rot` |
| Same goal re-selected for N>5 consecutive ticks with no cognition update | −2 per tick | `goal_lock_no_cognition` |
| Self-model updated and belief reflects new vital state | +1 | `self_model_active` |
| Zero belief updates population-wide in a 100-tick window | −15 | `belief_system_dormant` |
| All entities share identical lead certainty distributions | −20 | `omniscience_collapse` |

**Loop signal:** `goal_lock_no_cognition` at >70% of window → `loop_detected:goal_lock`

**Traceability path:**
```
grade F → worst_events[0]: tag="omniscience_collapse", tick=200
  → simulation_events.jsonl at tick 200: belief_updated events per entity?
  → cognition_graph_snapshots.jsonl: lead certainty distribution at tick 200
  → ENABLE_BELIEF_ASSIMILATION flag status
```

---

### AGENCY & ACTION

**Question:** Are entities taking purposeful, varied actions — or cycling through the
same DEFER loop indefinitely? Is behavioral entropy adequate?

**Pipeline:** PP-12 (`adventure_decision`), PP-13 (`action_routing`), PP-14 (`position_swaps`),
PP-15 (`movement_routing`), PP-30 (`strategic_intelligence`)

**Event types scored:** `action_executed`, `route_selected`, `defer_with_reason`,
`project_started`, `project_completed`, `project_abandoned`, `commitment_abandoned`,
`rejection_cascade_tick`, `route_family_first_use`

| Signal | Delta | Tag |
|---|---|---|
| Entity executes a meaningful non-DEFER action | +1 | `action_taken` |
| Entity executes a route family not seen in last 200 ticks (novelty) | +3 | `route_novelty` |
| Entity completes a commitment and transitions to next goal | +4 | `commitment_complete` |
| Project successfully completed | +3 | `project_done` |
| Entity movement resolves toward goal location | +1 | `navigation_active` |
| Entity receives DEFER_WITH_REASON | −1 | `defer_idle` |
| Entity receives DEFER for N>5 consecutive ticks (per-entity streak, tracked via instance state — not the shared scoring window) | −3 × cap (max −15, capped), applied exactly once per continuous streak — at the tick the streak first reaches `gate + cap` (streak=10), not at the first post-gate tick (streak=6); no further escalation for the rest of the streak; resets when the entity next takes a non-DEFER routing action | `stasis_N` |
| Population-level rejection cascade >100/tick | −5 | `rejection_cascade` |
| Population-level rejection cascade >500/tick sustained | −15 | `rejection_cascade_sustained` |
| Entity abandons and immediately restarts the same project | −2 | `project_cycle` |
| Route family entropy (H) per 100-tick window, per entity | +H×2 | `entropy_reward` |
| Zero non-DEFER actions population-wide for 20 ticks | −25 | `population_stasis` |

**Loop signal:** `stasis_N` at >70% of window → `loop_detected:entity_stasis`. Note: the `stasis_N`
**tag** continues to be applied on every qualifying event past the gate, for as long as the entity
remains in a genuine defer streak (this keeps the loop-detection signal meaningful for the whole
duration of a real stasis episode) — but the **score delta** it carries is the one-shot capped
escalation only on the event where the streak first crosses `gate + cap`; every other tagged event
carries only the flat `defer_idle` base. Tag-presence does not imply a repeating penalty.
**Loop signal:** `rejection_cascade_sustained` at >50% of window → `loop_detected:rejection_cascade`

**Traceability path:**
```
grade F → worst_events: tag="rejection_cascade_sustained", tick range 200–800
  → simulation_events.jsonl: adventure_decision events per entity in that range
  → Check ENABLE_ADVENTURE_ROUTING flag (defaults OFF — must be ON)
  → Check entity navigation.region_id (must not be None)
  → Check resource_nodes count in world state
```

---

### COMBAT

**Question:** Is combat balanced — engaging without instant extinction, occurring at a
rate appropriate to the world configuration, producing tactical variety?

**Pipeline:** PP-16 (`combat_engagement`), PP-31 (`near_death_hardening`),
PP-33 (`lifecycle` — death finalization), PP-11 (`military_conflict` — faction-level)

**Event types scored:** `combat_initiated`, `combat_resolved`, `combat_damage`,
`entity_killed`, `near_death_survival`, `combat_hard_law_violation`,
`attrition_threshold_crossed`

| Signal | Delta | Tag |
|---|---|---|
| Combat engagement initiated between two entities | +2 | `combat_active` |
| Combat resolved (clear winner, loser retreats or dies) | +3 | `combat_resolved` |
| Near-death hardening fires and entity survives | +2 | `survival_tension` |
| Tactical modifier used in combat (non-default modifier active) | +1 per unique modifier | `tactical_variety` |
| Entity dies in combat (attrition event) | −1 | `attrition` |
| First entity death before tick 10 | −10 | `early_extinction` |
| Population attrition exceeds 50% by tick 100 | −20 | `attrition_spiral` |
| Population attrition exceeds 90% by tick 200 | −50 | `extinction_degenerate` |
| Zero combat events in a world with hostile faction or spawn config, by tick 200 | −15 | `combat_dormant` |
| Combat events emitted with zero lifecycle resolution events (unresolved combat) | −8 per occurrence | `combat_unresolved` |
| Hard law violation in combat pipeline | −30 | `combat_hard_law` |

**Loop signal:** `attrition` appearing without `combat_resolved` at >80% of combat window
→ `loop_detected:unresolved_combat`

**Real producer (`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`):** `combat_resolved` had a real,
ready scorer handler since this pillar's own original design, but no real producer anywhere in
`src/` until this ticket — `event_shapers.py`'s `CombatShaper` now emits it for exactly the
`KILL`/`ESCAPED` outcomes of `combat_engagement_ended` (`TCK-20260809-COMBAT-LIFECYCLE-
OBSERVABILITY`), both literal matches for this row's own "clear winner, loser retreats or dies"
wording. `CAUGHT_FLEEING`/`PURSUIT_ABANDONED` deliberately excluded. See
`docs/simulation_quality/event_type_coverage.md` §3.10 for the full mapping.

**Real producer (`TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX`):** the same class of gap
as `combat_resolved` above — `tactical_variety` had a real, ready scorer handler
(`CombatScorer.score()`'s `combat_damage` branch reading `payload.get("tactical_modifier")`) but
zero real producers anywhere in `src/`, despite `CombatResolutionSystem.
calculate_tactical_multipliers()` computing a real, rich per-attack modifier trace on every
attack. `event_shapers.py`'s `CombatShaper` now selects the first real tactical-modifier key
present in that trace (mechanics-bible table order: `HIGH_GROUND`, `FLANKING`, `SURROUNDED`,
`COVER_REDUCTION`, `SHATTER`, `EXHAUSTION`, `STAMINA_EXHAUSTION`, `BOND_SYNERGY`) into
`combat_damage`'s own payload. Confirmed real in live corpus runs (`STAMINA_EXHAUSTION`
observed).

**Real, confirmed finding (`TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`, corrected
by `TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`):** `entity_killed` is emitted
by two separate mechanisms that co-exist by design (see `TCK-20260806-PUSH-CUTOVER-COMBAT-
ECONOMY-FACTION`'s own completion notes) — the push-shaper (`event_shapers.py`, narrow: fires
only on `outcome_kind=="KILL"`) and the older diffing extractor (`event_extractor.py`, broad:
fires on a `lifecycle.active` transition, kept to cover non-shaper-owned kill causes). Since
`entity_killed` scores negatively (`attrition`/`early_extinction`, both above), a monster-heavy
world is not expected to score *higher* on COMBAT than a civilian world purely from more kills —
more kills means more attrition penalty, not more credit. A C grade on a combat-active world is
not, by itself, evidence of under-crediting. **Correction:** the original finding's claim that
this broad path "correctly catches the opportunity-attack path's own real DEFEAT-outcome deaths"
does not hold — `LifecycleSystem.resolve_lifecycle()` only flips `lifecycle.active` for
`OLD_AGE` or `outcome_kind=="KILL"` specifically, never `DEFEAT` (`is_lethal=False`, the
opportunity-attack path's own hardcoded value), so a DEFEAT-outcome death cannot reach this
branch at all. See the `entity_killed` finding immediately below for the real cause the broad
path was actually (mis-)crediting.

**Real, confirmed finding (`TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`):** the
old diffing extractor's `combat_kill`/`entity_killed` fallback previously fired on *any*
`lifecycle.active` transition not already shaper-owned, regardless of real cause. Direct pipeline
instrumentation on `dungeon_crawl_seed42_2000t` (corpus-default flags) traced every one of the
run's 25 real `combat_kill` events to a `HAZARD`-preceded death (`world_dynamics.py`'s
environmental drain, already excluded from `_real_combat_update()` elsewhere in the same file) or
an unset `death_reason` (a mass despawn/old-age cluster) — zero traced to
`LifecycleSystem.resolve_lifecycle()`'s own authoritative `death_reason=="COMBAT"` value. Fixed
by additionally requiring `death_reason=="COMBAT"` before firing `combat_kill` (COMB-309,
`docs/parity_ledger/combat_movement.yaml`). Old-age/despawn deaths keep their own, unaffected
credit path (`demographic_mortality`, WORLD pillar, on `entities_remove`). Post-fix,
`dungeon_crawl`/`urban_political` COMBAT norm both moved from a small negative (false attrition
credit) to exactly `0.0` (an honest "no real credited combat activity" reading) — grade stayed C
for both (0 events is the scoring contract's own "no signal" default, not a boundary artifact).
This — not under-crediting of DEFEAT-outcome deaths — is the real, structural reason the pillar
sat at the B/C boundary even after this session's prior 5 combat fixes: its positive-scoring
surface (`combat_active`, `combat_resolved`, `tactical_variety`, `survival_tension`) never fired
because the corpus's own real `combat_engagement_ended` activity always resolved as
`PURSUIT_ABANDONED`, the one outcome excluded from `combat_resolved` credit — a separate,
out-of-scope, disclosed-but-unfixed follow-up question.

**Traceability path:**
```
grade F → worst_events: tag="extinction_degenerate", tick=200
  → world.yaml: spawn_density and faction hostile_config for each region
  → D08 multi-scenario data: dungeon_crawl shows 94–97% attrition is world-content-driven
  → Adjust spawn density or faction placement, not combat formula constants
```

---

### FACTION & MILITARY

**Question:** Are factions interacting — diplomatically and militarily — in a balanced,
dynamic way? Is any faction dominating without resistance?

**Pipeline:** PP-08 (`faction_decision` direct-call), PP-09 (`faction_awareness`),
PP-10 (`diplomatic_transitions`), PP-11 (`military_conflict`), PP-23 (`world_emergence`)

**Event types scored:** `diplomatic_transition`, `alliance_proposed`, `alliance_accepted`,
`war_declared`, `military_conflict_resolved`, `territory_ownership_changed`,
`resource_seized`, `faction_tension_delta`, `faction_extinct`, `faction_trajectory_stagnant`

| Signal | Delta | Tag |
|---|---|---|
| Diplomatic state transition fires (neutral→hostile, hostile→war, etc.) | +5 | `diplomacy_active` |
| Alliance proposal generated (common-enemy pair detected) | +4 | `coalition_forming` |
| Alliance accepted | +6 | `alliance_formed` |
| Military conflict resolved (battle outcome determined) | +3 | `military_active` |
| Territory ownership transition (conquest or liberation) | +6 | `territory_shifted` |
| Resource seizure event (faction acquires contested resource) | +2 | `economic_military_coupling` |
| Faction tension delta exceeds threshold (escalating or de-escalating) | +2 | `tension_active` |
| Zero diplomatic transitions in a 2+ faction world over 200 ticks | −20 | `diplomacy_dormant` |
| Single faction controls >80% of territory by tick 500 | −15 | `faction_monopoly` |
| Single faction controls 100% of territory | −40 | `faction_conquest_degenerate` |
| War declared but zero military conflict events follow within 50 ticks | −10 | `war_without_conflict` |
| Faction extinct within 50 ticks of run start | −8 | `faction_early_extinction` |
| All factions remain NEUTRAL for entire run | −25 | `all_factions_neutral` |
| Tension oscillates between same two values without crossing threshold, >5 cycles | −5 | `tension_oscillation` |
| Faction territory unchanged for 300+ ticks despite ongoing diplomatic activity for that faction (trajectory coherence, §7.6) | −8 | `faction_trajectory_stagnant` |

**Loop signal:** `tension_oscillation` at >60% of window → `loop_detected:tension_oscillation`

**Traceability path:**
```
grade F → worst_events: tag="all_factions_neutral", full run
  → faction state snapshots: are factions receiving directives from FactionDecisionPhase?
  → PP-08 direct-call: is FactionDecisionPhase.execute() producing non-empty directives?
  → Check faction objective config in world.yaml
```

---

### ECONOMY

**Question:** Is the resource loop alive — entities harvesting, crafting, trading,
accumulating and spending gold? Is resource ecology creating real scarcity and recovery?

**Pipeline:** PP-07 (`blacksmith`), PP-21 (`gold_sink`), PP-24 (`quest_rewards`),
PP-25 (`shop`), PP-26 (`paid_information`), PP-27 (`resource_transactions`),
PP-20 (`town_resolution`), WD-05 (node cooldown/recharge), WD-10 (`resource ecology`)

**Event types scored:** `resource_harvested`, `item_crafted`, `trade_executed`,
`shop_transaction`, `gold_transferred`, `resource_node_depleted`,
`resource_node_regenerated`, `gold_sink_fired`, `conservation_law_verified`,
`conservation_law_violated`, `paid_info_transaction`, `quest_reward_dispensed`

| Signal | Delta | Tag |
|---|---|---|
| Resource harvested (entity gains items from node) | +3 | `harvest_active` |
| Item crafted (blacksmith or entity produces output) | +4 | `crafting_active` |
| Trade / buy / sell event | +3 | `trade_active` |
| Gold changes hands (non-zero gold delta on any entity) | +1 | `gold_flow` |
| Quest reward dispensed | +3 | `quest_economy_coupling` |
| Resource node depleted (charges → 0; scarcity is real) | +1 | `scarcity_active` |
| Resource node regenerated after depletion (ecology cycle complete) | +2 | `ecology_cycling` |
| Conservation law verification passes (transfer balanced) | +1 | `conservation_valid` |
| Gold sink fired on inflation pressure | +2 | `inflation_controlled` |
| Paid information transaction | +2 | `knowledge_economy_active` |
| Zero harvesting events after tick 100 | −20 | `zero_harvest` |
| Zero crafting events after tick 200 | −15 | `zero_crafting` |
| Zero trade events after tick 300 | −15 | `zero_trade` |
| All resource nodes permanently depleted with zero ecology fires | −25 | `ecology_broken` |
| Conservation law violation | −50 | `conservation_violated` |
| Gold flat (no delta) for single entity over 500 ticks while entity is alive | −5 | `gold_frozen` |
| Zero gold flow population-wide for 100 ticks | −10 | `monetary_paralysis` |
| Zero ecology cadence fires despite depleted nodes | −10 | `ecology_cadence_broken` |

**Loop signal:** `zero_harvest` present and `ecology_cycling` absent across full run
→ `loop_detected:resource_loop_dead`

**Traceability path:**
```
grade F → worst_events: tag="zero_harvest", persists from tick 100 onward
  → Check ENABLE_ADVENTURE_ROUTING (must be ON for entities to route to resource nodes)
  → Check len(state.resource_nodes) after WorldCompiler.compile() (D04 found 0 in urban_political — RESOLVED, confirmed 3 nodes as of 2026-07-01, TCK-20260627-P0B-URBAN-RESOURCE-NODES)
  → Check entity navigation.region_id (D04 found all None after compile — RESOLVED, TCK-20260627-P0C-ENTITY-REGION-ASSIGN; reconfirmed 2026-07-03 via TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT: compiler.py always sets a real value now)
  → These two root causes (from D04 §6.2) are historical zero-harvest causes, both fixed — retained here as a diagnostic path in case of regression, not as an open gap
```

---

### PROGRESSION

**Question:** Are entities growing — gaining XP, leveling up, unlocking skills, expressing
traits, and evolving their playstyle? Or are they locked at level 1 for the entire run?

**Pipeline:** PP-24 (`quest_rewards`), PP-28 (`evolution`), PP-29 (`progression_conversion`),
PP-31 (`near_death_hardening`), PP-33 (`lifecycle`)

**Event types scored:** `xp_granted`, `level_up`, `skill_unlocked`, `trait_expressed`,
`pillar_trait_unlocked`, `progression_conversion_applied`, `near_death_survival`,
`progression_plateau_detected`, `capability_growth_stalled`, `life_arc_incoherent`

| Signal | Delta | Tag |
|---|---|---|
| XP granted to entity (any source) | +1 per 10 XP | `xp_active` |
| Level-up event fires | +8 | `level_milestone` |
| Skill unlocked | +5 | `skill_growth` |
| Trait expressed (personality trait actively modified a decision outcome) | +2 | `genetic_determinism_active` |
| Pillar trait unlocked (level 50/75/100 milestone) | +15 | `pillar_trait_milestone` |
| Progression conversion fires and produces permanent update | +4 | `soft_skill_evolution` |
| Near-death survival (hardening fires; entity below death threshold survives) | +3 | `survival_experience` |
| Entity alive for 200+ ticks with zero XP gain | −10 | `progression_frozen` |
| Entity at level 5+ with zero skill unlocks | −5 | `skill_system_silent` |
| All entities still at level 1 after tick 300 | −30 | `all_level_1` |
| XP gain rate drops to zero after tick 50 and never recovers | −8 | `xp_plateau` |
| Trait expression rate = 0 for entire run | −10 | `trait_system_silent` |
| Level cap reached: entity generates level_up event with no effect | −1 | `level_cap_reached` |
| Entity's level, skill count, equipped-gear count, and gold all flat for 300+ ticks simultaneously (capability trend, §7.6) | −10 | `capability_growth_stalled` |
| Entity reaches Hero's Journey generation 2+ (a rebirth already occurred) still at level 1 with zero skills (life-arc coherence, §7.6) | −15 | `life_arc_incoherent` |

**Loop signal:** `progression_frozen` at >80% of entity-ticks in window
→ `loop_detected:progression_stasis`

**Traceability path:**
```
grade F → worst_events: tag="all_level_1", tick=300
  → quest_rewards events: are XP grants being emitted from PP-24?
  → evolution system: are XP accumulation thresholds reachable?
  → Check quest completion events (zero quest completions = zero quest XP)
  → Economy pillar: if Economy also F, resolve economy first (quest XP requires quest completion)
```

---

### SOCIAL

**Question:** Are entities building social structures — cooperating, forming groups,
honoring contracts, shifting reputation — or acting in complete isolation?

**Pipeline:** PP-05 (`cooperation`), PP-34 (`groups`), PP-35 (`active_contracts`),
PP-36 (`expired_offers`), PP-18 (`interaction_enforcement` — trade/talk social effects)

**Event types scored:** `cooperation_event`, `group_joined`, `group_expelled`,
`contract_offer_created`, `contract_offer_accepted`, `contract_milestone_completed`,
`contract_completed`, `contract_lapsed`, `contract_expired_offer`,
`reputation_delta`, `social_memory_created`

| Signal | Delta | Tag |
|---|---|---|
| Cooperation event (joint task formed or help offer accepted) | +4 | `cooperation_active` |
| Group join event | +2 | `group_forming` |
| Contract milestone completed | +3 | `contract_honored` |
| Contract fully completed (all milestones) | +6 | `contract_complete` |
| Reputation delta > 0.5 on any entity (meaningful shift) | +2 | `reputation_shifting` |
| Social memory created (entity records significant interaction) | +2 | `relationship_depth` |
| Group expulsion event (enforcement working) | +1 | `group_enforcement` |
| Contract offer accepted | +2 | `negotiation_active` |
| Contract offer expired without acceptance | −1 | `offer_dead` |
| Contract lapsed (obligor missed milestone) | −3 | `contract_broken` |
| Zero cooperation events in multi-class world after tick 100 | −15 | `cooperation_dormant` |
| Zero group membership changes in 300 ticks | −8 | `social_structure_static` |
| All entities with reputation = 0 at tick 200 | −10 | `reputation_flat` |
| Entity with zero social interactions for entire run | −2 per isolated entity | `social_isolation` |

**Loop signal:** `offer_dead` at >80% of contract events in window
→ `loop_detected:contract_offer_dead_loop`

**Traceability path:**
```
grade F → worst_events: tag="cooperation_dormant", from tick 100
  → Check ENABLE_SOCIAL_COOPERATION flag (must be ON)
  → Verify entity proximity and personality compatibility conditions in cooperation phase
  → Check contract offer acceptance timeline: are offers reaching compatible entities?
```

---

### INFORMATION & BELIEF

**Question:** Are entities using imperfect information to make different decisions from
their peers? Is the knowledge economy (paid information, lead tracking) producing
behavioral divergence?

**Pipeline:** PP-04 (`information_belief`), PP-26 (`paid_information`), PP-30
(`strategic_intelligence` — lead re-scoring)

**Event types scored:** `belief_assimilated`, `lead_certainty_updated`,
`lead_contradiction_resolved`, `paid_information_transaction`,
`paid_info_changed_goal`, `belief_stale`, `decision_diverged_by_belief`, `route_new_query`

**Real producer (`TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES`):** `route_new_query` was a real,
live-emitted event (`src/observability/event_extractor.py`, `src/observability/event_shapers.py`,
originally added by `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) with no scorer wiring of any
kind — missed by both this table and `docs/simulation_quality/event_type_coverage.md`'s own
otherwise-complete audit until this ticket. Added to `InformationScorer.EVENT_TYPES` as the natural
sibling of `belief_assimilated`/`belief_stale` (a new information-seeking query started, rather
than a belief being updated by one already in flight).

| Signal | Delta | Tag |
|---|---|---|
| Belief assimilated from information event | +2 | `belief_active` |
| Lead certainty increased from new information | +2 | `intel_quality_up` |
| Entity routes a new information-seeking query | +2 | `information_seeking_active` |
| Entity pays for information (paid transaction) | +3 | `knowledge_economy_active` |
| Paid information changes entity's goal within 5 ticks | +5 | `info_has_impact` |
| Lead contradiction resolved (entity replanned from conflicting intel) | +4 | `intel_complexity` |
| Two entities in same region diverge on route choice due to belief difference | +6 | `subjective_divergence` |
| Lead certainty decayed to zero on an active lead | −2 | `knowledge_rot` |
| Belief unchanged after information response received | −1 | `belief_pipeline_deaf` |
| Zero paid information transactions in world with info NPCs after tick 200 | −10 | `knowledge_economy_dormant` |
| Zero belief updates population-wide for 100 ticks | −15 | `belief_system_silent` |
| All entities sharing identical lead certainty distributions at tick 200 | −20 | `omniscience_collapse` |
| Entity purchases same lead tip > 3 times in 100 ticks with no certainty gain | −5 | `paid_info_memory_failure` |

**Loop signal:** `knowledge_rot` at >70% of information events in window
→ `loop_detected:knowledge_rot_loop`

**Traceability path:**
```
grade F → worst_events: tag="omniscience_collapse"
  → Check ENABLE_BELIEF_ASSIMILATION flag
  → Check InformationProviderArchetype NPCs in world config
  → Cross-check Cognition pillar: if both Cognition and Information are F, belief
    assimilation is the common root cause — fix PP-04 first
```

---

### WORLD DYNAMICS

**Question:** Is the world itself alive — ecology regenerating, calamities striking,
bosses spawning, regions transforming, demographics shifting? Or is the world a
static backdrop that entities move through without consequence?

**Pipeline:** PP-20 (`town_resolution`), PP-22 (`world_dynamics` — all WD sub-phases),
WD-01 (`hazard drain`), WD-02 (`trauma`), WD-03 (`ownership/calamity`),
WD-04 (`region transformation`), WD-05 (node recharge), WD-06 (chest cooldown),
WD-07 (corpse decay), WD-08 (`calamity`), WD-09 (`spawn`), WD-10 (`ecology`),
WD-11 (`threat evolution`), WD-12 (`boss spawn`), WD-13 (`raid`),
WD-14 (`camp lifecycle`), WD-15 (`demographics`)

**Event types scored:** `calamity_spawned`, `boss_spawned`, `raid_party_spawned`,
`region_transformed`, `region_trauma_delta`, `region_ownership_changed`,
`ecology_cycle_completed`, `spawn_cadence_fired`, `demographic_birth`,
`demographic_mortality`, `camp_constructed`†, `hazard_drain_applied`,
`threat_evolved`, `node_recharged`, `building_sabotaged`, `spawn_occupancy_violation`,
`world_hard_law_violation`

†`camp_constructed` is registered, not currently emittable — see
`event_type_coverage.md` §3.9.

| Signal | Delta | Tag |
|---|---|---|
| Calamity spawned | +8 | `calamity_active` |
| Boss entity spawned | +6 | `boss_active` |
| Raid party spawned | +4 | `raid_active` |
| Region type transformation fires | +6 | `world_evolving` |
| Regional trauma escalating from combat deaths (trauma_delta > 0) | +2 | `trauma_feedback` |
| Region ownership transition | +5 | `political_change` |
| Resource ecology cycle completed (depleted → regenerated) | +3 | `ecology_cycling` |
| Monster spawn cadence fires and populates region | +2 | `world_repopulating` |
| Demographic birth event | +2 | `demographics_active` |
| Demographic mortality event | +1 | `natural_lifecycle` |
| Camp constructed | +1 | `persistent_structure` |
| Hazard drain applies damage in hazardous region | +1 | `hazard_active` |
| Building takes sabotage damage (hp_delta < 0 on building_updates) | +1 | `infrastructure_damaged` |
| Spawn placement violates occupancy/terrain legality (LAW-SPAWN-OCCUPANCY) | −30 | `spawn_occupancy_violation` |
| Hard law violated outside combat/spawn-occupancy domain (LAW-STAMINA-NONNEGATIVE, LAW-POSITION-FINITE, LAW-OCCUPANCY-COLLISION) | −30 | `world_hard_law_violation` |
| Zero calamity events in run of 500+ ticks | −8 | `calamity_dormant` |
| Zero spawn cadence fires (no monster repopulation after depletion) | −10 | `world_depopulating` |
| Zero region transformations in run of 1000+ ticks | −6 | `world_static` |
| All resource nodes permanently depleted with zero ecology fires | −20 | `ecology_broken` |
| Regional trauma monotonically increasing with no hazard_level effect | −5 | `trauma_hazard_broken` |
| Zero demographic events in world with demographic config | −8 | `demographics_dormant` |
| Boss spawn cadence never fires despite threat threshold exceeded | −6 | `boss_spawn_blocked` |
| World trauma everywhere = 0 despite significant combat activity | −8 | `trauma_accumulation_broken` |

**Loop signal:** `trauma_hazard_broken` present for >100 ticks
→ `loop_detected:trauma_feedback_broken`

**Traceability path:**
```
grade F → worst_events: tag="ecology_broken"
  → Check WD-10 ResourceEcologyService firing logs
  → Check cadence configuration: world_dynamics cadence fires every N ticks
  → Verify node.max_charges and regeneration_rate in resource node config
  → Cross-reference Economy pillar: ecology_broken typically causes Economy grade F too
```

---

### NARRATIVE

**Question:** Is there a story happening — quests starting and completing, the world
producing a unique history through chronicle entries, scenario objectives progressing,
narrative milestones forming?

**Pipeline:** PP-23 (`world_emergence`), PP-24 (`quest_rewards`), PP-33 (`lifecycle`
— death is a narrative event), PP-08 (`faction_decision` — diplomatic milestones)

**Event types scored:** `quest_started`, `quest_completed`, `quest_failed`,
`chronicle_entry_created`, `world_emergence_event`, `narrative_milestone`,
`scenario_objective_progressed`, `scenario_objective_completed`, `scenario_stalled`,
`hero_death_unrecorded`

| Signal | Delta | Tag |
|---|---|---|
| Quest started (entity accepts objective) | +5 | `quest_active` |
| Quest completed | +10 | `quest_resolved` |
| Quest failed (entity unable to complete) | −2 | `quest_failed` |
| Chronicle entry created (NarrativeLedger receives milestone) | +4 | `history_forming` |
| World emergence event fires (threshold-triggered narrative event) | +6 | `emergence_active` |
| Narrative milestone: first faction war declaration | +8 | `milestone_war` |
| Narrative milestone: first boss kill | +8 | `milestone_boss_kill` |
| Narrative milestone: first region sovereignty transfer | +6 | `milestone_sovereignty` |
| Scenario objective progressed | +4 | `scenario_advancing` |
| Scenario objective completed | +15 | `scenario_resolved` |
| Scenario stalled (no progress for N ticks; N configurable per scenario) | −10 | `scenario_stalled` |
| Zero quest starts after tick 200 (world has quest definitions) | −20 | `quest_system_dormant` |
| Zero chronicle entries after tick 300 | −15 | `history_silent` |
| Zero world emergence events in 500 ticks | −10 | `emergence_dormant` |
| Same quest repeatedly failed and restarted by same entity > 3 cycles | −6 | `quest_retry_loop` |
| Hero-class entity death with zero chronicle entry | −1 per hero | `hero_death_unrecorded` |

**Loop signal:** `quest_retry_loop` at >60% of quest events in window
→ `loop_detected:quest_retry_loop`

**Traceability path:**
```
grade F → worst_events: tag="quest_system_dormant", from tick 200
  → D07 finding: only 4 quest definitions exist total, only 3 of 14 world modules have quests
  → Check world.yaml quest_definitions count (must be > 0)
  → Check PP-24 quest_rewards: are completed objectives reaching the pipeline?
  → Check Economy pillar: quest rewards require economic preconditions (items, gold)
```

---

## 6. Scenario Registry

The canonical list of usage scenarios this module is designed to answer. Every scorer
rule must trace to at least one entry. Every entry must map to exactly one primary pillar.

When adding a new scorer rule or new pillar, consult this registry first:
- If the scenario already exists, the new rule must not duplicate an existing rule for the same scenario
- If the scenario is new, add it here before implementing the rule

| ID | Question | Primary | Secondary | Key Event Types | Conflict Notes |
|---|---|---|---|---|---|
| SQ-01 | Is the simulation in an infinite behavioral loop? | AGENCY | COGNITION | `defer_with_reason`, `route_selected` | Do not also score this in COGNITION — AGENCY owns loop detection |
| SQ-02 | Why do entities all do the same thing every tick? | AGENCY | COGNITION | `defer_with_reason`, `route_selected` | SQ-01 and SQ-02 share signals; AGENCY is always primary |
| SQ-03 | Is combat balanced — not instant extinction, not never-firing? | COMBAT | WORLD | `combat_initiated`, `entity_killed` | WORLD only scored if attrition correlates with spawn config |
| SQ-04 | Is any entity class dominating in combat? | COMBAT | PROGRESSION | `entity_killed`, `combat_resolved` | Class dominance is COMBAT; progression advantage is secondary |
| SQ-05 | Is any faction dominating politically or militarily? | FACTION | — | `territory_ownership_changed`, `faction_conquest_degenerate` | Do not score in COMBAT — faction military is FACTION-owned |
| SQ-06 | Are factions actually forming alliances? | FACTION | SOCIAL | `alliance_formed`, `alliance_proposed` | Alliance formation: FACTION primary; social contract aspects: SOCIAL secondary |
| SQ-07 | Is the economic loop alive (harvest, craft, trade)? | ECONOMY | WORLD | `resource_harvested`, `item_crafted`, `trade_executed` | Ecology (WD-10) is scored in WORLD, not ECONOMY, even though it enables economy |
| SQ-08 | Is resource ecology creating real scarcity and recovery? | WORLD | ECONOMY | `ecology_cycle_completed`, `resource_node_depleted` | `ecology_cycle_completed` scored in WORLD; `resource_harvested` scored in ECONOMY |
| SQ-09 | Is gold accumulating without being spent (inflation)? | ECONOMY | — | `gold_transferred`, `gold_sink_fired` | Inflation detection: ECONOMY only — do not duplicate in FACTION |
| SQ-10 | Are entities gaining XP and leveling up? | PROGRESSION | — | `xp_granted`, `level_up` | Do not score XP in ECONOMY even when XP comes from quest rewards |
| SQ-11 | Is progression plateauing — entities stuck at level 1? | PROGRESSION | AGENCY | `progression_frozen`, `all_level_1` | AGENCY secondary because stasis blocks XP-generating actions |
| SQ-12 | Are entities cooperating or acting in complete isolation? | SOCIAL | AGENCY | `cooperation_event`, `group_joined` | Cooperation requires action; AGENCY is secondary, not primary |
| SQ-13 | Are contracts completing or always expiring? | SOCIAL | — | `contract_completed`, `contract_lapsed` | Social contracts: SOCIAL only — do not score contract expiry in ECONOMY |
| SQ-14 | Is reputation changing meaningfully? | SOCIAL | — | `reputation_delta` | Reputation: SOCIAL only |
| SQ-15 | Is information asymmetry creating decision divergence? | INFORMATION | COGNITION | `decision_diverged_by_belief`, `belief_assimilated` | COGNITION is secondary because belief feeds cognition; INFO is the source |
| SQ-16 | Is the knowledge economy active (paid information)? | INFORMATION | ECONOMY | `paid_information_transaction` | Paid info has gold cost (ECONOMY secondary) but is primarily INFORMATION |
| SQ-17 | Is the world alive — calamities, bosses, region transformations? | WORLD | — | `calamity_spawned`, `boss_spawned`, `region_transformed` | World events: WORLD only — do not duplicate in FACTION or COMBAT |
| SQ-18 | Is ecology regenerating after resource depletion? | WORLD | ECONOMY | `ecology_cycle_completed`, `node_recharged` | WD-10 events owned by WORLD; economy impact is secondary |
| SQ-19 | Are quests starting and completing? | NARRATIVE | ECONOMY | `quest_started`, `quest_completed` | Quest economy coupling is ECONOMY secondary; quest activity is NARRATIVE primary |
| SQ-20 | Is the world producing history (chronicle entries, milestones)? | NARRATIVE | FACTION | `chronicle_entry_created`, `narrative_milestone` | Faction milestones contribute to chronicle: FACTION secondary |
| SQ-21 | Do entities behave as distinct RPG archetypes? | COGNITION | PROGRESSION | `decision_divergence_detected`, `trait_expressed` | Class divergence through personality: COGNITION; through stat growth: PROGRESSION |
| SQ-22 | Is the scenario progressing toward its objectives? | NARRATIVE | AGENCY | `scenario_objective_progressed`, `scenario_stalled` | Scenario stall is NARRATIVE; underlying action stall is AGENCY secondary |
| SQ-23 | Does infrastructure sabotage register as a real-world consequence? | WORLD | — | `building_sabotaged` | Building damage is WORLD-owned per building-events-have-no-existing-pillar-owner (§7.3); do not duplicate in FACTION even though urban_political's sabotage framing is faction-conflict-adjacent |
| SQ-24 | Does illegal spawn placement register as a real correctness fault? | WORLD | — | `spawn_occupancy_violation` | Frequency signal only — detection/legality is HardLawMonitor's job (LAW-SPAWN-OCCUPANCY); SimQ scores how often it occurs, not whether one placement is legal, per the determinism-exclusion precedent (TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC §2.2) |

---

## 7. Extensibility Protocol

### 7.1 Adding a New Pillar

1. Add `NEW_PILLAR_ID` to `PillarId` enum in `pillars.py`
2. Add metadata entry to `PILLAR_METADATA` dict: name, description, phase anchors, D01 reference
3. Add a section for the new pillar in `config/simulation_quality/scoring_weights.yaml`
   with all rule keys and initial delta values
4. Add the pillar's default weight (1.0) to `config/simulation_quality/profiles/default.yaml`
5. Create `src/simulation_quality/scorers/new_pillar.py` extending `PillarScorer`
6. Implement `score(envelope, context) -> ScoreRecord | None` using `self.weights["rule_key"]`
   — **no numeric literals in scorer code**
7. Register in `QualityHub.SCORER_REGISTRY`: `{event_type: [NewPillarScorer(weights)]}`
8. Add at least one scenario to the Scenario Registry (§6) for each new usage question
9. Add unit tests for every scoring rule in the new scorer
   (tests inject a `ScoringWeights` fixture, not production config values)

**Do not** register the same event_type in the new pillar AND an existing pillar with
the same delta sign for the same condition. Consult §6 Scenario Registry for overlap.

### 7.2 Adding a Scoring Rule to an Existing Pillar

1. Check §6: does the scenario already exist? If yes, is there already a rule for it in this pillar?
2. If no conflict:
   a. Add the rule's delta key and default value to `config/simulation_quality/scoring_weights.yaml`
      under the relevant pillar section
   b. Add the conditional logic to `scorer.py` using `self.weights["new_rule_key"]`
      — **no numeric literals**. This resolves to *this scorer's own pillar's* declared
      value (via the `PILLAR_ID`-bound `PillarWeightsView` set up in `__init__` — see
      §4.8), not a shared cross-pillar namespace, even if `new_rule_key` happens to also
      be declared in another pillar's section.
3. Add the tag to the pillar's tag documentation in §5
4. If the scenario is new: add a row to §6 Scenario Registry
5. Add a unit test for the new rule (inject a `ScoringWeights` fixture)
6. If the rule involves a new event_type: add the event_type to the pillar's "Event types scored" list in §5

### 7.3 Conflict Detection Rules

Before adding any scoring rule, verify:
- **No dual-ownership:** The event_type is not already scored in another pillar for the same scenario condition
- **No duplicate signals:** The tag for the new rule doesn't already exist in another pillar
- **Scenario mapping:** The rule traces to exactly one primary scenario in §6
- **Delta polarity consistency:** If event_type X is scored +N in Pillar A, it must not be scored −N in Pillar B for the same condition (contradictory scoring)

The only legitimate exception: one event can score in two pillars if the two scenarios
it maps to have different primary pillars (e.g., `paid_info_transaction` scores +3 in
INFORMATION for SQ-16 and is noted as secondary in ECONOMY for SQ-16). In this case,
exactly one pillar owns the primary score; the secondary is documentary only.

This primary/secondary dual-pillar design (SQ-15, SQ-08/SQ-16/SQ-18) requires each pillar
to read its *own* declared delta for the shared rule key — e.g. COGNITION's secondary
`subjective_divergence` (5.0) is deliberately a smaller magnitude than INFORMATION's
primary (30.0). Before `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s pillar-scoped
lookup fix, the shared flat-index mechanism silently collapsed every such pair to
whichever pillar was declared later in `scoring_weights.yaml`, so the secondary pillar's
scorer was actually reading the primary's value (or vice versa) instead of its own — the
primary/secondary design described here existed in config and in this doc, but the
lookup mechanism didn't honor it. `ScoringWeights.for_pillar()` (§4.8) is what makes this
section's design actually work as documented. One divergence from "documentary only"
survives this fix unresolved: `EconomyScorer`'s `paid_info_transaction` handling returns
a real, live-scored `ScoreRecord` added to ECONOMY's `raw_score`, not a documentary-only
non-contribution — flagged as a candidate follow-up, not fixed by this ticket (see
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s Implementation Notes).

### 7.4 Configuring Quality Profiles

A `QualityProfile` overrides default pillar weights for a specific scenario type:

```python
@dataclass(frozen=True)
class QualityProfile:
    name: str
    weights: dict[PillarId, float]   # only pillars to override; defaults apply for rest
    grade_threshold_overrides: dict[str, float]  # optional: override grade thresholds
    disable_pillars: set[PillarId]   # pillars irrelevant for this scenario type
```

Example: `QualityProfile("dungeon_crawl", {PillarId.COMBAT: 2.0, PillarId.FACTION: 0.1})`.

Profiles are defined in `src/simulation_quality/profiles.py` — not in world.yaml.

### 7.5 Pillar Completeness Audit (2026-07)

Per the user's request during `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` scoping ("consideration of
new pillars if warranted"), four candidate dimensions were checked against the §7.1 bar for a new
top-level pillar. Source: `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md`
§2. Each candidate below was re-verified against current repo state rather than trusted from that
investigation snapshot.

| Candidate dimension | Owning system (verified) |
|---|---|
| Determinism / replay-fidelity | `tests/certification/`, `tests/integration/kernel/test_long_run_determinism.py`, `tests/integration/observability/test_phase28_observability_determinism.py`, `tests/unit/kernel/test_replay_determinism.py` |
| Performance / tick-time budget | `tests/perf/` (38 files), tied to `docs/engine/performance_contract.md`'s hardware classes; SimQ's own scorer/accumulator microbenchmarks are budgeted in `tests/simulation_quality/test_performance.py`; SimQ's engine-level (disabled/in-process/broker) overhead is measured by `tests/perf/test_simq_isolation_overhead.py`, results in `docs/performance/simq_isolation_overhead.md` |
| Save/checkpoint integrity | `tests/integration/kernel/test_checkpoint_reproducibility.py`, `tests/unit/engine/test_scenario_checkpointer.py` |
| Content/catalog health | `src/content/validator.py`'s `CAT-REL-001`–`CAT-REL-004` and `CAT-REL-011`–`CAT-REL-019` rules (non-contiguous range; there is no `CAT-REL-005`–`CAT-REL-010`) |

§1's own "What this module is NOT" table already scopes SimQ away from determinism (owned by
`hard_law_monitor`/replay certification, not this module) and performance (`perf_baseline_policy.md`)
explicitly. A pillar duplicating either would violate that scope boundary. Checkpoint integrity and
content/catalog health are each likewise owned end-to-end by a dedicated existing system outside
`src/simulation_quality/`. **None of the four candidates justify a new top-level pillar.**

One genuine, narrow gap was found (investigation.md §2.6): `building_sabotage` (pipeline phase 15
per `docs/engine/authoritative_pipeline.md`, `src/engine/sabotage.py::BuildingSabotageSystem.resolve()`)
is a live, non-dead mechanic — it resolves `SABOTAGE` / `ENTITY_ACT(action=SABOTAGE)` intents
directed at buildings and mutates `building_updates` (`hp_delta`, `functional_set`) through the
authoritative pipeline. It is exercised by real corpus content (`urban_political`'s resolved world
spec at `data/worlds/urban_political/resolved/world.resolved.yaml` and
`data/content/world_modules/trading_company_hub.yaml`), but emits no
`ObservabilityEventEnvelope`/`SimulationEvent`, so it is invisible to every pillar's event-type/tag
list — including WORLD's own list in §5 (`calamity_spawned`, `boss_spawned`, `region_transformed`,
etc.; none cover building damage or functional-state changes).

Applying §7.1 vs §7.2: this is a single additional signal on an existing subsystem's usage question
("is the world itself alive") — not a new usage question requiring its own pillar — so it is a new
**WORLD-pillar scoring rule**, not an 11th top-level pillar. `FACTION` is a plausible secondary owner
given `urban_political`'s faction-conflict framing, but per §7.3's no-dual-ownership rule, WORLD is
the cleaner primary: no existing pillar currently claims building-state events, so there is no
conflict to resolve by picking a secondary. This gap is tracked and implemented by
`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` (event-emission prerequisite plus the WORLD-pillar
scoring rule itself), which cites this subsection as its evidence source.

**Conclusion: no new top-level SimQ pillar is justified at this time.**

### 7.6 Pillar Completeness Audit (2026-08) — Combat/Progression Boundary & Layer-Lifecycle Trajectory

A 2026-08-06 session discussion (post SimQ-epic closeout and full-corpus calibration refresh)
raised two further candidates, distinct from the four checked in §7.5: whether COMBAT and
PROGRESSION need clearer scope separation, and whether the simulation's other layers (entities,
regions, factions, world) each need their own progression/lifecycle signal. Both were checked
against the same §7.1-vs-§7.2 test.

**Boundary clarified — COMBAT vs. PROGRESSION.** COMBAT (§5, lines 642-678) already correctly
scores resolution mechanics only: damage, tactical-modifier variety (`tactical_variety`),
durability, wounds. PROGRESSION (§5, lines 771-810) scores XP/level/skill/trait events, but only as
isolated per-event deltas — it has no signal for whether an entity's overall **capability** (level +
equipped-gear quality + gold + unlocked skills, combined) is trending upward across its lifetime,
which is the fuller "growing richer/stronger" sense of progression. **Ruling: COMBAT stays
resolution-only. PROGRESSION owns capability-trend and entity life-arc coherence** — this is a new
scoring rule on PROGRESSION's existing usage question ("are entities growing"), not grounds for a
new pillar or for COMBAT to absorb build/capability concerns.

**Layer-lifecycle trajectory gap — entity and faction layers, not region/world.** WORLD already has
a real trajectory-*coherence* rule, not just an event-density check: `trauma_hazard_broken`
("regional trauma monotonically increasing with no hazard_level effect", line 942) catches a
degenerate trend over a window, the same pattern a "is this layer's lifecycle healthy" check would
need. Re-checking each layer against that bar:

| Layer | Existing trajectory-coherence rule? | Verdict |
|---|---|---|
| Entity | None — PROGRESSION has threshold/plateau checks (`all_level_1`, `progression_frozen`, `xp_plateau`) but nothing synthesizing level+gear+wealth+skills into one capability trend, or checking life-arc coherence (e.g. surviving 500+ ticks with zero growth, or reaching a late Hero generation without meaningful prior growth) | **Real gap** |
| Region | `trauma_hazard_broken` (WORLD, line 942) | Covered |
| Faction | None — FACTION (§5, lines 681-718) has threshold checks (`faction_monopoly`, `all_factions_neutral`, `tension_oscillation`) but nothing catching a faction's territory/influence staying flat across a run despite ongoing `military_conflict_resolved`/`diplomatic_transition` events | **Real gap** |
| World | `world_static`, `trauma_accumulation_broken`, `ecology_broken` (WORLD, lines 940-945) | Covered |

Applying §7.1 vs §7.2: both gaps are new scoring rules on an existing pillar's existing usage
question, not new usage questions requiring their own pillar. **Conclusion: no new top-level
pillar is justified.** PROGRESSION gains an entity capability-trend + life-arc coherence rule;
FACTION gains a `trauma_hazard_broken`-style faction-trajectory rule. Region and world layers need
no change — already covered. Tracked by
`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` and
`TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`, which cite this subsection as their rationale
source; full scoping context in `TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC`.

### 7.7 Idea-Level Pillar-Mapping Completeness Cross-Check (2026-09)

`TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (M7 epic, `TCK-20260823-EPIC-RPG-M7-SIMQ-
INTEGRATION`, child 2 of 2) cross-referenced ticket 1's own finished named-pillar mapping (all 65
rows of `docs/brainstorm/design_merit_scorecard.html`'s Pillar Reach column) against the 10 real
pillars, per the epic's own Scope item 5: "every idea Pillar Reach says should touch a pillar needs
a traceable rule or an explicit, written reason it doesn't." A checklist against a known-complete
list (ticket 1's own mapping), not a fresh open-ended per-idea trace.

**Method:** every named pillar on every row must be one of the 10 real pillars (all 10 already
confirmed by ticket 1's own 90-event-type audit to have real, scored event coverage), and the named
list's count must match the raw `N/10` the axis still records.

**Result: 65/65 rows accounted for, 0 real undisclosed gaps.**

| Category | Count | Notes |
|---|---|---|
| Named pillar(s), structurally consistent | 58 | Includes the 3 dormant ideas (56/57/62) — named for the pillars they would strengthen once built, per the axis's own forward-looking question text, despite zero live event backing today |
| Bare `0/10`, no named pillar | 7 | Ideas 8, 9, 15, 16, 17, 18, 19 — matches ticket 1's own already-disclosed "governance/doc-fix/investigation-only, no real event surface" exception list exactly |
| Unrecognized pillar name or count mismatch | 0 | — |

No real gap was found, so per this ticket's own Acceptance Criteria ("any real gap... fixed or
ticketed"), no fix and no follow-up ticket were needed. Script:
`stored_artifacts/TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS/completeness_check.py`.

**Conclusion: M7's own Scope item 5 is satisfied — every one of the 65 ideas is either backed by a
real, traceable signal rule, or has an explicit, already-written reason it isn't.**

---

## 8. Data Flow & Persistence

### 8.1 Event Routing

```
QualityHub.on_envelope(envelope: ObservabilityEventEnvelope):
    if QUALITY_SCORING_DISABLED: return
    scorers = SCORER_REGISTRY.get(envelope.event_type, [])
    for scorer in scorers:
        try:
            record = scorer.score(envelope, context)
            if record:
                accumulators[record.pillar].add(record)
                persistence.write(record)
        except Exception as e:
            log.warning("scorer_error", scorer=scorer.__class__.__name__, event=envelope.event_id, error=e)
```

`SCORER_REGISTRY` maps `event_type → list[PillarScorer]`. Multiple scorers can
respond to the same event_type (e.g., `entity_killed` scores in COMBAT and may also
score in NARRATIVE if the entity was a hero-class).

### 8.2 Persistence

`quality_scores.jsonl` — one JSON line per `ScoreRecord`, appended during the run.
Written by `QualityPersistence` which wraps a non-blocking file handle (same pattern
as `EventRecorder`).

`quality_report.json` — written at run end by `QualityReport.build()`. Contains:
```json
{
  "run_id": "...",
  "tick_count": 1000,
  "overall_score": 0.82,
  "overall_grade": "A",
  "generated_at": "2026-06-28T...",
  "pillars": {
    "ECONOMY": {
      "raw_score": 145.0,
      "normalized_score": 0.145,
      "grade": "B",
      "event_count": 87,
      "negative_count": 12,
      "loop_detected": false,
      "loop_flags": [],
      "worst_events": [...]
    }
  }
}
```

Both files live in `data/runs/{run_id}/`. They are cleaned by `rm -rf data/runs/*`
per the After Work workflow rule.

---

## 9. Traceability Design

The full drill-down path from a bad grade to root cause:

```
Step 1: QualityReport → identify low-grade pillar (e.g., ECONOMY grade F)

Step 2: pillar.worst_events[:5]
  → ScoreRecord(tick=200, event_id="abc123", delta=-20.0, tags=["zero_harvest"])

Step 3: Cross-reference event_id in data/runs/{run_id}/simulation_events.jsonl
  → SimulationEvent(entity_id=7, region_id="hometown", tick=200, event_type="adventure_decision")

Step 4 (entity-level): Cross-reference entity_id=7 in cognition_graph_snapshots.jsonl
  → Why was entity 7 not routing to resource opportunities?

Step 5 (world-level): Check world.yaml or compiled state
  → len(resource_nodes) for region "hometown"

Step 6: Known root-cause library (§5 traceability paths)
  → D04 §6.2 documents the three most common zero-harvest causes; check in order
```

**No new infrastructure required.** All cross-reference targets already exist.

---

## 10. REST API Surface

### Live query (during run)

```
GET /api/v1/quality/pillars
Response: PillarSummary[] — all 10 pillars with normalized_score and grade

GET /api/v1/quality/pillars/{pillar_id}
Response: PillarDetail — full accumulator state + worst_events (top 10)

GET /api/v1/quality/alerts
Response: Alert[] — all pillars graded D or F, or with active loop_flags

GET /api/v1/quality/report
Response: QualityReport — full report snapshot (same schema as quality_report.json)

GET /api/v1/quality/status
Response: { enabled: bool, run_id: str, tick_count: int, overall_grade: str }
```

### All endpoints return `{"enabled": false}` when `QUALITY_SCORING_DISABLED=1`.

---

## 11. Testing Contract

### 11.1 Unit Tests (per scorer)

One test file per scorer: `tests/simulation_quality/test_{pillar}_scorer.py`

Required tests for every scoring rule in every scorer:

| Test type | What to verify |
|---|---|
| Positive signal | The correct positive delta is returned for the expected event |
| Negative signal | The correct negative delta is returned for the degenerate event |
| Time-gated rule | Rule fires after the configured tick threshold, not before |
| Null return | Scorer returns `None` for an event_type it does not score |
| Tag assignment | Correct tags appear in the returned ScoreRecord |
| Context usage | If scorer uses context (e.g., `context.current_tick`), verify gate |

### 11.2 Integration Tests

`tests/simulation_quality/test_quality_hub_integration.py`

| Test | What to verify |
|---|---|
| Event routed to correct scorer | `on_envelope()` with known event_type produces ScoreRecord in correct pillar |
| Accumulator updated | raw_score, event_count, worst_events updated after `on_envelope()` |
| Persistence writes | quality_scores.jsonl receives the record |
| Error isolation | Scorer exception does not propagate; other scorers continue |
| Disable mechanism | `QUALITY_SCORING_DISABLED=1` prevents any scoring; simulation unaffected |
| Loop detection | Window buffer > LOOP_THRESHOLD triggers `loop_detected` flag |

### 11.3 Regression Tests (grade stability)

`tests/simulation_quality/test_grade_regression.py`

After calibration (E7-CALIBRATE), canonical scenarios produce stable grades:

| Scenario | Expected grade per pillar |
|---|---|
| `urban_political` seed=42, 100 ticks | COMBAT: B+, FACTION: A−, ECONOMY: F (known root causes from D04) |
| `sandbox_world` seed=42, 100 ticks | AGENCY: C (RC1/RC2/RC3 resolved?), ECONOMY: F (no resource nodes) |

These grades are committed as regression anchors. Each anchor entry in `grade_anchors.json`
is an object `{"grade": "S", "score": 2.87}` — `score` is the pillar's `normalized_score`
(§4.4), not `raw_score`. A regression is now detected along **two independent dimensions**,
either of which failing blocks the anchor as a regression:

1. **Letter-grade band (±1)** — unchanged: a code change that moves a pillar grade by more
   than one letter (e.g., B → D) must be explicitly justified and the anchor updated.
2. **Score tolerance** — the live `normalized_score` must stay within
   `max(0.05, 0.20 * |anchored_score|)` of the anchored value, independent of whether the
   letter grade moved. This catches within-band magnitude regressions the letter-only check
   cannot see (e.g., an S-graded pillar's score halved but still `>2.0`, still graded S).
   The tolerance width (absolute floor 0.05, relative 20%, whichever is wider) is derived
   from an 18-run_key/180-observation same-config repeat-trial dataset: real run-to-run
   noise (driven by the kernel's wall-clock tick-budget throttle, see
   `docs/audits/D20_simq_integration.md`) concentrates at low absolute magnitude (max
   observed ~0.019 absolute delta) even where relative deltas reach up to 43.5%; the 0.05
   floor comfortably absorbs that noise while the 20% relative threshold still catches a
   50%+ magnitude regression on higher-magnitude (e.g. S-band) pillars.

### 11.4 Performance Tests

`tests/simulation_quality/test_performance.py`

| Test | Limit | Method |
|---|---|---|
| `scorer.score()` overhead per event | < 0.1 ms | `timeit` on 10,000 events |
| `QualityReport.build()` time | < 50 ms | `timeit` on full accumulator state |
| Memory: worst_events list | ≤ 100 records per pillar | Assert after 10,000 events |
| Memory: window buffer | ≤ 200 records per pillar | Assert after 10,000 events |
| quality_scores.jsonl write latency | Non-blocking (< 1 ms per record) | Async write timing |

### 11.5 Scenario Coverage Tests

`tests/simulation_quality/test_scenario_coverage.py`

For each scenario in §6 Scenario Registry:
- At least one unit test exercises the event_types listed for that scenario
- The test verifies the correct pillar scores it (not a different one)
- The test verifies the correct polarity (positive for healthy, negative for degenerate)

### 11.6 Standing Evaluation Harness

`tools/evaluate_simq.py` — compares calibration grades against `tests/simulation_quality/fixtures/grade_anchors.json` using the same ±1 band tolerance as the regression tests.

**Invocation:**

| Command | What it does |
|---|---|
| `make evaluate` | Dry-run: reads existing `data/calibration/` reports, diffs against anchors. Fast — no engine re-run. |
| `make evaluate-full` | Re-runs engine for all 14 fast anchor scenarios (≤500t), then diffs. Use after significant engine changes. |
| `python3 tools/evaluate_simq.py --scenario dungeon_crawl_seed42_200t --dry-run` | Check a single scenario without re-running the engine. |

**Output:** Aligned table with columns `run_key / pillar / anchor / actual / status`. REGRESS rows are marked with `<<`.

**Exit codes:** 0 = all PASS (MISSING is a warning, not error); 1 = at least one REGRESS; 2 = setup error (anchor file missing or invalid JSON).

**Anchor update workflow (after an intentional scoring change):**
1. Re-run calibration: `python3 tools/calibrate_simq.py --name <world> --seed <N> --ticks <T>`
2. Inspect new grades in `data/calibration/<run_key>/quality_report.json`
3. Edit `tests/simulation_quality/fixtures/grade_anchors.json` with new grades
4. Run `make evaluate` to confirm all PASS
5. Commit calibration data, fixture, and any doc/ledger updates together

**Feature-flag activation is profile-driven, not harness-driven:** `evaluate_simq.py` does not
special-case any scenario by name to decide which feature flags are active during a calibration
run. Every flag — including `ENABLE_ADVENTURE_ROUTING` — is activated the same way: by adding a
`feature_flags:` block to that world's `config/simulation_quality/profiles/<name>.yaml` (see §4.8),
read generically by `calibrate_simq.py::_load_profile_feature_flags()`. `simq_routing_test.yaml`
sets `ENABLE_ADVENTURE_ROUTING: "ON"` this way; no other archetype world's profile sets it, so
`ENABLE_ADVENTURE_ROUTING` remains OFF (default) for `urban_political`, `dungeon_crawl`, and
`default` — consistent with `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`. (Prior to
`TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`, `simq_routing_test`'s 3 anchor scenarios were
the sole exception, activated via a hardcoded `ROUTING_KEYS` set and env-var injection inside
`evaluate_simq.py` itself; that special case has been removed.)

---

## 12. Acceptance Criteria

Closed out 2026-07-11 (`TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`, hotfix tier — verification and
citation only, no engine/scorer logic changed) — every item below was re-verified against current
`src/`/`tests/` state in that ticket's own session, not assumed unchanged since authoring. See
`tickets/done/TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT.md`'s Implementation Notes for the full
verification trail (test commands run, live code reads performed).

### Functional

- [x] All 10 pillars produce ScoreRecord entries when their event_types are emitted — `tests/simulation_quality/test_scenario_coverage.py` (36 tests spanning all 10 scorers, all passing) + 10 per-scorer unit test files (`tests/simulation_quality/test_{agency,cognition,combat,economy,faction,information,narrative,progression,social,world_dynamics}_scorer.py`)
- [x] Health grades assigned for all 10 pillars in `QualityReport` — `src/simulation_quality/quality_hub.py:109-111` (`QualityHub` builds one `PillarAccumulator` per `PillarId`, all 10) + `src/simulation_quality/quality_report.py:98-113` (`QualityReportBuilder.build` assigns a grade per accumulator passed in) + `tests/simulation_quality/test_report.py::test_overall_score_weighted_average` (iterates `for pillar in PillarId`)
- [x] `quality_scores.jsonl` written to `data/runs/{run_id}/` during every run — `src/simulation_quality/persistence.py:17-24` (`QualityPersistence.__init__` opens the file) + `tests/simulation_quality/test_persistence.py::test_write_appends_jsonl_line`
- [x] `quality_report.json` written at run end with correct schema — `src/simulation_quality/persistence.py:46-54` (`write_report`, atomic tmp+rename) + `src/engine/kernel.py:964-972` (`Kernel.shutdown()` calls `write_report` at run end) + `tests/simulation_quality/test_persistence.py::test_write_report_creates_json_file`
- [x] REST endpoints respond with correct data for live and post-run queries — `src/simulation_quality/api/routes.py` (5 `@router.get` endpoints) + `tests/simulation_quality/test_api_routes.py` (14 tests, all passing)
- [x] All 22 scenarios in §6 are covered by at least one unit test — `tests/simulation_quality/test_scenario_coverage.py` (36 tests passing, covering SQ-01 through SQ-23; §6 now has 23 registered scenarios, a superset of the "22" this item was authored against — all current entries are covered)

### Performance

- [x] Simulation tick timing is not measurably affected by quality scoring (< 1% overhead) — `src/observability/event_recorder.py::EventRecorder.record` (enqueues only, no scorer call on the tick thread) + `src/observability/queue.py::QueueDrainWorker._run` (invokes `quality_fn` on a separate daemon thread, `name="observability-drain-worker"`, fully decoupled from tick execution) — confirmed by direct code read 2026-07-11; **measured** 2026-08-04 (TCK-20260702-OBSISO-ISOLATION-PROOF, G5): `docs/performance/simq_isolation_overhead.md` — in-process mode showed no measurable engine-CPU overhead vs. the `QUALITY_SCORING_DISABLED=1` baseline (-8.4% on the committed run, i.e. within measurement noise, not a real cost), broker mode +0.6% — both consistent with the "< 1%" figure above; `tests/perf/test_simq_isolation_overhead.py`
- [x] `QUALITY_SCORING_DISABLED=1` produces bit-identical simulation output — `src/simulation_quality/feed.py::build_feed_from_env` lines 125-126, unconditional short-circuit re-read directly 2026-07-11 (`if os.environ.get("QUALITY_SCORING_DISABLED") == "1": return None`, checked before any mode branching) + `tests/simulation_quality/test_feed.py::test_build_feed_returns_none_when_disabled` — run this session, passes (see corrected `docs/parity_ledger/infrastructure.yaml` INFRA-233, whose `test_path` had gone stale)
- [x] Scoring exceptions are caught and logged; they do not propagate to simulation — `src/simulation_quality/quality_hub.py::QualityHub.on_envelope` lines 135-159 re-read directly 2026-07-11: disabled check at entry, then `try/except Exception` wraps every `scorer.score()` call individually, logging at `logger.warning(...)` — no exception can escape the loop + `tests/simulation_quality/test_quality_hub_integration.py::TestErrorIsolation::test_scorer_exception_does_not_propagate` — run this session, passes
- [x] `scorer.score()` runs in < 0.1 ms per event — `tests/simulation_quality/test_performance.py::test_agency_scorer_median_under_0_1ms`, `::test_combat_scorer_median_under_0_1ms` — run with `pytest -m slow` this session, passes
- [x] `QualityReport.build()` runs in < 50 ms — `tests/simulation_quality/test_performance.py::test_quality_report_build_under_50ms` — passes

### Scalability

- [x] `PillarAccumulator.worst_events` never exceeds 100 entries — `tests/simulation_quality/test_performance.py::test_worst_events_bounded_at_100` — passes
- [x] `PillarAccumulator.window_buffer` never exceeds 200 entries — `tests/simulation_quality/test_performance.py::test_window_buffer_bounded_at_200` — passes
- [x] Architecture is separate-process-ready: `QualityHub` consumes only serializable inputs — `src/observability/events.py::ObservabilityEventEnvelope` (dataclass of `str`/`int`/`dict`/`tuple` fields only, no live object references) + `src/simulation_quality/feed.py::BrokerQualityFeed` (delivers the same envelope type across a Redis stream in broker mode) — confirmed by direct code read 2026-07-11

### Extensibility

- [x] Adding a new pillar requires only: new `PillarId` value + new `PillarScorer` subclass + `SCORER_REGISTRY` entry + §6 scenario entry — zero changes to `QualityHub` routing logic — `src/simulation_quality/quality_hub.py:103-107` (`SCORER_REGISTRY` built generically from each scorer's declared `EVENT_TYPES`, no per-pillar branching) + `src/simulation_quality/scorers/__init__.py::build_all_scorers` (adding a pillar is one new list entry) — confirmed by direct code read 2026-07-11
- [x] Adding a new scoring rule to an existing pillar requires only: new branch in `scorer.score()` + new unit test + §6 scenario entry if new scenario — `src/simulation_quality/scorers/agency.py::AgencyScorer.score` (single method, one `score()` per pillar, event_type/payload-branched) + `tests/simulation_quality/test_agency_scorer.py` (one test per rule) — confirmed by direct code read 2026-07-11
- [x] `QualityProfile` overrides pillar weights without touching scorer code — `src/simulation_quality/weights.py::ScoringWeights.load`/`_load_profile_weights` (loads `config/simulation_quality/profiles/{profile}.yaml`, no scorer file touched) + `tests/simulation_quality/test_weights.py::test_dungeon_crawl_profile_overrides`, `::test_urban_political_profile_overrides` — passes

### Traceability

- [x] Every `ScoreRecord` in `worst_events` has a valid `event_id` that cross-references `simulation_events.jsonl` — `src/simulation_quality/scorers/*.py` (all 10 scorers set `event_id=envelope.event_id`, e.g. `src/simulation_quality/scorers/agency.py:51`) + `src/observability/event_recorder.py:114` (`EventRecorder` writes that same `envelope.event_id` into `simulation_events.jsonl`) — confirmed by direct code read 2026-07-11: both paths consume the same `ObservabilityEventEnvelope` instance, so the id is identical by construction
- [x] Every low-grade pillar has at least one worst_event with a tag matching §5 — `tests/simulation_quality/test_agency_scorer.py` (per-rule tests assert the exact §5-documented tag string is present on every produced `ScoreRecord`, e.g. `"stasis_N"`, `"population_stasis"`, `"rejection_cascade"`) + `tests/simulation_quality/test_accumulator.py::test_worst_events_sorted_by_abs_delta_desc` (`worst_events` preserves the full tagged `ScoreRecord`, no tag stripping) — passes
- [x] The traceability path in §9 is validated by an integration test — `tests/simulation_quality/test_traceability_path.py::test_worst_event_id_resolves_in_simulation_events_jsonl` and `::test_worst_event_id_matches_originating_envelope_exactly` (injects a `combat_hard_law_violation` event via a minimal `Kernel`, asserts `worst_events[0].event_id` from the in-memory `QualityReport` resolves to, and exactly matches the originating fields of, an entry in the same run's `simulation_events.jsonl`) — passes, resolved 2026-07-13 (TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST)

### Testing

- [x] Unit tests for every scoring rule in every scorer (positive, negative, null, time-gated) — 10 per-scorer test files (`tests/simulation_quality/test_{agency,cognition,combat,economy,faction,information,narrative,progression,social,world_dynamics}_scorer.py`) + `tests/simulation_quality/test_timegate_penalties.py` (4 time-gated test classes: `TestEconomyTimegate`, `TestProgressionTimegate`, `TestNarrativeTimegate`, `TestAgencyTimegate`) — full `tests/simulation_quality/` suite: 456 passed, 5 skipped (broker tests requiring `REDIS_AVAILABLE`), run 2026-07-11
- [x] Integration tests for hub routing, accumulation, persistence, error isolation, disable — `tests/simulation_quality/test_quality_hub_integration.py` (`TestEventRouting`, `TestAccumulation`, `TestPersistence`, `TestErrorIsolation`, `TestDisableMechanism` classes) — passes
- [x] Regression anchors committed for canonical scenarios — `tests/simulation_quality/test_grade_regression.py` + `tests/simulation_quality/fixtures/grade_anchors.json` — passes (`pytest -m "not slow"` and `pytest -m slow` both run clean 2026-07-11)
- [x] Performance tests pass against limits in §11.4 — `tests/simulation_quality/test_performance.py` — 6/6 passed with `pytest -m slow`, run 2026-07-11
- [x] Scenario coverage test verifies all 22 §6 entries have at least one test — `tests/simulation_quality/test_scenario_coverage.py` — 36/36 passed, covers all current §6 entries (SQ-01 through SQ-23)

---

## 13. Implementation Epics & Child Tickets

Parent epic: `tickets/inprogress/TCK-20260628-SIMQ-EPIC.md`

| Ticket | Title | Delivers |
|---|---|---|
| TCK-20260628-SIMQ-E1-FOUNDATION | Core Models & Data Layer | `PillarId`, `ScoreRecord`, `ScoringContext`, `PillarAccumulator`, `QualityReport`, `QualityPersistence` |
| TCK-20260628-SIMQ-E2-HUB-CORE | Hub Wiring + Core Scorers | `QualityHub` subscriber + routing; `AgencyScorer`, `CombatScorer` |
| TCK-20260628-SIMQ-E3-SCORERS-A | Scorers Batch A | `CognitionScorer`, `FactionScorer`, `EconomyScorer`, `ProgressionScorer` |
| TCK-20260628-SIMQ-E4-SCORERS-B | Scorers Batch B | `SocialScorer`, `InformationScorer`, `WorldDynamicsScorer`, `NarrativeScorer` |
| TCK-20260628-SIMQ-E5-API | REST API + Artifact Generation | REST routes, post-run `quality_report.json` |
| TCK-20260628-SIMQ-E6-TESTS | Full Test Suite | Unit, integration, regression, performance, scenario coverage tests |
| TCK-20260628-SIMQ-E7-CALIBRATE | Calibration & Threshold Tuning | Baseline runs, grade threshold constants, regression anchor commits |

Implementation order: E1 → E2 → E3 → E4 → E5 → E6 → E7.
E3 and E4 can proceed in parallel after E2.

---

## 14. Non-Goals for MVP

- Per-entity quality profiles (pillar scores are run-level; entity-level breakdown is post-MVP)
- Historical run comparison (cross-run scoring requires baseline storage infrastructure)
- Real-time WebSocket push alerts (REST polling sufficient for MVP)
- ML-based anomaly detection (deterministic rules only; ML requires labeled training data)
- Automatic world config suggestion ("your Economy score is F, try adding resource nodes") — advisory only, no automation
- Score-to-mastery engine feedback (future; controlled via authoritative pipeline §11 of investigation source)
