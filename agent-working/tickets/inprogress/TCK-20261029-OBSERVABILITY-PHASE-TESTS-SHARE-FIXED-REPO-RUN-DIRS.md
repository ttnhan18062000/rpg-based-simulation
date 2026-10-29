---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261029-OBSERVABILITY-PHASE-TESTS-SHARE-FIXED-REPO-RUN-DIRS
phase: open
date: 2026-10-29
tags: [observability]
---

# TCK-20261029-OBSERVABILITY-PHASE-TESTS-SHARE-FIXED-REPO-RUN-DIRS

## Title
Four observability integration tests write to fixed, cwd-relative directories under tests/. One errored on teardown in CI. Move them to tmp_path.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
On #784 at 04f07d31e, the Integration job errored on teardown of `tests/integration/observability/test_phase24_behavior_metric_artifacts.py::test_behavior_metric_window_artifact_written`. The run was 40867522436, job 123426102499, on xdist worker gw0. The test body had passed. The traceback ended:

```
shutil.rmtree(run_dir)
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/run_data_phase24_test'
```

lead-planner found it. Integration was green on main at 197f4c78b and 6d3f6235c, and #784 changes no observability code, so it is a probable flake.

The fixture does `os.path.exists(run_dir)` followed by `shutil.rmtree(run_dir)` on the fixed, cwd-relative path `tests/run_data_phase24_test`. The directory disappeared between the check and the delete. No other file on main names that path, so the remover is not identified. The candidates are a concurrent cleanup in another xdist worker, or a cwd change, and this ticket does not need to find out which.

The same anti-pattern, a fixed repo-relative directory with a check-then-rmtree teardown, is in three siblings:
- `tests/integration/observability/test_phase23_behavior_timeline_episode_artifacts.py:11` (`tests/run_data_phase23_test`)
- `tests/integration/observability/test_phase25_postrun_behavior_analysis.py:12` (`tests/run_data_phase25_test`)
- `tests/integration/observability/test_phase26_behavior_scorecard_artifacts.py:11` (`tests/run_data_phase26_test`)

A fourth, `test_event_recorder_live_publish.py:12`, makes its path per-pid. That is better, but it still writes into the repo.

## Scope
- Replace each fixed `run_dir` fixture in the four files above, plus `test_event_recorder_live_publish.py`, with pytest's `tmp_path`. Pass `str(tmp_path)` where the code under test needs a string. Drop the manual rmtree setup and teardown.
- Keep every assertion unchanged. This is test plumbing only.
- rpg-planner's conditions (2026-10-29, word for word in its relay):
  1. Make sure the code under test actually WRITES to tmp_path. The run dir must be passed in, not taken from a cwd-relative default inside src. If src hard-codes the location, STOP to rpg-planner: that would be a src change, out of hotfix scope.
  2. Record the remover hypothesis below, even though it's unconfirmed.
  3. Move live_publish's per-pid output to tmp_path too, so nothing writes into the repo tree.

## Out of Scope
- Any `src/` change.
- Finding the process that removed the directory, unless it turns out to be a `src/` or tool bug while you do the work. If so, report it; don't fix it here.
- Other test directories.

## Acceptance Criteria
1. No test under `tests/integration/observability/` writes to a fixed path under `tests/`. Check it with `git grep -n '"tests/run_data' tests/`, which must return nothing.
2. The five files pass under `pytest -n auto` and serially, and pass 3 times in a row with `-n 4` (`pytest -p no:randomly` is not needed).
3. Assertions are unchanged, and the diff shows only fixture and path plumbing.
4. After the full `-n auto` run, `git status` shows no new untracked directories under `tests/`.
5. Implementation Notes record the result of grepping `tests/` and `tools/` for `run_data` globs or rmtree on `tests/`. A remover found that way gets its own finding to rpg-planner-ubuntu, not a silent fix.

## Related Tickets
- #784 (where the error showed up; not part of that PR)

## Related Docs
- `docs/testing/observability_coverage.md` (Phases 22-26)

## Related Stored Artifacts
- none

## Related Code Areas
- `tests/integration/observability/test_phase23_behavior_timeline_episode_artifacts.py`
- `tests/integration/observability/test_phase24_behavior_metric_artifacts.py`
- `tests/integration/observability/test_phase25_postrun_behavior_analysis.py`
- `tests/integration/observability/test_phase26_behavior_scorecard_artifacts.py`
- `tests/integration/observability/test_event_recorder_live_publish.py`

## Assumptions / Open Questions
- Dispatch is under S4 (#715 6473439661), after rpg-planner OKs this plan. It doesn't change test expectations.
- It queues behind A (TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED) on the one implementer. Fold it into A's PR as a same-track test hotfix, before B (TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED).

- Remover hypothesis (unconfirmed): rpg-planner suggests either another fixture or test that cleans a `tests/run_data*` glob, or a data-run cleaner running at the same time from the repo root.
  - rpg-planner-ubuntu grepped `tests/ tools/ src/` on 197f4c78b for `run_data[*_]`, `glob(...run_data`, and `rmtree(...tests`. It found nothing outside the 5 files themselves and `tools/sessions/disk_headroom.py`, which only reports `run_data_bytes`.
  - The other observability `rmtree` calls target `tmp_path` or `data/runs/<id>`, not `tests/`.
  - So no static remover was found. The implementer re-checks this at its own head.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
