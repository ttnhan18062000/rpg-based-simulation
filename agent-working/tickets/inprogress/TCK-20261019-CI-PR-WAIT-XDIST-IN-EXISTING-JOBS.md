---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS

## Title
The three critical-path test.yml jobs (Integration, Tools f–z, API/CLI/engine) run their tests in parallel with pytest-xdist inside the job, after an audit shows the tests are safe to parallelise. No jobs are added.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of TCK-20261019-CI-RUNTIME-EPIC. The median PR wall time is 9.5 min. It is set by Integration (8.4 min median, p90 9.5), Tools f–z (6.7 min) and API/CLI/engine (6.3 min), each a single pytest process on a 4-vCPU `ubuntu-latest` runner. The baseline is in the epic's investigation.md.

Splitting jobs is not an option: Tests already starts 21 jobs against the free plan's 20-concurrent-job limit, so more jobs would queue (lead-planner-u24, 2026-10-19). Parallelising inside a job costs no concurrency.

## Scope
1. **Shared-state audit first** (investigation.md, before any workflow change). For every test in the three jobs, find shared mutable state. At minimum this covers:
   - `data/runs/` and `reports/` (including `reports/release_proof/`);
   - `data/calibration/`;
   - fixed tmp paths, ports, env vars and `os.chdir`;
   - module-level caches and registries;
   - the determinism and replay tests (two runs compared within one process, golden files).
   Each finding is fixed, or the test is grouped onto one worker (`xdist_group` with `--dist loadgroup`), or it stays serial in a separate step of the same job. Nothing is skipped or deselected.
2. Add `pytest-xdist` to the dev dependencies (pinned in `uv.lock`). Run the three jobs with `-n auto --dist loadgroup` (or a measured fixed `-n`).
3. **Before touching Tools f–z, send agent-working-planner an fyi.** The tests under `tests/tools/` are mostly their code, and #647 (agent-working-implementer, open) changes how tools tests are isolated. If #647 is still open, rebase onto it once it lands, or do Integration and API first and Tools f–z after.
4. The JUnit XML, the job summary and the base-branch collect-only diff step keep working under xdist. Check that `ci_junit_summary.py` reads the merged XML.
5. Optional, only if it keeps the net job count at or below today's: merge two tiny lanes (each under 1 min, for example Simulation quality and Agent orchestration). Record the choice either way.

## Out of Scope
- New jobs, or splitting a job into several.
- Changing which tests run, or any marker or deselection.
- The slow-regression lane, the SimQ drift job, and other workflows.

## Acceptance Criteria
- [ ] AC1: investigation.md lists the shared-state audit per job, with each finding and how it was handled (fixed, grouped or serial).
- [ ] AC2: the collected-test count per job is identical before and after, from `--collect-only -q` counts quoted in the Test Summary. No test is skipped, xfailed or deselected by this change.
- [ ] AC3: each of the three jobs passes 3 consecutive CI runs on the PR. Use re-runs to show there is no order-dependent flake, and quote the run ids.
- [ ] AC4: the median wall time of the three jobs over those runs is reported against the baseline (8.4 / 6.7 / 6.3 min). Target: the slowest of them at or below 5 min. A shortfall is reported, not hidden.
- [ ] AC5: the job count in test.yml does not grow.
- [ ] AC6: agent-working-planner's fyi was sent before the Tools f–z change, with its reply or "no reply" recorded.
- [ ] AC7: **lead-planner-u24 reviews the PR by comment**, in addition to testing-planner, before the user merges. Record the comment link.

## Related Tickets
- TCK-20261019-CI-RUNTIME-EPIC (parent)
- TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT (the base-branch collection step)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/investigation.md (baseline)

## Related Code Areas
- .github/workflows/test.yml (jobs `integration`, `tools-f-z`, `api-cli-engine`)
- pyproject.toml, uv.lock
- tests/conftest.py (resource budget, run-dir creation)
- tools/ci_junit_summary.py

## Assumptions / Open Questions
- The runner is 4 vCPU (ubuntu-latest, public repo). `-n auto` is the starting point; if memory pressure shows, use a measured `-n`.
- The local resource budget in conftest (60 s/8 GB) applies per test and must still apply per worker.

- **agent-working-planner's scan of tests/tools, 2026-10-19 (input to the audit, not a substitute for it):**
  - There are no raw `os.chdir` calls and no `os.environ` writes; env changes go through monkeypatch or a subprocess env.
  - The fixed `/tmp` strings are never written to.
  - `test_disk_warning.py` uses cwd=tmp_path, so it is isolated. `test_generate_registry.py` only reads the real REGISTRY.
  - To look at: modules loaded via sys.path insertion plus module-level `_REPO_ROOT` / tools/agent-monitoring path constants. These are safe under process workers but matter for any in-process cache reset.
  - Rebase Tools f–z onto #647.

## Implementation Notes
Audit and decisions: agent-working/staging_artifacts/TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS/investigation.md. `pytest-xdist` added to the dev group; `-n auto --dist loadgroup` on Integration, Tools f–z and the API job's steps. One shared-state finding (the visual_assets store flock, issue #657): that set runs in a serial step of the API job, the parallel step `--ignore`s it, and both JUnit files are merged. The serial step is removed when #657's fix is on main. Pins updated: `tests/tools/test_ci_split_tools_jobs.py` (step names, path set); new `tests/static/test_ci_xdist_in_critical_path_jobs.py`. JUnit consumers (lead-planner-u24 item 6): the only reader of the merged file is `tools/ci_junit_summary.py`, which takes ONE path (`reports/junit/api-cli-engine.xml`, the merged file) from the Job summary step, and `ci_aseprite_skip_line.py`, which now reads the same merged file; nothing sums the parts plus the merged file. The upload glob `api-cli-engine*.xml` keeps uploading the parts, the serial XML and the merged file, as before. #657's asset ticket: no ticket yet (record the id when filed). Second serial step, found by CI: `tests/tools/test_implement_ticket_native_refusal.py` writes a fixed-name temp file into the real `.claude/workflows/`, so it runs in its own serial step of Tools f–z (agent-working's file; fix tracked as TCK-20261019-NATIVE-REFUSAL-TEST-TEMP-COPY-IN-TMP-PATH, which carries a 3x `-n 3` AC). AC3, AC4 and AC7 need CI runs and the lead-planner-u24 review, so the ticket stays open until then.

## Test Summary
**AC2, collect/pass counts on CI, same image** (serial main run 39201326909 vs this PR, run 39204651987 attempt 1): Tools f–z 3465 passed + 28 skipped + 1 xfailed = 3494 before; 3456 + 9 (serial step) passed + 28 skipped + 1 xfailed = 3494 after. Integration 1077 + 6 skipped = 1083 both. API job: api/cli/logging/engine/observability 230 both; visual_assets 2335 + 216 skipped = 2551 before, (1024 + 198) + (1311 + 18) = 1222 + 1329 = 2551 after. Nothing skipped, deselected or re-marked by the change.

**AC3, three consecutive green runs on head d9194b77f (run 39204651987, attempts 1, 2, 3):** all jobs green in all three. Job ids: attempt 1 Tools 117904747800, Integration 117904826978, API 117904827035; attempt 2 Tools 117906488047, Integration 117906571873, API 117906571962; attempt 3 Tools 117908211627, Integration 117908289968, API 117908289884. No 60 s TimeoutError in any run. (The earlier head 8ecd10d62, run 39202868037, had attempts 1-2 green and attempt 3 red on the native_refusal race below; that is why the serial step exists.)

**AC4, job minutes (attempt 1 / 2 / 3, median) vs baseline 6.7 / 8.4 / 6.3:** Tools f–z 3.62 / 4.95 / 4.35, median 4.35. Integration 5.68 / 5.98 / 6.58, median 5.98. API 3.20 / 5.07 / 5.28, median 5.07. **Target (slowest of the three <= 5 min): NOT MET.** Integration's median is 5.98 min. Named cause: one test, `test_moon_cave_region_records_zero_trauma_across_full_corpus_run`, takes 122.8 s (52% of the job's pytest time, from `--durations=15` on CI); routed to rpg-planner as a question (split, move to slow, or leave). Runner variance is also large: the same Integration code took 236 s of pytest time on head 8ecd10d62 and 322-365 s here. PR-level wall time (workflow start to end): 6.05 / 6.37 / 6.97 min, median 6.37 min, against the 9.5 min median baseline.
**API per step, serial (main runs, s) vs xdist (this PR, three runs):** api 90-140 vs 33-49; cli 41-42 vs 14-24; logging 1 vs 2; engine 2 vs 1-3; observability 10-11 vs 7-11; visual_assets 266-274 vs 68-133 parallel plus 41-64 serial. logging and engine differ by 1-2 s, which is noise, so they stay parallel (testing-planner ruling).

## Files Changed
(implementer)

## Completion Summary
(implementer)
