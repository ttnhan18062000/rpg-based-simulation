---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-PR-RENDER-TITLE-NOT-WHITESPACE-COLLAPSED
phase: done
date: 2026-09-29
tags: [delivery, ai]
---

# TCK-20260929-PR-RENDER-TITLE-NOT-WHITESPACE-COLLAPSED

## Title

pr_render.py's render_title() uses a ticket's raw multi-line `## Title` text directly as the PR
title, without collapsing whitespace, unlike every other rendered section.

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

Found 2026-09-29 while opening the PR for `working-log-consolidation-cross-checkout-fix`
(TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS). That ticket's `## Title` is
multi-paragraph prose that wraps across several lines in the ticket source (a real, established
convention in this repo — recent merged PR titles like `4512eae30`'s are also long multi-sentence
descriptions, not short single-line summaries). `tools/delivery/pr_render.py --json` rendered the
PR `title` field with the raw embedded newlines intact:

```
"title": "observability: Working-log consolidation reads pending shards from the script's own checkout but appends the rows\nto the caller's cwd-relative `tickets/working_log.csv`, then deletes the shards. ..."
```

A multi-line string is not a valid `gh pr create --title` value and would break the PR creation
step this tool exists to support.

**Mechanism, confirmed from source:**

- `tools/delivery/pr_render.py`'s `_collapse_whitespace()` (used by `_render_table_cell()` and the
  multi-ticket `## What landed`/`## Tickets` bullet rendering) exists specifically to handle "a
  ticket's own multi-line `## Title` prose" per its own docstring.
- `render_title()` (the function that builds the actual PR title returned as `result["title"]`)
  uses `tickets[0]["title"]` directly, with no call to `_collapse_whitespace()` at all — the one
  rendered value that structurally most needs it (a `gh pr create --title` argument, and a GitHub
  PR title) is the one value the existing whitespace-collapse pattern never reaches.
- `tests/tools/test_delivery_pr_render.py::test_multiline_title_with_pipe_collapses_to_one_row`
  already seeds a multi-line-titled ticket and confirms the `## Tickets` table row and `## What
  landed` bullet both collapse correctly, but only asserts against `result["body"]` — it never
  asserts anything about `result["title"]`, so this gap was never caught.

## Scope

1. `render_title()` calls `_collapse_whitespace(text)` before formatting, for both the
   single-ticket and multi-ticket/theme branches.
2. Regression test: a ticket with a multi-line `## Title` renders a `result["title"]` with no
   embedded newline, and no words lost. Must fail on the pre-fix code.

## Out of Scope

- `theme` (the manually-supplied override for a themed multi-ticket PR) — already caller-supplied
  plain text in every real call site; not sourced from a ticket's raw `## Title` field, so not
  part of this bug's mechanism. Left untouched.

## Acceptance Criteria

- AC1: `render_title()`'s output never contains a newline character for a real ticket whose `##
  Title` wraps across multiple lines.
- AC2: No content lost — every word from the original multi-line title is still present in the
  collapsed title, same as the existing table-row/bullet behavior.
- AC3: The new regression test fails on the pre-fix code and passes after.

## Related Tickets

- TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS
- TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
- TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS (the PR this was found opening)

## Related Docs

- docs/guides/delivery_process.md (PR Lifecycle)

## Related Stored Artifacts

None (hotfix — no staging artifacts).

## Related Code Areas

- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py

## Assumptions / Open Questions

None.

## Implementation Notes

`render_title()` now wraps `text` in `_collapse_whitespace()` before formatting, for both the
single-ticket and multi-ticket branches (the `theme` branch is untouched — see Out of Scope). Added
`test_render_title_collapses_multiline_title_whitespace` to
`tests/tools/test_delivery_pr_render.py`, calling `pr_render.render_title()` directly with a
multi-line-titled ticket dict; confirmed to fail on the pre-fix code (asserts no `\n` in the
result) via the same revert/rerun/restore method used in
TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS.

## Test Summary

- New test `test_render_title_collapses_multiline_title_whitespace` confirmed to fail on pre-fix
  code, passes after (AC3).
- Full `tests/tools/test_delivery_pr_render.py` suite passes after the fix.

## Files Changed

- `tools/delivery/pr_render.py`
- `tests/tools/test_delivery_pr_render.py`

## Completion Summary

Fixed `render_title()` to collapse whitespace the same way every other rendered PR-body section
already does, so a ticket whose `## Title` legitimately wraps across multiple lines in its own
source (an established convention in this repo) no longer produces a multi-line PR title that
would break `gh pr create --title`. Found and fixed while opening the PR for
TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS, itself a case of exactly this
title shape.
