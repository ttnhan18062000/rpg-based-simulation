---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-WIRE-KERNEL
phase: done
date: 2026-06-30
tags: [simulation-quality, simq, integration, event-bus, observability, wiring]
---

# TCK-20260630-SIMQ-WIRE-KERNEL

## Title
Wire SimQ quality_fn into kernel event pipeline and remove competing consumer

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
D20 audit (2026-06-30) confirmed SimQ receives zero events in every run: `tick_count=0`,
all pillar `event_count=0`, all grades C. Root cause: `QueueDrainWorker` has a
`quality_fn: Optional[Callable]` slot (`src/observability/queue.py:97`) designed for
exactly this purpose, but the kernel's `EventRecorder` never populates it. As a result
`InProcessQualityFeed` creates a competing second `QueueDrainWorker` on the same queue,
which races against EventRecorder's worker and loses — `hub.on_envelope()` is never
called. This ticket wires the integration correctly and removes the competing consumer.

## Scope

### Gap G1 — Populate quality_fn in EventRecorder's QueueDrainWorker
- Add `quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None`
  parameter to `EventRecorder.__init__`
- Pass it through to the `QueueDrainWorker` constructor that EventRecorder creates
  (`src/observability/event_recorder.py:95–99`)
- In `Kernel.__init__`, build the SimQ hub **before** EventRecorder, then pass
  `quality_fn=hub.on_envelope` when constructing EventRecorder

### Gap G3 — Remove InProcessQualityFeed's competing consumer
- `InProcessQualityFeed.start(hub)` currently creates a second `QueueDrainWorker` on
  the global queue (`src/simulation_quality/feed.py:33–61`)
- Refactor `InProcessQualityFeed` to act as a lifecycle manager only — it should inject
  `quality_fn` into the existing `QueueDrainWorker` (owned by EventRecorder) rather than
  create a new one
- The `BrokerQualityFeed` path is unaffected (separate Redis stream, not the global queue)
- `build_feed_from_env()` return value and the disabled-hub path must stay stable

## Out of Scope
- Server-side `set_quality_hub()` wiring (→ TCK-20260630-SIMQ-WIRE-SERVER)
- Grade threshold calibration (→ TCK-20260630-SIMQ-RECALIBRATE; blocked on this ticket)
- Engine feedback path (quality signals influencing pipeline decisions)
- Changes to BrokerQualityFeed

## Acceptance Criteria
1. A 200-tick run on `sandbox_world` with `InProcessQualityFeed` active produces
   `tick_count > 0` and at least one pillar with `event_count > 0` in the quality report
2. No second `QueueDrainWorker` exists on the global observability queue during a run
3. Disabling SimQ (`SIMQ_ENABLED=false` or feed=None) still produces a correct simulation
   run with no errors — quality_fn path is strictly optional
4. All existing observability tests pass (`pytest tests/observability/ -x`)
5. All existing SimQ tests pass (`pytest tests/simulation_quality/ -x`)
6. New integration test: `tests/simulation_quality/test_kernel_simq_integration.py` —
   runs 20 ticks on sandbox_world with InProcessQualityFeed and asserts
   `report.tick_count > 0` and `report.pillars["AGENCY"].event_count > 0`

## Related Tickets
- TCK-20260628-SIMQ-EPIC — parent epic
- TCK-20260628-SIMQ-E2-HUB-CORE — original hub wiring design
- TCK-20260630-SIMQ-WIRE-SERVER — server-side wiring (parallel, independent)
- TCK-20260630-SIMQ-RECALIBRATE — blocked on this ticket

## Related Docs
- `docs/audits/D20_simq_integration.md` — audit findings (G1, G3)
- `docs/simulation_quality/quality_scoring_contract.md` — §4 hub wiring spec
- `docs/guides/simulation_quality.md` — in-process feed mode documentation

## Related Stored Artifacts
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/` — original design

## Related Code Areas
- `src/observability/queue.py:97` — `QueueDrainWorker.quality_fn` slot
- `src/observability/event_recorder.py:95–99` — where QueueDrainWorker is created
- `src/engine/kernel.py:226` — where EventRecorder is created in Kernel.__init__
- `src/simulation_quality/feed.py:33–61` — InProcessQualityFeed (competing consumer)
- `src/simulation_quality/quality_hub.py` — QualityHub.on_envelope entry point

## Assumptions / Open Questions
- EventRecorder's `QueueDrainWorker` is the authoritative consumer of the global queue.
  InProcessQualityFeed should piggyback as a callback, not as a second consumer.
- Thread-safety: `hub.on_envelope()` acquires a lock per accumulator; safe to call from
  the drain worker thread. No additional locking needed in this ticket.
- If no hub is configured (`quality_fn=None`), QueueDrainWorker falls through the
  existing `if self.quality_fn:` guard at line 144 — no behavioural change needed there.

## Implementation Notes
Implemented as planned. Construction order in Kernel.__init__:
1. `build_feed_from_env()` — returns None if disabled
2. `ScoringWeights.load()` + `build_all_scorers(weights)` + `QualityPersistence`
3. `QualityHub(scorers, weights, persistence, run_id=self._run_id)`
4. `EventRecorder(..., quality_fn=hub.on_envelope)` — wires fn into QueueDrainWorker
5. `feed.start(hub)` — lifecycle registration only

`InProcessQualityFeed` refactored to lifecycle manager: stores `_hub` ref, no QueueDrainWorker.
`scorers/__init__.py` — added `build_all_scorers(weights)` factory.
`Kernel` — added `quality_hub` read-only property; shutdown writes final QualityPersistence report.
Parity: INFRA-249 updated; INFRA-232 test_path corrected.

Files changed: src/observability/event_recorder.py, src/engine/kernel.py,
src/simulation_quality/feed.py, src/simulation_quality/scorers/__init__.py,
tests/simulation_quality/test_feed.py, tests/simulation_quality/test_kernel_simq_integration.py,
tests/unit/observability/test_event_recorder_quality_fn.py,
docs/parity_ledger/infrastructure.yaml

## Test Summary
- Unit: EventRecorder passes quality_fn to its QueueDrainWorker correctly
- Unit: InProcessQualityFeed.start() does not create a second QueueDrainWorker
- Integration: 20-tick sandbox_world run with InProcessQualityFeed → non-zero tick_count
- Regression: all existing observability + SimQ tests still pass

## Files Changed
- `src/observability/event_recorder.py` — added `quality_fn: Optional[Callable] = None` param; passes through to QueueDrainWorker
- `src/engine/kernel.py` — added `_quality_hub`/`_quality_feed` to __slots__; inserted SimQ hub construction before EventRecorder; added `quality_hub` property; extended shutdown to stop feed and write final report
- `src/simulation_quality/feed.py` — removed QueueDrainWorker import and competing worker; refactored InProcessQualityFeed to lifecycle-only registrar
- `src/simulation_quality/scorers/__init__.py` — added `build_all_scorers(weights)` factory
- `tests/simulation_quality/test_feed.py` — updated two tests that checked `_worker` attr (now checks `_hub`)
- `tests/simulation_quality/test_kernel_simq_integration.py` — NEW: 4 integration tests
- `tests/unit/observability/test_event_recorder_quality_fn.py` — NEW: 4 unit tests for quality_fn wiring
- `docs/parity_ledger/infrastructure.yaml` — INFRA-249 updated (G1+G3 fix); INFRA-232 test_path corrected

## Completion Summary
G1 and G3 gaps from D20 audit resolved. EventRecorder now passes `quality_fn=hub.on_envelope` to its
QueueDrainWorker at Kernel init time. InProcessQualityFeed is a lifecycle-only registrar with no competing
worker. build_all_scorers() factory centralizes scorer construction. 305 SimQ tests + 27 observability/unit
tests pass. tick_count is nonzero when events flow through the queue. Ready to unblock RECALIBRATE.
