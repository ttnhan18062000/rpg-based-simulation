---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-SIMQ-LONG-RUN-OBSERVATION-TEST-SERIAL
phase: done
date: 2026-10-19
tags: [testing, regression]
---

# TCK-20261019-CI-SIMQ-LONG-RUN-OBSERVATION-TEST-SERIAL

## Title
test_observe_world_cleans_up_its_own_run_dir runs in the serial step of Tools f–z, because it reads the whole shared data/runs directory.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
PR #663's Tools f–z job failed (run 39218625597, job 117948366417): 3494 passed, 1 failed. `tests/tools/test_simq_long_run_observation.py::test_observe_world_cleans_up_its_own_run_dir` lists all of data/runs before and after `observe_world` and asserts equality. Under `-n auto` (TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS) another worker creates a run directory in that window, read as leftover scratch data (`run_1792396476_5169_2377_1ef255cd`). Same class as the store-lock and native-refusal collisions; the test is agent-working's.

## Scope
Add the file to the Tools f–z serial step, to the parallel step's `--ignore`s and to the base collect-only step; comment the cause and the owner fix; update the two static pins.

## Out of Scope
Changing the test itself (agent-working's file; the proper fix is to snapshot only the run id observe_world made).

## Acceptance Criteria
- [x] AC1: test.yml's serial step runs the file; the parallel step ignores it; the base collect step lists it; a comment names the cause and the owner fix.
- [x] AC2: `tests/static/test_ci_xdist_in_critical_path_jobs.py` and `tests/tools/test_ci_split_tools_jobs.py` pass with the new serial set.
- [x] AC3: the collected count for Tools f–z is unchanged: 3516 parallel + 17 serial = 3533 = the count with no ignores (local, `-m "not slow and not extra_slow"`).

## Related Tickets
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
- TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH

## Related Docs
none

## Related Stored Artifacts
none

## Related Code Areas
.github/workflows/test.yml (tools-f-z)

## Assumptions / Open Questions
The step is removed when the test snapshots only its own run id.

## Implementation Notes
Hand-orchestrated hotfix at testing-planner's dispatch.

## Test Summary
30 passed (the two static pin files); collect counts as in AC3.

## Files Changed
.github/workflows/test.yml, tests/static/test_ci_xdist_in_critical_path_jobs.py, tests/tools/test_ci_split_tools_jobs.py

## Completion Summary
The test runs alone, after the parallel step, in the same job; no job added.
