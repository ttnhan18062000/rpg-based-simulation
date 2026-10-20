---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH
phase: done
date: 2026-10-19
tags: [testing, regression]
---

# TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH

## Title
The native-refusal test writes its temp script copy under tmp_path, not a fixed name in the real `.claude/workflows/`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Finding from testing-planner (2026-10-19, CI-runtime child 1, #659), verified by agent-working-planner on origin/main
94ff6b0bc. `tests/tools/test_implement_ticket_native_refusal.py::_run_with_unported_list` writes ONE fixed-name copy of
`implement-ticket.js` into the real `.claude/workflows/` (`_tmp_refusal_populated.js`) and unlinks it in `finally`.
Under pytest-xdist the parametrized tests on different workers delete each other's copy:
`FileNotFoundError` on `test_refusal_writes_a_run_row_and_event_best_effort` (CI job 117902609735; locally at `-n 3`,
2 of 9 fail on 3 of 3 tries; 9/9 green serially). It also writes into a tracked repo directory during a test.

Until this lands, #659 runs this one file in its own serial step of the "Tools · f–z" job. That step is removed after
this fix is on main (testing's change, not this ticket's).

## Scope
- `_run_with_unported_list` takes pytest's `tmp_path` (thread it from each caller, or use a fixture) and writes the
  populated copy there. The node harness reads the script by path (`fs.readFileSync(process.argv[1])`) and runs it in
  `vm`, with no sibling `require`, so the copy does not need to sit next to the original. Keep `cwd=REPO_ROOT` for the
  subprocess, as now.
- Nothing is written under `.claude/workflows/` (or anywhere in the repo tree) by this test file.

## Out of Scope
- Removing #659's serial step from `test.yml` (testing's file).
- Any change to `.claude/workflows/implement-ticket.js` or the refusal mechanism itself.
- Auditing other tools tests for xdist safety (testing's audit in #659).

## Acceptance Criteria
1. `grep -n '_tmp_refusal_populated\|SCRIPT.parent /' tests/tools/test_implement_ticket_native_refusal.py` finds no
   write into `.claude/workflows/`; the temp copy lives under `tmp_path`.
2. `pytest tests/tools/test_implement_ticket_native_refusal.py -n 3 -p no:randomly` passes 9/9 on 3 consecutive runs
   (record the three outputs in Test Summary), and passes serially.
3. After the runs, `git status --porcelain .claude/workflows/` is empty.
4. Same test count as before (9); nothing skipped or deselected.

## Related Tickets
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (testing, PR #659): the xdist change that exposed this.
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (epic; this test came from #324).

## Related Docs
- `docs/guides/cross_session_messages.md` (finding received from testing-planner)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/tools/test_implement_ticket_native_refusal.py` (`_run_with_unported_list`, `_run`)
- `.claude/workflows/implement-ticket.js` (read only)

## Assumptions / Open Questions
- Routing: `route.py` names rpg-planner and agent-working-planner for `tests/tools/**`. The test covers the
  agent-working pipeline script, so agent-working takes it.
- `pytest-xdist` is available in the venv (it is in #659's requirements). If not, AC 2 can run on #659's branch.

## Implementation Notes
`_run_with_unported_list` takes `tmp_path` and writes `refusal_populated.js` there (no `try/finally` unlink needed); the three
callers take the `tmp_path` fixture. `_run` keeps `cwd=REPO_ROOT`. No change to `implement-ticket.js` or `test.yml`.

## Test Summary
pytest-xdist was not in the venv; installed locally (`pip install pytest-xdist`, 3.8.0), requirements files untouched.
`pytest tests/tools/test_implement_ticket_native_refusal.py -n 3 -p no:randomly -q`, three consecutive runs:
`9 passed in 1.56s`, `9 passed in 1.60s`, `9 passed in 1.62s`. Serial: `9 passed in 0.47s`. Count stays 9, none skipped.
AC 1: the grep finds nothing (rc 1). AC 3: `git status --porcelain .claude/workflows/` is empty after the runs.

## Files Changed
- `tests/tools/test_implement_ticket_native_refusal.py`

## Completion Summary
The native-refusal test no longer writes into `.claude/workflows/`; its temp copy lives under `tmp_path`, so xdist workers cannot delete each other's copy.
