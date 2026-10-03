---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS
artifact_type: test_plan
tags: [delivery, ai]
---

# Test Plan: TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS

Extends `tests/tools/test_delivery_pr_render.py` (same file, new tests appended — this ticket
modifies that module's own check-comparison logic, not a separate concern warranting a new test
file).

## Normal flow
- AC1: live body = rendered body except `## Review notes` replaced with hand-written prose ->
  `matches is True`, `review_notes_hand_filled is True`, `differing_sections == []`.
- AC2: live body's `## Tickets` table content changed (simulating a ticket closed since the body
  was written) -> `differing_sections == ["## Tickets"]`.

## Edge cases
- AC3: both AC1 and AC2's results are distinguishable purely from `result` dict contents (no diff
  text parsing needed) — asserted directly on the dict shape.
- A live body with a hand-added, unrecognized `## Extra thoughts` section -> appears in
  `unexpected_sections`, `matches` unaffected by its presence.
- A live body missing the `## Why` section entirely (hand-deleted) -> reported as a difference
  naming `## Why`, not a crash.

## Failure modes / regression-prone paths
- AC4: `--check` still exits 0 for both a match and a difference, still performs no filesystem
  write (existing `test_no_write_side_effect` already covers the no-write half generally; a
  targeted assertion added for the new comparison path specifically).
- AC5: title comparison behavior is a direct carry-over of the existing
  `test_check_reports_no_difference_when_identical`/`test_check_reports_difference_when_changed` —
  both re-run unmodified against the new code to pin no regression.
- AC6: two-ticket fixture, each with a distinct FAIL-bearing `Test Summary` sentence -> both gap
  texts appear in the rendered body as separate, ticket-tagged entries, never merged into one
  semicolon-joined run-on line.
- AC7: addendum committed to `tickets/done/TCK-20260924-DELIVERY-PR-RENDERER.md`'s Implementation
  Notes (not a test-covered condition; verified by direct read at Verify).

## Existing tests checked for overlap
- `test_check_reports_no_difference_when_identical`/`test_check_reports_difference_when_changed` —
  re-run as regression guards (AC5), not duplicated.
- `test_known_gap_from_test_summary_renders_into_verification`/`test_no_gap_states_none_stated` —
  single-ticket gap cases, still valid; AC6's new test is the two-ticket case these don't cover.
