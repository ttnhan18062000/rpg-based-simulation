---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260628-E-LONGRUN-REGRESSION
phase: done
date: 2026-06-28
tags: [epic, long-horizon, regression, testing, p3, deferred]
---

# TCK-20260628-E-LONGRUN-REGRESSION

## Title
Epic: Long-Horizon Regression Suite (5,000-tick automated behavioral regression)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
No automated 5,000-tick regression test exists. Behavioral regressions across
refactors go undetected. P1-A (rejection cascade backoff) is now complete, making
the 5,000-tick run feasible without unbounded memory growth. This epic implements
the suite.

**Gate condition met:** P1-A (TCK-20260627-P1A-REJECTION-BACKOFF) DONE 2026-06-27.

## Scope
- Implement an automated 5,000-tick regression test harness.
- Define behavioral metric thresholds (entity alive_avg, activity_rate,
  quest_active_count, economic pressure presence) from a baseline run.
- Assert that subsequent runs with the same seed stay within threshold bands.
- Wire into CI as an optional slow-path job (gated, not blocking fast PRs).

## Out of Scope
- Fixing any behavioral regressions found by the suite — those are separate tickets.
- Modifying the kernel, scheduler, or any domain logic.
- Running at tick counts beyond 5,000 in the first version.

## Acceptance Criteria
- [ ] A 5,000-tick regression run completes under 10 minutes on Hardware Class B.
- [ ] Key behavioral metrics are captured and compared against a stored baseline.
- [ ] A regression (metric deviation > threshold) causes the job to fail with a
      named diagnostic (which metric, how much drift).
- [ ] Baseline is stored as a versioned artifact (`tests/regression/baseline_5k.json`
      or equivalent).
- [ ] CI slow job runs this suite on PRs targeting `main`.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Gate ticket: TCK-20260627-P1A-REJECTION-BACKOFF (DONE)
- P2-M (TCK-20260627-P2M-CI-ARTIFACTS): CI artifact upload already wired — use it.

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §Long-Horizon Regression Suite
- `docs/audits/D06_longrun_health.md` — metric definitions and prior 1,000-tick baselines
- `docs/plans/audit_fix_plan.md` §P3-A

## Related Stored Artifacts
- N/A

## Related Code Areas
- `tests/regression/` (new directory)
- `src/lab/workflows.py` — `Workflow.run()` methods for metric capture
- `.github/workflows/test.yml` — CI integration

## Assumptions / Open Questions
- Should the baseline be committed to the repo or generated on first CI run and stored
  as a CI artifact? Recommendation: generate on first run, store as committed JSON
  with a `make regression-baseline` target to refresh.
- Threshold bands need to be defined empirically from a first run. Suggest ±10% on
  alive_avg and activity_rate, ±20% on quest_active_count.

## Implementation Notes
- Built `tests/regression/test_behavioral_5k.py` — `collect_behavioral_metrics()` runs
  5000 ticks, samples `alive_entities`, `total_gold`, `quest_status_counts` every 100
  ticks via `MetricsService.extract_metrics()`, then compares averages against the baseline.
- Adventure routing explicitly enabled (1.0) to exercise non-survival goal pipeline.
- Comparison uses relative drift thresholds: alive_avg ±10%, gold_avg ±20%, quest ±20%.
- `tools/generate_regression_baseline.py` writes `tests/regression/baseline_5k.json`.
- `make regression-baseline` target added to Makefile.
- CI: test marked `@pytest.mark.extra_slow` → picked up by existing slow job
  (gated on main/PR-to-main, runs after all fast tests).

## Test Summary
- `_check_metric()` unit cases: 4/4 pass (in-band pass, out-of-band fail, abs tolerance).
- Baseline generated: 173s / 5000 ticks = 2.9 min (AC: <10 min). ✓
- Harness verified: imports clean, test collects in 0.04s.
- Baseline metrics: alive_avg=11.34, gold_avg=457.32, quest_active_count=0.0.
- Key fix: `flags={"no_frame_pacing": True}` disables tick-rate sleep (without it: 45 min).

## Files Changed
- `tests/regression/__init__.py` (new)
- `tests/regression/test_behavioral_5k.py` (new)
- `tests/regression/baseline_5k.json` (new, committed baseline)
- `tools/generate_regression_baseline.py` (new)
- `Makefile` (+regression-baseline target)
- `.github/workflows/test.yml` (slow step renamed to note 5k regression)

## Completion Summary
Implemented 5,000-tick behavioral regression suite. `collect_behavioral_metrics()` runs
urban_political (seed=42) for 5000 ticks with adventure routing enabled, sampling
MetricsService every 100 ticks. Baseline committed at `tests/regression/baseline_5k.json`.
Test marked `extra_slow` routes into existing CI slow job. `make regression-baseline`
refreshes the baseline. Key discovery: `flags={"no_frame_pacing": True}` required to
avoid kernel tick-rate sleep (500ms/tick × 5000 = 45 min without it).
