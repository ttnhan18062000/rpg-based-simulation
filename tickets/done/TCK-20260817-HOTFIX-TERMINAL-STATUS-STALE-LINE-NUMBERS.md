---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS

## Title
Fix hardcoded stale `FINALIZE_INCOMPLETE` call-site line numbers in 2 terminal-status tests

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Part of a large batch of tickets fixing real, pre-existing failures in the 16 test directories
added by commit `29d78798` that were never wired into any CI job. This one:
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py::test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`
and
`tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`
both hard-assert `call_sites == [1450, 1462]` for the `FINALIZE_INCOMPLETE` status.

Root cause (confirmed via investigation): the live
`.claude/workflows/implement-ticket.js`'s two `writeMonitoring('FINALIZE_INCOMPLETE')` call sites
are currently at lines 1457 and 1469 — a consistent +7 shift from the hardcoded expectation.
`git diff 6e25d4f2 29d78798 -- .claude/workflows/implement-ticket.js` confirms the same commit that
added these test files also edited `implement-ticket.js` (new pipeline phases, a new sidecar/seq
code block), shifting line numbers by +7 by the time the file reached its final squashed form. The
extractor logic itself is correct (a sibling passing test confirms 13 literal call sites / 12
distinct values, including exactly 2 `FINALIZE_INCOMPLETE` sites); only the two hardcoded absolute
line numbers are stale.

## Scope
- Update both hardcoded `[1450, 1462]` literals to `[1457, 1469]` in
  `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py:69` and
  `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:97`.

## Out of Scope
- Any other ticket in this batch.

## Acceptance Criteria
- [ ] Both tests pass.
- [ ] No other test in either file regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`

## Implementation Notes
Updated both hardcoded `[1450, 1462]` literals to `[1457, 1469]`, matching the real, current call
sites in `.claude/workflows/implement-ticket.js`. No production code change.

## Test Summary
- `pytest tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py -q`:
  6 passed.

## Files Changed
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — line 69.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` — line 97.

## Completion Summary
Fixed two stale hardcoded line-number literals that drifted out of sync with
`implement-ticket.js` after later, unrelated edits shifted the file's line numbers by +7. The
extractor's own logic was already correct and unaffected.
