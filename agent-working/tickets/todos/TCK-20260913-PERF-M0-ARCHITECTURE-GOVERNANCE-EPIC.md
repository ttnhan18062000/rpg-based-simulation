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
> **lifecycle correction only** — the ticket had sat in `agent-working/tickets/inprogress/` with no further
> content change since 2026-09-14 (verified via `git log --follow`, not file mtime), and its
> presence there was firing this repo's sidecar-check hook on every `Edit`/`Write` in every
> concurrent session on this machine. **Nothing about the ticket's own substance was
> investigated, debugged, or re-scoped as part of this move.** Anyone picking this up should
> treat it as unstarted backlog work and re-validate its premises first, since it predates a
> large amount of change in this repo.
>
> **Re-validated 2026-10-02 by the `perf-planner` session** against `origin/main` at `7dfd1349`.
> Findings and corrections are in `performance_optimization_roadmap.md`, "Plan review, 2026-10-02".
> Two things changed for this epic: the owner decided the ownership model, so naming ten role
> owners is no longer a blocker (see Out of Scope below); and an RPG-core stability entry gate now
> limits what may start to documents, tickets, and read-only tooling. Both child tickets were
> rewritten the same day. Work happens in the worktree `/home/vboxuser/Work/rpg-perf`, branch
> `perf-optimization-foundation`.

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
- Assigning owners beyond the ownership model the owner decided on 2026-10-02: the `perf-planner`
  session plans and reviews, the `perf-implementer` session implements, and the repository owner
  approves any change to an authority-P1 document. The 10 role names the epic doc lists
  (Architecture, Engine Architecture, Simulation Correctness, Simulation Semantics, Performance,
  Testing/CI, Arena, Simulation Quality, Release/Certification, Observability/Replay) are review
  perspectives under that model; `PERF-M0-T02` records the mapping and adds nothing to it.

## Acceptance Criteria
- [x] `PERF-M0-T01` and `PERF-M0-T02` exist as real, investigated `TCK-*.md` tickets linked to this
      epic's Related Tickets section.
- [x] Neither child ticket changes runtime behavior, governors, schedulers, hashing, pipeline
      execution, or client-facing behavior.
- [ ] This epic ticket is not moved to `agent-working/tickets/done/` until `PERF-M0-T01`-`T09` all have a
      disposition (done, blocked, or explicitly deferred) — per the source epic doc's own Exit
      Criteria.

## Related Tickets
- TCK-20260913-PERF-M0-SOURCE-AUDIT
- TCK-20260913-PERF-M0-OWNER-TRIAGE
- TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (evidence half of `PERF-M0-T08`)
- TCK-20261003-PERF-HASH-CALLSITE-INVENTORY (evidence half of `PERF-M0-T07`, call sites only)

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
- 2026-10-02: `PERF-M0-T01` (`TCK-20260913-PERF-M0-SOURCE-AUDIT`, commit `26be9ed0`) and
  `PERF-M0-T02` (`TCK-20260913-PERF-M0-OWNER-TRIAGE`, commit `3b30b52f`) are done; both commits
  touch only docs, tickets, stored artifacts, the registry, and monitoring shards. Their folder
  moved to `agent-working/tickets/done/perf-m0-architecture-governance/`.
- `PERF-M0-T05` (PERF-D3) is recorded closed in
  `docs/architecture/performance_optimization_decisions.md` §3.2 and needs no ticket.
- Next: the planner session drafts PERF-D1, D2, D4, D5, and D6 in that file. `PERF-M0-T07`
  (hash call-site audit) and `PERF-M0-T08` (re-runnable phase inventory) are the next tickets to
  create, as evidence-only work; `T03`, `T04`, `T06`, and `T09` follow the drafts and need the
  owner's approval where a P1 document changes.

## Test Summary


## Files Changed


## Completion Summary

