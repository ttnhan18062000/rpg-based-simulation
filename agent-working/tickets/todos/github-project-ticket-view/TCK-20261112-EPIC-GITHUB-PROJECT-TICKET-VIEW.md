---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW
phase: open
date: 2026-11-12
tags: [planning, delivery]
---

# TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW

## Title
A GitHub Project as a generated, read-only view of ticket state across seats and hosts

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The owner's request (#715 6813165811, "looking good with that proposal about github project, I think you can try"), relayed by
lead-planner-u24 with constraints 1-6. Designed by agent-working-designer-u24, and lead-planner-u24 OK'd the design. The full
design (§0-§10 plus the addendum) is the main-checkout draft
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

One tool, `tools/sessions/project_sync.py`, derives each ticket's state from the ticket files on origin/main, the worktree
branches on each host and open PRs. It reconciles one user-level GitHub Project of **draft items** to that state. The ticket
files stay the only source. The Project is never read back into tickets.

## Scope
Children, in order (see SEQUENCE.md):
| # | Child | Cost | Owner gate |
|---|---|---|---|
| P0 | `TCK-20261112-PROJECT-SYNC-DRY-RUN`: `project_sync.py --dry-run` on u24, rpg lanes; derive and print the plan, no Project writes | ~250 lines + ~13 tests | none (covered by 6813165811) |
| P1 | `--init` / `--apply` on u24, rpg lanes, run by hand | ~120 lines GraphQL + 4 tests (injected client) | owner creates the Project; token choice (fine-grained tested first, else classic `project`) |
| P2 | ubuntu runs the same tool (host-tagged facts, design §5) | ~40 lines + 3 tests | token on ubuntu |
| P3 | all lanes; per-host timer (cron or SessionStart) | config + a host change | the timer |
| P4 | claim-rule change: ticket file on a branch replaces #634 claim comments for ticketed work (design §7) | a docs line in session-roles guidance | the decision, after P3 |

P1-P4 are cut when their gate clears. The lead carries the P1 owner ask.

Decisions agreed in the design:
- Draft items, not issues. The title is `<ID>: <Title>`, with a one-line generated body.
- Fields are created by name, and no ids are stored. Status is derived by the 5-rule first-match order.
- One writer per host, doing a full reconcile. A `Sync hash` detects hand edits, which are reported and then overwritten.
- Facts are tagged by host.
- Done items cover only tickets after the pilot start and are archived after 14 days.
- #634 comments are never parsed.

## Out of Scope
(design §9)
- Writing back to ticket files or issues.
- Seats with no worktree, until P4.
- Detached scratch worktrees, except to report them as unattributed.
- Branches that are only on origin with no PR.
- Real-time updates.
- Historical Done tickets.
- Views, charts, iterations and estimates.
- Any change to the agent-ops dashboard.

## Acceptance Criteria
1. P0 is done and its dry-run plan has been reviewed against real u24 state.
2. Each later child is filed only when its owner gate clears, and is closed or explicitly dropped.
3. The epic closes when P3 runs on both hosts, or when the owner stops it at an earlier phase, with that recorded here.

## Related Tickets
- TCK-20261112-PROJECT-SYNC-DRY-RUN (P0)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (done; the run/monitoring dashboard, kept as is)
- Received 2026-11-14 from TCK-20261009-EPIC-SESSION-LEAD-PLANNER (closed, owner #715 6875225978): E2's cross-host fleet view is covered by this epic's per-seat ticket view; no separate fleet.py is planned.

## Related Docs
- docs/guidelines/session_roles/ (P4 target)

## Related Stored Artifacts
- Designer draft (main checkout): `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`

## Related Code Areas
- tools/sessions/status.py (`collect()`, `seat_infos()`, reused), tools/sessions/project_sync.py (new),
  registries/session_project.yaml (new), tests/tools/test_session_project_sync.py (new)

## Assumptions / Open Questions
- Simpler-fix check (6698958617): P0 is the simplest first step. It needs no token and no owner action, and it shows whether
  the derivation is right before anything is written. What it leaves out is any visible board until P1.
- Token (design §6): whether fine-grained tokens work for user-owned Projects isn't confirmed. The owner tests it in the P1 ask.
- This is code, so it doesn't ride along (#715 6793205403).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
