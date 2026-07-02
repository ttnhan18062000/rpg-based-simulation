---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E2-HUB-CORE
phase: done
date: 2026-06-28
tags: [simulation-quality, scoring, hub, agency, combat]
---

# TCK-20260628-SIMQ-E2-HUB-CORE

## Title
Simulation Quality Scoring — Hub Wiring + Agency & Combat Scorers

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the `QualityHub` subscriber that wires the quality layer to the observability
event bus, and implement the first two pillar scorers (Agency & Action and Combat).
These two scorers were chosen first because they cover the highest-signal scenarios
(SQ-01 through SQ-04) and validate the scorer pattern before batch implementation.

## Scope
- `src/simulation_quality/scorers/__init__.py`
- `src/simulation_quality/scorers/base.py` — `PillarScorer` abstract base class:
  `score(envelope: ObservabilityEventEnvelope, context: ScoringContext) -> ScoreRecord | None`
- `src/simulation_quality/quality_hub.py` — `QualityHub`:
  - Constructor takes `feed: QualityFeedAdapter` (dependency injection — not hardwired to drain)
  - `SCORER_REGISTRY: dict[str, list[PillarScorer]]` — event_type to scorer mapping
  - `on_envelope(envelope)` — route, score, accumulate, persist, catch exceptions
  - `QUALITY_SCORING_DISABLED` env var check at construction time
  - `build_context()` — assembles `ScoringContext` from current accumulator state
  - `get_pillar_score(pillar: PillarId) -> float` (read-only query)
  - `get_pillar_grade(pillar: PillarId) -> str` (read-only query)
  - `get_quality_report() -> QualityReport` (read-only query)
  - `start()` / `stop()` — delegates to `feed.start(self)` / `feed.stop()`
- `src/simulation_quality/feed.py` additions (building on E1 ABC + InProcess):
  - `BrokerQualityFeed` — wraps `RedisStreamConsumer` from `src/observability/stream/consumer.py`;
    calls `hub.on_envelope()` from the consumer callback; reads `QUALITY_BROKER_URL`,
    `QUALITY_STREAM_NAME`, `QUALITY_CONSUMER_GROUP` from env; skip gracefully if Redis unavailable
  - `build_feed_from_env()` factory extended: returns `BrokerQualityFeed` when
    `QUALITY_FEED_MODE=broker`
- `src/simulation_quality/worker.py` — `QualityWorker` entry point for separate-process mode:
  - Instantiates `BrokerQualityFeed` + `QualityHub` + `QualityPersistence`
  - Runs consumer loop until SIGTERM
  - Serves `GET /health` on `QUALITY_WORKER_PORT` (default 8082)
  - Intended invocation: `python -m src.simulation_quality.worker`
- `src/simulation_quality/scorers/agency.py` — `AgencyScorer`:
  All scoring rules from contract §5 AGENCY & ACTION
  Scenarios covered: SQ-01, SQ-02 (primary), SQ-12 (secondary via action signal)
- `src/simulation_quality/scorers/combat.py` — `CombatScorer`:
  All scoring rules from contract §5 COMBAT
  Scenarios covered: SQ-03, SQ-04 (primary)

## Out of Scope
- Remaining 8 scorers (E3, E4)
- REST API (E5)

## Acceptance Criteria
- [ ] `QualityHub.__init__` takes a `feed: QualityFeedAdapter` parameter; does NOT
  directly reference `BoundedObservabilityQueue` or `RedisStreamConsumer`
- [ ] `QualityHub.on_envelope()` catches all scorer exceptions and logs them at WARNING;
  simulation never receives the exception
- [ ] `QUALITY_SCORING_DISABLED=1` causes `QualityHub` to return immediately from
  `on_envelope()` without scoring or writing
- [ ] `InProcessQualityFeed.start(hub)` registers drain callback; simulation behavior unchanged
- [ ] `BrokerQualityFeed.start(hub)` creates a `RedisStreamConsumer` and begins consuming;
  skips gracefully (logs WARNING, sets health status "unavailable") if Redis is not reachable
- [ ] `BrokerQualityFeed` mode passes `QUALITY_FEED_MODE=broker` integration test
  (skipped automatically when `REDIS_AVAILABLE` is not set in CI)
- [ ] `worker.py` starts without error and exits cleanly on SIGTERM
- [ ] `AgencyScorer` covers all rules in contract §5 AGENCY & ACTION table
- [ ] `AgencyScorer` returns `None` for event_types not in its registry
- [ ] `CombatScorer` covers all rules in contract §5 COMBAT table
- [ ] Time-gated rules (e.g., "zero combat after tick 200") use `context.current_tick`
- [ ] Loop detection: `DEFER_WITH_REASON` at >70% of 200-tick window fires
  `loop_detected:entity_stasis` in AGENCY accumulator
- [ ] Unit tests: all scoring rules (positive + negative + null + time-gated + tag)
- [ ] Integration test: end-to-end `on_envelope()` → accumulator update → persistence write
- [ ] Integration test: scorer exception does not propagate; other scorers continue
- [ ] Integration test: disable env var → no accumulator update, no persistence write

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Requires: TCK-20260628-SIMQ-E1-FOUNDATION
- Next: TCK-20260628-SIMQ-E3-SCORERS-A, TCK-20260628-SIMQ-E4-SCORERS-B (parallel)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §2 (Architectural Position)
- `docs/simulation_quality/quality_scoring_contract.md` §3 (Performance Contract)
- `docs/simulation_quality/quality_scoring_contract.md` §5 AGENCY, COMBAT
- `docs/simulation_quality/quality_scoring_contract.md` §6 SQ-01–SQ-04
- `docs/simulation_quality/quality_scoring_contract.md` §7.1 (Extensibility Protocol)
- `docs/simulation_quality/quality_scoring_contract.md` §8 (Data Flow)
- `src/observability/queue.py` — drain callback subscription pattern

## Implementation Notes
Implemented as designed. `SCORER_REGISTRY` is built in `QualityHub.__init__` by iterating scorer `EVENT_TYPES` — no hardcoded dispatch chain. `BrokerQualityFeed.start()` uses lazy import of `RedisStreamConsumer` and converts `SimulationEvent → ObservabilityEventEnvelope.from_simulation_event()` before calling `hub.on_envelope()`. `BrokerQualityFeed` skips gracefully when Redis is unreachable (health=unavailable). `worker.py` blocks on SIGTERM and writes the final report on shutdown. All scorer deltas read from `ScoringWeights` config — no numeric literals.

## Test Summary
98 tests passing (55 new + 43 existing). Tests cover: AgencyScorer all rules (positive, negative, time-gated, null, tags), CombatScorer all rules, QualityHub integration (routing, accumulation, persistence, error isolation, disable mechanism, read-only queries), feed behavior (InProcess, Broker graceful skip on Redis unavailable). All E1 regression tests pass.

## Files Changed
- `src/simulation_quality/scorers/__init__.py` (new)
- `src/simulation_quality/scorers/base.py` (new — PillarScorer ABC)
- `src/simulation_quality/scorers/agency.py` (new — AgencyScorer)
- `src/simulation_quality/scorers/combat.py` (new — CombatScorer)
- `src/simulation_quality/quality_hub.py` (new — QualityHub)
- `src/simulation_quality/feed.py` (modified — BrokerQualityFeed full implementation)
- `src/simulation_quality/worker.py` (new — QualityWorker entry point)
- `tests/simulation_quality/test_agency_scorer.py` (new)
- `tests/simulation_quality/test_combat_scorer.py` (new)
- `tests/simulation_quality/test_quality_hub_integration.py` (new)
- `tests/simulation_quality/test_feed.py` (modified — updated BrokerQualityFeed test)
- `docs/parity_ledger/infrastructure.yaml` (modified — INFRA-236 through INFRA-239)

## Completion Summary
Implemented QualityHub (feed-mode-agnostic event router with SCORER_REGISTRY, exception isolation, disable env var, per-pillar accumulators, read-only query API), PillarScorer base class, AgencyScorer (all §5 rules including time-gated stasis, project cycle detection, population stasis), CombatScorer (all §5 rules including time-gated extinction detection, tactical variety tracking), BrokerQualityFeed (full Redis consumer wiring with graceful Redis-unavailable fallback), and QualityWorker subprocess entry point. 98 tests pass.
