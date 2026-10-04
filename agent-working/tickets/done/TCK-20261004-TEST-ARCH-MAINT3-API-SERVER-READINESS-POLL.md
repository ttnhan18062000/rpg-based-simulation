---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-TEST-ARCH-MAINT3-API-SERVER-READINESS-POLL
phase: done
date: 2026-10-04
tags: [testing]
---

# TCK-20261004-TEST-ARCH-MAINT3-API-SERVER-READINESS-POLL

## Title
tests/api: replace the fixed 3 s server wait with a /health readiness poll

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary

Four sites start `python -m src serve` as a subprocess and then `time.sleep(3)`. Replace the fixed wait with a
bounded poll of `GET /health`, failing with a clear message that includes whether the subprocess has exited.
Agreed on PR #322 (codebase handoff section 2); brief from `test-architecture-reviewer` (maintenance 3, T3).

## Scope

- New shared helper `tests/api/server_readiness.py::wait_for_server_ready(server, port)`: polls
  `http://127.0.0.1:{port}/health` every 0.1 s for up to 30 s, accepts HTTP 200, fails fast if `server.poll()` is not
  `None`, and on timeout or early exit raises `AssertionError` with the return code and the last probe error.
- Sites: `tests/api/test_live_entity_inspection.py`, `tests/api/test_live_observability_status.py`,
  `tests/api/test_rest_parity.py` (two sites, `test_api_rest_parity` and `test_api_compression`).
- The wait is the first statement inside each `try:` so the existing `finally` still terminates the server if the
  wait fails (the old sleep sat before the `try:`, which would have leaked the process on a raising wait).
- `import time` removed from the two files that no longer use it.

## Out of Scope

- The 0.5 s sleeps at `test_live_observability_status.py` lines 46 and 56: they follow the pause and resume POSTs
  and wait for state to settle, not for the server to boot, so they are not the same wait and stay.
- Ports, assertions, any other test, any `src/` change, quarantine (regression_policy section 6.1).
- **Noted only, not changed:** the tests use fixed ports (8011, 8012, 8002, 8003), which is a separate
  parallelism risk (two runs on one machine, or a leftover server, collide); the poll does not address it.

## Acceptance Criteria

- [x] No `time.sleep(3)` remains in the three files; one shared helper, not four copies.
- [x] Poll interval about 0.1 s, timeout about 30 s, failure message includes `server.poll()` state and return code.
- [x] The three files pass 5 times in a row; wall time before and after reported.
- [x] No port, assertion or other behaviour changed.

## Related Tickets

- Siblings: `TCK-20261004-TEST-ARCH-MAINT3-EPIC-B-COST-ROWS-AFTER-306`,
  `TCK-20261004-TEST-ARCH-MAINT3-SOCIAL-LEDGER-LINKS-AND-FINDING`,
  `TCK-20261004-TEST-ARCH-MAINT3-DECISION-TRACE-VACUOUS-ASSERT`

## Related Docs

- `docs/testing/regression_policy.md` section 6.1 (no quarantine)

## Related Stored Artifacts

None.

## Related Code Areas

- `tests/api/`; `src/api/server.py` (read only; `/health` is the only route exempt from API-key auth)

## Assumptions / Open Questions

- `/health` returns 503 when the engine reports `unhealthy`; the helper treats only 200 as ready, so a server that
  boots unhealthy times out with `HTTP 503` as the last probe in the message.
- `search_docs` and graphify gave nothing relevant here; not a gate.

## Implementation Notes

Control run: a subprocess that exits with code 3 immediately makes the helper fail with
`exited before becoming ready (returncode=3)` and the last connection error, well before the timeout.

## Test Summary

Before (5 runs of the three files, repo venv): 5 passed each, 14.7-15.0 s pytest time, 15.5-15.8 s wall per run,
**78.07 s total**. After: 5 passed each, 9.8-10.2 s pytest time, 10.6-11.0 s wall per run, **53.98 s total**, five
runs green. The roughly 5 s saved per run is the four fixed 3 s sleeps replaced by the time the server takes to
answer `/health`.

## Files Changed

- `tests/api/server_readiness.py` (new)
- `tests/api/test_live_entity_inspection.py`, `tests/api/test_live_observability_status.py`,
  `tests/api/test_rest_parity.py`

## Completion Summary

Done 2026-10-04. The three server-boot test files now wait on `/health` instead of sleeping 3 s, with a bounded,
diagnosable failure, and run about 24 s faster over five runs. Fixed ports remain a noted, unchanged risk.
