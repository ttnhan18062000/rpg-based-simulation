---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-CI-DROP-THE-THREE-SERIAL-XDIST-STEPS
phase: open
date: 2026-10-26
tags: [testing]
---

# TCK-20261026-CI-DROP-THE-THREE-SERIAL-XDIST-STEPS

## Title
The two serial steps in test.yml go now that their three owner fixes are on main: the visual_assets store-lock step in the API job, and the native-refusal / simq-observation step in Tools f–z

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (#659) put xdist in the existing jobs. It kept three test sets in serial steps, because each one collided with other xdist workers on shared state. All three owner fixes are now on main (checked 2026-10-26):
- visual_assets store lock: #692 (27f373a4e, TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK). The store tests take their lock under tmp_path. Issue #657 is still open only because nobody closed it (lead-planner-u24 finding, 2026-10-26).
- native refusal temp copy: TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH, in done/ on main.
- simq observe cleanup: TCK-20261019-SIMQ-OBSERVE-CLEANUP-TEST-OWN-RUN-DIR, in done/ on main.

The step comments in test.yml say to remove each step and its --ignore lines once the fix is on main.

## Scope
1. API job (`.github/workflows/test.yml`):
   - delete the "Run: tests/visual_assets (store lock, serial)" step;
   - delete the three `--ignore` lines (store, test_review_cli.py, test_key_usage.py) from "Run: tests/visual_assets";
   - delete the serial comment block;
   - drop `api-cli-engine-visual_assets-serial.xml` from the Merge JUnit XML step.
   The merged file name `api-cli-engine.xml` stays, because `ci_junit_summary.py` and `ci_aseprite_skip_line.py` read it.
2. Tools f–z job:
   - delete the "Run: tests/tools (f–z, workflow-file test, serial)" step and its comment block;
   - delete the two `--ignore` lines from the parallel step.
   Keep the parallel JUnit name and the merge step, which now has one input, so the uploaded `tools-f-z.xml` keeps its name. Alternatively, write `tools-f-z.xml` directly and drop the merge step. Pick one and say which in the ticket.
3. Update the pins: `tests/tools/test_ci_split_tools_jobs.py` (step names, path set) and `tests/static/test_ci_xdist_in_critical_path_jobs.py`. They must assert that the serial steps are GONE and that no `--ignore` for these files remains. Don't just delete the assertions.

## Out of Scope
- Closing issue #657 (asset's; tell lead-planner-u24 when this merges and the lead can close it).
- Any other xdist or CI timing change (CI-runtime epic children 2 and 3).

## Acceptance Criteria
- [x] AC1: before editing the workflow, run each formerly serial set 3 times locally under xdist (`-n 3`, or `-n auto` if the host allows), all green, and record the counts in Test Summary:
  - `tests/visual_assets/store tests/visual_assets/test_review_cli.py tests/visual_assets/test_key_usage.py`;
  - `tests/tools/test_implement_ticket_native_refusal.py`;
  - `tests/tools/test_simq_long_run_observation.py`.
  If any set fails, stop and report: that set's step stays.
- [x] AC2: the two steps and the five `--ignore` lines are gone, and the collected test count of each job is unchanged. Check with `pytest --collect-only -q` on the old and new commands and record both counts.
- [x] AC3: the pin tests assert the new shape and pass, along with `tests/static` and `tests/tools/test_ci_*`.
- [ ] AC4: the PR's CI is green, and the API and Tools f–z jobs show no store_locked, FileNotFoundError or leftover-run-dir failure.

## Related Tickets
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (parent change, #659)
- TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK (#692)
- TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH
- TCK-20261019-SIMQ-OBSERVE-CLEANUP-TEST-OWN-RUN-DIR
- TCK-20261019-CI-SIMQ-LONG-RUN-OBSERVATION-TEST-SERIAL

## Related Docs
- agent-working/stored_artifacts/TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS/investigation.md (if migrated; else the staging copy)

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/test.yml
- tests/tools/test_ci_split_tools_jobs.py
- tests/static/test_ci_xdist_in_critical_path_jobs.py

## Assumptions / Open Questions
- Heavy-job rule: these are unit-sized test sets, not simulation runs, but run them while no paired, gate or SimQ batch is on the host.

## Implementation Notes
- tools-f-z: chose to write `reports/junit/tools-f-z.xml` directly from the one parallel step and delete the Merge JUnit XML step (one input made the merge pointless). The upload glob `tools-f-z*.xml` and the Job summary path are unchanged.
- API job: the visual_assets step now runs the whole directory; the merged file `api-cli-engine.xml` keeps its name and now has one visual_assets input.
- Both base-branch collection steps drop the redundant explicit paths (they overlapped the directory and pytest collects a node once), so base and head commands stay identical.
- Pins rewritten, not dropped: `tests/static/test_ci_xdist_in_critical_path_jobs.py` now asserts every pytest step runs under xdist, no step named serial exists, no `--ignore=` for the five files returns, tools-f-z writes tools-f-z.xml with no merge step; `tests/tools/test_ci_split_tools_jobs.py` asserts one run step per tools job, the six per-directory API steps, and the coverage-parser path sets without the five paths.

## Test Summary
- AC1 (local, `-n 3`, main checkout .venv, 3 runs each, all green): visual_assets store + test_review_cli + test_key_usage 1332 passed x3 (36.4/36.6/37.5 s); test_implement_ticket_native_refusal.py 9 passed x3; test_simq_long_run_observation.py 8 passed x3.
- AC2 (`pytest --collect-only -q -m "not slow and not extra_slow"`): tools-f-z old command 3633/3661 (28 deselected), new 3633/3661; API job old 2797/2798 (1 deselected), new 2797/2798. Unchanged.
- AC3: tests/static + tests/tools/test_ci_* : 236 passed.
- AC4: pending the PR's CI run.

## Files Changed
- .github/workflows/test.yml
- tests/static/test_ci_xdist_in_critical_path_jobs.py
- tests/tools/test_ci_split_tools_jobs.py

## Completion Summary
