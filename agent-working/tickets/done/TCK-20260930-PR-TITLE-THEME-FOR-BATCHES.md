---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-PR-TITLE-THEME-FOR-BATCHES
phase: done
date: 2026-09-30
tags: [delivery, ai, documentation]
---

# TCK-20260930-PR-TITLE-THEME-FOR-BATCHES

## Title
Document --theme for multi-ticket PRs so batch titles don't default to the newest commit's ticket

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found on PR #261 (2026-09-30). The rendered title was "ai: Make REST PATCH plus a read-back check
... (4 tickets)", which names the batch's smallest ticket. The headline was the Workflow-runtime
pilot.

`tools/delivery/pr_render.py::render_title()` falls back to `tickets[0]["title"]` for a
multi-ticket batch when no `--theme` is given. Its own comment says this is a stated default, not
real synthesis. `discover_tickets()` orders tickets newest-commit-first, so the title always names
whichever ticket closed last. That's documented renderer behavior. The gap is that
`docs/guides/delivery_process.md`'s PR Lifecycle never mentions `--theme`, so no caller knows to
pass it.

## Scope
1. In the PR Lifecycle render step, state once that a multi-ticket batch PR passes
   `--theme "<one-line batch headline>"`, and that the same `--theme` goes to `--check`. Without
   it, the title names the most recently closed ticket.
2. REQUIRED (standing rule, user 2026-09-30: finish a feature completely; no optional scope): make `pr_render.py` print a one-line stderr hint when it renders
   a multi-ticket title without `--theme`. It stays advisory; don't make `--theme` required.

## Out of Scope
- Having the renderer infer the "most significant" ticket.
- Re-titling past PRs.

## Acceptance Criteria
1. `delivery_process.md` names `--theme` for multi-ticket batches exactly once, covering both
   render and `--check`.
2. A test shows the hint appears for more than one ticket with no theme, and
   doesn't appear for a single ticket or when a theme is given.

## Related Tickets
- TCK-20260924-DELIVERY-PR-RENDERER (done; introduced `--theme` and the fallback)
- TCK-20260930-PR-BODY-UPDATE-REST-PATCH-PRIMARY (done in PR #261; edited the same guide section)

## Related Docs
- `docs/guides/delivery_process.md` ("PR Lifecycle")

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/delivery/pr_render.py` (`render_title()`, `discover_tickets()`)

## Assumptions / Open Questions
- None.

## Implementation Notes
`render()` returns a new `hints` list (separate from `warnings`, because `render_body()` can
embed warnings in the PR body). It holds one line when `theme is None and len(tickets) > 1`.
`main()` prints each as `HINT: ...` on stderr in the plain (non-`--check`, non-`--json`) path only,
beside the existing `WARNING:` lines. `--theme` stays optional. `delivery_process.md` step 3 now
states once that a batch PR passes `--theme` to both the render and `--check`.

## Test Summary
`tests/tools/test_delivery_pr_render.py`: 46 passed, including 4 new tests (hint present for 2
tickets/no theme and absent from body+warnings; absent with theme; absent for 1 ticket; CLI prints
`HINT:` to stderr only).

## Files Changed
- `tools/delivery/pr_render.py`
- `tests/tools/test_delivery_pr_render.py`
- `docs/guides/delivery_process.md`

## Completion Summary
Multi-ticket renders without `--theme` now say so on stderr, and the guide tells callers to pass it.
