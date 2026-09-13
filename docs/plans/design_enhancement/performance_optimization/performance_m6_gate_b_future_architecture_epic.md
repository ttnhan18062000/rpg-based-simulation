---
status: active
layer: architecture
authority: P2
audience: developer
tags: [performance, architecture, determinism, governance]
---

# Epic Plan — Performance M6: Decision Gate B and Future Architecture

## Outcome

Close the exact-optimization program with a clean post-change evidence matrix, preserve the
continuous regression controls as owned infrastructure, decide whether approved targets were met,
and route any remaining scale problem without smuggling semantic changes into performance tickets.

## Entry conditions

- M4 Gate A is approved.
- Every selected M5 family is promoted, rejected, transferred, or rolled back; alternatively Gate
  A selected no exact work.
- M2/M3 identity and observation contracts remain valid for the final rerun.
- M4 assurance lanes and audit schema are active.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M6-T01 | Final clean assurance/matrix rerun | M5 closure or no-selection outcome | Same-scenario performance plus required E2E, Arena, SimQ, behavioral, identity, and work-cardinality evidence |
| PERF-M6-T02 | Optimization/reference retirement review | T01 | Per-family retain/retire/revisit decision and bounded maintenance ownership |
| PERF-M6-T03 | Gate B capacity and architecture decision | T01–T02 | Approved target-met/target-unmet decision with exact-work disposition |
| PERF-M6-T04 | Permanent documentation and terminology promotion review | T03 | P1 roadmap closeout plus decision whether the WIP terminology guide moves or remains |
| PERF-M6-T05 | Advanced architecture proposal, conditional | T03 proves unmet product need | Separate proposal request with semantics, migration, quality bounds, and authority review—not implementation |
| PERF-M6-T06 | Continuous guardrail ownership and response drill | T01–T04 | Named lane/threshold/baseline owners, alert SLO, regression ticket route, quarantine expiry review, and tested rollback/escalation drill |

T05 is not automatically created when a target is missed. Product scale must still justify the
semantic/authority complexity, and exact options must be shown as completed, rejected, or
insufficient.

## Gate B outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| Targets met | Exact work is sufficient for the approved capacity envelope | Close program; retain monitoring and revisit triggers |
| No exact work selected | Gate A found no material justified accelerator | Close exact program; advanced proposal requires independent product evidence |
| Targets partly met | Some scenarios pass and others remain constrained | Retain accepted work; decide whether remaining scenarios justify new scope |
| Targets unmet | Clean matrix still misses approved goals | Consider T05; Gate B itself authorizes no semantic implementation |
| Evidence invalid | Identity, mode, cardinality, observer, or correctness conditions fail | Reject rerun and repair evidence; no architecture conclusion |
| Quality regression | Arena, long-horizon, or SimQ acceptance fails despite faster execution | Reject promotion/closeout; classify drift and repair or seek explicit design decision |

## Conditional advanced-proposal boundary

A T05 proposal may evaluate concurrent RESOLUTION, aggregate/hierarchical simulation, fidelity
tiers, or another semantic architecture only when it defines:

- the product-scale requirement and scenarios exact work failed to satisfy;
- changed authoritative semantics and expected differences;
- phase/read-write/ordering and conflict-resolution model;
- determinism envelope, control trace, portability, and migration/version policy;
- emergent-behavior and Simulation Quality acceptance bounds;
- client/server and persistence consequences;
- reference/comparison strategy, rollout, rollback, and kill criteria.

Distributed writers, CRDT/eventual consistency, client prediction, and full ECS replacement remain
non-goals unless independently justified; popularity is not justification.

## Out of scope

- Implementing advanced semantic architecture.
- Retroactively weakening M4/M5 acceptance thresholds.
- Calling changed workload/fidelity an exact optimization.
- Deleting reference paths without retirement evidence.
- Promoting this P2 folder by implication.

## Exit criteria

- Final matrix is valid or explicitly rejected with a repair owner.
- Required E2E, Arena, behavioral, and SimQ results are linked from the final audit document.
- Gate B has named approvers and a durable decision.
- Every M5 reference/candidate path has a lifecycle disposition.
- P1 roadmap/epic status and permanent navigation are reconciled.
- The terminology guide promotion decision is explicit.
- Any advanced work is a separately authorized proposal with no implementation ticket leakage.
- Continuous checks have owners, bounded feedback/alert expectations, quarantine expirations, and
  a verified path from detected regression to rollback or ticket handoff.

## Revisit triggers

- New RPG features materially change phase count, working set, state shape, or client load.
- Supported runtime/hardware/executor matrix changes.
- Tail latency, memory, hash, IPC, or serving cost crosses contract thresholds.
- Correctness/parity evidence invalidates a promoted accelerator.
- A new product requirement needs intentional fidelity or authority changes.

## References

- `performance_optimization_prerequisite_execution_plan.md` Gate B boundary
- `../../../brainstorm/codex/system-design/performance_optimization_architecture_proposal.md` §§13, 15, 20
- `system_design_terms_and_concepts.md` §§13–14, 18
- `performance_m4_baseline_gate_a_epic.md` continuous assurance and audit contracts
