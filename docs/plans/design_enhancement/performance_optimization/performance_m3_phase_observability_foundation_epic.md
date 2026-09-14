---
status: active
layer: observability
authority: P2
audience: developer
tags: [performance, observability, engine, determinism]
---

# Epic Plan — Performance M3: Phase Identity and Bounded Observability

## Outcome

Make growing RPG phase work measurable and structurally governable without freezing the engine to
an arbitrary phase count or introducing a second execution authority.

## Entry conditions

- PA-05A has inventoried executable phase-like calls and explained counted units.
- PERF-D6 selects the phase-catalog authority and code/catalog relationship.
- PERF-D1 defines which pressure/control observations are semantic inputs.
- M2 stabilizes metric and benchmark identity.
- M1 ordering/hash dispositions are known where instrumentation observes them.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M3-T01 | Catalog authority promotion | PA-05A + PERF-D6 | Normative phase metadata and a single generation/conformance route |
| PERF-M3-T02 | Code/catalog/document order conformance | T01 | Tests proving handwritten execution, catalog identity/order, and generated prose do not drift |
| PERF-M3-T03 | Scheduling-funnel schema | M2-T02 | Bounded counters for eligible/candidate/admitted/processed/dropped/coalesced/deferred work |
| PERF-M3-T04 | Phase timing and cardinality instrumentation | T01, T03 | Stable IDs and costs for macro phases, refinement units, sort/merge, apply, persistence, projection |
| PERF-M3-T05 | Snapshot/freeze/IPC/hash/queue attribution | T04 | Separately attributable non-domain costs with backend and policy context |
| PERF-M3-T06 | Observer bounds and retention | T03–T05 | Label-cardinality, buffer, trace-size, retention, backpressure, and failure policies |
| PERF-M3-T07 | Observer-effect parity and overhead report | T06 | OFF/light/detail/audit state parity plus quantified overhead on identical checkpoints |

T01/T02 govern structure. T03–T07 govern measurement. T03 can begin after M2 identity is stable,
while T04 waits for stable phase IDs. Catalog-driven execution stays disabled unless a future
decision explicitly approves it after parity evidence.

**Worked example for T04, 2026-09-14** (TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER): enabling
a previously-dormant phase (`combat_engagement`) for the first time required a manual A/B
comparison of `kernel._phase_costs` totals across 20 ticks, flag OFF vs ON, plus an
`_event_listeners` hook to count real combat-event volume, to determine which of several phases
absorbed the resulting cost increase. That is exactly the per-phase timing/cardinality
instrumentation T04 is meant to make routine rather than one-off — see the "Confirmed field
evidence" note in `performance_m4_baseline_gate_a_epic.md` for the actual numbers this produced.

## Feature/phase growth contract

When a new RPG feature proposes a phase or refinement unit, its eventual ticket must declare:

- why an existing phase cannot own the semantics;
- authoritative inputs/outputs and accepted update types;
- read/write domains and affected-set propagation;
- placement constraints and canonical ordering;
- cadence, LOD, maximum staleness, and load-shedding behavior;
- invariants and reference/full-path oracle;
- timing/cardinality identity and bounded labels;
- M4 change-impact classification and required E2E, Arena, SimQ, and performance scenarios;
- migration/deprecation plan if it replaces an existing unit.

The catalog records semantic boundaries; it is not a reason to merge unrelated features merely to
reduce phase count. Conversely, a feature should not add a phase when it only needs a helper or
derived computation inside an existing semantic owner.

## Out of scope

- Automatically driving execution from new metadata.
- Concurrent RESOLUTION or a phase job graph.
- High-cardinality per-entity production tracing.
- Unbounded event retention.
- Optimizing a phase based only on a microbenchmark.

## Exit criteria

- One phase identity/order source is approved and all generated surfaces reproduce from it or
  conform to it exactly.
- New phase admission rules cover ownership and performance.
- The scheduling funnel reconciles from candidates through outcomes.
- Full tick cost includes Collection, sort/merge, refinement, apply, persistence, serving, and
  relevant queue/hash/IPC costs.
- Observer modes have explicit bounds and backpressure behavior.
- Instrumentation does not change authoritative state; overhead is quantified and heavy runs are
  not promoted as clean baselines.

## Primary surfaces

- `src/engine/pipeline.py`
- `src/engine/phase_graph.py`
- `src/engine/phase_domain_permissions.py`
- `src/engine/kernel.py`
- `src/observability/`
- `docs/engine/authoritative_pipeline.md`
- `tools/agent_orchestration_codex_adapter/generator.py`

## References

- `performance_optimization_prerequisite_execution_plan.md` PA-05A..06
- `../subphase_domain_contracts_epic.md`
- `system_design_terms_and_concepts.md` §§4, 6, 11
