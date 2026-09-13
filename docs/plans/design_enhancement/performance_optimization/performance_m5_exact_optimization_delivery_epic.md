---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, optimization, determinism, testing]
---

# Epic Plan — Performance M5: Evidence-Selected Exact Optimizations

## Outcome

Implement only the semantics-preserving accelerator families individually selected by Gate A.
M5 is conditional: if Gate A selects none, this milestone is skipped successfully and M6 records
that outcome.

## Entry conditions

- M4 Gate A is approved.
- M4 assurance routing, required-check wiring, and audit schema are active.
- Each selected family has contributor evidence, materiality threshold, owner, reference path,
  correctness oracle, impact classification, required test lanes, memory bound, rollout/rollback,
  and retirement rule.
- A real child ticket is created only for a selected family after fresh code investigation.

## Conditional child-ticket families

| Candidate ID | Family | Required Gate A evidence | Minimum delivery |
|---|---|---|---|
| PERF-M5-T01 | Scan, dirty, due-work, or index tightening | Material scheduling/full-scan cost and complete eligibility oracle | Exact candidate parity, invalidation coverage, full-scan fallback |
| PERF-M5-T02 | Typed compact phase-input routing | Material repeated routing scans | Typed views, insertion-order tests, full-path parity |
| PERF-M5-T03 | Deterministic memoization | Material pure-function cost and reuse rate | Complete semantic key, invalidation/versioning, bounded cache, bypass parity |
| PERF-M5-T04 | Hierarchical/incremental hashing | PERF-D5 permits it and flat hashing is material | Versioned scheme/tick/freshness, independent flat audit, same-scheme comparisons |
| PERF-M5-T05 | Snapshot/freeze/serialization/IPC improvement | Material data-movement cost on a supported backend | Immutable boundary preserved, backend parity, memory/copy bounds |
| PERF-M5-T06 | Dynamic Collection balancing | Measured imbalance/tail cost | Stable work identity, completion-order independence, local/thread/process parity |
| PERF-M5-T07 | Narrow SoA/data-oriented Collection view | Homogeneous hot loop remains material including view construction | Disposable derived view, rebuild/bypass path, exact output parity |
| PERF-M5-T08 | Server projection/interest management handoff | Material serving cost and live-map ownership agreement | Separate serving ticket under existing epic, passive-client and resnapshot/backpressure proof |

The table is a candidate eligibility menu, not authorization or commitment. Authorization requires
reconciled P1 authority plus the normal real-ticket workflow. Unselected rows do not become backlog.
Several families may need multiple tickets after investigation—for example schema/foundation,
implementation, and promotion—but each ticket remains independently reversible.

## Per-family delivery sequence

1. Reference/off path and oracle are executable.
2. Candidate implementation lands default OFF.
3. Unit/property/adversarial tests prove local invariants.
4. Impact-selected checkpoint/replay E2E, Arena, SimQ, and long-horizon checks run; any
   `NOT_APPLICABLE` result cites the preapproved M4 rule.
5. Differential parity and paired before/after performance runs cover the approved matrix.
6. Shadow mode measures correctness, hit/reuse rate, cost, memory, quality, and observer effects.
7. The durable audit summary links raw evidence and records every regression/drift disposition.
8. Controlled rollout reaches the predeclared adoption threshold.
9. Owner promotes, rejects, or rolls back.
10. Reference-path retirement occurs only under the predeclared rule; otherwise dual paths remain
   bounded and explicitly owned.

## Common invariants

- No worker/client/derived index directly mutates `AuthoritativeState`.
- No accelerator drops or duplicates eligible authoritative work.
- Completion timing does not become a semantic tiebreaker.
- Cache/hash/index identity includes every semantic input and version.
- Memory and retained history are bounded.
- Fallback reconstruction is deterministic.
- Performance comparison records equal processed work or declares the semantic difference.
- Arena conformance and Simulation Quality may not regress outside approved bounds.
- A green microbenchmark or unit suite cannot override a required E2E/quality failure.
- Baselines and SimQ anchors may change only through their reviewed drift/compatibility workflow.

## Explicitly excluded families

- Concurrent or distributed RESOLUTION.
- Multiple authoritative writers, CRDTs, or eventual consistency.
- Full ECS rewrite.
- Client prediction/rollback.
- Aggregate/fidelity-reduced distant simulation.
- Any optimization selected only by intuition, popularity, or inner-loop timing.

Those exclusions may be reconsidered only through M6's separate architecture path.

## Exit criteria

For every Gate-A-selected family:

- all real tickets are done, rejected, transferred, or rolled back;
- reference and candidate results meet the approved correctness oracle;
- end-to-end target improvement and scaling effect are measured;
- all impact-selected E2E, Arena, SimQ, and long-horizon gates pass or have an approved disposition;
- memory/retention and observer overhead remain within bounds;
- rollout state and fallback availability are documented;
- a schema-valid performance audit document identifies evidence, exceptions, decision, and owner;
- P1 docs, parity ledgers, baselines, and generated artifacts are updated through owners/tools.

## References

- `performance_optimization_prerequisite_execution_plan.md` §8
- `../../../brainstorm/codex/system-design/performance_optimization_architecture_proposal.md` §§7–12, 18
- `system_design_terms_and_concepts.md` §§7–12
- `performance_m4_baseline_gate_a_epic.md` assurance and audit contracts
