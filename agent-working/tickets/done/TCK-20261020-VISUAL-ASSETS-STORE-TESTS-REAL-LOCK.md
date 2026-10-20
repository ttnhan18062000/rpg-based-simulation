---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK
phase: done
date: 2026-10-20
tags: [testing, determinism]
---

# TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK

## Title
visual_assets store tests take their write lock in tmp, never on the real `visual_assets/catalog/.store.lock`

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
GitHub issue #657 (testing-planner, u24, 2026-10-19). Several visual_assets tests run a writing store command (`cli.main` intake/review/build/release/export-runtime, or `store_write_lock` directly). They take `LOCK_EX|LOCK_NB` on the real lock file, `visual_assets/store/lock.py::lock_path()` = `config.CATALOG_ROOT / ".store.lock"`, because the `roots` fixture (`tests/visual_assets/store/unit/conftest.py`) patches only `QUARANTINE_ROOT` and `REVIEW_ROOT`. Two processes at once (pytest-xdist, or a real store command running locally) give the second one `GateError store_locked`: `cli.main` returns 2 and the test fails (`test_cli.py::test_the_clock_is_read_only_here` IndexError at :49, `test_intake_exit_codes` `assert 2 == 0` at :38). Serial runs are green. Until this lands on main, testing runs the affected files serially in a separate step of the same CI job, recorded against this ticket.

The owner chose to scope it this week (2026-10-20, via lead-planner). It is a test-fixture fix only.

## Scope
1. Re-derive the affected set at the dispatch base. Grep `tests/visual_assets/**` for in-process writing store calls (`cli.main([...])` with intake/review/build/release/export-runtime/adopt/adopt-set/revoke/gc/draft keep, `store_write_lock`, and helpers that call them) whose `config.CATALOG_ROOT` is the real catalog. The issue lists 12 files under `store/unit/` plus `test_review_cli.py` and `test_key_usage.py`. Record the re-derived list in Implementation Notes.
2. Point the lock into tmp for those tests through fixtures, and **only when `config.CATALOG_ROOT` is the real catalog root**: `monkeypatch.setattr(lock, "lock_path", ...)` returning a path under `tmp_path`. A test that already points `CATALOG_ROOT` at a tmp catalog keeps its lock at `<tmp catalog>/.store.lock`. `test_lock.py`, `test_deletion_log.py:106` and `test_kill_mid_publish.py` assert on that location and must stay unchanged. Place it in `tests/visual_assets/store/unit/conftest.py`, as an autouse fixture there, or in `roots` if every affected test uses `roots`. For the two top-level files, use a local fixture or a shared helper module.
3. Add a regression test that fails on today's main. Within the fixture, `lock.lock_path()` is never under the real catalog. The reproduction from the issue also passes: hold `flock` on the real `visual_assets/catalog/.store.lock` from another process, then run the affected tests and see them pass. A test that holds the real lock in a child process (as `kill_helper.py` does) is preferred over a manual run, if it stays light.
4. Reply on #657 with the ticket id (planner does this at dispatch) and, after merge, tell testing the serial step can go (via lead).

## Out of Scope
- `src/**` and `visual_assets/store/**` production code. `lock.py` is NOT changed: the lock design (ADR D24) is right, and only the tests are wrong.
- The real catalog. No file under `visual_assets/catalog/` changes, and nothing deletes or touches the real `.store.lock`.
- **`tests/visual_assets/conftest.py` and `tests/visual_assets/drawing/conftest.py`.** They are guarded files in `docs/assets/aseprite_local_proof.json`. Editing either would need the Aseprite local proof refresh, a heavy slot. If the fix truly needs one, stop and ask the planner first.
- The CI serial step itself (testing's), and xdist adoption for visual_assets.

## Acceptance Criteria
- AC1: no test under `tests/visual_assets/` takes the real `visual_assets/catalog/.store.lock`. The re-derived list is in Implementation Notes, and the regression test proves it for the in-process paths.
- AC2: while another process holds `flock` on the real lock, the affected files pass (the issue's reproduction, recorded with counts).
- AC3: tests that point `CATALOG_ROOT` at a tmp catalog still see the lock at `<tmp catalog>/.store.lock` (`test_lock.py`, `test_deletion_log.py`, `test_kill_mid_publish.py` unchanged and green).
- AC4: no change to `src/**`, `visual_assets/**` or the two guarded conftests; `git diff --stat` of the batch shows only `tests/visual_assets/**` plus ticket/monitoring/REGISTRY files.
- AC5: `tests/visual_assets` not-slow is green (heavy slot via the planner and lead), and the paths guard passes.

## Related Tickets
- TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG (added the lock, ADR D24)
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (testing's, where the collision was found)

## Related Docs
- docs/assets/store_contract.md ("Store lock, deletion log and recovery (`ADR D24`)")
- docs/assets/retention_and_rollback.md (store operations)
- docs/assets/aseprite_local_proof.json (the guarded-file list)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG/

## Related Code Areas
- visual_assets/store/lock.py (`lock_path`, `store_write_lock`; read only)
- tests/visual_assets/store/unit/conftest.py (`roots`)
- tests/visual_assets/store/kill_helper.py (holds the lock in a child process)
- tests/visual_assets/test_review_cli.py, tests/visual_assets/test_key_usage.py

## Assumptions / Open Questions
- Assumed: monkeypatching `lock.lock_path` reaches every in-process caller, because `store_write_lock` looks `lock_path` up in its module at call time. Verify this. If any caller imported `lock_path` by name, patch that site as well, and note it.
- Assumed: no test runs a writing store command in a subprocess against the real catalog. The subprocess in `test_key_usage.py` is `git status` only. If one exists, report it before choosing a fix, because a monkeypatch cannot reach it.

## Implementation Notes
- Re-derived the affected set EMPIRICALLY at the dispatch base: with the real `.store.lock` held by another process (flock, child process) and no fix, `tests/visual_assets/store/unit` + `test_review_cli.py` + `test_key_usage.py` gave 6 failures in 4 files (`test_animation_metadata.py` 1, `test_atlas.py` 1, `test_cli.py` 3, `test_runtime_slices.py` 1), all `store_locked`. The issue's list is wider (12 files under store/unit); the fix is an autouse fixture for the whole directory, so every in-process writer there is covered, failing today or not.
- `store/lock.py` is untouched. `store_write_lock` looks `lock_path` up in its own module at call time, so `monkeypatch.setattr(lock, "lock_path", ...)` reaches every caller (cli.main and the drawing server's `submit_candidate`, which uses `store_lock.store_write_lock`). No caller imports `lock_path` by name. No test runs a writing store command in a subprocess against the real catalog (the assumption held; the one subprocess in the new test is the lock holder).
- New `tests/visual_assets/store/lock_isolation.py::redirect_real_catalog_lock(tmp_path, monkeypatch)`: `lock_path()` answers `tmp_path/.store.lock` only while `config.CATALOG_ROOT == REAL_CATALOG_ROOT`, checked at call time (so test order against the `env` fixture does not matter). A tmp catalog keeps `<tmp catalog>/.store.lock`.
- Wired as an autouse fixture in `store/unit/conftest.py` and in `test_review_cli.py` and `test_key_usage.py` (the two top-level files; neither guarded conftest is edited).
- Regression test `store/unit/test_lock_isolation.py` (3 tests): the real-catalog lock lives under tmp; a tmp catalog keeps its own; a writing command passes while a child process holds flock on the real lock. Two of three fail without the conftest line.
- Reproduction: with an external process holding flock on the real lock, the affected files give 1313 passed (was 6 failed).

## Test Summary
- Baseline on main with the real lock held by another process: 6 failed in 4 files (`test_animation_metadata.py` 1, `test_atlas.py` 1, `test_cli.py` 3, `test_runtime_slices.py` 1), all `store_locked`.
- With the fix, same lock held: `store/unit` + `test_review_cli.py` + `test_key_usage.py` 1313 passed.
- `test_lock_isolation.py` 3 passed (also with the real lock held by an external process, the `busy` path); with `test_lock.py` 41 passed; `test_lock`, `test_deletion_log`, `test_kill_mid_publish` and the two top-level files 106 passed, unchanged. Two of the three new tests fail without the conftest line.
- `tests/visual_assets -m "not slow"` at c6b235841: 2558 passed, 0 failed, 0 skipped, 403.71 s. Paths guard 11 passed. `tests/unit/tools` + `tests/tools` at efc2da7c0: 6102 passed, 1 failed, 53 skipped, 1 xfailed (996.92 s). The failure was `test_profiling_toolkit.py::test_end_to_end_tiny_profile_with_py_spy` ("No sampled stack contained the measured-ticks frame", py-spy sampling under host I/O load). It is unrelated to this batch, and the file re-run alone passed 27/27.

## Files Changed
- tests/visual_assets/store/lock_isolation.py (new); store/unit/test_lock_isolation.py (new); store/unit/conftest.py; test_review_cli.py; test_key_usage.py; this ticket.

## Completion Summary
Store tests that run a writing command while `config.CATALOG_ROOT` is the real catalog now take their write lock under `tmp_path` (autouse fixture from `tests/visual_assets/store/lock_isolation.py`, wired in `store/unit/conftest.py`, `test_review_cli.py`, `test_key_usage.py`). Tests on a tmp catalog keep `<tmp catalog>/.store.lock`. Only test code changed; `lock.py`, `visual_assets/**`, the catalog and both guarded conftests are untouched. A regression test holds the real lock in a child process. No known gap. After merge, tell testing the serial CI step can go (via lead).
