---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261007-LAUNCHER-RELAUNCH-FIXES
phase: done
date: 2026-10-07
tags: [ai, process-improvement]
---

# TCK-20261007-LAUNCHER-RELAUNCH-FIXES

## Title
Launcher relaunch fixes A-E: legacy-name transcripts, handover path line, merged-branch guard, second-instance lease, card wording

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Found while relaunching the live sessions on 2026-10-07 (draft: `.claude/handover/drafts/launcher-relaunch-fixes-draft-2026-10-07.md`, items A-E, by agent-working-designer). Dispatched by agent-working-planner with the owner's confirmation; the code was reviewed and approved by the planner.

## Scope
- A: `tools/sessions/launch.py` candidate transcripts also match the first instance's `legacy_session_name` (never a second instance's).
- B: the dry run prints `handover note: <absolute path>` (read from the main checkout); one doc sentence in `docs/guides/agent_session_reset_boundaries.md`.
- C: `ensure_worktree` does not recreate a missing worktree from a recorded branch already merged into `origin/main`.
- D: `session_start_hook.py` takes the writer lease only for the role's first instance (option i of the draft).
- E: implementer card wording "two instances never share one", cards regenerated, 400-token cap held.

## Out of Scope
- Whether the writer lease should exist at all for a worktree used only as a launch cwd (open owner question).
- A `-1` alias for the first instance; changing the one-writer-per-worktree model.

## Acceptance Criteria
- [x] A: a transcript titled with the seat's legacy name is a candidate of the first instance only
- [x] B: the dry run prints the absolute handover note path
- [x] C: a recorded branch that is an ancestor of origin/main is reported, not recreated
- [x] D: a `<role>-2` start neither takes the lease nor prints "WRITER LEASE NOT TAKEN"
- [x] E: card carries the two-instance rule and every composed card is within 400 tokens
- [x] `pytest tests/tools -k session` green (547 passed)

## Related Tickets
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS
- TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED

## Related Docs
- `docs/guides/agent_session_reset_boundaries.md`; `docs/guidelines/session_roles/functions/implementer.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `.claude/agents/session-*-implementer.md`, `tests/tools/test_session_launch.py`, `tests/tools/test_session_resolve_and_hook.py`

## Assumptions / Open Questions
- Open (owner): should the writer lease exist at all for a worktree used only as a launch cwd? D only stops the second instance from tripping it.
- C also refuses a freshly cut branch whose tip equals `origin/main`; accepted (nothing to lose, the message says to recreate from origin/main). A stale local `origin/main` only yields a false "not merged", the old behaviour.
- Card cap: to hold 400 tokens, "never mid-batch" and the "See cross_session_messages guide" pointer were cut from the implementer card; the planner accepted this.

## Implementation Notes
See the Scope list; each item has a regression test.

## Test Summary
`pytest tests/tools -k session`: 547 passed. New tests: legacy-title candidate, merged-branch guard, dry-run handover path, second-instance lease.

## Files Changed
`tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `docs/guidelines/session_roles/functions/implementer.md`, `docs/guides/agent_session_reset_boundaries.md`, `.claude/agents/session-{agent-working,codebase,rpg,testing}-implementer.md`, the two test files, this ticket.

## Completion Summary
Launcher fixes A-E landed in one local commit, unpushed; push and PR stay with the owner.
