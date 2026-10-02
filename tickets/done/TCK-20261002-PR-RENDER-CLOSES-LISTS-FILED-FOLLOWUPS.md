---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS
phase: done
date: 2026-10-02
tags: [delivery]
---

# TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS

## Title
pr_render must not list a ticket the PR only filed in `Closes:`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tools/delivery/pr_render.py` discovers tickets from commit-subject IDs. A PR that files a
follow-up names it in a commit subject; `find_ticket_file` finds it under `tickets/todos/`, so it
landed in `Closes:` and the title, and the mismatch warning stayed silent. Reported by
rpg-feature-planning (PR #276, #279); verified by `agent-working-design` on #279's real commits
(`.claude/handover/drafts/pr-render-closes-location/`).

## Scope
- `discover_tickets()` leaves out any ticket whose file is under `todos/` or `inprogress/` (first path part
  under the tickets root) and warns, naming the ticket and the move-to-`done/` remedy. Flat or unknown
  locations stay listed (all existing fixtures put tickets directly under the root).
- One line in `docs/guides/delivery_process.md`.

## Out of Scope
- `--exclude-ticket` behaviour (unchanged). Requiring tickets to be in `done/`.

## Acceptance Criteria
- A ticket under `todos/` or `inprogress/` is not in `Closes:`/title and is warned about.
- Flat-layout fixtures still render.
- New behavioural tests fail on the unpatched module.

## Related Tickets
- TCK-20260924-DELIVERY-PR-RENDERER

## Related Docs
- docs/guides/delivery_process.md
- docs/plans/agent_infrastructure/agent_working_direction.md

## Related Stored Artifacts
none (hotfix)

## Related Code Areas
- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py

## Assumptions / Open Questions
- `tests/tools/test_test_scope_coverage_static.py` only maps `pr_render.py` to `tests/tools/`; it pins nothing about
  ticket locations. No other test places tickets under `todos/` or `inprogress/`.

## Implementation Notes
Applied design's `pr_render.patch` verbatim (tool + 2 tests), plus the doc line.

## Test Summary
`tests/tools/test_delivery_pr_render.py` and `tests/tools/test_test_scope_coverage_static.py`: 78 passed.
Negative control: with the tool reverted, the 2 new behavioural tests fail (2 failed, 47 passed).

## Files Changed
- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py
- docs/guides/delivery_process.md
- docs/plans/agent_infrastructure/agent_working_direction.md (rows for #277 and #280, text from agent-working-design)

## Completion Summary
A PR that only files a follow-up no longer claims to close it.
