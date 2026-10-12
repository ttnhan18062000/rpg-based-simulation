---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP
phase: open
date: 2026-10-11
tags: [performance, benchmarking, regression]
---

# TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP

## Title
PERF-M2-T03b: Run the paired base/head tripwire as a report-only step in the perf-cert-arena CI job

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED (#496) shipped tools/perf/tripwire.py but held the `.github/workflows/test.yml` edit until testing-planner, who owns that file, agreed the CI selector. testing-planner said YES on issue #488 (2026-10-11), on six conditions. This ticket adds the CI step on those conditions. It also recalibrates the provisional §5 threshold on the CI runner, because the owner approved max(5 ms, base × 1.40) as provisional until it is measured there (2026-10-10).

## Scope
- Add a paired tripwire step to the `perf-cert-arena` job in `.github/workflows/test.yml`, on testing-planner's six conditions from #488:
  1. Set `timeout-minutes` on the job, at about 2x today's p95 for the job plus headroom. Take the p95 from recent runs and cite it in the PR. A hung base run must fail the job, not hold the runner.
  2. The job keeps its path filter (`changed-files` → `run_perf_cert_arena`). `tests/static/test_ci_narrow_path_filtered_jobs.py` still passes, with its intent unchanged.
  3. The step is report-only (OD-8). Its result goes to `$GITHUB_STEP_SUMMARY` and an uploaded artifact. A tripwire REGRESSION or INCONCLUSIVE never fails the job; only infrastructure errors do (checkout, a crash, the timeout). A comment next to the step says so.
  4. Check out the base with a second `actions/checkout` at `ref: ${{ github.event.pull_request.base.sha }}` and its own `path:`; head stays the default workspace. On events other than `pull_request`, skip the paired step and say why in the summary. Never guess `HEAD~1`.
  5. Run each side in a fresh process on the same runner, base then head (`tripwire.py run` already does this). The artifact records both SHAs and the runner's CPU model.
  6. The `test.yml` diff and any change to `tests/static/test_ci_*` shape tests go in this ticket's PR. testing-planner reviews that PR by comment before the user merges.
- Recalibrate on the CI runner: run `tripwire.py calibrate` there (a `workflow_dispatch` input or a one-off run on the PR are both fine), and record the measured A/A noise in the PR. If 1.40 does not hold on the runner, propose the new §5 value to the owner in the PR body. `docs/engine/performance_contract.md` is rpg-owned P1, so the owner approves the edit; do not apply it without that.

## Out of Scope
- Making any perf check blocking (OD-8)
- Any change under src/
- Moving the paired run to an off-hour lane. testing-planner allows this only if the doubled job becomes the critical path for perf PRs, and only after asking testing-planner first; it would go in `slow-regression` or its own scheduled workflow.
- Changing the tripwire algorithm itself (the T03 follow-up nits, such as alternating base/head on the retry, stay optional and separate)

## Acceptance Criteria
- [ ] On a `pull_request` run, `perf-cert-arena` runs the paired tripwire, writes the verdict table to the step summary, and uploads an artifact with base SHA, head SHA, runner CPU model and the per-scenario results
- [ ] A tripwire REGRESSION or INCONCLUSIVE leaves the job green. The PR shows this with a forced-regression dry run or a test, plus the step comment.
- [ ] On a non-PR event the paired step is skipped, and the summary says why
- [ ] The job has `timeout-minutes`, and the PR cites the p95 it was sized from
- [ ] `tests/static/test_ci_narrow_path_filtered_jobs.py` and the other `tests/static/test_ci_*` tests pass
- [ ] The CI-runner A/A noise measurement is recorded in the PR. Either 1.40 is confirmed, or a new §5 value is proposed to the owner.
- [ ] testing-planner has reviewed the PR by comment

## Related Tickets
- TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED (done, #496)
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Related Docs
- docs/engine/performance_contract.md §3.3, §5 (provisional threshold), §5.2
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md ("Delivery plan", OD-2, OD-8)
- Issue #488 (testing-planner's conditions)

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml (`perf-cert-arena` job; owned by testing-planner)
- tools/perf/tripwire.py (`run`, `calibrate`)
- tests/static/test_ci_narrow_path_filtered_jobs.py

## Assumptions / Open Questions
- Route `.github/workflows/test.yml` with `python3 -m tools.sessions.route .github/workflows/test.yml --from perf` before editing. testing-planner granted the edit for this ticket on #488.
- If the base side cannot run tripwire.py because the base predates T03 (#496), the step reports SKIPPED for that reason. That can only happen to a PR branched before #496 merged.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
