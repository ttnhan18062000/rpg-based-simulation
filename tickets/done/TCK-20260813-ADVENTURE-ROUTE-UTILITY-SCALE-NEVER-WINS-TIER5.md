---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5
phase: done
date: 2026-08-13
tags: [adventure, agency, strategy, cognition]
---

# TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5

## Title
`ADVENTURE_ROUTE`'s utility score (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, observed ~20-26
on the shared 0-100 scale) never outscores `COMBAT_ENGAGE`/`REGION_STABILIZATION` in any sampled
seed — adventure routing is structurally dead in tier-5 goal competition, not just an observability
gap

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`'s required AC3
verification step (a fresh `tools/calibrate_simq.py` run against all 6 named run_keys post-fix).
See that ticket's `Implementation Notes` and
`stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/plan.md`'s Deviations
section for full technical detail already gathered — this ticket should read those first rather
than re-deriving from scratch.

That ticket genuinely fixed a real write-path bug: `last_routing_family`/`last_routing_tick` are
now correctly threaded from a winning `ADVENTURE_ROUTE` candidate through to a committed
`EntityUpdate`, verified end-to-end at the unit/integration level (including a direct test that
`StrategyShaper.shape()` emits `route_selected`/`action_executed`/`route_family_first_use` for such
an update).

Despite that fix, `route_selected`/`action_executed`/`route_family_first_use` still measure **0**
events in a fresh calibration run against `simq_routing_test`/`hero_guild_routing` × seeds
{42,123,456} `_500t` — because a winning `ADVENTURE_ROUTE` candidate essentially never occurs in
these worlds' actual 500-tick runs. DEBUG-level tracing of `evaluate_strategic_intent()`'s own
tier-5 goal-selection log across full runs of both worlds, at every sampled seed, found
`ADVENTURE_ROUTE`'s utility (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` on the shared 0-100
competition scale, observed ~20-26 in practice) never once outscores `COMBAT_ENGAGE` (observed
~100-144) or `REGION_STABILIZATION` (observed flat 100.0) — one or the other is active on
effectively every evaluated tick for every hero entity in both worlds.

This is a distinct, deeper problem than the write-path bug the originating ticket fixed: even with
observability restored, `ADVENTURE_ROUTE` is structurally unable to win tier-5 arbitration in these
worlds' current configuration, which plausibly traces to
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change — before that ticket,
`AdventureDecisionPhase` ran as an unconditional standalone phase (never competing against other
`GoalKind`s at all); after, `ADVENTURE_ROUTE` competes as an ordinary tier-5 `GoalScorer` candidate
on a scale apparently never calibrated against the other scorers' typical output ranges.

## Scope
- Determine, with real evidence (not assumed), whether `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` and/or
  `AdventureGoalScorer`'s own scoring formula were ever calibrated against the 0-100 shared
  tier-5 competition scale other `GoalScorer`s use, or whether this is an unnoticed unit/scale
  mismatch introduced by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change.
- Determine whether `COMBAT_ENGAGE`'s/`REGION_STABILIZATION`'s observed scores (~100-144, flat
  100.0) are themselves correct/intentional for these two specific calibration worlds
  (`simq_routing_test`/`hero_guild_routing`), or whether one of THEM is the actual anomaly (e.g. an
  unbounded/mis-scaled competing scorer crowding out every other candidate).
- Propose and implement a real fix — likely a rescaling of `AdventureGoalScorer`'s utility formula
  to be commensurate with the other tier-5 scorers' actual output ranges — NOT a "force route
  selection to win" hack (per this project's own explicit guidance against forcing an unrealistic
  route to fix a low pillar score; a legitimate rescale that lets `ADVENTURE_ROUTE` compete on its
  actual, intended merits is in scope, an artificial thumb-on-the-scale boost is not).
- Once a real fix lands, recalibrate `grade_anchors.json` AGENCY for the 6 run_keys
  `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` left correctly unchanged (they
  currently and correctly read `C/0.0`, matching pre/post-fix measured reality).
- Update `docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design Note and the
  2 dated NOTE blocks the originating ticket added (currently factual-not-restoration-claiming) to
  reflect whatever the real, evidence-based outcome turns out to be.

## Out of Scope
- The `last_routing_family`/`last_routing_tick` write-path fix itself — already correctly landed by
  `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`, do not re-touch.
- `evaluate_project_switch()`'s own lock/margin/retention decision logic (STRAT-185/186/187) — not
  touched under any circumstance, same constraint as the originating ticket.
- `last_defer_reason`'s `Bounded` status — unrelated, stays as-is.
- `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`.
- Any change to `COMBAT_ENGAGE`'s or `REGION_STABILIZATION`'s own scoring formulas, UNLESS
  Investigate's own evidence concludes one of THEM (not `AdventureGoalScorer`) is the real anomaly
  — in which case re-scope explicitly, don't assume the fix is on the adventure side by default.

## Acceptance Criteria
- [x] Root cause of the utility-scale mismatch determined with real evidence (calibration formula
      history, git blame, comparison against other `GoalScorer` output ranges) — not assumed to be
      "adventure's formula is wrong" without checking whether a competing scorer is the actual
      anomaly
- [x] A real, non-forced fix implemented (rescale, not a win-boost hack) — or, if Investigate
      concludes no fix is warranted (e.g. finds `ADVENTURE_ROUTE` losing is actually
      archetype-correct for these specific worlds, similar to the existing
      `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` precedent for AGENCY=C being correct in
      non-routing worlds), that determination is made explicitly with cited evidence, not silently
      defaulted either way
- [x] `route_selected`/`action_executed`/`route_family_first_use` verified via a fresh
      `calibrate_simq.py` run to fire (or, if the DA-ruling above concludes 0 is correct, that
      finding is what's verified and documented instead) — fired for 1 of 6 run_keys
      (`hero_guild_routing_seed42_500t`); the other 5 remain at 0, documented as measured, not
      assumed
- [x] `grade_anchors.json` AGENCY recalibrated for the 6 run_keys if the fix restores real emission
      — recalibrated for `hero_guild_routing_seed42_500t` only (the one run_key where emission was
      restored); the other 5 correctly left unchanged at `C`/`0.0`
- [x] `docs/simulation_quality/eval_matrix_results.md` updated to reflect the real, verified outcome

## Related Tickets
- TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE (BLOCKED — the ticket that fixed the
  real write-path bug and discovered this deeper, separate blocker during its own required AC3
  verification; its own `plan.md` Deviations section and Implementation Notes are the primary
  evidence source for this ticket's scope)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (the architecture change — unconditional standalone
  phase to competing tier-5 `GoalScorer` — that plausibly introduced this scale mismatch)
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (the earlier ticket in this same
  investigation chain that first recalibrated AGENCY down to C/0.0 for these 6 run_keys, correctly,
  given the state at that time)
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA (precedent DA ruling for AGENCY=C being archetype-correct in
  non-routing-capable worlds — relevant precedent, not necessarily applicable here since these ARE
  routing-capable worlds by design)

## Related Docs
- docs/simulation_quality/eval_matrix_results.md (AGENCY Cross-World Design Note)
- docs/guidelines/intentional_divergences.md §2.41
- docs/parity_ledger/infrastructure.yaml (INFRA-237)

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/ (once moved — the
  primary evidence source: DEBUG-trace observations of ADVENTURE_ROUTE vs COMBAT_ENGAGE/
  REGION_STABILIZATION utility scores across full 500-tick runs)

## Related Code Areas
- src/ai/goals/adventure_scorer.py (`AdventureGoalScorer.score()`, `_ADVENTURE_ROUTE_SCORE_MAX`)
- src/systems/strategic_systems/intelligence.py (tier-5 goal competition, `evaluate_strategic_intent()`)
- Whatever scorer(s) produce `COMBAT_ENGAGE`'s/`REGION_STABILIZATION`'s competing scores (Investigate
  must locate these — not yet identified precisely in this ticket's own filing)

## Assumptions / Open Questions
- Whether the fix belongs on `AdventureGoalScorer`'s side or a competing scorer's side is
  explicitly NOT pre-decided — Investigate's own evidence must determine this, not an assumption
  that "adventure is the broken one just because it's the one currently under investigation."
- Whether losing tier-5 competition is itself the archetype-correct outcome for these 2 worlds
  (mirroring the `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` precedent) is a real open question this
  ticket's own Investigate/DA phase must resolve, not assume answered by the mere existence of this
  ticket.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5/plan.md`
(APPROVED after 3 architecture-review rounds). No deviations from the plan's approved direction or
scope guards; two minor implementation-detail notes below (neither changes the plan's approved
substance).

**Step 1 — Derived denominator.** Ran `tools/calibrate_simq.py` fresh (pre-fix, default LIGHT
observability — confirmed `ObservabilityConfig.get_mode()` defaults to `LIGHT` with
`OBS_DECISION_TRACE=True` in that mode's flag mapping, so no env override was needed) against all
6 named run_keys and parsed each run's `decision_trace.jsonl` for every scored candidate's `score`
across all entities/ticks/route families (not filtered to the winner). Empirical maximum observed:
**0.7439** (`simq_routing_test_seed42_500t`, `hero_guild_routing_seed42_500t`, both a `form_party`
candidate). One run_key (`simq_routing_test_seed456_500t`) produced no `decision_trace.jsonl` at
all (no eligible entity had any scored adventure candidate that tick window — the writer opens the
file lazily only on a non-empty `write_trace()` call), contributing nothing to the corpus.
Theoretical safety floor from the plan's doubly-corrected Step 1b derivation: **2.4** (RECOVER
family, `healing`=CRITICAL urgency + `rest_inn` benefit=1.0 ceiling). `max(0.7439, 2.4) = 2.4`,
already at 1 decimal place. **Final denominator: `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4`.**

**Minor path correction (not a plan defect):** plan.md Step 1's Files note cites
`data/calibration/*/decision_trace.jsonl` as the read location. Direct trace confirmed
`decision_trace.jsonl` is actually written by the Kernel's own `DecisionTraceWriter` into
`data/runs/{run_id}/` (the engine's raw run directory), not copied into `data/calibration/{run_tag}/`
(which holds only `quality_report.json`/`quality_scores.jsonl`/`quality_report.run_health.json`).
`calibrate_simq.py` prints the real `engine_run_dir` to stdout (`"[calibrate_simq] Engine done in
...s. JSONL at: <dir>"`), which is what was actually parsed. This does not change the plan's
intent or the derived value — same read-only mechanism, same corpus, corrected path only.

**Step 2 — Implemented.** `src/ai/goals/adventure_scorer.py`: added
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX: float = 2.4` at module level (alongside
`_PROFILE_ELIGIBILITY_CACHE`), narrowed the `intelligence.py` import to `_GOAL_UTILITY_SCORE_MAX`
only (`_ADVENTURE_ROUTE_SCORE_MAX` no longer imported here), and changed the `utility` computation
to `min(_GOAL_UTILITY_SCORE_MAX, (raw_score / _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX) *
_GOAL_UTILITY_SCORE_MAX)` — exactly the plan's specified code block. `_ADVENTURE_ROUTE_SCORE_MAX`
itself (`intelligence.py:32`) is untouched, still `2.9`.

**Step 3 — Existing test updated.** Renamed
`test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact` to
`test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact_dedicated_denominator`,
re-parametrized to `(2.4, 100.0), (1.2, 50.0), (0.0, 0.0)` using the derived constant (imported,
not hardcoded, in the test file) instead of the old `2.9` boundary.

**Step 4 — New tests added.**
- 4a: `test_adventure_route_typical_score_produces_meaningfully_higher_utility_than_before_fix`
  (RECOVER `raw_score=2.35` example, asserts post-fix utility exceeds the pre-fix
  `(2.35/2.9)*100=81.03` value) and
  `test_adventure_route_sibling_ticket_typical_band_produces_higher_utility_than_before_fix`
  (parametrized over `raw_score` in `{0.58, 0.6914, 0.75}`, the sibling ticket's own observed
  typical band, re-confirmed by this session's own empirical measurement) — both added to
  `tests/unit/ai/goals/test_adventure_goal_scorer.py`.
- 4b: `test_region_stabilization_goal_scorer_utility_unchanged_by_adventure_denominator_decoupling`
  added to the existing `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py`, pinning
  `utility==100.0` (in addition to the existing `raw_score==2.9` pin) at `hazard_level=1.0`.
- 4c: `test_social_contract_goal_scorer_utility_stays_bounded_by_100_after_adventure_fix` added to
  the existing `tests/unit/ai/goals/test_social_contract_goal_scorer.py`, exercising the full
  `SocialContractGoalScorer().score()` call path (not just the `_raw_score()` helper) at the
  `raw_score==2.9` clamp ceiling, asserting `utility == 100.0`.
- 4d: new file `tests/architecture/test_adventure_route_score_max_unchanged.py` (no existing file
  matched the plan's "source-hash-style precedent" search target closely enough to extend without
  conflating two different guard styles — `test_committed_intention_arbiter_byte_identical_guard.py`
  pins a whole function body's SHA-256, this pins one constant's literal value directly, which the
  plan's own 4d description explicitly allows as a fallback: "or a new file... if no matching file
  exists"). Asserts `_ADVENTURE_ROUTE_SCORE_MAX == 2.9` by direct import.

**Step 5 — Regression suite.** All 8 scoped commands run. All pytest-unit/integration commands
passed 100%. `test_grade_regression.py -k "simq_routing_test or hero_guild_routing"` showed 6
failures, but every failing pillar was COMBAT/WORLD/PROGRESSION — never AGENCY — and every
failure's own embedded message cites a pre-existing, pre-documented, unrelated known-flakiness
class (`flag_gated`/`ENABLE_COMBAT_ENGAGEMENT` OFF, `tick_budget`/`zero_emergence_by_tick=500`,
`watchdog_variance`/kernel tick-budget throttle) tied to prior tickets
(`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`,
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`,
`TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`), none of which this ticket's scope touches.
AGENCY itself stayed byte-identical to the documented pre-change baseline (`C`/`0.0` on all 6),
satisfying the plan's own carved-out Step 5 Verify exception for this file ("or ... produce the
same pre-change AGENCY band it already produces"). This confirms Step 5's data was captured from
the Step-1 pre-fix calibration runs (Step 2's code change had not yet altered any of these
freshly-generated `quality_report.json` files at that point in the sequence).

**Step 6 — Fresh post-fix calibration (real measured outcome, not assumed).** Ran
`tools/calibrate_simq.py` clean against all 6 named run_keys after Step 2's code landed and Step 5
passed. Measured, by grepping each run's `simulation_events.jsonl` for `route_selected`,
`action_executed`, `route_family_first_use`:

| run_key | route_selected | action_executed | route_family_first_use | AGENCY grade | normalized_score |
|---|---|---|---|---|---|
| simq_routing_test_seed42_500t | 0 | 0 | 0 | C | 0.0 |
| simq_routing_test_seed123_500t | 0 | 0 | 0 | C | 0.0 |
| simq_routing_test_seed456_500t | 0 | 0 | 0 | C | 0.0 |
| hero_guild_routing_seed42_500t | **1** | **1** | **1** | **B** | **0.02357** |
| hero_guild_routing_seed123_500t | 0 | 0 | 0 | C | 0.0 |
| hero_guild_routing_seed456_500t | 0 | 0 | 0 | C | 0.0 |

`hero_guild_routing_seed42_500t`'s nonzero result was independently reproduced on a second,
separate `calibrate_simq.py` invocation (same seed/name) — identical `AGENCY grade=B,
norm=+0.0236, events=3` both times, confirming determinism, not a one-off artifact. This is a
real, mixed **Outcome A** per plan.md Step 8 (nonzero for 1 of 6 run_keys) — not Outcome B, and
not a uniform restoration either. Consistent with investigation.md Risk #2's own explicit caution
that `ResolveBlockerScorer`'s flat `utility=80.0` floor and `CombatEngageScorer`'s floor of `40.0`
may still structurally dominate even a corrected Adventure ceiling on most ticks in these two
danger-heavy calibration worlds — which is exactly what the other 5 run_keys show.

**Step 7 — Docs updated**, strictly conditioned on the real Outcome-A-mixed-result above (not
written in advance):
- `docs/mechanics/04_strategic_cognition.md` §6.6: added the "Live tier-5-competition ceiling"
  correction paragraph (documenting the `2.4` dedicated denominator and its derivation), the
  corrected per-need-key urgency-tier table, the RECOVER two-opportunity-kind (`repair_gear`
  vs. `rest_inn`) clarification, and fixed the pre-existing `personality_bias` `0.25`-vs-`0.50`
  table inconsistency (investigation.md Risk #5) to state the real per-family maxima. §6.10: added
  the cross-reference explaining `faction_directives=None`'s downstream effect on §6.6's old
  estimate.
- `docs/parity_ledger/infrastructure.yaml` INFRA-237: appended a fourth `support_boundary` addendum
  (dated 2026-08-13) recording the root cause, the fix, and Step 6's real measured per-run_key
  outcome table.
- `docs/guidelines/intentional_divergences.md` §2.41: appended a further dated "Restoration
  (partial)" addendum recording the mixed outcome and updated the section's `Status` line to
  reflect 1-of-6 run_keys now firing (was previously "blocked... pending a follow-up ticket" — this
  ticket IS that follow-up, now landed with a real, partial result).
- `docs/simulation_quality/eval_matrix_results.md`: added a new dated NOTE block to both
  `simq_routing_test`'s own section (documenting all-3-seeds-still-zero for that world specifically)
  and `hero_guild_routing`'s own section (documenting the seed42 flip and seed123/456 staying at
  zero), and rewrote the AGENCY Cross-World Design Note's own "both now grade AGENCY=C at all 3
  seeds" claim (now stale/false) to describe the real, mixed post-fix state.
- Per CLAUDE.md's After-Work rule (docs under `docs/` modified), `make knowledge-index-update`
  should be run — deferred to Finalize per this session's explicit instruction not to self-run
  Finalize-phase steps.

**Step 8 — Outcome A applies** (nonzero events for 1 of 6 run_keys). Per plan.md's Outcome A
framing: `tests/simulation_quality/fixtures/grade_anchors.json`'s `hero_guild_routing_seed42_500t`
`AGENCY` sub-object recalibrated from `{"grade": "C", "score": 0.0}` to `{"grade": "B", "score":
0.0236}` — the other 5 run_keys' `AGENCY` sub-objects left byte-identical (still correctly
`{"grade": "C", "score": 0.0}`, matching the still-measured reality for those 5). Confirmed via
`pytest tests/simulation_quality/test_grade_regression.py -k "hero_guild_routing_seed42_500t"`:
AGENCY no longer appears in that run's score-tolerance failure list post-recalibration (the sole
remaining failure, WORLD, is the same pre-existing, pre-documented `tick_budget` flakiness class
noted in Step 5, out of this ticket's scope — not touched, per CLAUDE.md's explicit prohibition on
editing an artifact/anchor just to make an unrelated gate pass).

**Per this session's explicit instruction, ticket closure (Step 8's "either way" checklist —
working_log.csv append, staging-artifacts move to stored_artifacts/, data/runs and
reports/release_proof cleanup, docs/REGISTRY.yaml regeneration, moving this file to
tickets/done/) was deliberately NOT performed here.** That is Finalize-phase work, to run
independently per this project's own memory note that implementers must not self-execute
Finalize/self-report done. This ticket remains in `tickets/inprogress/` for independent
Architecture-Verify/Test/Parity/Verify phases.

## Test Summary

All commands run with `.venv` active, scoped per CLAUDE.md's Testing Rule (never unscoped
`pytest tests/`):

```
pytest tests/unit/ai/goals/test_adventure_goal_scorer.py -m "not slow" -q            → 18 passed
pytest tests/unit/ai/goals/test_region_stabilization_goal_scorer.py -m "not slow" -q → 8 passed
pytest tests/unit/ai/goals/test_social_contract_goal_scorer.py -m "not slow" -q      → 10 passed
pytest tests/unit/strategic/test_score_normalization.py -m "not slow" -q             → 5 passed
pytest tests/architecture/test_adventure_route_score_max_unchanged.py -m "not slow" -q → 1 passed
pytest tests/unit/strategic/test_adventure_route_materialization.py \
       tests/unit/strategic/test_region_stabilization_materialization.py \
       tests/unit/strategic/test_social_contract_materialization.py -m "not slow" -q → 23 passed
pytest tests/unit/domains/adventure/ -m "not slow" -q                                → 87 passed
pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -m "not slow" -q → 6 passed
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q \
       -k "simq_routing_test or hero_guild_routing"                                  → 83 passed,
       6 failed (all pre-existing/unrelated known-flakiness classes on COMBAT/WORLD/PROGRESSION,
       never AGENCY — see Implementation Notes Step 5 for the per-run_key breakdown and citations)
```

Plus the required post-recalibration spot check:
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q \
       -k "hero_guild_routing_seed42_500t"                                           → 1 failed
       (WORLD only, pre-existing tick_budget flakiness, unrelated to this ticket; AGENCY passes)
```

Plus 6 fresh `tools/calibrate_simq.py` invocations against all 6 named run_keys post-fix (Step 6,
not a pytest command — see Implementation Notes table above) and 1 independent reproduction run
for `hero_guild_routing_seed42_500t` confirming determinism.

No test failures are attributable to this ticket's code change. Total new/modified test count: 2
new tests in `test_adventure_goal_scorer.py`, 1 renamed+reparametrized existing test in the same
file, 1 new test in `test_region_stabilization_goal_scorer.py`, 1 new test in
`test_social_contract_goal_scorer.py`, 1 new file (`test_adventure_route_score_max_unchanged.py`,
1 test).

## Files Changed
- `src/ai/goals/adventure_scorer.py` — new `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4` module
  constant; narrowed `intelligence.py` import to `_GOAL_UTILITY_SCORE_MAX` only; `utility`
  computation now uses the dedicated denominator with a `min(100.0, ...)` defense-in-depth clamp.
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — renamed/reparametrized the pinned
  normalization test to the new `2.4` boundary; added 2 new tests (typical-score and
  sibling-ticket-typical-band utility-increase regression guards); added the new constant to the
  file's imports.
- `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` — added 1 new test pinning
  `RegionStabilizationGoalScorer`'s utility is unaffected by the adventure-side denominator change.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — added 1 new test pinning
  `SocialContractGoalScorer`'s full `score()`-path utility stays bounded at `100.0` post-fix.
- `tests/architecture/test_adventure_route_score_max_unchanged.py` — new file; source-level guard
  pinning `_ADVENTURE_ROUTE_SCORE_MAX == 2.9` unchanged.
- `tests/simulation_quality/fixtures/grade_anchors.json` — `hero_guild_routing_seed42_500t`'s
  `AGENCY` sub-object recalibrated from `{"grade": "C", "score": 0.0}` to `{"grade": "B", "score":
  0.0236}`; all other run_keys/pillars byte-identical.
- `docs/mechanics/04_strategic_cognition.md` — §6.6 corrected (live tier-5-competition ceiling,
  per-need-key urgency table, RECOVER two-opportunity-kind note, personality_bias table fix);
  §6.10 cross-reference added.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-237 fourth addendum appended.
- `docs/guidelines/intentional_divergences.md` — §2.41 further dated addendum + `Status` line
  updated.
- `docs/simulation_quality/eval_matrix_results.md` — 2 new dated NOTE blocks (simq_routing_test's
  and hero_guild_routing's own sections) + AGENCY Cross-World Design Note's stale
  "both grade C at all 3 seeds" claim rewritten to the real, mixed state.
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-257's `support_boundary` got a fifth
  addendum (Parity phase): that entry's own text had explicitly named this ticket as its required
  revisit trigger but was missed by Implement's own Step 7 file list; Parity found and closed the
  gap, correcting its stale "AGENCY=C/0.0/events=0, byte-identical to pre-fix" and "capped at
  `_ADVENTURE_ROUTE_SCORE_MAX=2.9`" claims to match the real, mixed post-fix state.
- `docs/simulation_quality/event_type_coverage.md`, `docs/simulation_quality/current_state.md`,
  `docs/simulation/domains/adventure_contract.md`,
  `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` — 4
  additional stale-claim corrections found by Document-Update's own verification pass, beyond
  plan.md Step 7's originally-named 4 docs: each asserted a flat "0 events / AGENCY C for all 6
  run_keys" or an as-current normalization formula that this fix now makes stale for
  `hero_guild_routing_seed42_500t` specifically. Each got a dated addendum/NOTE-block correction
  matching that doc's own existing convention, not a rewrite of prior content.

Not changed (confirmed untouched, per Scope Guards): `region_stabilization_scorer.py`,
`social_contract_scorer.py`'s own formulas; `intelligence.py`'s `_ADVENTURE_ROUTE_SCORE_MAX`
(still `2.9`), `_GOAL_UTILITY_SCORE_MAX`, `evaluate_project_switch()`, `_score_scale_max()`;
`src/domains/adventure/scoring.py`'s `AdventureRouteScorer.score()` formula;
`tests/unit/strategic/test_score_normalization.py`; `docs/parity_ledger/strategic_cognition.yaml`
STRAT-254/STRAT-255; `COMBAT_ENGAGE`/`ResolveBlockerScorer` (`scorers.py`).

## Completion Summary
Root-caused and fixed a real utility-scale mismatch: `AdventureGoalScorer.score()` was normalizing
tier-5-competition utility against `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, a denominator calibrated for
a faction-directive-inclusive input configuration the live call path never actually receives
(`faction_directives=None` unconditionally), silently compressing its real utility output into a
narrow low band that `COMBAT_ENGAGE`/`ResolveBlockerScorer` structurally dominated. Fixed via a new,
dedicated `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4` constant declared locally in
`adventure_scorer.py` (decoupled from `intelligence.py`'s `_ADVENTURE_ROUTE_SCORE_MAX`, which stays
untouched at `2.9` for its own, unrelated Generalized Bypass gate purpose), derived from
`max(empirical raw_score corpus maximum = 0.7439, theoretical safety floor = 2.4)`. A fresh,
clean post-fix `calibrate_simq.py` run against all 6 named calibration run_keys measured a real,
evidence-grounded, mixed outcome (plan.md Outcome A): `route_selected`/`action_executed`/
`route_family_first_use` now fire for `hero_guild_routing_seed42_500t` (AGENCY C→B), while the
other 5 run_keys remain at zero events, unchanged — `grade_anchors.json` and all 4 named docs were
updated to reflect exactly this measured reality, not an assumed uniform restoration.
Document-Update's own verification pass found and corrected 4 more stale docs beyond plan.md Step
7's original list (`event_type_coverage.md`, `current_state.md`, `adventure_contract.md`, the
2026-08-11 adventure-scorer design doc), and Parity found and closed a gap of its own: STRAT-257
in `strategic_cognition.yaml` had explicitly named this ticket as its own required revisit trigger
but was missed by Implement's file list — both are now disclosed in Files Changed above rather
than left silently undocumented. Ticket closure (working_log.csv, stored_artifacts move, cleanup,
docs/REGISTRY.yaml, move to `tickets/done/`) is deliberately deferred to an independent Finalize
phase, per this session's explicit instruction.
