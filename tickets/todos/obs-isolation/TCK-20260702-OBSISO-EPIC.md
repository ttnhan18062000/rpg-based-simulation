---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-EPIC
phase: open
date: 2026-07-02
tags: [epic, observability, simulation-quality, process-isolation, broker-mode, hot-path]
---

# TCK-20260702-OBSISO-EPIC

## Title
Observability & SimQ Process Isolation — make external evaluation components engine-isolated, toggleable, and separate-process capable

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
External evaluation components (SimQ scoring, decision tracing) must not affect engine main-process performance, must not be tied into the engine, must be toggleable, and must be runnable as a separate process (future: container). Investigation (2026-07-02) found the architecture ~80% built — stream producer, consumer, broker feed, and a standalone `QualityWorker` all exist — but four verified defects block the requirements: a producer/consumer stream-name default mismatch, a 2-of-10-pillar scorer registry in the worker, unverified kernel feed routing in broker mode, and a hot-path contract violation in `DecisionTraceWriter`. Isolation is also unproven by measurement. Full analysis: `docs/plans/observability_process_isolation.md`.

## Scope
Track and sequence the four child tickets. No direct implementation.

## Out of Scope
- Containerization artifacts (Dockerfile/compose) — follow-up after broker mode is proven end-to-end
- Intention-log behavioral extensions (ring buffer, Chronicle surprise, social-memory annotation) — remain ideas per `idea_intention_log_first_class.md`
- NATS/Kafka stream backends

## Acceptance Criteria
- All four child tickets DONE
- A run with `QUALITY_FEED_MODE=broker` + `python -m src.simulation_quality.worker` produces grades equivalent to in-process mode with zero SimQ code executing in the engine process
- `DecisionTraceWriter` performs no file IO on the hot path
- Documented overhead numbers for off / in-process / broker modes

## Related Tickets
TCK-20260702-OBSISO-TRACE-ASYNC, TCK-20260702-OBSISO-BROKER-CONFIG, TCK-20260702-OBSISO-WORKER-PARITY, TCK-20260702-OBSISO-ISOLATION-PROOF. Prior art: TCK-20260520-SIM-OBS-M36 (RedisStreamAdapter), TCK-20260630-SIMQ-WIRE-KERNEL (quality_fn wiring), TCK-20260619-E22A (DecisionTraceWriter).

## Related Docs
docs/plans/observability_process_isolation.md, docs/architecture/observability_hot_path_safety_contract.md, docs/engine/contracts/infrastructure_compat_contract.md, docs/guides/simulation_quality.md, docs/observability/decision_trace_contract.md

## Related Stored Artifacts
none yet

## Related Code Areas
src/observability/event_recorder.py, src/observability/stream/, src/observability/queue.py, src/simulation_quality/feed.py, src/simulation_quality/worker.py, src/observability/cognition/decision_trace_writer.py, src/engine/kernel.py

## Assumptions / Open Questions
- Redis is the accepted broker for separate-process mode (already the shipped adapter); container orchestration is deferred.
- Grade parity between modes is defined as identical `ScoreRecord` streams for the same replayed event stream (determinism law applies to scoring, not just the engine).

## Implementation Notes
Sequencing rationale in SEQUENCE.md: TRACE-ASYNC is independent; BROKER-CONFIG must land before WORKER-PARITY (parity test needs a connectable pipeline); ISOLATION-PROOF benchmarks all modes last.

## Test Summary
(epic — see children)

## Files Changed
(epic — see children)

## Completion Summary
(pending)
