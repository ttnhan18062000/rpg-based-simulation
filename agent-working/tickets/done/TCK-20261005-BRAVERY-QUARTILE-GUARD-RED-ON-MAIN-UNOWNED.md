---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED
phase: done
date: 2026-10-05
tags: [combat, testing, investigation]
---

# TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED

## Title

`test_bravery_quartile_combat_rate_2x` has been failing on `main` with no ticket owning it — the
quartile size collapses to 1, so the guard's own precondition is unmet

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

`tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x` fails
on `main` and has no ticket. It is a guard created by the now-closed
`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`, so closed work's assertion is red and
unowned — it shows up as "a known base failure" in every session that runs the scenarios suite, which is
exactly how a real regression would be waved through.

**Three independent confirmations, on three different commits, by three sessions:**

| who | commit | result |
|---|---|---|
| `rpg-feature-planning` | `foundation-scope-and-retreat-ruling` (#328 branch) | failing; enumerated in #328's pre-existing set |
| `rpg-implementer` | clean checkout of `246ee09f7` (pre-#328) | fails identically |
| `rpg-implementer-2` | clean `origin/main` `1c59e01f4` (post-#328), throwaway worktree | fails identically |

So it is **not** caused by #328, and not caused by the `dungeon_crawl` 32→12 entity correction — it fails
on both sides of that change.

**Symptom:** `quartile size collapsed to 1`. That is the test's *precondition* failing, not its
hypothesis: with one entity per quartile there is no distribution left to compare, so a "2x combat rate
between bravery quartiles" assertion cannot be evaluated either way. Two candidate explanations, and the
ticket must distinguish them rather than pick one:

1. **The population it samples has shrunk** — a corpus/world content change reduced the entity count so
   quartiles no longer have members. Then the guard needs to sample a world that can populate quartiles,
   or state a minimum population as an explicit precondition with a clear skip.
2. **Differentiation genuinely stopped happening** — entities no longer spread across bravery values, so
   the quartiles degenerate. That is a real behavioural defect and the guard is correctly red.

One measured detail from #328's investigation, relevant to (1): this test **builds its own spec and never
constructs a `ScenarioSetupResolver`**, so it does not go through the production world-loading path. Its
population therefore may not match any world the simulation actually runs — establish what it samples
before concluding anything about differentiation.

## Scope

- Determine which of the two explanations above holds, with the entity count and bravery distribution
  measured, not inferred.
- If (1): give the guard a population it can actually quartile, or an explicit minimum-population
  precondition that **skips loudly** rather than failing obscurely. Do not lower the 2x threshold to go
  green — the threshold is the hypothesis.
- If (2): file the behavioural defect, and keep this guard red (or `xfail(strict=True)`) pointing at it.
- Either way: the test must stop being an un-owned "known base failure".

## Out of Scope

- `test_long_run_stability`, the other failure in that known-base pair (a conftest timeout, seed-4
  population guard) — related only by both being tolerated-red.
- Re-opening `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`. Its conclusion stands; this
  is about its guard's current state.
- Any change to the 2x coefficient itself. See
  `TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL` (open, in the `embedding-latent-cognition` folder).

## Acceptance Criteria

1. The entity count and bravery distribution the test actually samples are measured and recorded, with
   the world/spec named.
2. The explanation is stated as (1), (2) or something else, with evidence — not left ambiguous.
3. The test is either green for a stated reason, or `xfail(strict=True)` against a named filed defect.
   **"Known base failure" is not an acceptable end state.**
4. If a minimum-population precondition is added, an under-populated run **skips with a message naming
   the shortfall**, and a green run proves quartiles had members.
5. The 2x threshold is unchanged, or its change is justified separately and recorded in the parity
   ledger / `intentional_divergences.md` as appropriate.

## Related Tickets

- `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` — **done**; created this guard
- `TCK-20260822-BRAVERY-COEFFICIENT-CALIBRATION-TOOL` — open, owns the coefficient itself
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` — done (#328); enumerated this as pre-existing
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — done (#333); halted its Test gate on this
  failure and confirmed it at a clean pre-#328 commit
- `TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION` — P1; the "builds its own spec,
  never constructs a resolver" detail is the same measurement-path concern

## Related Docs

- `docs/mechanics/02_combat_laws.md` — bravery's role in engagement
- `docs/mechanics/01_entity_anatomy.md` — attribute distribution at spawn
- `docs/testing/test_taxonomy.md` — where an integration-tier population guard belongs
- `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` — combat/cognition is **Lane A**

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION/` — the
  pre-existing-failure enumeration

## Related Code Areas

- `tests/integration/scenarios/test_entity_differentiation.py` — the guard, and the spec it builds itself
- `src/entities/` — attribute spread at spawn
- `src/domains/combat_engagement/` — the engagement rate being compared

## Assumptions / Open Questions

- **UQ-1:** which world/spec does the test sample, and what was its entity count when the guard was
  written? Without the original number there is no way to say whether the population shrank or never
  sufficed. Check `TCK-20260810`'s artifacts for the figure it was calibrated against.
- **UQ-2:** has this ever passed in CI? If it was red from the day it landed, that reframes it from
  regression to a guard that never held — a different and more embarrassing finding worth stating.
- The three confirmations above were reported by the named sessions; the `246ee09f7` and `1c59e01f4`
  measurements were **not** re-taken by this ticket's author. Re-derive before relying on them.

## Implementation Notes

Full evidence in `investigation.md`. Summary against the acceptance criteria:

1. **AC1 (measured).** The test builds its own spec, `differentiation_arena`: 16 heroes + 8 monsters, one 45x45
   arena, never the production loader. Live heroes at tick 400 across seeds 1..24:
   `[7, 8, 8, 9, 9, 9, 10, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14, 14, 15, 15, 15]`.
2. **AC2 (explanation).** Neither candidate as posed. Differentiation has not stopped: the top/bottom bravery
   quartile combat-engage ratio is **2.40** over all 24 seeds and **2.40** over the 23 populated ones
   (asserted threshold 1.5; recorded at calibration 1.74). The population did not shrink by content: the spec is
   the test's own. What changed is survivor count: the calibration recorded `n_alive >= 8` at all 24 seeds and
   seed 9 now ends with 7, deterministically (three identical repeats), so `q_size` is 1. **The cause of the
   extra attrition is not established.** A candidate, the retired hero rebirth (divergence 2.63), is
   unverified because the same seed was not run before that change.
3. **Two failures were hiding as one.** Locally the test never reached that assertion: it is `extra_slow`
   (about 90 to 270 s here) without `resource_budget_large`, so conftest's default 60 s budget raised
   `TimeoutError` first. That is the local "known base failure". CI's slow job passes `--resource-budget large`.
4. **UQ-2 (ever passed in CI).** Not answerable from recent history, and the history is a finding: in the 40
   most recent `push` runs on `main` the `Slow regression` job's corpus-diversity step failed or was cancelled
   and the step that runs this guard (step 6) was `skipped` in all 35 runs that carry step data (5 carry none).
   This guard has not executed in CI in that window. Why step 5 fails is not this ticket's.
5. **The change.** Only `tests/integration/scenarios/test_entity_differentiation.py`: the per-seed hard
   `assert q_size >= 2` became an explicit precondition. A seed whose survivors cannot fill two-hero quartiles is
   excluded from the aggregate (selection by survivor count only, never by a rate); fewer than
   `MIN_QUALIFYING_SEEDS = 20` qualifying seeds **skips loudly**, naming the shortfall and the excluded
   `(seed, n_alive)` pairs. `resource_budget_large` added. The 1.5x assertion, the seed list and the spec are
   untouched, and `src/entities/` (the hold granted for this ticket) was **not** edited.
6. Sensitivity of the exclusion: ratio 2.403 with seed 9 included vs 2.399 without.

## Test Summary

- Before: `--resource-budget off` fails at seed 9 (`quartile size collapsed to 1 (n_alive=7)`); default budget
  fails with the conftest 60 s `TimeoutError`.
- After: `pytest tests/integration/scenarios/test_entity_differentiation.py -rsf` runs under its own large
  budget: 2 passed in 273 s (the guard evaluated the hypothesis on 23 seeds); the new fast skip-path test
  `test_bravery_quartile_skips_loudly_below_min_qualifying_seeds` passes in 0.25 s and proves the skip message
  names the shortfall and the excluded seeds. CI's 600 s large budget leaves room for the 273 s measured on a
  loaded machine.
- Environment: ruff/mypy/complexipy/ast-grep/prek are absent locally (tests are not ruff-checked in any case).
- Not covered: why survivors fell below the calibrated floor.

## Files Changed

`tests/integration/scenarios/test_entity_differentiation.py` only (plus the ticket and its artifacts).

## Completion Summary

The guard is no longer an unowned "known base failure". It now states its population precondition, excludes
the one seed that cannot form quartiles (seed 9: 7 live heroes), skips with the shortfall named if fewer than 20
seeds qualify, and runs under the budget it needs. On the 23 populated seeds the bravery hypothesis holds with
margin (2.40 vs the asserted 1.5), so this was a precondition and budget problem, not a differentiation
regression. Open: the cause of the survivor-count drop below the calibrated floor, and the fact that this guard
has not run in CI in the last 40 main pushes because the slow job's earlier corpus-diversity step fails.
