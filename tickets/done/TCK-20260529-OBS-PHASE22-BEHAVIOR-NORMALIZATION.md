# TCK-20260529-OBS-PHASE22-BEHAVIOR-NORMALIZATION

## Title

Phase 22 — Async Behavior Normalization Worker

## Status

DONE

## Request Summary

Implement Phase 22 of the Observability & Behavior Profiling roadmap: convert raw simulation events into semantic behavior events outside the hot path. Also includes Phase 28 initial guard (queue full, worker failure, determinism checks).

## Scope

- Define `BehaviorEvent` dataclass in `src/observability/behavior/`
- Implement `BehaviorEventNormalizer` mapping SimulationEvent types → behavior categories/families
- Implement `BehaviorWorker` for async/post-run processing from JSONL or in-process queue
- Add Phase 28 initial guard tests: queue full non-blocking, worker failure isolation, OFF/ON determinism
- Unit and integration tests per roadmap spec

## Out of Scope

- Phase 23 (timelines/episodes)
- Phase 24 (behavior metrics)
- Phase 25+ (pattern detectors, scorecards)
- Dashboard or warehouse integration

## Acceptance Criteria

- `BehaviorEvent` is frozen dataclass with all required fields
- `BehaviorEventNormalizer` maps: MovementEvent→movement/travel, CombatDamageEvent→combat/engage, CombatKillEvent→combat/kill_or_defeat, QuestEvent→quest/progress, GoldTransactionEvent→trade/buy_sell_or_reward
- Unknown events are skipped or handled deterministically
- `BehaviorWorker` can process a JSONL file post-run
- `BehaviorWorker` failure does not affect engine
- Phase 28 initial guard: queue full does not block tick, worker exception does not crash engine
- All tests pass

## Related Tickets

- TCK-20260529-OBS-PHASE19 (done)
- TCK-20260529-OBS-PHASE20 (done)
- TCK-20260529-OBS-PHASE21 (done)

## Related Docs

- docs/architecture/observability_behavior_profiling_boundary.md
- entity_enhance_phase19_28.md (Phase 22 section)

## Related Stored Artifacts

- staging_artifacts/TCK-20260529-OBS-PHASE22-BEHAVIOR-NORMALIZATION/

## Related Code Areas

- src/observability/behavior/
- src/observability/events.py
- src/observability/queue.py
- tests/unit/observability/behavior/
- tests/integration/observability/

## Assumptions / Open Questions

- BehaviorWorker processes JSONL for post-run use; in-process queue drain is secondary
- Normalization does not require world state — stateless per-event mapping
- Phase 28 initial guard tests reuse Phase 21 queue/worker infrastructure

## Implementation Notes

(to be filled during work)

## Test Summary

- tests/unit/observability/behavior/test_phase22_behavior_event_model.py
- tests/unit/observability/behavior/test_phase22_behavior_event_normalizer.py
- tests/integration/observability/test_phase22_behavior_worker_from_jsonl.py
- tests/integration/observability/test_phase22_behavior_worker_from_stream.py
- tests/unit/observability/budget/ (Phase 28 initial guard)
- tests/integration/observability/test_phase28_observability_degradation.py

## Files Changed

(to be filled)

## Completion Summary

(to be filled)
