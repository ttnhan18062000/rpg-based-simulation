---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260628-E-LONGRUN-REGRESSION
phase: open
date: 2026-06-28
tags: [epic, long-horizon, regression, testing, p3, deferred]
---

# TCK-20260628-E-LONGRUN-REGRESSION

## Title
Epic: Long-Horizon Regression Suite (5,000-tick automated behavioral regression)

## Status
OPEN

## Tier
epic

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

## Test Summary

## Files Changed

## Completion Summary
