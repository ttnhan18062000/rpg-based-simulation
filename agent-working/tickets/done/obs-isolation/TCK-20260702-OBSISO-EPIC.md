---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-EPIC
phase: done
date: 2026-07-02
tags: [epic, observability, simulation-quality, process-isolation, broker-mode, hot-path]
---

# TCK-20260702-OBSISO-EPIC

## Title
Observability & SimQ Process Isolation — make external evaluation components engine-isolated, toggleable, and separate-process capable

## Status
DONE

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
- [x] All four child tickets DONE. Verified directly: `TCK-20260702-OBSISO-TRACE-ASYNC`,
      `TCK-20260702-OBSISO-BROKER-CONFIG`, `TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX`,
      `TCK-20260702-OBSISO-ISOLATION-PROOF` all show `## Status DONE` in `tickets/done/`.
- [x] A run with `QUALITY_FEED_MODE=broker` + `python -m src.simulation_quality.worker` produces
      grades equivalent to in-process mode with zero SimQ code executing in the engine process.
      Verified directly: `test_kernel_broker_mode_builds_zero_quality_hub` and
      `test_kernel_broker_mode_starts_zero_consumer_threads` (`INFRA-318`, P0) both pass; worker
      now scores all 10 pillars via `build_all_scorers()` matching the in-process path
      (`INFRA-319`, P0).
- [x] `DecisionTraceWriter` performs no file IO on the hot path. Verified directly:
      `test_write_trace_has_no_reachable_file_io` and
      `test_write_trace_does_not_reference_file_handle_or_index_append` both pass.
- [x] Documented overhead numbers for off / in-process / broker modes. Verified directly:
      `docs/performance/simq_isolation_overhead.md` exists with real measured wall-clock TPS and
      `cpu_time_total_delta_s` for all 3 modes, bound to `(Profile, Scenario, Hardware Class)` per
      `certification_contract.md` §5.

## Related Tickets
TCK-20260702-OBSISO-TRACE-ASYNC, TCK-20260702-OBSISO-BROKER-CONFIG, TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX (supersedes TCK-20260702-OBSISO-WORKER-PARITY), TCK-20260702-OBSISO-ISOLATION-PROOF. Prior art: TCK-20260520-SIM-OBS-M36 (RedisStreamAdapter), TCK-20260630-SIMQ-WIRE-KERNEL (quality_fn wiring), TCK-20260619-E22A (DecisionTraceWriter).

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

2026-08-04: G2's scope (worker.py hardcoding 2 of 10 pillar scorers) landed as
TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX instead of TCK-20260702-OBSISO-WORKER-PARITY. Verified
during that ticket that the `build_all_scorers()` factory this ticket's own Request Summary assumed
still needed extracting from the kernel path already existed and needed no broker pipeline to wire
in, so the fix landed directly as a hotfix without waiting on BROKER-CONFIG. The cross-process
grade-parity proof (real broker pipeline, two hub construction paths compared) is deferred to
ISOLATION-PROOF, which already needs a working broker pipeline for its own benchmark work.

## Test Summary
Epic — see each child ticket's own Test Summary for full detail. Aggregate: 58 (TRACE-ASYNC) + 30
non-Redis + 3 Redis-gated (BROKER-CONFIG) + 7 (WORKER-PARITY-HOTFIX) + 1330 across 4 verification
rounds (ISOLATION-PROOF) — all genuinely re-run and passing, including real Docker Redis broker-mode
legs verified multiple times independently across sibling tickets. `INFRA-211`, `INFRA-212`,
`INFRA-317`, `INFRA-318`, `INFRA-319`, `INFRA-320` (all P0/P1, all `verified`) collectively prove
every gap this epic tracked.

## Files Changed
Epic — see each child ticket's own Files Changed. Summary by area:
- `src/observability/cognition/decision_trace_writer.py`, `tick_index.py`, `src/engine/kernel.py`
  (G4 — async hot-path fix, TRACE-ASYNC)
- `src/simulation_quality/feed.py`, `worker.py`, `src/engine/kernel.py` (G1+G3 — stream-config
  unification + kernel routing fix, BROKER-CONFIG)
- `src/simulation_quality/worker.py` (G2 — scorer parity fix, WORKER-PARITY-HOTFIX)
- `src/perf/bench_harness.py`, `src/simulation_quality/run_health.py`, `persistence.py`,
  `tools/calibrate_simq.py`, `tools/evaluate_simq.py` (G5 — benchmark + drop guard,
  ISOLATION-PROOF)
- `docs/plans/observability_process_isolation.md` — all 5 gaps (G1-G5) marked RESOLVED
- `docs/parity_ledger/infrastructure.yaml` — 6 entries (`INFRA-211`, `INFRA-212`, `INFRA-317`,
  `INFRA-318`, `INFRA-319`, `INFRA-320`)

## Completion Summary
All four child tickets landed and all four epic-level acceptance criteria independently verified
true. `docs/plans/observability_process_isolation.md`'s G1-G5 gap analysis is now fully RESOLVED:
G1 (stream-name mismatch) and G3 (in-engine hub/thread leak in broker mode) fixed by
`BROKER-CONFIG`; G2 (2-of-10-pillar scorer registry) fixed by `WORKER-PARITY-HOTFIX`, landed
directly as a hotfix once investigation found the shared factory it needed already existed; G4
(hot-path file IO violation) fixed by `TRACE-ASYNC`; G5 (unmeasured isolation, unguarded queue
drops) closed by `ISOLATION-PROOF`'s real benchmark and hard-fail calibration guard. External
evaluation components (SimQ scoring, decision tracing) now satisfy all four original requirements:
performance isolation is measured (not just asserted), loose coupling and toggleability were
already met, and process separation (broker mode) is proven end-to-end — genuine Redis
provisioning and a real `QualityWorker` subprocess were used repeatedly across this batch's
verification passes, not simulated or skipped. Sequencing deviated once from the original plan
(WORKER-PARITY-HOTFIX landed independently of BROKER-CONFIG, ahead of schedule, once investigation
found it didn't actually need a connectable broker pipeline) — documented in this epic's own
Implementation Notes at the time, not silently absorbed.
