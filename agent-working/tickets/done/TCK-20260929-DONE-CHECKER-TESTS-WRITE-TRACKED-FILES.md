---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES
phase: done
date: 2026-09-29
tags: [agent-monitoring, data-quality]
---

# TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES

## Title
Fast-tier tests rewrite docs/REGISTRY.yaml and working_log.csv, and consolidate live monitoring shards

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Reported by `test-architecture-implementer` on 2026-09-29. On a clean detached checkout of
origin/main (`1b05a5c9c`), `pytest tests/ -m "not slow and not extra_slow"` leaves tracked files
modified:
- `docs/REGISTRY.yaml` (~14 lines added)
- `tickets/working_log.csv`

In a worktree that holds other sessions' pending shards, the same run also **deleted** those
per-branch `*.tools.jsonl` shards and folded them into the canonical
`agent-monitoring/data/2026-W39/tools.jsonl` and `2026-W40/tools.jsonl`. The deleted shards were
`test-architecture-assessment.tools.jsonl` (W39 and W40) and
`working-log-consolidation-cross-checkout-fix.tools.jsonl`. CLAUDE.md requires `git add
agent-monitoring/` on every commit, so an ordinary test run followed by an ordinary commit ships
those deletions and consolidations. This is the same damage class as the known "running
done_checker_static.py in a review checkout folds pending shards" trap, but here a routine test
run triggers it.

The peer attributed it by hashing files before and after each test file:
- `tests/tools/test_done_checker_static.py` is a direct writer.
- `tests/tools/test_monitoring_consolidation.py` is only an **indirect** trigger. Its
  `test_done_checker_static_suite_still_passes` runs `pytest tests/tools/test_done_checker_static.py`
  in a subprocess with the real repo as cwd. Its other tests use `tmp_path` correctly.

Likely mechanism, from design-side reading (not yet confirmed per test):
- `done_checker_static.py`'s registry condition (~l.1168) defaults
  `registry_output=Path("docs/REGISTRY.yaml")`, a cwd-relative path, and calls `generate_registry()`,
  which writes unconditionally.
- Its working_log / pending-shard condition consolidates pending rows into the real
  `tickets/working_log.csv` and the real `agent-monitoring/data/` when called with default paths.

Any test that drives these conditions, or the CLI, without tmp paths writes to the live checkout.

**Confirmed/corrected during implementation:** the first bullet was exactly right — one test,
`test_cli_still_importable_and_callable_as_plain_functions`, called `run_finalize_selfcheck()`
with zero isolation, unconditionally regenerating the real `docs/REGISTRY.yaml` (reproduced,
fixed, and verified by temporarily reverting the fix — see Implementation Notes). The **second
bullet was wrong**: direct source read confirms `done_checker_static.py` never calls any
`monitoring_consolidation` function at all (`grep -n "consolidat"` finds only docstring prose, no
call sites) — `check_working_log_no_row_yet`/`check_working_log_exactly_one_row` and their
`_rows_for_ticket`/`_pending_rows_for_ticket_as_lists` helpers are all read-only. The real
shard-consolidation mechanism is `tools/agent-monitoring/generate_retro.py`'s `main()` (not
`generate()`), which unconditionally calls `consolidate_all()` with no `data_dir` override — an
entirely different file, not in this ticket's Related Code Areas. Filed as a sibling ticket:
`TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS`.

## Scope
1. Identify every test in `test_done_checker_static.py` that writes a tracked file or a live
   monitoring shard. Bisect with a git-status or hash check per test node, in a real checkout at
   origin/main and not under /tmp.
2. Fix each one to pass tmp paths or monkeypatch the default roots. Change the tests, not
   production behavior. `done_checker_static.py` must keep regenerating the real registry and
   consolidating when run for a real closure.
3. Decide on `test_done_checker_static_suite_still_passes` in `test_monitoring_consolidation.py`.
   It's redundant, since CI runs `test_done_checker_static.py` directly, and it doubles the side
   effects. Recommendation: delete it, and say so in Implementation Notes.
4. Add one regression test that runs the fixed done-checker tests and asserts that `git status
   --porcelain` over `docs/REGISTRY.yaml`, `tickets/working_log.csv` and `agent-monitoring/data/`
   is unchanged. Or use an equivalent autouse fixture scoped to these two test modules.

## Out of Scope
- A repo-wide tracked-file-mutation guard. That's the test-architecture Epic A's optional advisory,
  owned by the test-architecture sessions.
- `docs/brainstorm/mechanism_verification_view.md`, already fixed under
  `TCK-20260929-VERIFICATION-VIEW-TEST-TRACKED-WRITE` (test-architecture-implementer's batch).
- Changing `done_checker_static.py`'s own real-closure write behavior.

## Acceptance Criteria
1. On a clean checkout at the fix commit, `pytest tests/tools/test_done_checker_static.py
   tests/tools/test_monitoring_consolidation.py -q` leaves `git status --porcelain` empty.
2. With a planted `<branch>.tools.jsonl` pending shard present, the same run leaves the shard
   in place and leaves the canonical `tools.jsonl` byte-identical.
3. Every existing assertion still holds. No test is weakened to stop writing; each one writes to
   a tmp root instead.
4. The Scope 4 regression test exists and fails if the isolation is reverted. Verify this by
   temporarily reverting one fix.

## Related Tickets
- TCK-20260929-VERIFICATION-VIEW-TEST-TRACKED-WRITE (sibling fix, same defect class, other owner)
- TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS (filed from this ticket's own
  investigation — the real shard-consolidation mechanism this ticket's own "Likely mechanism"
  hypothesis got wrong; a different file, its own fix)
- TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS (done; the consolidation path
  involved here)
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE (done; added the CLI)
- TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION (done)

## Related Docs
- `docs/agent-monitoring/schema.md` (pending-shard model)

## Related Stored Artifacts
- None yet. The reporter's run logs (`a3_combined.log`, `base_combined.log`) are in
  test-architecture-implementer's session scratchpad; ask that session for them if needed.

## Related Code Areas
- `tests/tools/test_done_checker_static.py`
- `tests/tools/test_monitoring_consolidation.py` (~l.301)
- `tools/gate_checks/done_checker_static.py` (~l.1168 registry condition; working_log condition)
- `tools/working_log_writer.py`, `tools/agent-monitoring/monitoring_consolidation` module (read-only)

## Assumptions / Open Questions
- The per-test attribution in Scope 1 is still unconfirmed. The mechanism above is inferred from
  reading, not bisected.

## Implementation Notes
- Exactly one direct writer, found by scanning every `run_finalize_selfcheck(`/
  `run_static_precheck(`/`check_registry_entry_regenerated(` call site in the file for missing
  `monkeypatch.chdir`: `test_cli_still_importable_and_callable_as_plain_functions`. Fixed with the
  same `tmp_path`/`monkeypatch.chdir` pattern every sibling test in the file already uses.
- Verified the fix actually matters, not just plausible-looking: temporarily reverted the
  isolation, ran the test alone, and confirmed a real `docs/REGISTRY.yaml` diff appeared in the
  working tree — then restored both the fix and the file (`git checkout --`).
- `test_monitoring_consolidation.py`'s `test_done_checker_static_suite_still_passes` deleted per
  the ticket's own recommendation — redundant with CI's direct run of `test_done_checker_static.py`,
  and it doubled the (now-fixed) side effect via a cwd-inheriting subprocess.
- Scope 4's regression guard is a module-scoped `autouse` `git status --porcelain` fixture in both
  files (cheaper than re-running the whole suite in a subprocess, which is exactly the pattern just
  removed for `test_monitoring_consolidation.py`), verified to fail when the fix above is reverted.
- AC2's premise needed correcting, not just satisfying: `done_checker_static.py` never actually
  calls any `monitoring_consolidation` function (confirmed by direct grep — only docstring prose
  mentions "consolidat"), so the shard-consolidation symptom originally attributed to this file's
  tests doesn't come from here at all. Added an explicit isolated test proving a planted pending
  shard and canonical file both survive a real `run_finalize_selfcheck()` call byte-identical, and
  filed `TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS` for the real mechanism
  (`generate_retro.py`'s `main()`, a different file) rather than silently expanding this ticket's
  scope to cover it.

## Test Summary
`pytest tests/tools/test_done_checker_static.py tests/tools/test_monitoring_consolidation.py -q`
— 158 passed, `git status --porcelain -- docs/REGISTRY.yaml tickets/working_log.csv
agent-monitoring/data/` empty afterward (AC1). New AC2 test plants a pending shard + canonical
`tools.jsonl` in an isolated `tmp_path` and confirms both survive `run_finalize_selfcheck()`
byte-identical. Scope 4's guard fixture verified to fail when the isolation fix is reverted (AC4).

## Files Changed
- `tests/tools/test_done_checker_static.py` — isolated
  `test_cli_still_importable_and_callable_as_plain_functions`; added the module-scoped guard
  fixture; added the AC2 pending-shard/canonical-file test.
- `tests/tools/test_monitoring_consolidation.py` — deleted the redundant subprocess test; added
  the matching module-scoped guard fixture.
- `tickets/todos/TCK-20260930-GENERATE-RETRO-MAIN-CONSOLIDATES-REAL-SHARDS.md` — new sibling
  ticket for the real shard-consolidation mechanism this ticket's investigation found.

## Completion Summary
Fixed the one real unisolated test (`test_cli_still_importable_and_callable_as_plain_functions`)
that regenerated the live `docs/REGISTRY.yaml` on every run, deleted a redundant subprocess test
that doubled the effect, and added a cheap module-scoped regression guard to both files —
verified to actually catch the original bug by reverting the fix and confirming it fails. The
ticket's own "Likely mechanism" hypothesis about a second, shard-consolidating writer in this
file's own working_log condition was investigated and disproven (that check is read-only); the
real shard-consolidation mechanism was traced to a different file (`generate_retro.py`'s `main()`)
and filed as its own sibling ticket rather than folded in here.
