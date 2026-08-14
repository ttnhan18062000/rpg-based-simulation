---
status: closed
layer: observability
authority: P0
audience: agent
ticket_id: TCK-20260701-SIMQ-KERNEL-WIRE
phase: done
date: 2026-07-01
tags: [simq, kernel, wiring, observability, integration]
---

# TCK-20260701-SIMQ-KERNEL-WIRE

## Title
Wire SimQ hub into Kernel startup and server lifespan (G1 / G2 / G3 fix)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
The SimQ module has 79 scored event types, full pillar infrastructure, and a working hub
— but produces zero signal in every production run because the `QualityHub` is never
connected to the event delivery path.

Three independent gaps block live scoring (identified in `docs/audits/D20_simq_integration.md`):

- **G1** (`src/engine/kernel.py`): `EventRecorder`'s `QueueDrainWorker` is created without
  `quality_fn`. The slot exists at `src/observability/queue.py` and was designed for this.
- **G2** (`src/api/server.py`): `set_quality_hub()` is defined in `src/api/dependencies.py`
  but never called in the server `lifespan`. REST quality endpoints always return the
  hub=None path.
- **G3** (`src/simulation_quality/feed.py`): `InProcessQualityFeed` creates a **second**
  `QueueDrainWorker` on the same queue, racing against the kernel's worker. Events are
  consumed by the kernel's (unhoooked) worker before the feed's worker can route them.

The result: `QualityHub.on_envelope()` is never called, `tick_count` stays 0, all pillar
scores are 0, and `tools/calibrate_simq.py` is blocked.

## Scope
1. **G1 fix** — in `Kernel.__init__`, construct `QualityHub` and pass `quality_fn=hub.on_envelope`
   to the `QueueDrainWorker` created inside `EventRecorder`. Confirm the drain worker's
   `quality_fn` slot signature matches `Callable[[ObservabilityEventEnvelope], None]`.
2. **G2 fix** — in `src/api/server.py` `lifespan`, call `set_quality_hub(hub)` after the
   kernel/manager starts. Confirm the shutdown handler already reads `get_quality_hub()`.
3. **G3 fix** — deprecate or thin-wrap `InProcessQualityFeed` so it does not create a
   second consumer. It should inject `quality_fn` into the existing drain worker rather than
   competing with it. `BrokerQualityFeed` (Redis path) is unaffected.
4. Re-run D20 audit config (sandbox_world, 200 ticks, seeds 42/137) and confirm:
   - `hub.tick_count > 0`
   - At least COMBAT and AGENCY pillars score > 0 (both have events confirmed in D06)
5. Run `tools/calibrate_simq.py` to generate grade baselines across calibration corpus.
6. Update `docs/audits/D20_simq_integration.md` findings F1–F5 to RESOLVED.

## Out of Scope
- Changing scorer weights or thresholds
- Modifying event routing or translation tables
- Performance tuning of the drain worker

## Acceptance Criteria
- [ ] 200-tick sandbox_world run with seeds 42 and 137 produces `hub.tick_count > 0`
- [ ] COMBAT pillar grade ≥ B in sandbox_world (combat events confirmed in D06)
- [ ] AGENCY pillar grade ≥ B in sandbox_world (route_selected confirmed in D06)
- [ ] REST endpoint `GET /quality/summary` returns live scores (not hub=None path)
- [ ] `InProcessQualityFeed` no longer creates a second drain worker
- [ ] No regression in existing observability tests

## Related Tickets
- TCK-20260628-SIMQ-EPIC — parent epic
- TCK-20260701-SIMQ-EMIT-AGENCY2, TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS,
  TCK-20260701-SIMQ-EMIT-PROGRESSION, TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY,
  TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS — emission gaps resolved upstream

## Related Docs
- `docs/audits/D20_simq_integration.md` — original audit with G1/G2/G3 diagnosis
- `docs/simulation_quality/quality_scoring_contract.md` — hub contract

## Related Code Areas
- `src/engine/kernel.py` — G1: QueueDrainWorker construction
- `src/api/server.py` — G2: lifespan set_quality_hub call
- `src/api/dependencies.py` — G2: set_quality_hub / get_quality_hub
- `src/observability/queue.py` — QueueDrainWorker.quality_fn slot
- `src/simulation_quality/feed.py` — G3: InProcessQualityFeed competing consumer
- `src/simulation_quality/quality_hub.py` — QualityHub.on_envelope

## Assumptions / Open Questions
- `Kernel.__init__` may need the hub passed in or built internally; confirm whether the
  kernel already constructs a QualityHub or expects one injected.
- The drain worker may need a thread-safe reference swap if quality_fn is set after
  worker start; confirm whether the slot is read on each pop or cached at start.

## Implementation Notes
- The D20 audit pseudocode in `docs/audits/D20_simq_integration.md §Recommended Fix`
  shows the minimal G1 pattern.
- Confirm `QueueDrainWorker.quality_fn` is `Optional[Callable]` and called as
  `self.quality_fn(envelope)` in the drain loop before merging.

## Test Summary
- Unit: mock drain worker — verify quality_fn is called on each envelope
- Integration: 50-tick sandbox_world run — assert hub.tick_count == 50
- Integration: REST endpoint returns non-null scores after 10 ticks

## Files Changed
(to be filled at implementation)

## Completion Summary
**Ticket created in error.** All three gaps (G1/G2/G3) were already resolved on 2026-06-30:
- G1 + G3: `TCK-20260630-SIMQ-WIRE-KERNEL` — `quality_fn=hub.on_envelope` wired into `QueueDrainWorker`; `InProcessQualityFeed` refactored to not create a competing consumer
- G2: `TCK-20260630-SIMQ-WIRE-SERVER` — `set_quality_hub()` called in server lifespan

The D20 audit was written before those fixes and was not updated when the fixes landed. This ticket was created against stale audit text. No implementation required. Closing as duplicate.
