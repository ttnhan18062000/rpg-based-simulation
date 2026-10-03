---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260804-BACKLOG-PHASE-VALIDATOR-FIX
phase: done
date: 2026-08-04
tags: [documentation, process-improvement]
---

# TCK-20260804-BACKLOG-PHASE-VALIDATOR-FIX

## Title
validate_frontmatter.py's PHASE_VALUES enum is missing 'backlog', contradicting the documented ticket-lifecycle convention

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`docs/ai/ticket-lifecycle.md` documents `phase: backlog` as the required frontmatter value for
tickets deliberately moved to `tickets/backlogs/` ("update the ticket's own `## Status` to `BACKLOG`
... plus its frontmatter `phase: backlog`"), with `tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md`
cited as the worked example. `tools/validate_frontmatter.py`'s `PHASE_VALUES` enum
(`{"open", "inprogress", "blocked", "done"}`, line 56) was never updated to include it — confirmed
directly: running the validator against that exact worked-example ticket, sitting in the repo right
now, fails with `phase: invalid value 'backlog'`. Found while attempting to move
`TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC` to `tickets/backlogs/` per the same documented
convention and hitting the identical validator failure.

## Scope
- `tools/validate_frontmatter.py`: add `"backlog"` to `PHASE_VALUES` (line 56).
- `tests/tools/test_validate_frontmatter.py:690`: update the existing assertion
  `PHASE_VALUES == {"open", "inprogress", "blocked", "done"}` to include `"backlog"`.

## Out of Scope
- Any other frontmatter enum (`status`, `authority`, `layer`, `tags`) — untouched, this is
  `phase` only.
- Retroactively re-validating every other file under `tickets/backlogs/` beyond confirming the one
  worked example now passes — not aware of other backlog tickets with a different, real
  frontmatter defect.
- Changing `docs/ai/ticket-lifecycle.md`'s own documented convention — it is already correct; the
  code was the thing out of sync with the doc.

## Acceptance Criteria
- [x] `PHASE_VALUES` in `tools/validate_frontmatter.py` includes `"backlog"`.
- [x] `python3 tools/validate_frontmatter.py tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md --content-type ticket`
      passes (confirms the fix against the real, pre-existing worked example, not just a synthetic
      test). Verified directly: now returns "OK: 1 file(s) checked — no violations" (was failing
      before this fix).
- [x] `tests/tools/test_validate_frontmatter.py`'s `PHASE_VALUES` assertion updated and passing.
- [x] Existing `tests/tools/test_validate_frontmatter.py` suite passes with no other regression.
      Verified directly: 83 passed, 0 failed.

## Related Tickets
- `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC` — the ticket whose own backlog-move (same
  session) surfaced this bug; that move is blocked on this fix landing first.
- `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC` — the epic that originally moved
  `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` to `tickets/backlogs/` and established the
  `phase: backlog` convention in `docs/ai/ticket-lifecycle.md`, apparently without the validator
  ever being updated to match at the time.

## Related Docs
- `docs/ai/ticket-lifecycle.md` (the "`tickets/backlogs/`" section, lines ~610-638) — the
  authoritative convention this fix brings the validator into parity with; no change needed to
  this file itself, it was already correct.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tools/validate_frontmatter.py`
- `tests/tools/test_validate_frontmatter.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Single-line fix in `tools/validate_frontmatter.py:56` (`PHASE_VALUES` gains `"backlog"`) plus the
matching test-assertion update in `tests/tools/test_validate_frontmatter.py:690`. No other code
touched. Confirmed the bug was real and pre-existing (not introduced by this session) by running
the validator against the actual worked-example ticket cited in `docs/ai/ticket-lifecycle.md`
before making any change — it failed exactly as described.

## Test Summary
`pytest tests/tools/test_validate_frontmatter.py -q` → 83 passed, 0 failed.
`python3 tools/validate_frontmatter.py tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md --content-type ticket`
→ passes (previously failing).

## Files Changed
- `tools/validate_frontmatter.py`
- `tests/tools/test_validate_frontmatter.py`

## Completion Summary
`PHASE_VALUES` now includes `"backlog"`, matching `docs/ai/ticket-lifecycle.md`'s already-correct
documented convention. The real, pre-existing worked-example ticket in `tickets/backlogs/` now
validates cleanly for the first time since that convention was established. Unblocks
`TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`'s own backlog move, done in the same session.
