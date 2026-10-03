---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
artifact_type: test_plan
tags: [delivery, ai]
---

# Test Plan: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION

Extends `tests/tools/test_delivery_pr_render.py` (same module this ticket modifies).

## Normal flow
- AC1: two discovered tickets, one recorded exclusion -> `render()`'s title `(N tickets)` count,
  `## What landed`, `## Tickets`, `## Why`, `## Verification`, `Closes:` all agree with the
  post-exclusion set of one ticket. Uses the same isolated-diff shape that found the bug (AC7):
  compare a fully-excluded render against a fully-unexcluded render via `compare_generated_body`
  and assert the *expected* sections differ for the *right* reason (title/all 5 change because the
  ticket count changed, not because of a bug).
- AC2: `check_against_live()` against a live body that already reflects the recorded exclusion
  (and nothing else) -> `matches: True`, `review_notes_hand_filled` still reported separately.

## Edge cases
- AC3: `check_against_live()` called with no `exclusions` kwarg at all reproduces a previously-
  recorded exclusion purely by fetching the live PR body (via the fake `gh pr view` runner) and
  calling `extract_recorded_exclusions()` on it internally — proving the record is read
  automatically from the one place that's actually durable (the live body), not from any local
  state the caller must remember.
- AC4: excluding a ticket ID that was never in the discovered commit-subject set -> a warning
  naming it, output otherwise unaffected.
- AC6: no `exclusions` argument passed at all (the default, every existing call site) ->
  `render()`'s output byte-identical to a call from before this ticket (regression-pinned against
  the existing `test_two_tickets_title_and_table_rows` fixture, re-run unmodified).

## Failure modes / regression-prone paths
- AC5: with an exclusion recorded for the exact ticket ID already causing a commit-subject/
  changed-file mismatch, the mismatch warning still appears (recording an exclusion is about
  presentation, not about suppressing the disagreement diagnostic).
- The real PR #251 scenario, reconstructed as a fixture (not asserted against the live PR, which
  is merged and gone): 4 commit-subject tickets, one with no changed file and no ticket file on
  the branch at all (matching the real shape — the excluded ticket's `.md` file was never touched
  on this branch either), excluded and reasoned -> the remaining 3 render consistently.
- `render_exclusion_comment()`/`extract_recorded_exclusions()` round-trip: formatting a comment
  then parsing it back yields the original `(ticket_id, reason)` pair, including a reason
  containing a comma or an em dash (real reason text in this repo's own style), proving the regex
  isn't fooled by punctuation inside the quoted reason.
- Multiple recorded exclusions in one body: `extract_recorded_exclusions()` finds all of them, not
  just the first match.

## Existing tests checked for overlap
- `test_two_tickets_title_and_table_rows`, `test_body_contains_all_spec_sections_in_order_and_closes`
  — re-run unmodified as AC6's regression guard (no exclusions file -> unchanged).
- `test_check_reports_no_difference_when_identical`/`test_check_reports_difference_when_changed`
  (from `TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS`) — re-run unmodified; confirm this ticket's
  change doesn't regress the sibling ticket's own section-aware comparison fix.
