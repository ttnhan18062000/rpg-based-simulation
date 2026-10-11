---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-SESSION-START-FOR-ROLE-ISSUES
phase: open
date: 2026-10-11
tags: [ai, process-improvement, delivery]
---

# TCK-20261011-SESSION-START-FOR-ROLE-ISSUES

## Title
SessionStart lists the role's open GitHub issues labelled `for:<role>` (Epic E, part E4a)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child of Epic E (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`), part E4, from GitHub issue #492 (owner-approved
2026-10-10). Cross-host handoffs now go out as GitHub issues labelled `for:<role>`; all 17 labels exist.
Sessions see them only when someone prompts them, because SessionStart injects just the card and the handover
note. Today, agent-working-planner found #492, #495 and #498 only because the owner said "check issues".

## Scope
- In `tools/sessions/session_start_hook.py`, for sources `startup`, `resume` and `clear` (not `compact`), append
  after the handover note a short list of the role's open `for:<role>` issues: number, title and age only, never
  bodies. A second instance (`<role>-N`) uses its role's label.
- One call: `gh issue list --label for:<role> --state open --json number,title,createdAt --limit 11`, with a short
  timeout (about 3 s; fix the value in plan.md).
- Fail open: when `gh` is missing, unauthenticated, offline, slow or returns bad JSON, print nothing and never
  block or delay the start beyond the timeout. Log nothing to the session context in that case.
- Cap the list at 10 items, then "and N more" (N is unknown past the limit: say "and more").
- Document the convention in `docs/guides/cross_session_messages.md`. A `for:<role>` issue is a durable,
  cross-host `finding` or `question`. The owning planner turns an accepted one into its own ticket. Closing it
  means "absorbed into <ticket>" or "answered", with a link.

## Out of Scope
- The per-seat `for:<role>` count in `fleet.py`: that belongs to E2, which does not exist yet. Record it in E2's
  scope when E2 is filed.
- Creating or managing labels; reading issue bodies; any write to GitHub.
- The lead board and status messages (sibling `TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD`).

## Acceptance Criteria
1. With a stubbed `gh` returning one issue labelled for the role, the hook output lists it after the handover note.
   An issue labelled for another role is not requested and does not appear.
2. With `gh` missing, failing (non-zero exit), hanging past the timeout, or returning invalid JSON, the hook output
   equals the output without the feature. The hang case finishes within the timeout plus a small margin (tested).
3. More than 10 issues show 10 plus the "and more" line.
4. `compact` does not run the call.
5. `docs/guides/cross_session_messages.md` documents the convention.
6. `pytest tests/tools/test_session_*.py` passes.

## Related Tickets
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER (parent, E4)
- TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD (sibling, E4b)
- GitHub issue #492

## Related Docs
- docs/guides/cross_session_messages.md
- docs/plans/agent_infrastructure/session_layer_working_process.md (§9.0)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/session_start_hook.py
- tests/tools/test_session_resolve_and_hook.py

## Assumptions / Open Questions
- `gh` is authenticated on both hosts today. The TLS failures seen against api.github.com on host u24desktop are
  exactly the slow/offline case and must stay invisible.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
