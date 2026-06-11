---
status: archive
authority: P2
audience: historical
layer: testing
original_date: unknown
---

You are an expert simulation-engine architect and observability engineer.

We have reviewed your second-pass observability report. Before implementation planning, we need one final clarification focused on feasibility and prioritization.

Do not repeat the full audit.

Focus only on implementation readiness.

## 1. Validate referenced active V2 paths

Your report references many paths/classes, including:

- `src/engine/concurrency.py`
- `src/workers/daemon.py`
- `src/systems/world_systems/calamity.py`
- `src/systems/world_systems/governance.py`
- `src/services/inventory_service.py`
- `src/engine/governor.py`
- `src_legacy/workers/ai_worker_daemon.py`
- `src_legacy/utils/watchdog.py`

Please produce a table:

- Path
- Exists in active V2?
- Exists only in legacy?
- Referenced class/function
- Current status: usable / legacy-only / proposed / missing
- Implementation implication

Do not guess. Verify from codebase.

## 2. Prometheus metrics implementation readiness

For the metrics listed in your report, classify them into:

- P0: definitely exists and should be exported first
- P1: useful but requires minor new collector logic
- P2: depends on optional/domain systems
- Not ready: referenced source does not exist or is legacy-only

Output a table:

- Metric name
- Priority
- Existing source
- Required new logic
- Exporter process: FastAPI / worker / certification / unknown
- Notes

## 3. HardLawMonitor V1 feasibility

Please refine the proposed V1 laws into three groups:

- Every tick, DirtySet-scoped
- Periodic full scan
- Certification/post-run only

For each law, provide:

- Domain
- Required data
- Estimated cost
- DirtySet usable?
- Suggested cadence
- Failure behavior by mode: LIGHT / DEBUG / CERTIFICATION / LONG_RUN

Pay special attention to global gold conservation, occupancy collision, and registry referential integrity.

## 4. Event emission V1 scope

Your report proposes event policies for 11 domains.

Please classify concrete event types into:

- V1 always emit
- V1 emit only on anomaly
- V1 aggregate into metrics only
- Later

Output a table:

- Event type
- Domain
- V1 classification
- Expected frequency
- Required fields
- Reason

The goal is to avoid event storming.

## 5. TraceEvent and SimulationEvent migration path

Please provide a migration plan that keeps `TraceEvent` stable.

Answer:

- Which current `TraceEvent` usage must not change?
- Where should `SimulationEvent` be introduced first?
- Should `SimulationEvent` be emitted from Kernel, systems, ApplyPath, or observers?
- How do we prevent `SimulationEvent` from affecting deterministic replay?
- What tests prove separation?

## 6. Anomaly architecture staged recommendation

Your report recommends an out-of-process daemon.

Please compare this staged plan:

- V1: post-run analyzer over event chunks
- V2: in-process lightweight anomaly counters
- V3: out-of-process daemon with Redis/Kafka

For each stage, explain:

- Value delivered
- Runtime risk
- Implementation complexity
- Required dependencies
- What code must exist before moving to the next stage

Then confirm whether you still recommend starting directly with out-of-process daemon, or switching to staged delivery.

## 7. Entity timeline retention V1

Please refine the timeline retention model.

Compare:

- per-entity ring buffer
- global event ring buffer
- flagged-entity-only timeline
- reconstruct from event chunks

Output:

- Memory cost
- Debug value
- Implementation complexity
- Recommended V1 model
- Recommended default mode behavior

## 8. Final implementation-ready milestone proposal

Based on the answers above, propose a final implementation sequence with no more than 6 milestones.

For each milestone include:

- Goal
- Included components
- Excluded components
- Acceptance criteria
- Main risks

Do not provide code.
Be specific and practical.
