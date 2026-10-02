---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-PR-RENDER-CITED-ONLY-AND-TICKETLESS-BRANCHES
phase: done
date: 2026-10-02
tags: [delivery]
---

# TCK-20261002-PR-RENDER-CITED-ONLY-AND-TICKETLESS-BRANCHES

## Title
pr_render: leave cited-only tickets out of `Closes:`, and render a branch that closes no ticket

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Two gaps found by rpg-feature-planning on a docs plus stored_artifacts branch (own-01-derived-stats-evidence),
reproduced by `agent-working-design` (`.claude/handover/drafts/pr-render-cited-and-ticketless/`):
1. A ticket named in a commit subject but whose file the branch does not change (a follow-up commit to an
   already-closed ticket) landed in `Closes:` and the title, so merging would re-close a closed ticket. A third
   variant of the `Closes:` defect after `TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS`.
2. A branch that changes no ticket file could not be rendered (wrong body, or `title: None` with
   `--exclude-ticket`), so it could not be PR'd within the rule that PR bodies are rendered.

## Scope
- `discover_tickets()`: a commit-subject ticket whose file is found but not changed by the branch is left out
  with a "cited, not closed" warning.
- `render()`: with no tickets left, `--theme --scope --why` render a ticketless body (title
  `<scope>: <theme> (no tickets)`, changed directories with file counts, last line `Closes: (none)`);
  without the flags the tool says what to pass. `--check` accepts the same flags.
- One paragraph in `docs/guides/delivery_process.md`; two older tests now pass `b_changed=True` because they used
  an unchanged cited ticket as a normal one.

## Out of Scope
- Inventing theme or why text (they come from the caller). Anything else parsing `Closes:` (checked: nothing does).

## Acceptance Criteria
- A cited-only ticket is not in `Closes:` or the title and is warned about.
- A ticketless branch renders with the three flags and ends in `Closes: (none)`.
- The 5 new tests fail on the previous module.

## Related Tickets
- TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS
- TCK-20260924-DELIVERY-PR-RENDERER

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
none (hotfix)

## Related Code Areas
- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py

## Assumptions / Open Questions
- Tier: hotfix, since it adds flags to an existing tool without changing any contract; design read it the same way.
- Changed files come from the existing `base_ref..HEAD` diff, so a ticket the branch changes is never excluded.

## Implementation Notes
Applied design's `pr_render2.patch` verbatim (3 files, +149/-8). Reviewed the two older-test edits: both used
the "phantom" fixture ticket as a changed ticket; `b_changed=True` restores that intent, and the manual
`--exclude-ticket` path is still tested on a changed ticket.

## Test Summary
`tests/tools/test_delivery_pr_render.py` and `tests/tools/test_test_scope_coverage_static.py`: 83 passed.
Negative control: against the previous module the 5 new tests fail (5 failed, 49 passed).

## Files Changed
- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py
- docs/guides/delivery_process.md

## Completion Summary
A cited-only ticket no longer re-closes; a branch with no ticket can be PR'd with a rendered body.
