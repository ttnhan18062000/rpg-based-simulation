---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-PR-RENDER-TICKETLESS-DROPS-EXCLUSION
phase: done
date: 2026-10-08
tags: [delivery, ai]
---

# TCK-20261008-PR-RENDER-TICKETLESS-DROPS-EXCLUSION

## Title

`pr_render.py` drops recorded ticket exclusions on the ticketless path, so `--check` can never match such a body.

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

Dispatched by agent-working-planner. When every commit-subject ticket is excluded, `render()` takes the `if not tickets:` path and calls `render_ticketless_body()`, which never writes the `pr-render:exclude` comment. `--check` then reads back `{}`, rediscovers the excluded ticket from the subject, renders "(1 ticket)" and reports `matches: False` for ever. Real case: PR #427 (closed epic TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING excluded, record-only append).

## Scope

Pass `exclusions` into `render_ticketless_body` and append `render_exclusion_comment` lines exactly as `render_body` does (after `Closes:`, sorted). Keep `Closes: (none)`.

## Out of Scope

Editing PR #427's body (testing-planner re-renders it after merge).

## Acceptance Criteria

1. A ticketless render with every subject ticket excluded contains each exclude comment.
2. `--check` against that body reports `matches: True`.
3. The ticketless path with no exclusions is unchanged byte-for-byte.
4. The scoped pr_render tests pass.

## Related Tickets

TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION

## Related Docs

docs/guides/delivery_process.md

## Related Stored Artifacts

None.

## Related Code Areas

tools/delivery/pr_render.py, tests/tools/test_delivery_pr_render.py

## Assumptions / Open Questions

None.

## Implementation Notes

`render_ticketless_body` gained an optional `exclusions` argument; `render()` passes its own. Output with no or empty exclusions is identical to before.

## Test Summary

`pytest tests/tools/test_delivery_pr_render.py`: 62 passed (3 new: comments recorded, `--check` matches, no-exclusion output unchanged).

## Files Changed

tools/delivery/pr_render.py, tests/tools/test_delivery_pr_render.py

## Completion Summary

Fixed; all four acceptance criteria met. No known gaps.
