---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT
phase: done
date: 2026-08-13
tags: [simulation-quality, calibration, corpus, agency, cognition, adventure]
---

# TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT

## Title
AGENCY has drifted to 0/C on all 4 `ENABLE_ADVENTURE_ROUTING=ON` COGNITION-anchor items, plus a
milder COGNITION+AGENCY score-tolerance drift on the un-named `seed123` variants — disclosed but
explicitly out of scope by `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`,
and the two stale `_1000t` SLOW-tier COGNITION guard tests sharing the same root-cause family

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While implementing `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` (a
COGNITION-only recalibration for 4 named `ENABLE_ADVENTURE_ROUTING=ON` FAST-tier anchors plus
`lifecycle_full_coverage_world_seed42_200t`'s 8-pillar drift), that ticket's own mandatory
Implement-time fresh re-verification (`tools/calibrate_simq.py`'s real internals, 2 independent
trials per item, run 2026-08-13) surfaced findings beyond its named scope that it explicitly did
not fix, per its own Decision 2 and Scope Guards:

**(1) AGENCY drift, confirmed broader than originally disclosed.** Investigation for that ticket
had flagged AGENCY drifting from `A/0.918` to `0 events/0.0/C` on exactly one run_key
(`simq_routing_test_seed42_500t`), plausibly caused by
`docs/guidelines/intentional_divergences.md` §2.41 "Adventure-Route Defer-Reason Observability
Gap" (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` deleting `AdventureDecisionPhase` without
porting `last_defer_reason`/`defer_with_reason` emission). Fresh re-verification during
Implement (2 independent trials each, bit-identical) confirms the SAME `0 events/0.0/C` AGENCY
outcome on **all 4** of that ticket's named COGNITION-anchor run_keys, not just one:
- `simq_routing_test_seed42_500t` AGENCY: anchor A/0.918 → actual 0/0.0/C (band-crossing failure)
- `simq_routing_test_seed456_500t` AGENCY: anchor A/0.6415 → actual 0/0.0/C (band-crossing failure)
- `hero_guild_routing_seed42_500t` AGENCY: anchor A/0.9777 → actual 0/0.0/C (band-crossing failure)
- `hero_guild_routing_seed456_500t` AGENCY: anchor A/0.6727 → actual 0/0.0/C (band-crossing
  failure; ECONOMY and PROGRESSION also drifted beyond score tolerance on this run_key, both
  score-tolerance-only, not band-crossing — see raw pytest output cited in Related Stored
  Artifacts)

**(2) A milder, previously-undisclosed COGNITION+AGENCY score-tolerance drift on the un-named
`seed123` variants of the same two worlds** (neither is one of the 4 items named by the
originating ticket, so its own scope never covered them):
- `simq_routing_test_seed123_500t`: COGNITION actual_score=0.04 vs anchor 0.5295 (score-tolerance
  failure, NOT a band crossing — grade stays in-band); AGENCY actual_score=0.168 vs anchor 0.6415
  (same, score-tolerance only)
- `hero_guild_routing_seed123_500t`: COGNITION actual_score=0.0467 vs anchor 0.5295 (score-tolerance
  only); AGENCY actual_score=0.1963 vs anchor 0.6415 (score-tolerance only)

Note `tests/simulation_quality/fixtures/score_ceilings.json` already carries a
`simq_routing_test_seed123_500t`/PROGRESSION `watchdog_variance` entry (from
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) whose own reason text states COGNITION
was "stable at 0.5295/52 events across both re-runs" for this run_key at the time — i.e. this is a
**new** drift since that entry was written, not a re-confirmation of already-known variance.

**(3) Two stale, currently-failing SLOW-tier COGNITION guard tests sharing Finding 1's exact root
cause** (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, bisected to commit `3d992dd0`) for
the `_1000t` variant of the same two worlds:
`tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability`
(line ~600) and `::test_hero_guild_routing_seed42_1000t_cognition_grade_stability` (line ~684).
Both still carry the old 3-trial tolerance-guard shape and a stale F6/watchdog-variance-framed
docstring, and are mechanically excluded from `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-
LIFECYCLE-ANCHOR-GAP`'s own AC5 gate (`-m "not slow"` never runs `@pytest.mark.slow` tests).

None of (1)/(2)/(3) were fixed by the originating ticket — its own Decision 2 and Scope Guards
explicitly ruled AGENCY-fixing and the `_1000t` guards out of scope (different pillar / different
root-cause ticket than its own Finding 1), directing this follow-up instead of silently absorbing
or silently leaving them untracked.

## Scope
1. Determine the precise root cause of the AGENCY drift on all 4 `simq_routing_test_seed{42,456}
   _500t` / `hero_guild_routing_seed{42,456}_500t` run_keys — confirm or rule out
   `docs/guidelines/intentional_divergences.md` §2.41's `defer_with_reason` observability gap as
   the mechanism (not yet verified beyond a plausibility note), and determine why it manifests as
   a full `0/C` band-crossing on these 4 items but only a partial score-tolerance drift on the
   `seed123` variants.
2. Recalibrate `grade_anchors.json`'s AGENCY field for the 4 confirmed-drifted run_keys (and
   COGNITION/AGENCY for the 2 `seed123` variants, if confirmed same cause) following the
   established point-edit methodology, once root cause is confirmed.
3. Update `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
   `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` to the deterministic
   bit-identical shape (matching how
   `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` converted the sibling
   `_500t` guard), once their own root cause is confirmed via a fresh multi-trial repro (not
   assumed identical just because the 500t sibling was).

## Out of Scope
- Any further work on `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`'s
  own named 4 COGNITION items or the `lifecycle_full_coverage_world_seed42_200t` anchor — already
  closed by that ticket.
- The pre-existing, unrelated `[known tick_budget: ...]` score-tolerance failures across the wider
  FAST_ANCHOR_KEYS corpus (computed deterministically from `detection_params.yaml` time_gates vs.
  `corpus_registry.yaml` tick counts, `tools/simq_ceiling.py`) — accepted, already-documented
  noise per established precedent, not this ticket's concern.
- `src/domains/adventure/`, `src/systems/strategic_systems/intelligence.py`, or any other
  production strategic-cognition code — Investigate first; only Plan/Implement touches source if a
  real code gap (not just a stale anchor) is confirmed.

## Acceptance Criteria
- [x] Root cause of the AGENCY drift confirmed (or ruled out) as §2.41's `defer_with_reason` gap,
      via direct evidence (event-extractor/shaper trace), not assumed — confirmed BROADER than
      §2.41 previously disclosed: the deleted `AdventureDecisionPhase.apply()` was the sole writer
      of BOTH `last_defer_reason` (originally documented) AND `last_routing_family` (newly
      disclosed, feeding 3 of AGENCY's 4 event types). §2.41 broadened accordingly (Step 5).
- [x] `grade_anchors.json` AGENCY (and COGNITION/AGENCY for the `seed123` variants, if in scope
      per Investigate's findings) recalibrated to confirmed live values — all 6 named run_keys
      recalibrated to `{"grade": "C", "score": 0.0}`, confirmed via 2 independent fresh
      Implement-time trials each (bit-identical), matching investigation.md's own snapshot exactly.
- [x] `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
      `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` re-verified fresh and
      updated to match their confirmed current behavior (deterministic bit-identical shape if
      confirmed no-longer-variable, matching the `_500t` sibling's precedent) — converted to the
      `_500t` sibling's idle+induced-load tolerance-guard (2b) shape; fresh induced-load trial
      (2x core oversubscription, `_busy_loop` mechanism) found no residual at this tick count for
      either scenario, but 2b was kept as the safer default per Decision 3. Both isolated
      invocations pass.
- [x] `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` shows 0
      unexplained failures for the 6 run_keys named in this ticket's Request Summary — confirmed:
      AGENCY/COGNITION failures eliminated on all 6; remaining failures on other pillars are
      pre-existing, already-documented corpus noise (watchdog_variance/flag_gated/tick_budget
      ceilings) unrelated to this ticket, EXCEPT `hero_guild_routing_seed456_500t`'s
      ECONOMY/PROGRESSION and a newly-found `simq_routing_test_seed456_500t` PROGRESSION drift,
      both deliberately deferred to follow-up ticket
      `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` per Decision 1/plan Step 9b (full sweep
      `git diff` before/after this ticket's edits shows the identical 32-failed/39-passed count —
      zero new failures introduced).
- [x] `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow -v` shows the 2 named
      `_1000t` guards passing (or a documented, deliberate decision not to convert them, with
      reasoning recorded) — both pass in isolated invocation; full
      `make simq-corpus-diversity-slow-isolated` sweep run as the final gate (see Test Summary).

## Related Tickets
- TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP (originating ticket;
  disclosed these findings via its own Implement-time fresh re-verification rather than fixing or
  silently absorbing them)
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (DONE — root cause of the COGNITION-side
  drift for the same 4 run_keys; plausibly also touches AGENCY's mechanism, not confirmed)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (DONE — introduced §2.41's `defer_with_reason`
  observability gap, the leading hypothesis for the AGENCY drift)
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (DONE — established the
  `watchdog_variance` ceiling mechanism and the `simq_routing_test_seed123_500t`/PROGRESSION
  ceiling entry whose own reason text is the "COGNITION stable" baseline this ticket's finding
  (2) contradicts)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.40, §2.41
- docs/simulation_quality/eval_matrix_results.md (`simq_routing_test`, `hero_guild_routing`
  sections — NOTE blocks added by the originating ticket)

## Related Stored Artifacts
- staging_artifacts/TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP/ (once
  moved to stored_artifacts/ — investigation.md's "Adjacent, out-of-scope discovery" section and
  this ticket's own Implementation Notes record the raw pytest evidence for findings (1) and (2))

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json (AGENCY fields for the 6 named run_keys)
- tests/unit/worldassembly/test_corpus_diversity.py (`test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`)
- src/domains/adventure/ (AGENCY event emission — `last_defer_reason`/`defer_with_reason`)
- src/observability/event_extractor.py / event_shapers.py (AGENCY event shaping)

## Assumptions / Open Questions
- Whether the full-zero AGENCY outcome on the 4 named `_500t` items vs. the partial score-tolerance
  drift on the 2 `seed123` variants is the same mechanism at different magnitudes, or two distinct
  mechanisms, is not yet determined — Investigate's job, not assumed here.
- Whether `docs/guidelines/intentional_divergences.md` §2.41 is the complete explanation, or only
  a partial one (given 3 more tier-5 GoalScorer commits landed in the same window per the
  originating ticket's investigation.md Risk #1), is not yet determined.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/plan.md`'s
9 steps, in order. No `src/` edits at any point (recalibrate-and-disclose ticket, as scoped).

**Step 1 (fresh re-verification, precondition for Steps 2-4):** Ran 2 independent trials each via
`tools/calibrate_simq.py --ticks 500 --seed {42,123,456} --name {simq_routing_test,
hero_guild_routing}` for all 6 named run_keys (12 runs total). All 6 confirmed bit-identical AGENCY
`0 events/0.0/C` across both trials; the `seed123` pair additionally confirmed bit-identical
COGNITION `0 events/0.0/C`. Every value matched investigation.md's Finding 1/2 tables exactly — no
divergence found, so Steps 2-4 proceeded on Investigate's own cited values (now independently
re-confirmed, not blindly copied).

**Steps 2-3 (grade_anchors.json recalibration):** Edited AGENCY for the 4 named `_500t` keys and
COGNITION+AGENCY for the `seed123` pair to `{"grade": "C", "score": 0.0}`. `git diff` confirms
exactly the 6 intended top-level keys' AGENCY/COGNITION sub-objects changed, nothing else. Verified
via scoped `test_grade_within_anchor_band` runs before/after: AGENCY/COGNITION band-crossing
failures eliminated on all 6; only pre-existing, already-ceiling-documented pillar noise remains
(watchdog_variance for `simq_routing_test_seed{42,123}_500t` PROGRESSION, flag_gated for
COMBAT on `_seed456` keys, tick_budget for `hero_guild_routing_seed{42,123}_500t` WORLD).

**Discovery beyond plan.md's named scope:** confirmed `hero_guild_routing_seed456_500t`'s
ECONOMY/PROGRESSION drift (already flagged by plan.md, deferred to Step 9b) AND found a
previously-invisible `simq_routing_test_seed456_500t` PROGRESSION score-tolerance drift, unmasked
only because this ticket's AGENCY fix removed the band-crossing failure that had been
short-circuiting `test_grade_within_anchor_band`'s assertion order (band-check runs before
score-check) before the fix landed. This second finding was NOT named by plan.md. Per CLAUDE.md's
"no material gap left unstated" rule, it is disclosed here and folded into follow-up ticket (b)'s
scope (broadened beyond plan.md's original framing of that ticket) rather than fixed in this
ticket or silently dropped — see "Deviations" in plan.md.

**Step 4 (score_ceilings.json annotation):** Prepended the `SUPERSEDED-IN-PART` annotation to the
`simq_routing_test_seed123_500t`/PROGRESSION entry's `reason` field exactly as plan.md specified,
preserving the original text. Verified: JSON still parses, PROGRESSION ceiling classification
still applies (annotation is additive to the `reason` string only).

**Step 5 (§2.41 broadening):** Added a new "Broadened disclosure" paragraph to §2.41 disclosing the
`last_routing_family` loss (feeding `route_selected`/`action_executed`/`route_family_first_use`),
citing the follow-up ticket ID. Also corrected the stale `intelligence.py:1409` line-number
citation (in the pre-existing Rationale paragraph) to the current `intelligence.py:1450` —
confirmed via fresh `grep -n "utility < 20.0"`.

**Step 6 (INFRA-237 addendum):** Appended a second addendum block to the `support_boundary` field
recording the re-verification result. YAML confirmed still parses.

**Step 7 (eval_matrix_results.md correction):** Rewrote the "Root cause" paragraph (lines 584-599
pre-edit) to state `AdventureDecisionPhase`/`phase.py` is deleted and no replacement writes
`last_routing_family`, rather than describing it as still-live. Left the "Anti-drift" paragraph
unaltered per plan.md. Added dated 2026-08-13 NOTE blocks to both the `simq_routing_test` and
`hero_guild_routing` sections, matching the existing COGNITION NOTE's pattern.

**Step 8 (`_1000t` guard conversion):** Per Decision 3, ran a fresh idle+induced-load probe (the
`_500t` sibling's own `_busy_loop`/`multiprocessing` mechanism, 2x core oversubscription) against
both `_1000t` scenarios before finalizing shape. Both scenarios came back clean in every condition
(`event_count=0, grade=C, loop_detected=False`) — no residual observed, unlike the `_500t`
sibling's own history. Per Decision 3's explicit guidance, defaulted to the same tolerance-guard
(2b) shape as the `_500t` sibling anyway (safer default; low cost of staying at 2b vs. guaranteed
future-flake risk of prematurely locking 2a). Converted both tests' bodies verbatim from the
`_500t` sibling's shape (idle strict-assert + induced-load tolerance-assert), adjusted for
`ticks=1000`, and updated both docstrings to drop the stale F6/decision_divergence_detected framing.
Both pass in isolated invocation (`--resource-budget large --tb=short -q -m slow`).

**Step 9 (follow-up tickets):** Filed both as standard-tier tickets under `tickets/todos/`
(neither is being implemented by this ticket):
- `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` (layer: strategy) — the
  `last_routing_family` code-fix, citing this ticket's own Decision 1 schema-change evidence.
- `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` (layer: simulation) — broadened beyond
  plan.md's original framing to also cover the newly-found `simq_routing_test_seed456_500t`
  PROGRESSION drift discovered during this ticket's own Step 2 verification (see "Discovery beyond
  plan.md's named scope" above).

Both new tickets pass `tools/validate_frontmatter.py --content-type ticket` and
`tools/ticket_field_values.py`.

## Test Summary

- `tools/calibrate_simq.py` fresh re-verification: 12/12 runs (2 trials x 6 run_keys) bit-identical,
  matching investigation.md exactly — PASS.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "<6 named
  run_keys>"`: AGENCY/COGNITION band-crossing eliminated on all 6; remaining failures are
  pre-existing pillar noise (ceiling-documented, or deferred to follow-up ticket (b)) — PASS on
  this ticket's own scope.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` (full 89-key sweep):
  32 failed / 39 passed / 18 deselected, identical count before and after this ticket's edits
  (confirmed via `git stash`/`git stash pop` A-B comparison) — zero new failures introduced.
- `pytest tests/simulation_quality/test_agency_scorer.py -q`: 26 passed.
- `pytest tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py
  tests/unit/ai/goals/test_adventure_goal_scorer.py
  tests/unit/strategic/test_adventure_route_materialization.py
  tests/unit/observability/test_event_extractor_agency2.py
  tests/unit/observability/test_decision_trace.py -q`: 74 passed.
- `test_grade_anchor_file_exists_and_valid`,
  `test_score_tolerance_override_table_scoped_to_named_pillars`,
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`: 3 passed.
- `pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability"
  --resource-budget large --tb=short -q -m slow`: 1 passed (66.34s).
- `pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_hero_guild_routing_seed42_1000t_cognition_grade_stability"
  --resource-budget large --tb=short -q -m slow`: 1 passed (59.53s).
- `make simq-corpus-diversity-slow-isolated` (final full-sweep gate, 32 isolated nodeids, run to
  completion): **21 passed / 11 failed.** Both of this ticket's own converted guards
  (`test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`) PASS. The 11 failures are on
  completely different run_keys/tests this ticket did not touch and does not name in scope
  (`test_unit_selfmodel_pilot_seed42_1000t_...`, `test_urban_political_seed42_1000t_...`,
  `test_urban_political_seed123_1000t_...`, `test_urban_political_selfmodel_probe_seed42_200t_...`,
  `test_generated_frontier_3_42_seed123_200t_...`, `test_urban_political_seed42_200t_...`,
  `test_frontier_extended_seed42_200t_...`, `test_frontier_extended_seed123_200t_...`,
  `test_frontier_living_world_seed42_200t_...`, `test_frontier_living_world_seed123_200t_...`,
  `test_frontier_marches_seed42_200t_...` — all COGNITION/SOCIAL/NARRATIVE/COMBAT grade-stability
  guards for `unit_selfmodel_pilot`/`urban_political`/`generated_frontier_3_42`/
  `frontier_extended`/`frontier_living_world`/`frontier_marches`, none of which are
  `simq_routing_test` or `hero_guild_routing`). Confirmed pre-existing and unrelated to this
  ticket's edits, not a regression introduced here: `git diff` of `test_corpus_diversity.py` shows
  only the 2 named target functions were touched (verified via `git diff ... | grep '^@@'`,
   3 hunks total, all inside the 2 converted tests' bodies), and none of `grade_anchors.json`'s 6
  edited top-level keys overlap with any of these 11 failing run_keys. This matches the same
  widespread, already-documented "active churn" pattern the full `-m "not slow"` FAST_ANCHOR_KEYS
  sweep above also shows (32 pre-existing failures across unrelated worlds) — consistent with
  investigation.md's own characterization of this corpus area under active multi-ticket churn, not
  something this ticket introduced or is scoped to fix. AC5 ("shows the 2 named `_1000t` guards
  passing") is satisfied; the other 11 failures are out of this ticket's named scope and not
  claimed as fixed.
- `python3 -c "import json; json.load(...)"` on `grade_anchors.json`/`score_ceilings.json`: both
  parse cleanly.
- `python3 -c "import yaml; yaml.safe_load(...)"` on `infrastructure.yaml`: parses cleanly.

## Files Changed

- `tests/simulation_quality/fixtures/grade_anchors.json` — AGENCY recalibrated for 4 `_500t` keys;
  COGNITION+AGENCY recalibrated for the `seed123` pair (6 keys total, Steps 2-3).
- `tests/simulation_quality/fixtures/score_ceilings.json` — `SUPERSEDED-IN-PART` annotation
  prepended to `simq_routing_test_seed123_500t`/PROGRESSION's `reason` field (Step 4).
- `docs/guidelines/intentional_divergences.md` — §2.41 broadened with a new "Broadened disclosure"
  paragraph on the `last_routing_family` loss; stale `intelligence.py:1409` citation corrected to
  `:1450` (Step 5).
- `docs/parity_ledger/infrastructure.yaml` — INFRA-237 `support_boundary` field, second addendum
  appended recording the re-verification result (Step 6).
- `docs/simulation_quality/eval_matrix_results.md` — AGENCY Cross-World Design Note's "Root cause"
  paragraph rewritten; dated 2026-08-13 NOTE blocks added to both `simq_routing_test` and
  `hero_guild_routing` sections (Step 7).
- `tests/unit/worldassembly/test_corpus_diversity.py` —
  `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` converted from the stale 3-trial
  mean-tolerance shape to the `_500t` sibling's idle+induced-load tolerance-guard shape (Step 8).
- `tickets/todos/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE.md` — new follow-up
  ticket (Step 9a).
- `tickets/todos/TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT.md` — new follow-up ticket
  (Step 9b, scope broadened per the Step 2 discovery above).
- `docs/simulation/domains/adventure_contract.md` — corrected to state that
  `AdventureGoalScorer.score()` no longer emits any `EntityUpdate.property_updates` (neither
  `last_defer_reason` nor `last_routing_family`/`last_routing_tick`), attributing this to the
  deleted `AdventureDecisionPhase.apply()`; cross-references §2.41 and the Step 9a follow-up
  ticket (Document-Update phase, not one of Implement's own numbered steps).
- `docs/simulation_quality/current_state.md` — added a targeted correction to the AGENCY summary
  paragraph noting the fresh Implement-time re-verification found `simq_routing_test`/
  `hero_guild_routing` now also grade C on their `_500t` anchors (a real observability regression,
  not the pre-existing `ENABLE_ADVENTURE_ROUTING`-opt-in design the paragraph otherwise still
  correctly describes); explicitly defers a full corpus refresh as out of scope for a docs-only
  pass, per this doc's own stated convention (Document-Update phase).
- `docs/simulation_quality/event_type_coverage.md` — corrected the `route_selected`,
  `action_executed`, and `route_family_first_use` rows' explanatory text, which previously stated
  stale historical hit-counts (`20`, `20`, `0`) as if still current; now notes these events cannot
  fire in any `ENABLE_ADVENTURE_ROUTING=ON` world today given the confirmed `last_routing_family`
  writer loss (Document-Update phase).
- `tickets/inprogress/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT.md` — this file
  (Implementation Notes, Test Summary, Files Changed, Acceptance Criteria).

## Completion Summary

Recalibrated `grade_anchors.json` AGENCY (4 named `_500t` keys) and COGNITION+AGENCY (`seed123`
pair) to the confirmed-current `0/0.0/C` values, following a mandatory fresh 2-trial-per-run_key
re-verification that matched Investigate's snapshot exactly. Annotated the now-partially-stale
`score_ceilings.json` PROGRESSION reason text without deleting it. Broadened
`docs/guidelines/intentional_divergences.md` §2.41 to disclose that the deleted
`AdventureDecisionPhase.apply()` was also the sole writer of `last_routing_family` (not just
`last_defer_reason`), corrected a stale line-number citation in the same section, added the
INFRA-237 re-verification addendum, and corrected `eval_matrix_results.md`'s AGENCY design note to
stop citing the deleted phase as live. Converted both stale `_1000t` COGNITION guard tests to the
corrected idle+induced-load tolerance-guard shape after confirming via a fresh induced-load trial
that no residual exists at this tick count (kept the safer 2b shape per Decision 3 regardless).
Filed two follow-up tickets: one for the `last_routing_family` code-fix (a real `StrategicUpdate`
schema change, deliberately out of this recalibrate-only ticket's scope), and one for
`hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift, broadened during Implement to also
cover a newly-found `simq_routing_test_seed456_500t` PROGRESSION drift that Investigate's snapshot
had not surfaced. Zero `src/` changes. Full FAST_ANCHOR_KEYS sweep shows the identical
32-failed/39-passed count before and after this ticket's edits — no regressions introduced.
