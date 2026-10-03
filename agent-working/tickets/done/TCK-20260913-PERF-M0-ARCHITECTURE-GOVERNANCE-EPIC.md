---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC
phase: done
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
DONE

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
- [x] This epic ticket is not moved to `agent-working/tickets/done/` until `PERF-M0-T01`-`T09` all have a
      disposition (done, blocked, or explicitly deferred) — per the source epic doc's own Exit
      Criteria.

## Related Tickets
- TCK-20260913-PERF-M0-SOURCE-AUDIT
- TCK-20260913-PERF-M0-OWNER-TRIAGE
- TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (evidence half of `PERF-M0-T08`)
- TCK-20261003-PERF-HASH-CALLSITE-INVENTORY (evidence half of `PERF-M0-T07`, call sites only)
- TCK-20261003-PERF-PROFILING-TOOLKIT (PR #296; profiling tooling delivered beside the M0 inventories, not an M0 candidate)
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY (PR #306; input to T06's clause reconciliation and T09)
- TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY (PR #306; PERF-D1 amendment A1)
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (PR #306; `PERF-M0-T09`)
- TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT (PR #306; pairs with T09 items 6-7)
- TCK-20261003-PERF-M0-EPIC-CLOSURE (closes this epic)

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
- 2026-10-03 closure (`TCK-20261003-PERF-M0-EPIC-CLOSURE`). Dispositions, from `agent-working/tickets/done/` and `git log origin/main`:

  | Candidate | Disposition | Closing record |
  |---|---|---|
  | T01 source audit | done | `TCK-20260913-PERF-M0-SOURCE-AUDIT` (PR #287) |
  | T02 owner triage, C-01..C-17 | done | `TCK-20260913-PERF-M0-OWNER-TRIAGE` (PR #287) |
  | T03 PERF-D1 determinism | closed without a ticket | PERF-D1 with amendment A1 in `docs/architecture/performance_optimization_decisions.md` §3.3, owner-approved 2026-10-03; P1 text applied by `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` (PR #306). Implementation deferred to `PERF-M1` |
  | T04 PERF-D2 portability | closed without a ticket | PERF-D2, same file, owner-approved 2026-10-03; P1 text via T09 |
  | T05 PERF-D3 debt semantics | closed without a ticket | PERF-D3, §3.2 (recorded 2026-09-13) |
  | T06 PERF-D4 authority | closed without a ticket | PERF-D4, owner-approved 2026-10-03; inputs `TCK-20261003-PERF-M2-CLAUSE-INVENTORY` (PR #306); P1 text via T09 |
  | T07 PA-03A hash audit, PERF-D5 | done (evidence) and closed (decision) | `TCK-20261003-PERF-HASH-CALLSITE-INVENTORY` (PR #296); PERF-D5 owner-approved 2026-10-03. Mechanism changes deferred to `PERF-M1-T03` |
  | T08 PA-05A inventory, PERF-D6 | done (evidence) and closed (decision) | `TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT` (PR #296); PERF-D6 owner-approved 2026-10-03. Typed catalog deferred to `PERF-M3-T01` |
  | T09 P1 reconciliation | done | `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` and `TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT` (PR #306); the owner reviewed and merged the P1 wording |

- Exit Criteria of the M0 epic doc, each checked on 2026-10-03:
  1. PERF-D1..D6 approved or blocked: met. D1, D2, D4, D5, D6 approved 2026-10-03; D3 closed (decisions file, status lines under §3).
  2. C-01..C-17 each with evidence status, owner, route, safe interim reading: met (decisions file §2, one row per ID; C-17 resolved).
  3. P1 owners reconciled the older roadmap and epics: met (PR #306; `design_enhancement_roadmap.md` "Execution plan and authority" records C-01 as applied).
  4. Exactly one program-navigation outcome: met (`design_enhancement_roadmap.md` "One discoverable execution order", eight steps each naming its gate; the P1 roadmap is the parent authority).
  5. M1/M2/M3 entry gates evaluable without unstated assumptions: met (the same ordered list, the RPG-core stability entry gate in `performance_optimization_roadmap.md`, and the decision records state each gate).
- The one acceptance criterion that was unchecked (a disposition for every T01..T09) is now met. The P2 roadmap's "Until M0 closes" sentence was updated to record the closure.
- Not met and carried forward, not M0 exit criteria: `docs/parity_ledger` schema validation (330 pre-existing errors), and the entry gate, which still bars `src/` edits and baselines for M1+.

## Test Summary
Bookkeeping only; no code changed. `python3 tools/validate_frontmatter.py` run on the closed epic and the closure ticket (result recorded in the closure ticket).

## Files Changed
This file; `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (one status sentence).

## Completion Summary
All nine candidates PERF-M0-T01..T09 are done, closed by an approved decision, or deferred to a named M1/M3 ticket, and every M0 Exit Criterion is met. Closed 2026-10-03 by `TCK-20261003-PERF-M0-EPIC-CLOSURE`.
