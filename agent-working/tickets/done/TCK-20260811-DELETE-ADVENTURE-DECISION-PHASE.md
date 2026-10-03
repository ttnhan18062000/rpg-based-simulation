---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE
phase: done
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE

## Title
Delete AdventureDecisionPhase and relocate its eligibility helpers

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Remove the AdventureDecisionPhase class and its pipeline.py registration entirely, once the new scorer-based path is live. _resolve_cognition_profile_id/_supports_adventure_routing move to wherever AdventureGoalScorer lives, unchanged internally. This is the final step-3 cutover of the staged migration plan.

## Scope
- Remove AdventureDecisionPhase class and its ENABLE_ADVENTURE_ROUTING-gated registration in src/engine/pipeline.py
- Relocate _resolve_cognition_profile_id and _supports_adventure_routing (currently src/domains/adventure/phase.py lines 49-96) to AdventureGoalScorer's module (src/ai/goals/), byte-identical internally
- Migrate the 5-6 tests currently importing AdventureDecisionPhase directly to exercise the AdventureGoalScorer/tier-5 path with equivalent coverage
- Update STRAT-236 text+v2_evidence and docs/simulation/domains/adventure_contract.md's 'Engine Phase' section so neither references AdventureDecisionPhase/phase.py as the live mechanism

## Out of Scope
- _threat_resolved() relocation and evaluate_project_switch() signature change -- confirmed this belongs to THREAT-RESOLVED-ARBITER-RELOCATION (C2), not this ticket; C3's own investigation only names the eligibility helpers as its relocation scope
- Building AdventureGoalScorer itself -- ADVENTURE-GOAL-SCORER's (C1) job, a hard prerequisite for this ticket
- Building the shadow-mode diff test -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job, also a hard prerequisite for this ticket

## Acceptance Criteria
- [x] This ticket's Implement phase does not proceed until TCK-20260811-ADVENTURE-GOAL-SCORER (C1) and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4) are both in tickets/done/ -- Scope must verify both exist and are DONE before allowing Implement to proceed; if not, this ticket is held/blocked. Verified both present in tickets/done/ before any implementation started.
- [x] AdventureDecisionPhase class and its pipeline.py registration are removed; grep for AdventureDecisionPhase in src/engine/pipeline.py returns no matches. src/domains/adventure/phase.py deleted entirely (no other src/ importer remained); pipeline.py's "adventure_decision" run_phase block removed.
- [x] _resolve_cognition_profile_id and _supports_adventure_routing exist byte-identical in AdventureGoalScorer's module (src/ai/goals/), same inputs/outputs as before. Relocated verbatim into src/ai/goals/adventure_scorer.py; covered by test_eligibility_cognition_profile.py (4 tests) and the new byte-identical-signature guard test.
- [x] All 5-6 (corrected: 9) tests currently importing AdventureDecisionPhase directly are migrated to exercise the AdventureGoalScorer/tier-5 path with equivalent coverage. All 9 migrated and passing; 2 additional files with a lazy-import-path dependency on the deleted module (test_adventure_goal_scorer.py, test_adventure_route_materialization.py, found beyond investigation's 9-file count) also fixed.
- [x] STRAT-236 text+v2_evidence and adventure_contract.md's 'Engine Phase' section no longer reference AdventureDecisionPhase/phase.py as the live mechanism. STRAT-236/252/253 updated in strategic_cognition.yaml; adventure_contract.md's Engine Phase section and 04_strategic_cognition.md lines 30/311 rewritten; verified via 2 new doc-guard tests.

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
- TCK-20260810-D22-DORMANT-WIRING-AUDIT
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
- TCK-20260811-ADVENTURE-GOAL-SCORER, TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION,
  TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (hard prerequisites, all DONE)
- TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION (pre-existing test failures re-confirmed
  in this ticket's Test Summary)
- TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP (pre-existing SimQ
  failures re-confirmed, with 2 additional undisclosed-but-pre-existing failures noted)
- TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION (follow-up filed for a newly-discovered,
  confirmed pre-existing, unrelated test failure — see Test Summary)

## Related Docs
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- PRIMARY RISK -- this ticket's real 'delete' action is explicitly gated behind TCK-20260811-ADVENTURE-GOAL-SCORER and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE landing first -- creating/implementing this ticket ahead of those must be rejected or held at Scope if attempted prematurely
- Blast radius wider than '2 functions relocate' -- 6 test files break immediately on deletion
- Confirmed via sibling investigation: _threat_resolved's relocation belongs to TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION, not this ticket
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md §5, §7

## Implementation Notes

Implemented exactly per the twice-reviewed, APPROVED plan.md, steps 1-11, in the plan's own
recommended safe order (additive Steps 1/3/4 -> Step 5 test migration against the still-live
class -> Step 2 deletion -> Step 6 port-then-delete -> Steps 7-9 docs/ledger -> Steps 10-11
verify).

Beyond plan.md's own Step 7/9 enumerated file lists, the Document-Update and Parity phases each
independently found additional stale references to the deleted class that the plan had not
anticipated, and fixed them: 6 docs (`design_patterns.md`, `adventure_routing_contract.md`,
`decision_trace_contract.md`, `cooperation_contract.md`, `faction_contract.md`,
`decision_trace_writer.py`'s own module docstring) plus 1 test docstring
(`test_project_system_precedence.py`) during Document-Update, and 2 parity-ledger files outside
`strategic_cognition.yaml` (`infrastructure.yaml`, `substrate.yaml`) during the Parity phase. All
are genuine, correct fixes for real staleness this deletion caused; none change tested behavior.
They were verified content-correct at the time but omitted from this section's original draft —
now added to Files Changed below.

- Step 1: `_resolve_cognition_profile_id`/`_supports_adventure_routing` relocated
  byte-identical from `src/domains/adventure/phase.py` into `src/ai/goals/adventure_scorer.py`
  (after imports/`_PROFILE_ELIGIBILITY_CACHE`, before the class). Removed the now-dead lazy
  function-local import + its surrounding circular-import comment block in `score()` (the
  comment explained why the import needed to be lazy; once the function lives in the same
  module there is no import at all, so the comment no longer applied and would have been
  misleading left in place).
- Step 2: deleted `AdventureDecisionPhase` and `pipeline.py`'s "Enhanced RPG Phase 3: Adventure
  Routing" block. Confirmed via repo-wide grep that no other `src/` module imported
  `src.domains.adventure.phase` after Step 1's relocation, so the file was deleted outright
  rather than left as a dead module.
- Step 3: ported the decision-trace-writer call into `AdventureGoalScorer.score()`, placed
  immediately after `AdventureDecisionService.decide()` and before the
  DEFER_WITH_REASON/target-resolution branches, mirroring the deleted phase's own
  per-hero-loop placement exactly.
- Step 4: added the "Adventure-Route Defer-Reason Observability Gap" entry (table row + §2.41
  detailed record, `**Status**: ACTIVE` per the file's own established convention) to
  `docs/guidelines/intentional_divergences.md`, citing the corrected utility-floor-discard
  mechanism (`intelligence.py:1412`) rather than return-site-counting.
- Step 5: migrated all 9 real-dependency test files. `test_spawn_lock_condition.py`'s migration
  required care: with the default `CognitionProfile` (`resistance_multiplier=30.0`), no
  ADVENTURE_ROUTE-scale raw score (ceiling 2.9) can ever clear `evaluate_project_switch()`'s
  final unconditional raw-score comparison, and a near-ceiling synthetic candidate always clears
  the 0.8 urgency floor regardless of `_threat_resolved` — both would make "lock released"
  indistinguishable from "lock held" by a naive assertion. Fixed by giving the test hero a
  zero-margin `CognitionProfile` and calibrating the injected candidate's raw_score (1.5) to sit
  strictly between the urgency-floor cutover point and the (now-small) effective_current_score,
  isolating the mechanism under test.
- Step 6: ported `_diff_routes()` + `test_shadow_diff_report_separates_raw_score_from_utility_mismatches`
  into `test_adventure_route_materialization.py` first, confirmed passing, then deleted
  `test_adventure_shadow_migration_parity.py` in full — strict order followed, not reversed.
- Step 7: STRAT-236 (removed the stale "AdventureDecisionPhase's own pre-filter... remains a
  separate, still-active gate" sentence from v2_evidence; test_path's 3rd entry needed no
  re-pointing since the migrated test kept its exact pre-migration name), STRAT-252 (text +
  support_boundary, see Deviations), STRAT-253 (all 4 named fields: text, status ->
  legacy_verified, test_path, divergence_note, support_boundary).
- Step 8: added 4 new guard tests in a new file,
  `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`.
- Step 9: rewrote `adventure_contract.md`'s "Engine Phase" section and
  `04_strategic_cognition.md` lines 30 and 311 (line 311's fix required stating honestly that
  `faction_directives` is NOT threaded into the live `AdventureGoalScorer.score()` call path,
  per the plan's own Anti-Drift Note).
- Steps 10-11: full scoped regression run (321 passed / 3 failed, see Test Summary), targeted
  SimQ re-check, and the STRAT-185/186/187 sanity re-run (both pass).

### Post-Verify cleanup pass (Architecture-Verify NEEDS_CHANGES, 5 findings)

A follow-up Architecture-Verify pass on this ticket's diff found 5 cleanup gaps left behind by
the deletion (not problems with the deletion logic itself). All 5 fixed:

1. `src/engine/phase_graph.py:66` — removed the orphaned `"adventure_decision"` entry from
   `PhaseDependencyGraph.PHASES`. Confirmed via repo-wide grep that `pipeline.py` no longer has
   any `run_phase("adventure_decision", ...)` call site, so nothing reads this dict key anymore.
2. `src/engine/faction_decision.py:4` — module docstring rewritten to describe the real current
   phase ordering (`FactionDecisionPhase.execute()` is a direct call, not a `run_phase()`
   registration, running between `blacksmith` and `faction_awareness`) and to state plainly that
   the `faction_directives` it produces are not threaded into `AdventureGoalScorer.score()`
   today.
3. `docs/engine/authoritative_pipeline.md` — removed the `adventure_decision` row from the
   32-phase table (missed by this ticket's own doc-update pass) and corrected the phase count to
   31 throughout (heading, callout, and re-numbered the `#` column of all subsequent rows).
4. `docs/engine/known_limitations.md` §1.5 — added a clarifying note that
   `ENABLE_ADVENTURE_ROUTING` no longer gates any live behavior (the phase it used to gate is
   deleted; `AdventureGoalScorer` runs unconditionally). The flag entry itself was left in place
   since it is still registered in `FeatureFlagManager` and referenced by existing tests/configs.
5. `src/ai/goals/adventure_scorer.py` (~line 105-117) — rewrote the stale "unwired from
   pipeline.py, C3 must decide" comment, which this ticket's own diff directly contradicts. It
   now states plainly that this IS the live, sole adventure-decision path today, and that
   `faction_directives=None` is a disclosed, intentional simplification (not a not-yet-wired
   placeholder), citing `docs/mechanics/04_strategic_cognition.md` §6.10 and
   `docs/systems/faction_contract.md`.

Informational (not fixed, reported as a residual known gap): `docs/mechanics/content_usage_matrix.md`
has no YAML frontmatter. Confirmed this is generator-owned — `generate_matrix_report()` in
`src/content/matrix.py` never emits frontmatter, and `tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report`
unconditionally overwrites the file with the generator's output on every test run. The file is
already pinned in `tests/tools/test_validate_frontmatter.py`'s `_PREVIOUSLY_FRONTMATTER_MISSING_DOCS`
regression list as an accepted frontmatter-missing doc, so a manual frontmatter addition would be
immediately wiped by the next test run and provide no lasting benefit. Per this pass's own
instructions, the generator was not modified (out of scope).

Scoped regression re-run after the 5 fixes (`tests/unit/ai/goals/ tests/unit/domains/adventure/
tests/integration/domains/adventure/ tests/unit/strategic/test_adventure_route_materialization.py
tests/unit/observability/test_decision_trace.py tests/unit/observability/test_event_extractor_agency2.py`):
149 passed, 2 failed. Both failures are the same pre-existing `test_harvest_to_event.py` failures
already tracked in this ticket's own Test Summary/Related Tickets
(`TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION`) — reconfirmed unrelated to these 5
fixes by re-running the same 2 tests with the 5 fixes stashed out (identical failure, identical
error).

## Deviations from plan.md (documented per CLAUDE.md's Workflow Rule; also appended to
staging_artifacts/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE/plan.md's own Deviations section)

1. **2 additional real-dependency files beyond the plan's 9, found during implementation**:
   `tests/unit/ai/goals/test_adventure_goal_scorer.py` and
   `tests/unit/strategic/test_adventure_route_materialization.py` both monkeypatched
   `"src.domains.adventure.phase._supports_adventure_routing"` by string path (a dependency on
   the deleted module's import path, not on the `AdventureDecisionPhase` class name the
   investigation's grep searched for). Fixed by retargeting both monkeypatch strings to
   `"src.ai.goals.adventure_scorer._supports_adventure_routing"` — a mechanical consequence of
   Step 1's relocation, not a scope expansion.
2. **`test_filters_out_locked_projects` (`test_phase3_adventure_decision_phase.py`) crashed**
   after migration: `b.replace_self_model(None)` (an unrelated pre-existing test-setup artifact)
   crashed `AdventureRouteGenerator.generate()`'s real `entity.self_model.self_awareness` read
   once route generation became reachable for a locked entity (the deleted phase's own
   pre-filter used to prevent this entity from ever reaching the generator at all when locked;
   the new tier-5 path runs the scorer unconditionally, matching the "already live" framing).
   Removed the unnecessary `replace_self_model(None)` call — `V2EntityBuilder`'s own default
   (`SelfModelBundle()`) is what the comment ("simple default self model") actually intended.
3. **STRAT-252's `support_boundary` field updated**, not just `text` as plan.md's Step 7 literally
   enumerated for this entry — left unmodified it would state "no pipeline.py phase currently
   drives a live tick through this path," which is now false post-deletion. This mirrors the
   same kind of gap the plan itself found for STRAT-253's `divergence_note`/`support_boundary`
   ("found independently in this planning pass, not called out by investigation.md's own list").
4. **STRAT-236's `test_path` needed no re-pointing** — plan anticipated the migrated
   `test_lock_released_when_hp_high_and_no_hostiles` might get a new name/class during Step 5
   item 4's migration, but it kept its exact pre-migration name (only gained a `monkeypatch`
   fixture parameter), so the citation is already correct unchanged.
5. **Two tests in `test_grade_regression.py -k "simq_routing_test or hero_guild_routing"`
   (`simq_routing_test_seed123_500t`, `hero_guild_routing_seed123_500t`) fail on score-tolerance
   (COGNITION/AGENCY), not the discrete grade-band check** — these are NOT among the 4 items
   `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` discloses. Confirmed
   NOT a regression from this ticket's own action: the underlying
   `data/calibration/{run_key}/quality_report.json` files these tests read have mtimes ~5.7
   hours before this implementation session started (this ticket never runs calibration/
   simulation generation, only reads pre-existing committed report JSON), so the failing data
   predates any code this ticket touched. Reported per Step 10's own instruction ("flag for a
   decision on whether a new ticket is needed") rather than silently folded into the existing
   follow-up ticket's scope or fixed by touching the explicitly out-of-scope
   `FAST_ANCHOR_KEYS`/`grade_anchors.json`/`score_ceilings.json`.

## Test Summary

Scoped regression run (test_plan.md's command, all Step 1-9 touched unit/integration/perf
files): **321 passed, 3 failed**.

Failures:
1. `tests/integration/domains/adventure/test_harvest_to_event.py::test_crafting_project_produces_item_crafted_event_through_full_pipeline`
   — known pre-existing (tracked: `TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION`).
2. `tests/integration/domains/adventure/test_harvest_to_event.py::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`
   — known pre-existing (tracked: `TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION`).
3. `tests/integration/test_scenario_feature_flag_defaults.py::test_feature_flag_defaults_are_stable_across_instances`
   — pre-existing, unrelated to this ticket. `ENABLE_PUSH_EVENT_SHAPERS` has been hardcoded to
   `FeatureMode.ON` in `src/domains/optimization/feature_flags.py` since commit `11b83f37`
   (2026-08-08, an unrelated push-event-shaper observability epic), 3 days before this session;
   this file was never touched by this ticket. Fails even in complete isolation (single-file
   run), independently re-confirmed. Tracked as follow-up ticket
   `TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION`.

SimQ targeted re-check (`test_grade_regression.py -k "simq_routing_test or hero_guild_routing" -m
"not slow" -q`): 6 failed, 83 deselected. 4 match
`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`'s exact disclosed list
(`simq_routing_test_seed42_500t`/`seed456_500t` and `hero_guild_routing_seed42_500t`/
`seed456_500t`, all COGNITION grade-band crossings). 2 additional failures
(`simq_routing_test_seed123_500t`, `hero_guild_routing_seed123_500t`, both score-tolerance, not
band-crossing) are undisclosed by that ticket but confirmed pre-existing (see Deviations #5) —
reported, not silently folded in or fixed.

STRAT-185/186/187 sanity re-run (`test_score_normalization.py`'s 2 named tests): both pass.

STRAT-236's `test_path` (3 tests) and STRAT-253's new `test_path` (1 test): all pass.

## Files Changed

Modified:
- `src/ai/goals/adventure_scorer.py` (relocation + Post-Verify comment rewrite)
- `src/engine/pipeline.py`
- `src/engine/phase_graph.py` (Post-Verify cleanup: removed orphaned `adventure_decision` entry)
- `src/engine/faction_decision.py` (Post-Verify cleanup: docstring rewrite)
- `src/content/matrix.py`
- `docs/guidelines/intentional_divergences.md`
- `docs/parity_ledger/strategic_cognition.yaml`
- `docs/simulation/domains/adventure_contract.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/mechanics/content_usage_matrix.md` (auto-regenerated report file, byproduct of
  `src/content/matrix.py`'s edit + running `test_content_usage_matrix.py`)
- `docs/engine/authoritative_pipeline.md` (Post-Verify cleanup: removed stale phase-table row,
  corrected 32->31 phase count)
- `docs/engine/known_limitations.md` (Post-Verify cleanup: corrected `ENABLE_ADVENTURE_ROUTING`
  gating claim in §1.5)
- `docs/guidelines/design_patterns.md` (Document-Update: removed `AdventureDecisionPhase` from the
  representative-implementation code example, swapped to `CombatEngagementPhase`)
- `docs/mechanics/adventure_routing_contract.md` (Document-Update: Lifecycle section rewritten to
  describe `AdventureGoalScorer` as the sole live entry point)
- `docs/observability/decision_trace_contract.md` (Document-Update: "Wired at" citation updated from
  `AdventureDecisionPhase.apply()` to `AdventureGoalScorer.score()`)
- `docs/parity_ledger/infrastructure.yaml` (Parity phase: INFRA-211 citation updated to new
  location+test; INFRA-237/SIMQ-CALIBRATED-001 addenda flagging stale gating citations)
- `docs/parity_ledger/substrate.yaml` (Parity phase: SUB-373 addendum for the `matrix.py` runtime
  consumer rename)
- `docs/simulation/domains/cooperation_contract.md` (Document-Update: `BlockerState`/lock-respect
  row updated to cite `evaluate_project_switch()`'s shared gate instead of `AdventureDecisionPhase`)
- `docs/systems/faction_contract.md` (Document-Update: "Directive Propagation to Entity Scoring"
  section rewritten to disclose `faction_directives` is no longer threaded into the live path)
- `src/observability/cognition/decision_trace_writer.py` (module docstring updated to cite
  `AdventureGoalScorer.score()` as the wiring site instead of the deleted `AdventureDecisionPhase.apply()`)
- `tests/unit/strategic/test_project_system_precedence.py` (module docstring rewritten to describe
  the single-phase, post-deletion merge semantics; the tested `StrategicUpdate.merge()` last-write-wins
  behavior itself is unchanged)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`
- `tests/unit/domains/adventure/test_eligibility_cognition_profile.py`
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`
- `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py`
- `tests/unit/strategic/test_adventure_route_materialization.py`
- `tests/unit/systems/test_spawn_lock_condition.py`
- `tests/unit/observability/test_decision_trace.py`
- `tests/unit/observability/test_event_extractor_agency2.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/perf/test_phase3_adventure_decision_budget.py`

Created:
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`

Deleted:
- `src/domains/adventure/phase.py`
- `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

Not touched (confirmed comment-only, no code dependency): `test_craft_upgrade_execution.py`,
`test_threat_resolved_lock_release.py`, `test_event_extractor_social_faction.py`,
`test_resource_region_coverage_corpus.py`, `test_scenario_feature_flag_defaults.py`.

## Completion Summary

Deleted `AdventureDecisionPhase` and its `pipeline.py` registration, relocating
`_resolve_cognition_profile_id`/`_supports_adventure_routing` byte-identical into
`AdventureGoalScorer`'s module and porting the decision-trace-writer call into `score()`. The
`last_defer_reason`/`defer_with_reason` signal was deliberately NOT ported (recorded as an
intentional, disclosed divergence) since it is discarded by the shared tier-5 utility-floor
check before any commit site is reached. All 9 real-dependency test files (plus 2 more found
during implementation with an import-path-only dependency) were migrated to exercise the
surviving `AdventureGoalScorer`/tier-5 path with equivalent-or-stronger coverage; the
shadow-migration-parity suite's one independently-valuable assertion was ported before the
24-test file was deleted. STRAT-236/252/253, `adventure_contract.md`, and
`04_strategic_cognition.md` were all updated to describe `AdventureGoalScorer` as the sole live
adventure-decision mechanism. Scoped regression run: 321 passed, 3 failed (2 already-tracked
pre-existing harvest/craft-event failures, 1 newly-discovered-but-pre-existing unrelated
feature-flag-default failure, confirmed unrelated to this ticket's diff). Targeted SimQ re-check
found the 4 already-disclosed COGNITION band-crossing items plus 2 additional pre-existing
score-tolerance failures (confirmed via calibration-file mtimes to predate this session) not yet
disclosed by the tracking ticket — reported, not silently absorbed or fixed.

**Post-Verify cleanup pass**: a follow-up Architecture-Verify pass found 5 concrete cleanup gaps
left behind by the deletion — an orphaned `phase_graph.py` dict entry, a stale docstring in
`faction_decision.py`, a stale phase-table row and count in `authoritative_pipeline.md`, a false
gating claim in `known_limitations.md` §1.5, and a stale "unwired" comment in
`adventure_scorer.py` that this ticket's own diff directly contradicted. All 5 fixed; scoped
regression re-run (149 passed, 2 failed — the same pre-existing, already-tracked
`test_harvest_to_event.py` failures, reconfirmed unrelated via a stash-and-rerun check).
