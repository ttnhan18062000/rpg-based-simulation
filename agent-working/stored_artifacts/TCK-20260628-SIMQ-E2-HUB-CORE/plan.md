---
artifact_type: plan
ticket_id: TCK-20260628-SIMQ-E2-HUB-CORE
---

# Plan — TCK-20260628-SIMQ-E2-HUB-CORE

## Ordered Steps

### Step 1 — Scorer base class
**File:** `src/simulation_quality/scorers/base.py`
- `PillarScorer(ABC)` with `EVENT_TYPES: tuple[str, ...]`, `__init__(weights: ScoringWeights)`, abstract `score(envelope, context) -> ScoreRecord | None`
- `src/simulation_quality/scorers/__init__.py` — empty init

**Scope guard:** No imports from engine/domains/systems.

---

### Step 2 — AgencyScorer
**File:** `src/simulation_quality/scorers/agency.py`

EVENT_TYPES: `action_executed`, `route_selected`, `defer_with_reason`, `project_started`, `project_completed`, `project_abandoned`, `commitment_abandoned`, `rejection_cascade_tick`, `route_family_first_use`

Logic (all deltas from `self.weights["key"]`; time gates from `self.weights.int_param("key")`):
- `action_executed` → +`action_taken`, tags=(`action_taken`,)
- `route_family_first_use` → +`route_novelty` + +`entropy_reward`, tags=(`route_novelty`, `entropy_reward`)
- `project_completed`:
  - if `payload.get("is_commitment")` → +`commitment_complete`, tags=(`commitment_complete`,)
  - else → +`project_done`, tags=(`project_done`,)
- `route_selected` → +`navigation_active`, tags=(`navigation_active`,)
- `defer_with_reason`:
  - base: +`defer_idle`, tags=(`defer_idle`,)
  - check window: `context.window_tag_counts[AGENCY].get("defer_idle", 0)` > `stasis_gate_ticks` → add +`stasis_per_tick` × (count − gate), tags+=(`stasis_N`,)
  - if window shows action_taken=0 and tick > gate → score `population_stasis` once (_pop_stasis_fired flag)
- `rejection_cascade_tick`:
  - payload `count` > 500 → +`rejection_cascade_sustained`
  - elif count > 100 → +`rejection_cascade`
- `project_abandoned`: store `_last_abandoned[entity_id] = payload.get("project_type")`
- `project_started`: if `_last_abandoned.get(entity_id)` == `payload.get("project_type")` → +`project_cycle`, then clear entry

Scorer maintains minimal state: `_last_abandoned: dict[int, str]`, `_pop_stasis_fired: bool`

---

### Step 3 — CombatScorer
**File:** `src/simulation_quality/scorers/combat.py`

EVENT_TYPES: `combat_initiated`, `combat_resolved`, `combat_damage`, `entity_killed`, `near_death_survival`, `combat_hard_law_violation`, `attrition_threshold_crossed`

Logic:
- `combat_initiated` → +`combat_active`
- `combat_resolved` → +`combat_resolved`
- `near_death_survival` → +`survival_tension`
- `combat_damage`: if `payload.get("tactical_modifier")` and not in `_seen_modifiers` → +`tactical_variety`, add to set
- `entity_killed`:
  - always: +`attrition`
  - if tick < `early_extinction_before_tick` and not `_early_ext_fired` → +`early_extinction`, set flag
- `attrition_threshold_crossed`:
  - `payload["threshold"] >= 0.9` and tick ≤ `attrition_90pct_by_tick` → +`extinction_degenerate`
  - elif `payload["threshold"] >= 0.5` and tick ≤ `attrition_50pct_by_tick` → +`attrition_spiral`
- `combat_hard_law_violation` → +`combat_hard_law`
- time-gated zero-combat (`combat_dormant`): on any combat event scored after `zero_combat_by_tick` if `context.pillar_event_counts.get(PillarId.COMBAT, 0) == 0` and not `_dormant_fired` → +`combat_dormant`

Scorer maintains: `_seen_modifiers: set[str]`, `_early_ext_fired: bool`, `_dormant_fired: bool`

---

### Step 4 — QualityHub
**File:** `src/simulation_quality/quality_hub.py`

```python
class QualityHub:
    def __init__(self, scorers: list[PillarScorer], weights: ScoringWeights, 
                 persistence: QualityPersistence, run_id: str = "unknown") -> None:
        self._disabled = os.environ.get("QUALITY_SCORING_DISABLED") == "1"
        self._weights = weights
        self._persistence = persistence
        self._run_id = run_id
        self._tick = 0
        self._entity_count = 0
        # Build SCORER_REGISTRY from scorers' EVENT_TYPES
        self.SCORER_REGISTRY: dict[str, list[PillarScorer]] = {}
        for scorer in scorers:
            for et in scorer.EVENT_TYPES:
                self.SCORER_REGISTRY.setdefault(et, []).append(scorer)
        # Per-pillar accumulators
        self._accumulators: dict[PillarId, PillarAccumulator] = {
            pid: PillarAccumulator(pid, weights) for pid in PillarId
        }
        self._lock = threading.Lock()
    
    def on_envelope(self, envelope: ObservabilityEventEnvelope) -> None:
        if self._disabled:
            return
        with self._lock:
            self._tick = max(self._tick, envelope.tick)
        context = self.build_context()
        scorers = self.SCORER_REGISTRY.get(envelope.event_type, [])
        for scorer in scorers:
            try:
                record = scorer.score(envelope, context)
                if record is not None:
                    self._accumulators[record.pillar].add(record)
                    self._persistence.write(record)
            except Exception as exc:
                logger.warning("scorer_error scorer=%s event=%s error=%s", 
                               scorer.__class__.__name__, envelope.event_id, exc)
    
    def build_context(self) -> ScoringContext:
        with self._lock:
            tick = self._tick
            entity_count = self._entity_count
        snaps = {pid: acc.snapshot() for pid, acc in self._accumulators.items()}
        pillar_scores = {pid: snaps[pid]["raw_score"] for pid in PillarId}
        pillar_event_counts = {pid: snaps[pid]["event_count"] for pid in PillarId}
        window_tag_counts: dict[PillarId, dict[str, int]] = {}
        for pid in PillarId:
            tag_counts: Counter[str] = Counter()
            for rec in snaps[pid]["window_buffer"]:
                for tag in rec.tags:
                    tag_counts[tag] += 1
            window_tag_counts[pid] = dict(tag_counts)
        return ScoringContext(
            run_id=self._run_id,
            current_tick=tick,
            entity_count=entity_count,
            pillar_scores=pillar_scores,
            pillar_event_counts=pillar_event_counts,
            window_tag_counts=window_tag_counts,
        )
    
    def update_entity_count(self, count: int) -> None:
        with self._lock:
            self._entity_count = count
    
    def get_pillar_score(self, pillar: PillarId) -> float:
        return self._accumulators[pillar].snapshot()["raw_score"]
    
    def get_pillar_grade(self, pillar: PillarId) -> str:
        from src.simulation_quality.quality_report import _assign_grade, QualityReportBuilder
        snap = self._accumulators[pillar].snapshot()
        normalized = snap["raw_score"] / max(1, self._tick)
        return _assign_grade(normalized, self._weights.grade_thresholds)
    
    def get_quality_report(self) -> QualityReport:
        return QualityReportBuilder.build(self._accumulators, self._tick, self._run_id, self._weights)
    
    def start(self, feed: QualityFeedAdapter) -> None:
        feed.start(self)
    
    def stop(self, feed: QualityFeedAdapter) -> None:
        feed.stop()
```

---

### Step 5 — BrokerQualityFeed (complete implementation)
**File:** `src/simulation_quality/feed.py` (modify existing)

Replace stub `start()` with:
- Create `RedisStreamConsumer(broker_url, stream_name, consumer_group)`
- Try `connect()` — if fails, log WARNING, set `_health_status = "unavailable"`, return
- Spawn daemon thread running `_consume_loop(hub)`
- `_consume_loop`: calls `consumer.read_and_process(callback)` in a loop; callback converts `SimulationEvent → ObservabilityEventEnvelope.from_simulation_event()` then calls `hub.on_envelope()`
- `stop()`: set `_running = False`, join thread, call `consumer.close()`
- `health()`: return status based on `_health_status`

---

### Step 6 — worker.py
**File:** `src/simulation_quality/worker.py`

- `QualityWorker` class: creates `BrokerQualityFeed`, `QualityPersistence`, `QualityHub`
- Loads `ScoringWeights` from config
- Builds full scorer list: `AgencyScorer(weights)`, `CombatScorer(weights)` (others added in E3/E4)
- Runs `feed.start(hub)` and blocks on SIGTERM
- Serves `GET /health` on `QUALITY_WORKER_PORT` (default 8082) in a daemon thread
- `if __name__ == "__main__"` entry point for `python -m src.simulation_quality.worker`

---

### Step 7 — Tests
**Files:**
- `tests/simulation_quality/test_agency_scorer.py`
- `tests/simulation_quality/test_combat_scorer.py`
- `tests/simulation_quality/test_quality_hub_integration.py`

---

## Scope Guards

- Do NOT change any file in `src/engine/`, `src/domains/`, `src/systems/`
- Do NOT modify `PillarAccumulator`, `ScoreRecord`, `ScoringContext`, `QualityReport`, `QualityPersistence`, `ScoringWeights` (E1 artifacts)
- Do NOT import from `src/engine/` or `src/domains/` in any scorer or hub file
- `BrokerQualityFeed` only imports `RedisStreamConsumer` from observability; QualityHub does not

## Dependency Map

Step 1 (base) → Step 2 (agency) → Step 3 (combat) → Step 4 (hub) → Step 5 (broker) → Step 6 (worker) → Step 7 (tests)

## Acceptance Criteria Mapping

- AC 1 (hub takes feed param) → Step 4 (constructor signature)
- AC 2 (exception catch) → Step 4 (on_envelope try/except)
- AC 3 (QUALITY_SCORING_DISABLED) → Step 4
- AC 4 (InProcess.start) → E1 already done
- AC 5 (BrokerFeed.start) → Step 5
- AC 6 (QUALITY_FEED_MODE=broker test) → Step 7
- AC 7 (worker.py) → Step 6
- AC 8–12 (scorer rules) → Steps 2–3
- AC 13–16 (tests) → Step 7
