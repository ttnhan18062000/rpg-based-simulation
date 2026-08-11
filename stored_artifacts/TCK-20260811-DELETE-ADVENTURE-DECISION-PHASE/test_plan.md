---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE
artifact_type: test_plan
tags: [cognition, adventure]
---

# Test Plan — TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE

## Acceptance Criteria Map

| AC | Concrete test(s) |
|---|---|
| AC1 (Implement doesn't proceed until C1/C4 both DONE) | `test_prereq_tickets_c1_and_c4_are_in_done` (new, Scope-phase-style guard, see below) |
| AC2 (`AdventureDecisionPhase` + pipeline.py registration removed) | `test_pipeline_module_has_no_adventure_decision_phase_reference` (new, replaces the ticket's own "grep returns no matches" check with an importable regression guard) |
| AC3 (`_resolve_cognition_profile_id`/`_supports_adventure_routing` byte-identical in `AdventureGoalScorer`'s module) | `test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source` (new); plus the migrated `test_eligibility_cognition_profile.py` suite (below) exercising real behavior, not just source-text |
| AC4 (~5-6 [corrected: 9] dependent tests migrated with equivalent coverage) | Full migration table below, one row per file |
| AC5 (STRAT-236 + `adventure_contract.md` no longer reference `AdventureDecisionPhase`/`phase.py` as live) | `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase` (new, parity-ledger text-content guard, mirrors the pattern `test_content_usage_matrix.py` already uses for ledger-adjacent string assertions) |

## Regression Surface

**Unit:**
- `tests/unit/domains/adventure/` (all — `test_craft_upgrade_execution.py`,
  `test_eligibility_cognition_profile.py` post-migration, others)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` (existing, ticket-1 coverage — must keep
  passing unmodified; this is the file new eligibility/trace/defer-reason tests likely get added
  to)
- `tests/unit/strategic/test_score_normalization.py`,
  `tests/unit/strategic/test_adventure_route_materialization.py`,
  `tests/unit/strategic/test_enum_drift.py`,
  `tests/unit/strategic/test_threat_resolved_lock_release.py` (generalized, non-adventure-specific
  — comment-only `AdventureDecisionPhase` reference, no code dependency)
- `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py` (post-migration,
  count changes 3→2 call sites — see migration table)
- `tests/unit/systems/test_spawn_lock_condition.py` (post-migration)
- `tests/unit/observability/test_decision_trace.py`, `test_event_extractor_agency2.py`,
  `test_event_extractor_social_faction.py` (post-migration/comment-fix)
- `tests/unit/content/test_content_usage_matrix.py` (post-migration —
  `runtime_consumer_evidence` string check)

**Integration:**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` (post-migration)
- `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py` (retired — see
  migration table, decision required)
- `tests/integration/domains/test_fused_loop.py`
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/integration/content/test_resource_region_coverage_corpus.py` (comment-only reference)
- `tests/integration/test_scenario_feature_flag_defaults.py` (comment-only reference; re-verify
  `ENABLE_ADVENTURE_ROUTING` default-value assertions still make sense once the flag is inert —
  see investigation.md Risk #2)
- `tests/integration/kernel/test_snapshot_integrity.py`
- `tests/integration/pipeline/test_no_hidden_mutation.py`

**Arena-combat / perf:**
- `tests/perf/test_phase3_adventure_decision_budget.py` (post-migration, retargeted call site,
  likely re-baselined threshold — see migration table)

**Parity-adjacent (sanity re-run, no expected change):**
- `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  (STRAT-186)
- `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
  (STRAT-187)

## Per-File Migration Table (AC3/AC4)

**9 files with real code-level dependencies on `AdventureDecisionPhase`** (corrected from the
ticket's own "~5-6" estimate — see investigation.md Risk #3 for the full recount, including 6
comment-only files needing no code change):

1. **`tests/unit/observability/test_decision_trace.py`** —
   `test_adventure_decision_phase_wires_writer` (1 test). Depends on the decision-trace-writer
   Plan decision (investigation.md Risk #1). If ported: rewrite as
   `test_adventure_goal_scorer_wires_writer`, same mock-writer/patch pattern, calling
   `AdventureGoalScorer().score(entity, state, trace_writer=...)` (or wherever the writer call
   lands) instead of `AdventureDecisionPhase.apply(state, trace_writer=...)`. If not ported:
   replace with a guard asserting the divergence is the documented, intentional one (references
   the `intentional_divergences.md` entry), not a silent deletion.
2. **`tests/unit/domains/adventure/test_eligibility_cognition_profile.py`** — 4 tests
   (`test_eligibility_resolves_via_cognition_profile_not_role`,
   `test_hero_role_with_ineligible_profile_excluded`,
   `test_cognition_profile_id_missing_does_not_crash`,
   `test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`). None of
   `tests/unit/ai/goals/test_adventure_goal_scorer.py`'s existing tests exercise the real 3-tier
   resolution logic end-to-end (they all monkeypatch `_supports_adventure_routing` to a fixed
   bool via the `_eligible()` helper) — these 4 are not redundant and must migrate. Rewrite to
   import `_resolve_cognition_profile_id`/`_supports_adventure_routing` directly from
   `src.ai.goals.adventure_scorer` (their new home) and call them directly on a built entity +
   cache dict, instead of going through `AdventureDecisionPhase.apply(state)` and inspecting
   `update.entity_updates`. This is a *more* direct unit test of the exact logic under test, not
   a downgrade.
3. **`tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py`** —
   `test_three_production_call_sites_thread_state_argument`. AST-counts
   `evaluate_project_switch(...)` call sites across `AdventureDecisionPhase.apply()` (1 site) +
   `evaluate_strategic_intent()` (2 sites) = asserts exactly 3. After deletion, only
   `evaluate_strategic_intent()`'s 2 sites remain. Migration: drop the `AdventureDecisionPhase`
   half of the AST walk, change the asserted count from `3` to `2`, update the docstring/assert
   message accordingly. Must not silently loosen the guard (e.g. change to `>=`) — keep it exact.
4. **`tests/unit/systems/test_spawn_lock_condition.py`** — 6 calls across
   `TestLockEarlyRelease`/`TestLockHeldWhenThreatActive` and related classes, including the
   STRAT-236-cited `test_lock_released_when_hp_high_and_no_hostiles` (currently a near-vacuous
   `assert True` — see investigation.md). Migration: retarget each `AdventureDecisionPhase.apply(state)`
   call to `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)` (single-entity
   signature) and assert on the returned `StrategicUpdate.current_project_id_set`/lock-respecting
   behavior directly, which is a strictly stronger assertion than the current
   `assert True` placeholder — while keeping the migration itself scoped to "equivalent coverage,"
   not a broader quality pass. STRAT-236's `test_path` entry must be re-pointed to whichever test
   name survives this migration.
5. **`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`** — 2 tests,
   AST guard confirming `AdventureDecisionPhase.apply()`'s commit branch never constructs
   `StrategicUpdate(...)` directly, always going through `evaluate_project_switch()`. The
   guarded property (no adventure-specific direct-write bypass) still matters post-deletion,
   just at a different call site: `intelligence.py`'s `ADVENTURE_ROUTE` materialization branch
   (~lines 1440-1467) already falls through to the same shared
   `switch_up = StrategicIntelligenceSystem.evaluate_project_switch(...)` call every other
   `best_candidate.kind` branch uses (line ~1494) — confirmed by direct reading, no separate
   commit path exists for `ADVENTURE_ROUTE` today. Migration: retarget the AST walk at
   `evaluate_strategic_intent`'s source, scoped to (or noting) the `ADVENTURE_ROUTE` branch
   specifically, asserting it does not construct a `StrategicUpdate(` with
   `current_project_id_set=` directly and does reach the shared `evaluate_project_switch` call.
6. **`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`** — 5
   `AdventureDecisionPhase.apply(state)` calls (`test_filters_out_locked_projects` and 4 more,
   covering lock-respecting, threat-resolved bypass, and full decision-to-commit flow). Migration:
   retarget each to `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)` (or
   `fused_strategic_pass(state, StateUpdate(), cadence=None)` for the whole-state variant where
   the original test iterated multiple entities), asserting on the resulting
   `StrategicUpdate`/`StateUpdate` shape. This is the largest single migration in this ticket —
   the tests currently assert against `update.entity_updates` (an `AdventureDecisionPhase`-only
   return shape); the new call path returns a single entity's `StrategicUpdate` from
   `evaluate_strategic_intent()`, which is a different but equivalent-purpose shape (asserts on
   `current_project_id_set`/`projects_add_or_update` instead).
7. **`tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`** — entire
   24-test file's premise (diff two coexisting decision paths) disappears once one path is
   deleted; it cannot be "migrated" like the others. **Recommendation: delete the file**, since
   (a) it was explicitly transitional scaffolding per the design doc's own §7 step 2 framing
   ("surfaces normalization miscalibration before it's live" — a pre-cutover verification tool,
   not intended as permanent regression coverage), and (b) STRAT-253 (its parity-ledger entry)
   needs a `status`/`text` update regardless of whether the file survives, since its own `text`
   narrates "the live path... and... the not-yet-wired path" as a present-tense two-path
   situation that stops being true either way. **Before deleting, port one specific assertion
   that guards a real, independently-valuable defect class**: the raw-score-vs-utility
   separation covered by `test_shadow_diff_report_separates_raw_score_from_utility_mismatches`
   (Step 4/AC3 of ticket 3's own scope) guards the exact scale-mismatch bug shape design doc §4
   describes — this property doesn't need two paths to verify and should live on as a standalone
   regression test in `tests/unit/strategic/test_adventure_route_materialization.py` (which
   already exists and already tests this exact materialization branch, per STRAT-252's
   `v2_evidence`) rather than disappearing with the rest of the shadow file. Flag this specific
   disposition decision for Plan to ratify explicitly (delete file + port 1 assertion), not
   silently execute.
8. **`tests/perf/test_phase3_adventure_decision_budget.py`** —
   `test_phase3_adventure_decision_perf_budget`, currently benchmarks
   `AdventureDecisionPhase.apply(state)` over 105 entities against a 70ms budget (already
   re-baselined once before, per the file's own comment history — establishing precedent that
   re-baselining on a call-path change is normal, not scope creep). Migration: retarget to
   `AdventureGoalScorer().score(entity, state)` looped over the same 105 entities (isolating
   adventure-scoring cost specifically, the fairest analog to the old phase's per-tick loop cost)
   rather than the much broader `evaluate_strategic_intent()` (which includes tiers 1-4, unrelated
   to adventure routing specifically and would conflate budgets). **Do not assume the existing
   70ms threshold transfers unchanged** — remeasure under the new call path and set the budget
   from the real measurement, same discipline the file's own prior 5ms→70ms rebaseline used.
9. **`tests/unit/observability/test_event_extractor_agency2.py`** —
   `test_defer_property_name_constant_matches_phase_and_extractor` (`TestAntiDriftGuards` class),
   currently `inspect.getsource(phase_mod.AdventureDecisionPhase.apply)` and asserts
   `"last_defer_reason"` appears in its source. **Directly entangled with investigation.md Risk
   #0** (the `last_defer_reason`/`defer_with_reason` event gap) — this guard cannot be
   meaningfully migrated until Plan decides where (if anywhere) the `last_defer_reason`
   property-write lands in the new path. If ported: retarget
   `inspect.getsource(...)` at wherever the write now lives (likely
   `AdventureGoalScorer.score()`'s `DEFER_WITH_REASON` branch, or the tier-5 caller). If not
   ported: this guard must fail loudly (not be silently deleted) until the divergence is recorded
   — do not leave `defer_with_reason` event emission silently dead with no test noticing.

**6 comment-only files, no code change required** (references to `AdventureDecisionPhase` exist
only in docstrings/comments, confirmed via `grep` context read): `test_craft_upgrade_execution.py`,
`test_threat_resolved_lock_release.py`, `test_event_extractor_social_faction.py`,
`test_resource_region_coverage_corpus.py`, `test_scenario_feature_flag_defaults.py`,
`test_content_usage_matrix.py` (this last one is comment-only for the docstring reference at line
209, but line 222's `assert "AdventureDecisionPhase" in cognition_entry.runtime_consumer_evidence`
**is** a real code dependency — update this assertion to check for the new runtime consumer name
once `docs`/content metadata `runtime_consumer_evidence` string is updated to reference
`AdventureGoalScorer` instead).

## New Tests Required

- **`test_pipeline_module_has_no_adventure_decision_phase_reference`** — architecture guard
  (unit). Verifies `"AdventureDecisionPhase"` does not appear anywhere in
  `inspect.getsource(src.engine.pipeline)` (stronger than a one-off manual grep — a permanent
  regression guard). Lives in `tests/unit/systems/` or alongside the routing-guard tests in
  `tests/unit/domains/adventure/`.
- **`test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source`** —
  architecture guard (unit). Not literally comparable to deleted source post-deletion, so
  implemented as: assert `_resolve_cognition_profile_id`/`_supports_adventure_routing` exist in
  `src.ai.goals.adventure_scorer`, have the identical signature (`inspect.signature`), and the
  existing behavioral tests (item 2 above) pass unchanged — "byte-identical internals" is
  ultimately proven by behavior parity, not textual diffing, since the functions physically move
  files.
- **`test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase`** — doc/parity guard
  (unit), mirrors `test_content_usage_matrix.py`'s existing pattern of asserting on ledger-adjacent
  string content. Loads `docs/parity_ledger/strategic_cognition.yaml`, finds the `STRAT-236` entry,
  asserts `"AdventureDecisionPhase"` and `"phase.py:129"` (or equivalent stale line citation) do
  not appear in its `v2_evidence`.
- **`test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase`** — doc
  guard (unit). Reads `docs/simulation/domains/adventure_contract.md`, asserts the "Engine Phase"
  section text does not contain `"AdventureDecisionPhase"`.
- Whatever concrete test(s) Plan selects for the Risk #0 (`last_defer_reason`) and Risk #1
  (decision-trace-writer) resolutions — not named here since the resolution itself (port vs.
  document-as-divergence) is an open Plan decision, not one this investigation makes unilaterally.

## Scoped Pytest Commands

```
pytest tests/unit/domains/adventure/ tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py tests/unit/strategic/test_threat_resolved_lock_release.py tests/unit/systems/test_spawn_lock_condition.py tests/unit/observability/test_decision_trace.py tests/unit/observability/test_event_extractor_agency2.py tests/unit/observability/test_event_extractor_social_faction.py tests/unit/content/test_content_usage_matrix.py tests/integration/domains/adventure/ tests/integration/domains/test_fused_loop.py tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py tests/integration/content/test_resource_region_coverage_corpus.py tests/integration/test_scenario_feature_flag_defaults.py tests/integration/kernel/test_snapshot_integrity.py tests/integration/pipeline/test_no_hidden_mutation.py tests/perf/test_phase3_adventure_decision_budget.py -v
```

Post-cutover SimQ re-check (design doc §7 step 4 obligation, discharged by this ticket per
investigation.md's resolution — not part of the main scoped regression run above, run separately
in Verify):

```
pytest tests/simulation_quality/test_grade_regression.py -k "simq_routing_test or hero_guild_routing" -m "not slow" -q
```

## Anti-Drift Test Guards

- `test_pipeline_module_has_no_adventure_decision_phase_reference` (above) — catches any future
  reintroduction of the deleted phase.
- `test_three_production_call_sites_thread_state_argument` (migrated, count now 2) — catches a
  new `evaluate_project_switch()` call site silently forgetting to thread `state`, which would
  silently break STRAT-236's threat-resolved early-release for that new site.
- `test_apply_commit_branch_does_not_construct_strategic_update_directly` (migrated to target the
  `ADVENTURE_ROUTE` materialization branch in `intelligence.py`) — catches a future edit
  reintroducing a direct, arbiter-bypassing `current_project_id_set` write specifically for
  adventure routing, the exact defect class `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`
  fixed once already.
- Whichever test resolves Risk #0/#1 — must fail loudly (not silently pass or silently vanish) if
  a future edit to `AdventureGoalScorer.score()` drops decision-trace-writer or
  `last_defer_reason` wiring after this ticket adds it (or, if the divergence is accepted instead,
  must fail loudly if someone re-adds the wiring without updating the recorded divergence).
- Post-cutover SimQ re-check (above) — catches a *new* COGNITION/AGENCY-pillar regression
  introduced by this ticket's specific deletion, distinct from (and not to be confused with) the
  pre-existing, already-tracked drift `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`
  owns. If this re-check shows *new* failures beyond that ticket's already-disclosed 4 items,
  that is new information to report truthfully, not to silently fold into the existing follow-up
  ticket's scope.
