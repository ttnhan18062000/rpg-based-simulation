---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES
phase: done
date: 2026-09-25
tags: [delivery, testing]
---

# TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES

## Title

`pr_render.py` emits multi-line ticket titles raw into the `## Tickets` markdown table, breaking it

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

Found on `pr_render.py`'s **first real use** — rendering the body for this epic's own PR, which is
exactly the dogfooding the tool was built for.

A ticket's `## Title` section is frequently multi-line prose wrapped across several lines. The
renderer copies it verbatim into a `## Tickets` table cell:

```
| TCK-20260924-DELIVERY-COST-MEASUREMENT | standard | Report `gh`-calls-per-PR and subject traceability over a week range in one command, so this epic's
before/after is measured rather than asserted |
```

A markdown table row is terminated by a newline, so the embedded newline ends the row mid-cell. Every
affected row renders as broken table markup on GitHub. In the render for this epic's PR, **7 of 9
rows** were affected — only the two tickets whose `## Title` happens to be a single line survived.

The same raw-copy issue applies to the `## What landed` bullets, which are also multi-line, though
there it degrades to odd wrapping rather than structurally broken markup.

This is not a content problem — the tickets' titles are fine, and rewrapping them to appease the
renderer would be fixing the wrong artifact. The renderer must normalize whitespace for a cell whose
format cannot contain newlines.

## Scope

- Collapse internal whitespace (newlines and runs of spaces) to single spaces for any value rendered
  into a `## Tickets` table cell.
- Escape or collapse a literal `|` in a title, which would otherwise split a cell the same way. Not
  observed in this render, but the same class and trivial to close while here.
- Normalize the `## What landed` bullets to a single line each, for the same reason.
- A test rendering a fixture ticket whose `## Title` spans multiple lines and contains a `|`, and
  asserting the produced table has exactly one line per ticket and the expected column count.

## Out of Scope

- **Rewrapping or shortening any ticket's `## Title`.** The tickets are correct; the renderer is not.
- Truncating long titles. Collapse whitespace, don't elide content — a truncated title in a PR table
  is a worse failure than a long one.
- The `## Verification` section's verbosity (it renders each ticket's full recorded Test Summary,
  which is faithful but long). Out of scope here — raise separately if it proves unwieldy in review.
- Any other renderer behaviour. This is a formatting fix, not a redesign.

## Acceptance Criteria

1. Rendering a ticket whose `## Title` spans multiple lines produces exactly one table row on one
   line.
2. A `|` in a title does not add a column.
3. The rendered table's column count is identical on every row, asserted by a test.
4. No title's content is lost or truncated — only whitespace is collapsed.
5. `## What landed` emits one line per ticket.
6. Existing `tests/tools/test_delivery_pr_render.py` tests pass unchanged.

## Related Tickets

- `TCK-20260924-DELIVERY-PR-RENDERER` — shipped the renderer; this is a defect in its output found
  on first real use.
- `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — owns `pr_template_spec.json`, the section spec the
  renderer consumes. Unaffected: the spec defines sections, not cell formatting.

## Related Docs

- `docs/guides/delivery_process.md` — "PR Body Template".

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-DELIVERY-PR-RENDERER/`

## Related Code Areas

- `tools/delivery/pr_render.py` — the `## Tickets` table and `## What landed` emitters
- `tests/tools/test_delivery_pr_render.py`

## Assumptions / Open Questions

1. Whether to collapse at the point of reading a ticket's `## Title` or at the point of rendering a
   cell. **Rendering is the right place** — `## Why` legitimately wants the multi-line form, so
   normalizing at read time would damage a section that is currently correct. Confirmed against the
   module's actual structure, not taken on faith: `load_ticket()` reads `title`/`request_summary`
   raw and unmodified; `_render_section()` is the only place that shapes a value differently per
   heading (`## Why` already calls `_first_paragraph()` there, distinct from `## Tickets`/`## What
   landed`'s own formatting). Collapsing in `_render_table_cell()`/`_collapse_whitespace()`, called
   only from the `## Tickets` and multi-ticket `## What landed` branches, leaves `## Why`'s
   multi-line `_first_paragraph()` output completely untouched.

## Implementation Notes

Added `_collapse_whitespace()` (all whitespace, including embedded newlines, collapsed to single
spaces) and `_render_table_cell()` (collapse + escape a literal `|` as `\|`) in
`tools/delivery/pr_render.py`. Applied to all three `## Tickets` table cells (ticket_id/tier/title)
per the ticket's literal Scope wording ("any value rendered into a `## Tickets` table cell"), and to
title only in the multi-ticket `## What landed` bullet branch (the single-ticket `## What landed`
path renders `_first_paragraph(request_summary)` as prose, not a one-line-per-item list, and is
correctly out of scope — a wrapped paragraph is not broken markdown the way a table cell or list
item is).

`## Why`'s own rendering path (`_first_paragraph()`) is untouched, confirming the Open-Questions
answer above by direct inspection rather than assumption.

## Test Summary

- `tests/tools/test_delivery_pr_render.py` — added
  `test_multiline_title_with_pipe_collapses_to_one_row`: two tickets, one with a title spanning two
  lines and containing a literal `|`. Asserts exactly one table row per ticket, that splitting each
  row on markdown-unescaped pipes (`re.split(r"(?<!\\)\|", row)`) yields exactly 5 segments (3 real
  cells), that every word from the original multi-line title survives (AC4: nothing truncated), and
  that the multi-ticket `## What landed` list also emits exactly one line for that ticket.
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
  tests/tools/test_delivery_pr_render.py -q` — **19 passed** (18 existing + 1 new).
- Full delivery-tooling regression:
  `tests/tools/test_delivery_pr_render.py tests/tools/test_delivery_ci_triage_classifier.py
  tests/tools/test_delivery_cost_measurement.py tests/tools/test_delivery_pre_push_advisory.py
  tests/tools/test_delivery_pr_status.py tests/tools/test_delivery_templates.py` — **101 passed**,
  0 failed.

## Files Changed

- `tools/delivery/pr_render.py` — `_collapse_whitespace()`/`_render_table_cell()` added;
  `_render_section()`'s `## Tickets` and multi-ticket `## What landed` branches use them.
- `tests/tools/test_delivery_pr_render.py` — 1 new regression test, `re` import added.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Fixed the renderer, not the tickets: a ticket's multi-line `## Title` (or one containing a literal
`|`) no longer breaks the `## Tickets` markdown table or the multi-ticket `## What landed` bullet
list. Confirmed the fix belongs at render time by reading the module's structure directly (`## Why`
already uses a different, correct rendering path unaffected by this change) rather than assuming.
No content lost — only whitespace collapsed and `|` escaped, exactly as scoped. Full delivery-
tooling regression stayed green throughout. No known material gap.
