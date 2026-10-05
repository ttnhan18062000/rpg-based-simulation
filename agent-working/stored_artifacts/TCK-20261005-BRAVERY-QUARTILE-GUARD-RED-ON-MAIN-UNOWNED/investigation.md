---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED
artifact_type: investigation
tags: [combat, testing, investigation]
---

# Investigation: why `test_bravery_quartile_combat_rate_2x` is red

## Context scan

`search_docs` (bravery quartile, engagement inversion), then the guard, its stored ticket and conftest.

## What the test samples (AC1)

The test builds its **own** spec (`_build_differentiation_spec`, world `differentiation_arena`: 16 heroes and
8 monsters in one 45x45 arena plus a village region) and never goes through the production world loader, so
its population matches no corpus world. Seeds 1..24, 400 ticks, `ENABLE_COMBAT_ENGAGEMENT` and
`ENABLE_ADVENTURE_ROUTING` ON, non-audit mode, `CLASS_B` profile with `max_tick_budget_ms=200`.
The spawn population is fixed by the spec (24 entities, 16 heroes), so explanation (1) in the ticket, "the
sampled population shrank because content changed", does not apply: nothing the test spawns comes from world
content.

## Two different failures, one of them environmental

1. **Local default budget.** The test is `extra_slow` (about 90 s on this machine; its own docstring measured
   129 s) but had no `resource_budget_large` marker, so under conftest's default 60 s budget it dies with
   `TimeoutError` before evaluating anything. This is what a local session sees as the "known base failure".
   CI's slow job runs `pytest -m "slow or extra_slow" --resource-budget large`, so the budget does not apply
   there.
2. **The real failure (budget off or large).** `AssertionError: seed=9: quartile size collapsed to 1
   (n_alive=7)`. Seed 9 ends the 400 ticks with 7 of 16 heroes alive, `q_size = max(1, 7 // 4) = 1`. The
   test's per-seed population guard hard-fails before the hypothesis is evaluated: the symptom is the
   precondition, as the ticket said.

## Per-seed measurement (all 24 seeds, no assertions; `quartile_probe.py`, not in the repo)

Live heroes at tick 400, sorted: `[7, 8, 8, 9, 9, 9, 10, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14, 14,
15, 15, 15]`. Only seed 9 is below 8. Seed 9 is deterministic: three further runs gave identical
`n_alive=7` and identical quartile tick counts.

Aggregate over the 24 seeds, top vs bottom bravery quartile combat-engage rate: bottom 0.154, top 0.370, ratio
**2.40**. Restricted to the 23 seeds with `q_size >= 2`: bottom 0.160, top 0.383, ratio **2.40**. The test's
hypothesis (ratio >= 1.5) holds with wide margin and is stronger than the 1.74 recorded when it was
calibrated (bottom 0.4576, top 0.7972). Excluding seed 9 changes the ratio by less than 0.01.

## Explanation (AC2)

It is neither (1) nor (2) as posed. Differentiation has **not** stopped (explanation 2 is refuted: the
quartiles differ by 2.4x in the predicted direction). The population has not shrunk by content (explanation 1 is
refuted: the spec is the test's own). What changed is **survivor count**: the calibration recorded
`n_alive >= 8` at every one of the 24 seeds; today one seed ends with 7. The cause of the extra attrition is
**not established here**. A candidate is the retired hero rebirth (divergence 2.63, 2026-10-01: no role is
exempt from death), which would make dead heroes stay dead, but that is unverified: it would need the same seed
run before that change, which was not done.

## UQ-1 and UQ-2

- UQ-1: spec and original numbers are in `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s own
  docstring and plan: 16 heroes at spec, `n_alive >= 8` claimed at all 24 seeds at calibration.
- UQ-2, whether it ever passed in CI: **cannot be answered from recent history, and the recent history is itself
  a finding.** Of the 40 most recent `push` runs on `main` (2026-10-03 to 2026-10-05), 35 show the `Slow regression` job's
  step 5 (corpus diversity) failed or cancelled and step 6, "Slow tests (includes 5k behavioral regression)",
  the only step that runs this guard, `skipped`; the other 5 carry no step data for that job (absent, or still
  running when read). No run in the window shows step 6 executing. This guard has not executed in CI in that
  window at all. Whether it passed before 2026-10-03 was
  not checked.

## Not done

Why survivors fell from the calibrated floor; whether the 5k regression test has the same missing
`resource_budget_large` marker (it also times out locally; not this ticket's); why step 5 of the slow job fails.
