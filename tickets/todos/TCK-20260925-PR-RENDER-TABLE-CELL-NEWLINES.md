---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES
phase: open
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
   normalizing at read time would damage a section that is currently correct. Confirm against the
   module's structure rather than taking this on faith.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
