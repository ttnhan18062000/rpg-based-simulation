---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261025-HANGING-GH-TEST-BOUND-RELATIVE-TO-BASELINE
phase: open
date: 2026-10-25
tags: [testing, determinism]
---

# TCK-20261025-HANGING-GH-TEST-BOUND-RELATIVE-TO-BASELINE

## Title
The hanging-gh test bounds the extra time the gh cut-off adds, not the hook's whole run time, so a loaded runner cannot fail it

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
lead-planner finding (2026-10-25): `tests/tools/test_session_resolve_and_hook.py::test_a_hanging_gh_is_cut_off_at_the_timeout`
failed in a full serial `tests/tools` session-suite run on host ubuntu: 5.07 s against `assert time.monotonic() - start < 5`
with `ISSUE_TIMEOUT_S = 0.5`. It passes alone and with its file. The ~4.5 s is the hook's non-gh work under load, so the
absolute bound measures machine load, not the cut-off. This is the second fragility in this test after
TCK-20261024-SESSION-HOOK-TEST-STUBS-DISK-HEADROOM (#732). User approved filing it and folding it into the
TCK-20261025-RPG-UBUNTU-SEATS PR (agent-working-planner's terminal, 2026-10-25).

## Scope
1. Time the baseline `_ctx(...)` call too. Assert that the hanging-gh call takes at most `baseline_elapsed + ISSUE_TIMEOUT_S + margin`,
   with a margin of about 2 s (say why that value). Keep a generous absolute ceiling well under the 30 s `sleep`, e.g. `< 20`, so a
   cut-off that never fires still fails.
2. Check the file's other timing assertions, if any, for the same absolute-bound shape.

## Out of Scope
- Making the hook itself faster (if the 4.5 s looks wrong, record it as a finding with numbers; don't fix it here).

## Acceptance Criteria
- The test still fails if the gh cut-off is removed: show it by temporarily setting `ISSUE_TIMEOUT_S` to 60 in a scratch run, or
  state how you verified.
- It passes in the full serial session suite on host ubuntu.

## Related Tickets
- TCK-20261024-SESSION-HOOK-TEST-STUBS-DISK-HEADROOM, TCK-20261025-RPG-UBUNTU-SEATS

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/tools/test_session_resolve_and_hook.py`, `tools/sessions/session_start_hook.py` (`ISSUE_TIMEOUT_S`)

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
