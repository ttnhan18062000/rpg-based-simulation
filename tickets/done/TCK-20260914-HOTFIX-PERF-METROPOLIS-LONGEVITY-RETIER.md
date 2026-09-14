---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260914-HOTFIX-PERF-METROPOLIS-LONGEVITY-RETIER
phase: done
date: 2026-09-14
tags: [performance, testing, benchmarking]
---

# TCK-20260914-HOTFIX-PERF-METROPOLIS-LONGEVITY-RETIER

## Title
`test_perf_metropolis_longevity` re-tiered to `extra_slow` + `resource_budget_large` — `main`'s
`Perf / cert / arena` CI job has failed on six consecutive merges since `ENABLE_COMBAT_ENGAGEMENT`
went live; bisected to a real, already-measured, already-accepted cost this test was never re-tiered
for, unlike its sibling `test_perf_metropolis_stress`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P0

## Request Summary
`main` has failed `Perf / cert / arena` on every merge since `#190`
(`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`, which turned `ENABLE_COMBAT_ENGAGEMENT` on by
default). PR #196 inherited the failure by merging `main`, which is what surfaced this.

Bisected via direct A/B measurement rather than assumption (two hypotheses tested and falsified
first: a candidate about `state.groups` retention, and a phase-cost diff between two specific
commits that turned out identical because both had the flag on):

- `test_perf_metropolis_stress` (1000 entities) was already re-tiered `extra_slow` +
  `resource_budget_large` when `#190` landed, with user sign-off, because enabling the flag pushed
  its wall-clock time over the "medium" 60s budget.
- `test_perf_metropolis_longevity` (500 entities, 5 warmup + 100 sample ticks) was **not**
  re-tiered at the same time — it only produced a soft `PerformanceThresholdWarning` locally at the
  time, not a hard failure, so it was left on the default "medium" (60s) budget.
- On CI's own weaker (2-core) runner, the same real cost that stayed under 60s locally now exceeds
  it, tripping `tests/conftest.py`'s own hard wall-clock `TimeoutError` — not the perf assertion
  itself (`assert_perf_threshold` defaults to `hard=False`; the perf gate has still never fired in
  either flag state for this test).

**Measured, flag ON vs OFF, same box, back to back** (`build_metropolis_state(entity_count=500)`,
60 ticks, `ENABLE_COMBAT_ENGAGEMENT` toggled via `FeatureFlagManager` override):

| | ON (default) | OFF | Δ |
|---|---|---|---|
| tick_ms mean | 469.84 | 164.60 | −305.24 (−65%) |
| `advancement` | 237.80 | 59.94 | −177.86 |
| `resolution_overhead` | 128.64 | 43.96 | −84.68 |
| `cooperation` | 63.64 | 41.93 | −21.71 |
| `combat_engagement` | 63.07 | 0.02 | −63.05 |
| `final_integrity` | 51.47 | 17.81 | −33.66 |

`combat_engagement`'s own phase cost is only ~21% of the total delta — the other ~79% is
`advancement`/`resolution_overhead`/`cooperation`/`final_integrity` doing more real work because
the world behaves differently with the flag on. This independently reproduces the ~82% downstream
split `#190`'s own profiling already found for the 1000-entity stress scenario — two separate
measurements agreeing.

**User's decision**: accept the cost (same call already made for the stress test) and re-tier this
test the same way, rather than reduce the cost right now. Explicit conditions, all applied below:
1. Justify the re-tier on what the test *is* (a genuine multi-tick, 500-entity benchmark that was
   mistakenly under-tiered), not solely on "our feature broke it."
2. Change the tier only — no assertion or threshold edited. The soft `avg_tps > 5.0` breach stays
   visible and stays breached (ON: ~2.1 TPS; OFF: ~6.1 TPS, would clear it).
3. State plainly, in the test docstring, the ticket, and the commit: a passing re-tiered test means
   the wall clock fits, not that performance is acceptable.
4. Record the measurement in `performance_m4_baseline_gate_a_epic.md`, including the explicit note
   that real savings must come from `advancement`/`resolution_overhead`/`cooperation` — not
   `combat_engagement`, which is only ~a fifth of the cost.
5. Note explicitly that this is the **second** test re-tiered for the same underlying cause — a
   pattern, not an isolated exception; a third should be read as evidence the cost needs reducing,
   not accommodating.

## Scope
- Add `@pytest.mark.extra_slow` and `@pytest.mark.resource_budget_large` to
  `tests/perf/test_perf_metropolis.py::test_perf_metropolis_longevity`.
- Update that test's own docstring with the justification, the measured numbers, and the explicit
  "does not mean performance is acceptable" sentence.
- Update `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`'s
  "Confirmed field evidence" section with the longevity-scenario measurement and the
  savings-must-come-from note.
- Confirm the re-tiered test is excluded from the CI `Perf / cert / arena` job's own
  `-m "not slow and not extra_slow"` filter, and passes when run directly under
  `--resource-budget large`.

## Out of Scope
- Reducing the actual cost (optimizing `advancement`/`resolution_overhead`/`cooperation`) — the
  user explicitly chose accommodation over reduction this time; that work belongs to the
  performance epic, not this hotfix.
- Any change to `assert_perf_threshold` calls, thresholds, or `hard=` defaults.
- The two other real regressions this batch falsified before finding this one (`state.groups`
  retention, the #190/#192 phase-identical A/B) — no code exists to revert; they were hypotheses,
  not defects.

## Acceptance Criteria
- [ ] `test_perf_metropolis_longevity` carries `@pytest.mark.extra_slow` +
      `@pytest.mark.resource_budget_large`, matching its sibling stress test.
- [ ] No assertion or threshold value changed.
- [ ] Docstring states the measured cost and that a pass means wall-clock fit, not acceptable
      performance.
- [ ] Performance epic doc records the measurement and the savings-target note.
- [ ] `pytest tests/perf/test_perf_metropolis.py -m "not slow and not extra_slow"` no longer
      selects this test.
- [ ] `pytest tests/perf/test_perf_metropolis.py::test_perf_metropolis_longevity
      --resource-budget large` passes.
- [ ] CI on `main` (post-merge) confirmed green on `Perf / cert / arena`.

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (#190 — the ticket that turned the flag on and
  re-tiered the sibling stress test, but not this one)
- `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT` (the already-filed diagnosis of why the perf gate
  itself never fires — this ticket doesn't touch that gap, only the wall-clock tier)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  (updated as part of this ticket)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tests/perf/test_perf_metropolis.py`
- `tests/conftest.py` (`resource_budget_large` marker → 600s wall-clock budget, unchanged, just
  applied)
- `.github/workflows/test.yml` (`perf-cert-arena` job's own `-m "not slow and not extra_slow"`
  filter, unchanged, just now excludes this test)

## Assumptions / Open Questions
None — this is a direct, user-approved tier change with the measurement already in hand.

## Implementation Notes
`test_perf_metropolis_longevity` re-tiered `@pytest.mark.extra_slow` + `@pytest.mark.resource_budget_large`,
matching `test_perf_metropolis_stress`'s own precedent exactly. Docstring updated with the
justification (a genuine 500-entity/105-tick benchmark mistakenly under the default medium tier),
the measured ON/OFF numbers, the explicit "does not mean performance is acceptable" sentence, and
the "second test re-tiered for the same cause" note. No assertion or threshold value touched.
`performance_m4_baseline_gate_a_epic.md`'s "Confirmed field evidence" section extended with a
second dated sub-section carrying the full phase table and the explicit
savings-must-come-from-advancement/resolution_overhead/cooperation-not-combat_engagement note.

## Test Summary
- `pytest tests/perf/test_perf_metropolis.py -m "not slow and not extra_slow" --collect-only`:
  confirms the re-tiered test is now deselected (1/3 collected, 2 deselected — both metropolis
  benchmarks).
- `pytest tests/perf/test_perf_metropolis.py::test_perf_metropolis_longevity --resource-budget
  large`: 1 passed in 52.74s. The soft `PerformanceThresholdWarning` (avg TPS 1.71 vs limit 5.0,
  BREACHED) is still visibly reported — confirmed the breach stays visible per explicit condition.
- Full scoped suite, `pytest tests/perf tests/certification tests/arena -m "not slow and not
  extra_slow"`: 119 passed, 1 skipped, 57 deselected — clean, matches CI's own `perf-cert-arena`
  job filter exactly.

## Files Changed
- `tests/perf/test_perf_metropolis.py` — added markers + docstring to `test_perf_metropolis_longevity`.
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md` —
  new "Second confirmed instance" sub-section under "Confirmed field evidence."

## Completion Summary
`main`'s `Perf / cert / arena` CI job had failed on six consecutive merges. Two hypotheses were
tested and falsified first (unbounded `state.groups` retention; a phase-cost diff between two
specific commits that turned out identical because both already had the flag on) before a direct
A/B toggle of `ENABLE_COMBAT_ENGAGEMENT` on the actual failing scenario isolated the real cause: a
real, already-measured, already-accepted-once cost (`#190`'s own combat-engagement rollout) that
this specific test was never re-tiered for, unlike its sibling. Re-tiered the same way, with the
measurement recorded in the performance epic and the explicit caveat that a pass here means wall-
clock fit, not acceptable performance — and an explicit flag that this is now a two-instance
pattern, not a one-off.
