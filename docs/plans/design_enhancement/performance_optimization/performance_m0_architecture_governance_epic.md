---
status: active
layer: architecture
authority: P2
audience: developer
tags: [performance, architecture, determinism, governance]
---

# Epic Plan — Performance M0: Architecture Governance

## Outcome

Establish one durable, owned, conflict-aware decision foundation before performance implementation.
M0 converts the proposal's assumptions into approved decisions or explicit blocked dispositions;
it does not change runtime behavior.

## Entry conditions

- The proposal, prerequisite plan, conflict review, terminology guide, and this folder are durable
  review inputs.
- P1 owners agree to review conflicts without treating this P2 plan as their replacement.
- Architecture, Engine Architecture, Simulation Correctness, Simulation Semantics, Performance,
  Testing/CI, Arena, Simulation Quality, Release/Certification, and Observability/Replay roles
  receive named accountable owners.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M0-T01 | Source durability and semantic overlap audit | None | Registered-source inventory; reuse/merge/supersede/defer report against open/done tickets |
| PERF-M0-T02 | Decision ownership and conflict triage | T01 | Owner/approver matrix and C-01..C-17 dispositions |
| PERF-M0-T03 | PERF-D1 determinism/control-trace decision | T02 | Canonical/certification and Live bounded contract decision, control-input sufficiency, ordering boundary |
| PERF-M0-T04 | PERF-D2 portability decision | T03 | Supported runtime/platform/executor tier matrix and claim language |
| PERF-M0-T05 | PERF-D3 debt-semantics decision | T02 | Capacity-debt definition and boundary for any future semantic deferred-work queue |
| PERF-M0-T06 | PERF-D4 performance-authority charter | T02, informed by T04 | Selected P1 authority and clause-reconciliation mandate for M2 |
| PERF-M0-T07 | PA-03A hash audit and PERF-D5 decision | T02 | Call-site/consumer/freshness/cost evidence, followed by approved policy or blocked disposition |
| PERF-M0-T08 | PA-05A phase inventory and PERF-D6 decision | T02 | Executable inventory, counted-unit reconciliation, catalog-authority decision |
| PERF-M0-T09 | P1 roadmap and contract reconciliation | T03–T08 | Updated/superseded P1 plans through their owners; one discoverable execution order |

These are candidate scopes, not tickets. T03–T08 may run in parallel after T02 except where T04
informs T06. T09 waits for every decision that changes an affected P1 document.

## Decision requirements

Every PERF-D record includes:

- context, decision, rejected alternatives, and trade-offs;
- evidence and remaining uncertainty;
- authority/source-of-truth location;
- named approvers;
- compatibility, baseline, and migration consequences;
- required verification, audit evidence, failure routing, and accountable gate owner;
- child packages released or blocked;
- revisit/rollback condition.

T07 and T08 are evidence-first: their audits may run without approving a hash or phase-catalog
change, but no behavior/catalog promotion follows until PERF-D5/PERF-D6 is approved.

## Explicit non-goals

- No governor, scheduler, hash, pipeline, executor, benchmark, or client behavior change.
- No hand-edit of generated `AGENTS.md` or `docs/REGISTRY.yaml`.
- No declaration that P2 prose supersedes P1.
- No preselection of M5 accelerators.

## Exit criteria

- PERF-D1..D6 are approved, or each dependent milestone is explicitly blocked.
- C-01..C-17 each has evidence status, owner, decision route, and safe interim interpretation.
- P1 owners have reconciled the older roadmap/epics or explicitly retained their conflicting scope.
- Exactly one active program-navigation outcome is documented.
- M1/M2/M3 entry gates can be evaluated without relying on unstated assumptions.

## Verification

- Frontmatter and registry validation.
- Decision IDs and owner fields mechanically complete.
- Link/path checks for all cited sources.
- Architecture review confirms no durable-state or authority change is hidden in M0.

## References

- `performance_optimization_prerequisite_execution_plan.md` §§4–7
- `performance_optimization_conflict_approval_review.md`
- `system_design_terms_and_concepts.md` §§13–14
- `../../../engine/authoritative_pipeline.md`
