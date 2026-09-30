---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS
phase: open
date: 2026-09-30
tags: [agent-monitoring, data-quality]
---

# TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS

## Title
Three test_generate_retro.py tests calling generate_retro.main() directly trigger a real, unisolated consolidate_all() against the live checkout

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found incidentally while implementing `TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT`
(sibling ticket: `TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`, same defect class, other
file). Running this session's own full pytest sweep (which included the unmodified
`tests/tools/test_generate_retro.py`) twice folded 10 other sessions' pending per-branch
`agent-monitoring/data/2026-W{39,40}/*.jsonl` shards into the canonical week files and deleted the
originals — confirmed twice in the same session, restored both times via `git checkout --`
against the parent commit.

**Root cause, confirmed by direct source read, not the `test_done_checker_static.py` sibling
ticket's original hypothesis about `done_checker_static.py` itself** (that file was checked and
never calls any `monitoring_consolidation` function — grep for `consolidat` in
`tools/gate_checks/done_checker_static.py` finds only docstring prose, zero call sites):

`tools/agent-monitoring/generate_retro.py`'s `main()` function (not `generate()`, the plain
function most tests call) unconditionally calls `consolidate_all()` with no `data_dir` override
— `consolidate_all(data_dir: Path = DEFAULT_DATA_ROOT)`, where `DEFAULT_DATA_ROOT` resolves to the
real checkout's `agent-monitoring/data/`. Exactly 3 tests in `test_generate_retro.py` call
`generate_retro.main()` directly:
- `test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts`
- (the test immediately following it in the same file, also calling `main()` a second time for
  the hand-authored-notes-preservation scenario)
- `test_main_dedupes_before_computing_run_summary`

Each one monkeypatches `RUNS_FILE`/`EVENTS_FILE`/`RETRO_DIR` (and in one case
`_load_runs_and_events`/`_load_source`) to isolate the *report-generation* half of `main()`, but
none of them patches `consolidate_all` itself or its `DEFAULT_DATA_ROOT` default — so the
consolidation side effect runs for real, against the real checkout, every time, regardless of how
well the rest of the test is isolated.

## Scope
1. Fix each of the 3 tests to monkeypatch `consolidate_all` itself (e.g.
   `monkeypatch.setattr(generate_retro, "consolidate_all", lambda: None)`) or pass/patch an
   isolated `data_dir`, matching whichever approach the sibling ticket's own fix settles on for
   consistency between the two files. Change the tests, not `main()`'s real-closure behavior — a
   real `generate_retro.py` invocation (via `make agent-monitoring-retro` or the retro skill)
   must keep consolidating for real; that's the documented, intentional cadence
   (`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`).
2. Add a regression guard for this file, mirroring the sibling ticket's module-scoped
   `git status --porcelain` autouse fixture over `agent-monitoring/data/` (and
   `docs/REGISTRY.yaml`/`tickets/working_log.csv` if any other untouched test in this file also
   turns out to touch them — verify, don't assume only `main()`'s 3 callers are at risk).
3. Verify by temporarily reverting one of the 3 fixes and confirming the new guard fails.

## Out of Scope
- `tools/gate_checks/done_checker_static.py` / `tests/tools/test_done_checker_static.py` /
  `tests/tools/test_monitoring_consolidation.py` — that's
  `TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`'s own scope, already fixed there. Confirmed
  those files never call any consolidation function themselves.
- Changing `generate_retro.py`'s real consolidation cadence or `main()`'s own behavior.
- A repo-wide tracked-file-mutation guard (test-architecture Epic A's own optional advisory).

## Acceptance Criteria
1. On a clean checkout, `pytest tests/tools/test_generate_retro.py -q` leaves `git status
   --porcelain -- agent-monitoring/data/ docs/REGISTRY.yaml tickets/working_log.csv` empty.
2. All 3 `generate_retro.main()`-calling tests still pass with their original assertions intact —
   isolate the consolidation call, don't weaken the test.
3. A regression guard exists for this file and is verified to fail when one of the 3 fixes is
   temporarily reverted.

## Related Tickets
- TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES (sibling fix, same defect class, correctly
  scoped to a different file — this ticket exists because that one's own investigation disproved
  its "Likely mechanism" hypothesis and traced the real shard-consolidation cause here instead)
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (done; where this was found, twice, during
  an ordinary pre-commit test sweep)
- TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE (done; added the real
  `consolidate_all()` call this ticket's tests unintentionally trigger)

## Related Docs
- `.claude/handover/agent-working-design.md` ("Traps": the same symptom, previously documented
  without a root cause)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` (`main()`, the `consolidate_all()` call site)
- `tests/tools/test_generate_retro.py` (the 3 `main()`-calling tests)

## Assumptions / Open Questions
- Whether any other, not-yet-identified test in `test_generate_retro.py` also touches
  `agent-monitoring/data/`, `docs/REGISTRY.yaml`, or `tickets/working_log.csv` some other way is
  unconfirmed — the regression guard in Scope 2 should catch it if so, rather than assuming these
  3 are exhaustive from static reading alone.

## Implementation Notes
_(pending)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
