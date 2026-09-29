---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC
phase: open
date: 2026-09-13
tags: [architecture, performance, determinism]
---

# TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC

> **Moved back to the backlog, 2026-09-20, at the user's direct instruction.** This is a
> **lifecycle correction only** — the ticket had sat in `tickets/inprogress/` with no further
> content change since 2026-09-14 (verified via `git log --follow`, not file mtime), and its
> presence there was firing this repo's sidecar-check hook on every `Edit`/`Write` in every
> concurrent session on this machine. **Nothing about the ticket's own substance was
> investigated, debugged, or re-scoped as part of this move.** Anyone picking this up should
> treat it as unstarted backlog work and re-validate its premises first, since it predates a
> large amount of change in this repo.

## Title
Performance-optimization M0: architecture governance — decision ownership, conflict triage, PERF-D1..D6

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
A new evidence-gated performance-optimization proposal was reviewed on 2026-09-13
(`docs/plans/design_enhancement/performance_optimization/`) alongside the repo's existing active
P1 performance roadmap (`docs/plans/design_enhancement/design_enhancement_roadmap.md` Section A,
`performance_milestones_epic.md`). The review found 17 confirmed real conflicts (C-01..C-17) and 6
open architecture decisions (PERF-D1..D6) between the two, plus zero cross-linkage between them.
Before any behavior-changing performance milestone (M1+) can start under the new proposal, M0 must
establish real named decision owners and formally disposition the conflicts and decisions — this
epic tracks that scoping work only. It changes no runtime behavior.

`PERF-D3` (capacity-debt semantics) was already fast-closed during the 2026-09-13 review:
`AuthoritativeState.work_debt` is already a plain aggregate int with no competing
semantic-deferred-work pattern anywhere in `src/`, matching the proposal's own default. This epic's
`T05` child ticket should record that closure rather than re-investigate it.

## Scope
- Scope-only epic: full design is in
  `docs/plans/design_enhancement/performance_optimization/performance_m0_architecture_governance_epic.md`'s
  "Candidate child tickets" table (`PERF-M0-T01`..`T09`). Detailed, investigated child tickets are
  created separately via `create-tickets` and linked here.
- This pass authorizes creating tickets for `PERF-M0-T01` (source durability/semantic-overlap
  audit) and `PERF-M0-T02` (decision ownership and conflict triage) only — the two candidates with
  no unmet prerequisite per the epic doc's own dependency column.
- `PERF-M0-T03`-`T08` (the individual PERF-D1/D2/D4/D5/D6 decisions) depend on `T02`'s
  owner/approver matrix landing first and are explicitly NOT created by this pass.
- `PERF-M0-T09` (P1 roadmap reconciliation) depends on `T03`-`T08` and is explicitly NOT created by
  this pass.

## Out of Scope
- Any M1+ milestone of the new performance-optimization proposal.
- Any change to `performance_milestones_epic.md`'s own M1-M4 scope (already reviewed 2026-09-13 and
  found to have adequate built-in gates — per-item determinism/fidelity justification, a hard
  sequencing dependency on `subphase_domain_contracts_epic.md` before M3, and a SimQ/arena
  regression-comparison requirement for M3/M4).
- Naming the actual accountable owners for the 10 roles the epic doc's Entry Conditions require
  (Architecture, Engine Architecture, Simulation Correctness, Simulation Semantics, Performance,
  Testing/CI, Arena, Simulation Quality, Release/Certification, Observability/Replay) — that is a
  human/organizational decision this ticket cannot make; `PERF-M0-T02`'s own scope is to produce
  the matrix structure, not to unilaterally assign people to it.

## Acceptance Criteria
- [ ] `PERF-M0-T01` and `PERF-M0-T02` exist as real, investigated `TCK-*.md` tickets linked to this
      epic's Related Tickets section.
- [ ] Neither child ticket changes runtime behavior, governors, schedulers, hashing, pipeline
      execution, or client-facing behavior.
- [ ] This epic ticket is not moved to `tickets/done/` until `PERF-M0-T01`-`T09` all have a
      disposition (done, blocked, or explicitly deferred) — per the source epic doc's own Exit
      Criteria.

## Related Tickets
- TCK-20260913-PERF-M0-SOURCE-AUDIT
- TCK-20260913-PERF-M0-OWNER-TRIAGE

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m0_architecture_governance_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_conflict_approval_review.md`
- `docs/plans/design_enhancement/design_enhancement_roadmap.md` (Section A, PERF-D/C-01..17 disposition notes added 2026-09-13)
- `docs/plans/design_enhancement/performance_milestones_epic.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `src/engine/pipeline.py` (phase-count reconciliation relevant to PERF-D6)
- `src/engine/governor.py`, `src/engine/worker_manager.py` (PERF-D3/queue-zero semantics context)

## Assumptions / Open Questions
- Assumes P1 owners agree to review conflicts without treating this P2 plan as their automatic
  replacement, per the source epic doc's own Entry Conditions — not yet confirmed with named
  individuals.
- `PERF-M0-T03`-`T09` are intentionally left uncreated pending `T02`'s output; re-run
  `create-tickets` against the same source doc once `T02` lands rather than hand-authoring them.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

