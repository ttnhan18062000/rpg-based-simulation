---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-SIMQ-OBSERVE-CLEANUP-TEST-OWN-RUN-DIR
phase: done
date: 2026-10-19
tags: [testing, regression]
---

# TCK-20261019-SIMQ-OBSERVE-CLEANUP-TEST-OWN-RUN-DIR

## Title
The observe_world cleanup test asserts that only its own run dir is gone, not that all of data/runs is unchanged

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
This is a finding from testing-planner (2026-10-19, after #659), verified by agent-working-planner on origin/main 4f6a44901.

`tests/tools/test_simq_long_run_observation.py::test_observe_world_cleans_up_its_own_run_dir` lists the whole of
`data/runs/` before and after `slro.observe_world(...)` and asserts that the two sets are equal. Under pytest-xdist (Tools f–z,
since #659), another worker's run dir can appear in that window. One did in CI run 39218625597 on PR #663:
`run_1792396476_5169_2377_1ef255cd`.

The test means "observe_world removes the dir it created". It checks "nobody else wrote to `data/runs`". Until this
lands, testing runs this file in test.yml's serial step. Removing that step is testing's change, not this ticket's.

## Scope
- Change the test only. Capture the run dir that `observe_world` actually created. For example, wrap
  `entity_lifecycle_score._run_for_analysis` with a spy via `monkeypatch`, the way `test_engine_driven_only_once_per_world`
  already does, and record `run_dir` from its return value. Then assert that this one directory no longer exists after
  `observe_world` returns.
- Also assert that the captured `run_dir` is non-empty and starts with `data/runs/`, so the test cannot pass vacuously.

## Out of Scope
- `tools/simq_long_run_observation.py`, including its hard-coded `startswith("data/runs/")` cleanup guard. That guard is
  why a tmp_path runs root is NOT the chosen fix: cleanup would silently skip a run dir outside `data/runs/`. This file
  belongs to the simq/rpg side and is not changed here.
- Removing the serial step from `test.yml` (testing's file).
- Auditing other tests for whole-`data/runs` listings. You may list any you notice in Completion Summary, but don't fix them here.

## Acceptance Criteria
1. The test no longer compares listings of `data/runs/`. It asserts on the captured run dir only.
2. Regression check: temporarily comment out the `shutil.rmtree` in `observe_world` locally (don't commit this). The
   test must then fail. Record this in Test Summary.
3. `pytest tests/tools/test_simq_long_run_observation.py -n 3 -p no:randomly` passes on 3 consecutive runs, and it passes
   serially. Record the outputs in Test Summary.
4. The test count is unchanged, and nothing is skipped or deselected.

## Related Tickets
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (testing, PR #659): the xdist change that exposed this.
- TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH: the same class of xdist race in tests/tools.

## Related Docs
- `docs/guides/cross_session_messages.md` (finding received from testing-planner)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/tools/test_simq_long_run_observation.py` (`test_observe_world_cleans_up_its_own_run_dir`)
- `tools/simq_long_run_observation.py::observe_world` (read only)
- `tools/entity_lifecycle_score.py::_run_for_analysis` (read only; returns `(run_dir, health, final_entities)`)

## Assumptions / Open Questions
- Routing: `tests/tools/**` is agent-working's, and the fix is test-only, so agent-working takes all of it. rpg has
  no half unless `observe_world` itself needs to change, which it doesn't.

## Implementation Notes
The test wraps `entity_lifecycle_score._run_for_analysis` with a `monkeypatch` spy (as `test_engine_driven_only_once_per_world` does), captures the returned `run_dir`, and asserts it is non-empty, starts with `data/runs/`, and no longer exists. No whole-`data/runs` listing remains. `tools/simq_long_run_observation.py` unchanged.

## Test Summary
`pytest tests/tools/test_simq_long_run_observation.py -n 3 -p no:randomly -q`, three runs: `8 passed in 4.96s`, `8 passed in 4.58s`, `8 passed in 4.59s`. Serial: `8 passed in 5.85s`. Count unchanged (8), nothing skipped.
Regression check: with the `shutil.rmtree(run_dir)` on line 107 of `tools/simq_long_run_observation.py` temporarily replaced by `pass`, the test fails (1 failed); the file was restored with `git checkout` and not committed. The stray run dir that check created was removed by run id.

## Files Changed
- `tests/tools/test_simq_long_run_observation.py`

## Completion Summary
The cleanup test now checks only the run dir `observe_world` created, so another xdist worker's run dir can no longer fail it. testing can drop the serial step for this file (their change). Other tests listing whole `data/runs/` were not audited.
