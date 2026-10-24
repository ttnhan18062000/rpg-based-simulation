---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261024-SESSION-HOOK-TEST-STUBS-DISK-HEADROOM
phase: done
date: 2026-10-24
tags: [testing, determinism]
---

# TCK-20261024-SESSION-HOOK-TEST-STUBS-DISK-HEADROOM

## Title
The session-start hook tests stub the disk-headroom probe, so a runner below 10 GB free cannot make them flaky

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Reported independently by lead-planner (PR #529 at a5428660e, run 40103684867 job 120900845021) and
codebase-planner (PR #731 at f62ca3c78, twice): `tests/tools/test_session_resolve_and_hook.py::
test_a_hanging_gh_is_cut_off_at_the_timeout` fails in "Tools · f–z" on PRs with no tools/ change. It builds the
SessionStart context twice and asserts `out == baseline`. Below 10 GB free the context embeds the live disk-headroom
line ("only 6.8 GB free"), so the two strings differ whenever free space crosses a 0.1 GB step between the calls
(diff is exactly `6.8` vs `6.7`). Main is green; it depends on the runner's disk.

## Scope
1. In the `world` fixture (or an autouse fixture in that file), monkeypatch the disk-headroom probe the hook calls
   (`tools.sessions.disk_headroom` / `tools.sessions.disk_warning`; trace the actual call from
   `hook.build_context`) to a fixed result, so every `_ctx(...)` call in the file is deterministic. Prefer one stub
   over editing each comparison.
2. Keep or add one test that asserts the disk line *does* appear when the stub reports low space, so the stub does
   not hide the feature.
3. Check the file's other `== baseline` tests (lines ~445-471) pass under the stub; grep `tests/tools/` for other
   tests that compare whole SessionStart output twice and apply the same stub if any exist.

## Out of Scope
- Changing the disk warning's text, threshold or rounding.

## Acceptance Criteria
- No test in the file reads the real filesystem's free space.
- The test passes with the probe forced below the threshold and changing between calls (prove it with a test that
  makes the stub return different values per call against the old code path, or state how you verified).
- `tests/tools/test_agent_working_paths_guard*.py` passes.

## Related Tickets
- TCK-20261008-SESSION-DISK-HEADROOM-GUARD (the warning)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/tools/test_session_resolve_and_hook.py`, `tools/sessions/disk_headroom.py`, `tools/sessions/disk_warning.py`

## Assumptions / Open Questions
None.

## Implementation Notes
The hook's `_disk_line` calls `disk_headroom.free_bytes(root)`. The `world` fixture now monkeypatches that to 500 GB, so no context in the file carries the disk line. New test `test_the_disk_line_appears_when_the_probe_reports_low_space` flips the stub to 3 GB and asserts the line. Only this file compares whole SessionStart output twice.

## Test Summary
86 passed (`test_session_resolve_and_hook.py` + `test_agent_working_paths_guard*.py`). Proved against the trigger: with the stub replaced by a probe that drops 0.1 GB per call from 6.8 GB, `test_a_hanging_gh_is_cut_off_at_the_timeout` fails (the CI failure); with the fixed stub it passes. The real disk (13 GB free) is above the threshold, so the real trigger cannot be hit naturally here.

## Files Changed
- tests/tools/test_session_resolve_and_hook.py

## Completion Summary
The session-hook tests no longer read the runner's free disk space.
