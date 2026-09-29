---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT
phase: open
date: 2026-09-12
tags: [simulation-quality, calibration, corpus, grade-thresholds]
---

# TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT

## Title
Multiple `test_corpus_diversity.py` NARRATIVE/COMBAT-narrative grade-stability tests drift
deterministically on unmodified `main` — including one re-drifting after its own most recent
2026-08-29 re-baseline

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while verifying `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own
fix caused no regressions in `tests/unit/worldassembly/test_corpus_diversity.py`. **Confirmed
pre-existing on unmodified `main` via `git stash`** (reverting the count-expansion changes and
re-running identically) — these failures are unrelated to that ticket, not caused by it.

Five real, deterministic (not timing-noise) grade/score assertions currently fail:
- `test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability`
- `test_frontier_extended_seed42_200t_narrative_grade_stability`
- `test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability`
- `test_frontier_living_world_seed123_200t_combat_narrative_grade_stability`
- `test_frontier_marches_seed42_200t_narrative_grade_stability` (also throws a
  `QueueDrainWorker` thread-leak teardown error in the same run — likely a separate, unrelated
  session-hygiene issue, not conflated with the grade drift here)

Sample evidence (identical across all 3 trials each run — a deterministic shift, not noise):
```
generated_frontier_3_42_seed123_200t -- NARRATIVE: mean_score=0.3600 across 3 trials outside
  tolerance of anchor_score=0.0 (abs_floor=0.05) -- per-trial values: [0.36, 0.36, 0.36]
frontier_extended_seed42_200t -- NARRATIVE: grade=A outside +/-1 band of anchor grade=C (all 3 trials)
frontier_extended_seed123_200t -- COMBAT: mean_score=0.8959 outside tolerance of anchor_score=0.32
  (abs_floor=0.2631)
frontier_living_world_seed123_200t -- NARRATIVE: mean_score=0.3600 outside tolerance of
  anchor_score=0.0 (abs_floor=0.05)
frontier_marches_seed42_200t -- NARRATIVE: grade=A outside +/-1 band of anchor grade=C (2 of 3 trials)
```

**Not a fresh finding for this file in general** — `docs/testing/regression_policy.md` §9 and
`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` (2026-08-29) already established the
methodology for this exact class of issue and re-baselined 3 tests then, **including
`frontier_extended_seed42_200t_narrative_grade_stability` itself** (per that ticket's own working-log
summary: "Re-baselined 3 of 13 named tests (highland_traverse population floor 60%->50%;
frontier_extended_seed42_200t_narrative and frontier_living_world_seed42_200t_social grade-stability
tolerances)"). **This is therefore a second, fresh drift on an anchor already re-baselined two weeks
ago** — not the same unresolved issue re-surfacing, a new one. The other four tests above were not
part of that batch's 13 named tests at all (new/different failures), or were part of the "explicitly
NOT re-baselined" 10 per that ticket's own Option A disposition and may simply not have been
re-checked since.

## Addendum — 2026-09-21 (do not re-baseline yet; parked alongside a related CI decision)

**1. This ticket stays parked under the same 2026-09-16 user decision that parked
`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`** (`main`'s own `Slow regression` job
has failed on every push run at step 5, `make simq-corpus-diversity-slow-isolated`, since that
date; deliberately deprioritised P2->P3, OPEN->BLOCKED, until the engine re-architecture lands).
The user has just confirmed the parking stays in effect. The two tickets describe the same CI step
from different angles: `TCK-20260822-...-EXIT-CODE-2` covers the job-level failure (the `make`
invocation's own exit code), this ticket covers the assertion content underneath it (which
specific `(world, pillar)` combos drift and why). Neither should be picked up independently of the
other while the underlying engine work is still pending.

**2. Do not re-baseline any of this ticket's own anchors until two things are true**: the
`TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` P0 is fixed, and the post-#222
combat state has settled. Reason, plainly: this ticket's own recorded "current" scores above (e.g.
`frontier_extended_seed123_200t -- COMBAT: mean_score=0.8959`) were measured BEFORE PR #222 removed
85-96% of real `resolve_multi_attack()` combat volume across the corpus worlds
(`TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION`'s own measurement: most of that
volume was phantom hostility from the pre-fix legacy `Faction` enum, not real catalog hostility).
Separately, `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` means every one of these
COMBAT numbers also reflects entities whose species-specific base stats have been silently wiped
toward generic defaults by any ordinary action taken before the measurement window — confirmed by
`TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT` to be destroying a real, formula-
exact determinant of combat outcomes, not a cosmetic drift. Anchoring against either state now
would lock in a simulation already known to be wrong on two independent, unfixed axes.

**3. Treat any anchor set at a narrative score of exactly 0.0 as suspect, not as ground truth.**
Several of this ticket's own failing tests are anchored at `anchor_score=0.0`
(`generated_frontier_3_42_seed123_200t`, `frontier_living_world_seed123_200t`), meaning the test
effectively asserts that NO narrative-scored event happens at all. The simulation now scores 0.36
on both. A failure against a 0.0 anchor may mean the simulation improved (narrative events that
previously never fired now do), not that it regressed. Whoever picks this ticket up has to decide
bug-versus-correct-behavior for each such test on its own evidence before touching any anchor — per
this repo's own standing rule against forcing a route just to lift or preserve a score
(`docs/testing/regression_policy.md` §9's already-established "do not assume a directionally-
plausible cause is proof of legitimacy" lesson, cited in this ticket's own Scope below, applies with
equal force in the opposite direction: a directionally-plausible IMPROVEMENT is not proof either).

**4. The `exit code 2` reported by CI is not itself diagnostic.** It is `make`'s own generic return
code for any failed recipe under `make simq-corpus-diversity-slow-isolated` — it does not by itself
distinguish a pytest run that was interrupted (timeout, crash, OOM) from one where a real assertion
failed. Whoever triages this needs the real pytest output, not just the exit code, to know which
case applies to a given run.

## Scope
- Per `docs/testing/regression_policy.md` §9's own established lesson: **do not assume a
  directionally-plausible cause (e.g. "improved population density") is proof of legitimacy** — first
  re-derive each failing `(world, pillar)` combo's classification against `tools/simq_ceiling.py`
  to rule out pre-existing structural noise (`tick_budget`/`watchdog_variance`/`flag_gated`) before
  treating any of them as a genuine re-baseline candidate.
- For each combo confirmed genuine: run the established 2-batches-combined-plus-verification-batch
  methodology (`test_corpus_diversity.py`'s own module docstring §5, and
  `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s own precedent) to derive a fresh,
  evidence-backed anchor/tolerance, not an invented one.
- Investigate whether a specific, identifiable behavior change (not just "more entities exist")
  actually drove each drift — e.g. did a specific NARRATIVE-scored event type's frequency change,
  and why — mirroring how prior tickets in this same lineage (`TCK-20260817-STANDARD-SIMQ-NARRATIVE-
  EVENT-EMISSION-REGRESSION-FRONTIER`, `TCK-20260824-TOWN-CENTER-POINTER-FIX`) root-caused their own
  drifts rather than treating "grades changed" as self-explanatory.
- Investigate `test_frontier_marches_seed42_200t_narrative_grade_stability`'s own `QueueDrainWorker`
  thread-leak teardown ERROR separately from its grade-drift FAILED result — confirm whether it's
  the same known session-teardown artifact `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-
  REFRESH` already disclosed ("Associated ERROR diagnosed to a session-teardown thread-leak
  artifact, not a floor issue") or a new instance.

## Out of Scope
- `TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE`'s own
  crash (`test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`) — a hard
  crash, not a grade/score drift; that test cannot even be measured for a legitimate NARRATIVE/SOCIAL
  drift until the crash itself is fixed, so it is explicitly excluded from this ticket's own list.
- The ~4 tests showing pure run-to-run pass/fail inconsistency on identical unmodified `main` code
  (`test_generated_frontier_3_42_extended_population_stability`,
  `test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_urban_political_seed42_1000t_social_grade_stability`,
  `tests/integration/entities/test_entity_construction_bridge.py::
  test_construction_is_deterministic`) — these already carry explicit, extensive
  wall-clock-timing/watchdog-variance documentation in their own docstrings (matching
  `tools/simq_ceiling.py`'s existing `tick_budget`/`watchdog_variance` classification), consistent
  with genuine session-load-dependent non-determinism rather than a code drift. Not re-investigated
  here; flagged as already covered by existing documented policy.
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own scope — confirmed via
  `git stash` to be unrelated to and not caused by that ticket's fix.

## Acceptance Criteria
- [ ] Each of the 5 failing `(world, pillar)` combos classified against `simq_ceiling.py`
      (genuine drift vs. pre-existing structural noise), not assumed.
- [ ] Genuine drifts re-baselined with fresh, evidence-derived anchors/tolerances per the
      established methodology, with the specific behavioral driver identified for at least the
      re-drifted `frontier_extended_seed42_200t_narrative` combo (why did an anchor set 2 weeks ago
      already drift again?).
- [ ] `test_frontier_marches_seed42_200t_narrative_grade_stability`'s teardown ERROR triaged
      separately from its grade-drift FAILED result.
- [ ] No regression in the rest of `tests/unit/worldassembly/test_corpus_diversity.py -m slow`.

## Related Tickets
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (the ticket during whose
  verification this was found; confirmed unrelated via `git stash`)
- `TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE`
  (found in the same verification pass; the crash there blocks measuring one of the 6 originally-
  observed failures, explicitly excluded from this ticket's own scope)
- `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` (most recent prior comprehensive
  triage of this file; re-baselined `frontier_extended_seed42_200t_narrative` two weeks before this
  ticket's own finding of a fresh drift on the same test)
- `TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH`,
  `TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER` (prior NARRATIVE-pillar
  drift investigations on this same corpus family, establishing the "confirm the real driver, don't
  just re-baseline" precedent this ticket should follow)
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (2026-09-21 addendum: the same CI step
  from the job-failure angle; both stay parked under the same 2026-09-16 user decision)
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`,
  `TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT` (2026-09-21 addendum: why
  re-baselining any COMBAT anchor here now would lock in a simulation already known to be wrong)

## Related Docs
- `docs/testing/regression_policy.md` §9 (the established triage/re-baseline methodology for this
  exact test file)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` (the 5 failing tests)
- `tools/simq_ceiling.py` (structural-noise classification)
- `src/simulation_quality/scorers/` (NARRATIVE/COMBAT pillar scoring, if the real driver traces
  there)

## Assumptions / Open Questions
- Whether these 5 drifts share one root behavioral cause or are 5 independent events is not
  assumed here — Scope's own first step (per-combo `simq_ceiling.py` classification) is what
  determines this, not this ticket's own framing.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
