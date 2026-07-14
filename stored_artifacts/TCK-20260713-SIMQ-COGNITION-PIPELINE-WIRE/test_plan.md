---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
artifact_type: test_plan
tags: [simulation-quality, cognition, information, self-model]
---

# Test Plan — TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

## Regression Surface

**Unit**
- `tests/unit/cognition/` — self-model materialization, must be unaffected by a new downstream
  call site.
- `tests/unit/domains/information/` (including
  `test_phase5_information_intent_resolver.py`, `test_phase5_information_query_router.py`) — Branch
  B routing/resolution logic itself is out of scope for this ticket; must stay green unmodified.
- `tests/unit/strategic/test_intents.py` — direct `ActionIntentAdapter.execute()` unit tests
  (MOVE_TO / BUY_ITEM / requirement-failure paths) — must keep passing byte-identical since this
  ticket does not touch `.execute()`'s internals.
- `tests/unit/observability/test_event_extractor_information2.py` — `route_new_query` event
  extraction, unrelated to the new call site but shares the same feature area.
- `tests/unit/domains/adventure/`, `tests/unit/strategic/test_classifier.py` — confirms the
  adventure-domain (`ObjectiveIntentResolver`) `ASK_INFORMATION` path stays byte-identical; this
  ticket adds a call site but must not change which branch of `execute()` any existing caller hits.

**Integration**
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — including
  `test_ask_information_intent_execution_closes_the_loop` (must pass **unmodified**, per Acceptance
  Criteria) and `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`.
- `tests/integration/domains/information/test_phase5_branch_b_realworld.py` — real
  `urban_political`-state routing regression (seeds 42/123/456).
- `tests/integration/domains/test_fused_loop.py` — including
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`, must pass
  unmodified (cross-tick-boundary anchor for Branch B).
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — confirms no *shipped* world
  profile turns on a gated flag; the new flag must not appear ON in any live-world-resolved profile
  (`expected_world_flag_state.json` fixture untouched).
- `tests/perf/test_phase5_information_belief_budget.py` — tick-budget regression for the
  information_belief phase; a new adjacent phase must not blow this budget when the flag is OFF
  (default state).

**Simulation-quality / calibration**
- `tests/simulation_quality/test_grade_regression.py` — specifically
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor` (existing probe,
  `urban_political_selfmodel_probe.yaml`) must remain unaffected — this ticket must not repurpose
  that specific probe file (see investigation.md's Risks section); the fast-anchor
  parametrized tests for the untouched corpus worlds must also stay green.
- `python3 tools/evaluate_simq.py --dry-run` — full-corpus 0-regression check with the new flag
  left at its default OFF state (Acceptance Criteria's explicit requirement).

**Architecture**
- `tests/architecture/test_phase_domain_permissions.py` — confirms no `TickPhase`-level permission
  change was introduced (this ticket's new phase is a `RESOLUTION`-internal sub-phase, not a new
  `TickPhase`); should be unaffected, but run to confirm no accidental drift.

## New Tests Required

1. **`test_action_intent_execution_phase_fires_in_real_tick_pipeline`**
   — Category: integration.
   — Verifies: constructs a real `AuthoritativeState` with an entity carrying an
   `UnknownFact`/`self_model.knowledge.unknowns` entry and a reachable `InformationSourceProfile`
   (mirroring `test_ask_information_intent_execution_closes_the_loop`'s setup, but driven through
   `AuthoritativeApplyPipeline.refine()` end-to-end, not direct `ActionIntentAdapter.execute()`
   invocation), with the new flag, `ENABLE_SELF_MODEL_COGNITION`, and `ENABLE_BELIEF_ASSIMILATION`
   all `ON` (via `state.feature_flags`). Asserts: the returned `StateUpdate`'s entity update for
   the actor carries `self_model_bundle_set` with the unknown resolved into `facts` (the
   `.execute()` postcondition) — proving the call fired through the pipeline, not just that
   `intent_results` was populated by `information_belief`.
   — Where: `tests/integration/domains/information/test_phase5_information_belief_phase.py` (new
   test function alongside the existing direct-invocation test) or a new
   `tests/integration/domains/information/test_action_intent_execution_phase.py` — implementer's
   call based on which keeps the file cohesive.

2. **`test_action_intent_execution_phase_off_by_default_is_a_noop`**
   — Category: integration / regression guard.
   — Verifies: the same real-pipeline setup as test 1, but with the new flag left unset /
   default (`OFF`) — asserts the entity's `self_model_bundle_set` is **not** populated by the new
   phase (Branch B's routed `ActionIntent` sits in `intent_results` but is never executed), proving
   the flag genuinely gates production reachability and the new phase is inert by default. This is
   the direct verification of Acceptance Criterion 4 at the unit/integration level (the
   `evaluate_simq.py --dry-run` sweep verifies it at the corpus level).
   — Where: same file as test 1.

3. **`test_action_intent_execution_phase_filters_non_action_intent_entries`**
   — Category: unit / architecture guard.
   — Verifies: the anti-drift hazard from investigation.md — an `EntityUpdate.intent_results` list
   containing a real `IntentResult` (the field's declared type, from `src/core/state.py:655`, e.g.
   as `economy.py`/`patches.py` construct) must **not** be passed to
   `ActionIntentAdapter.execute()` as if it were an `ActionIntent`. Construct an `EntityUpdate`
   with a mixed/`IntentResult`-only `intent_results` list and confirm the new phase either raises
   nothing / calls `.execute()` zero times (assert via `ActionIntentAdapter.get_traces()` being
   empty after `clear_traces()`), or filters correctly if both types are present together.
   — Where: wherever the new phase function/class lives, e.g.
   `tests/unit/engine/pipeline_phases/test_information_intent_execution.py` (new file, mirroring
   the `tests/unit/domains/information/` and `tests/engine/pipeline_phases/` naming pattern already
   used for other `run_phase` sub-phases).

4. **`test_action_intent_execution_phase_preserves_deterministic_entity_order`**
   — Category: unit / architecture guard.
   — Verifies: with multiple entities each carrying a routed `ActionIntent` in `intent_results` in
   the same tick, the new phase processes them in sorted entity-ID order (mirroring
   `ActionRoutingPhase.route()`'s `sorted(actors_with_tasks)` convention, `actions.py:108`) —
   assert via `ActionIntentAdapter.get_traces()` ordering after `clear_traces()`, or via a
   deterministic-replay double-run hash comparison if that harness is already available for phase
   tests.
   — Where: same file as test 3.

5. **Calibration probe fixture + grade-anchor test** (mirrors `urban_political_selfmodel_probe`'s
   existing pattern, per Acceptance Criterion 2).
   — Category: integration / calibration.
   — New profile file, e.g. `config/simulation_quality/profiles/
   urban_political_selfmodel_execution_probe.yaml` (do **not** repurpose the existing
   `urban_political_selfmodel_probe.yaml` — see investigation.md's Risks section for why), turning
   `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, and the new flag all `ON`.
   — New test, e.g. `test_urban_political_selfmodel_execution_isolated_grade_anchor` in
   `tests/simulation_quality/test_grade_regression.py`, asserting `COGNITION`/`INFORMATION` pillar
   grades for a real calibration run of this profile, plus a direct assertion that at least one
   `ActionIntentAdapter`-attributable event fired (via `ActionIntentAdapter.get_traces()` if the
   calibration harness exposes it in-process, or via a new/existing observability event emitted by
   the phase — implementer's call on the exact signal, but it must be something that could only be
   true if `.execute()` actually ran through the real `Kernel.tick_once()` loop, not merely that
   Branch B routed a query).
   — Where: `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml`
   (new), `tests/simulation_quality/test_grade_regression.py` (new test function),
   `tests/simulation_quality/fixtures/grade_anchors.json` (new key, generated from a real
   calibration run, not hand-authored — **must use the `{grade, score}` per-pillar schema
   `TCK-20260713-SIMQ-RAWSCORE-PERSIST` (same epic batch, done) introduced**, using
   `normalized_score`; a bare-grade-string entry will fail that ticket's independent score-tolerance
   assertion regardless of letter-grade correctness).

6. **`test_new_flag_registered_in_feature_flag_manager`**
   — Category: unit / regression guard.
   — Verifies: the new flag name exists in `FeatureFlagManager()._flags` and defaults to
   `FeatureMode.OFF` — directly guards against the "flag silently no-ops because it was never
   registered" failure mode identified in investigation.md as the most likely silent-failure path
   for this ticket.
   — Where: `tests/unit/domains/optimization/test_feature_flags.py` if it exists (check first,
   likely alongside the other flags' coverage), else a new small test module.

## Scoped Pytest Commands

```bash
# Core regression surface — information/cognition domain + the new phase's own tests
pytest tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/ \
  tests/unit/strategic/test_intents.py tests/unit/observability/test_event_extractor_information2.py \
  -q

# Adventure-domain byte-identical guard (confirms shared execute() branch untouched for the other caller)
pytest tests/unit/domains/adventure/ tests/unit/strategic/test_classifier.py -q

# Cross-tick-boundary + fused-loop anchor
pytest tests/integration/domains/test_fused_loop.py -q

# Shipped-profile guardrail (new flag must not leak into any live world profile)
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q

# Perf budget guard for the information_belief-adjacent pipeline section
pytest tests/perf/test_phase5_information_belief_budget.py -q

# New phase's own unit tests (path depends on implementer's chosen file location — update once known)
pytest tests/unit/engine/pipeline_phases/test_information_intent_execution.py -q

# Grade-anchor / calibration regression (existing + new probe)
pytest tests/simulation_quality/test_grade_regression.py -k "urban_political or unit_selfmodel_pilot" -q

# Architecture guard (no TickPhase permission drift)
pytest tests/architecture/test_phase_domain_permissions.py -q

# Full-corpus dry-run — flag left OFF, must show 0 regressions (Acceptance Criterion 4)
python3 tools/evaluate_simq.py --dry-run
```

Never run the unscoped `pytest tests/` — the domains above (`information`, `cognition`,
`adventure` byte-identical guard, pipeline architecture, simulation_quality calibration) are the
full relevant surface for this ticket.

## Anti-Drift Test Guards

- **Test 2** (`test_action_intent_execution_phase_off_by_default_is_a_noop`) is the primary guard
  against the single biggest risk in this ticket: a new engine phase that silently activates
  outside its flag gate. It must be added regardless of how the implementer structures the phase
  function.
- **Test 3** (`intent_results` type-filtering) guards against the pre-existing `IntentResult`
  vs. `ActionIntent` type-annotation mismatch in `EntityUpdate.intent_results`
  (`src/core/updates.py:638`) being silently exploited by a naive "iterate everything in
  `intent_results` and call `.execute()`" implementation — `economy.py`/`patches.py` construct real
  `IntentResult` objects in that same field for an unrelated purpose (resource-transfer outcomes).
  Without this guard, a future economy-domain change that also populates `intent_results` could
  crash or silently misbehave when this new phase runs.
- **The adventure-domain regression group** (`tests/unit/domains/adventure/`,
  `test_classifier.py`, plus `ObjectiveIntentResolver`'s `ASK_INFORMATION` byte-identical branch)
  guards against this ticket accidentally changing *which* entities' `ActionIntent`s reach
  `.execute()` — this ticket adds exactly one new call site (Branch B's routed intents), not a
  general-purpose intent-execution dispatcher that could pick up adventure-domain intents too.
- **The shipped-profile guardrail test** (`test_world_profile_feature_flag_guardrail.py`) is the
  test-level enforcement of the ticket's Out-of-Scope line ("Turning the new flag on in any shipped
  world profile"). Its `_GATED_FLAGS` tuple
  (`tests/integration/test_world_profile_feature_flag_guardrail.py:33`) is a hardcoded 3-name tuple
  that will **not** automatically include the new flag — if the implementer wants this specific
  guardrail mechanism (rather than relying solely on "no shipped profile sets it") to catch a
  future accidental shipped-profile activation, the tuple needs an explicit addition as part of
  this ticket's diff. Flag this decision explicitly in `plan.md` rather than silently skipping it.
- **`test_urban_political_selfmodel_cognition_isolated_grade_anchor`** (the *existing* probe test)
  passing **unmodified**, with its hardcoded `pillars["INFORMATION"]["event_count"] == 0` assertion
  still true, is itself an anti-drift guard: it proves the new work did not repurpose or mutate
  `urban_political_selfmodel_probe.yaml` in a way that would make Branch A/B start firing in that
  specific isolated-materialization probe.
- **Known pre-existing flaky signal, not this ticket's to fix:** `TCK-20260713-SIMQ-SCORE-CEILING-FIX`
  (same epic batch, done) recorded an environment-load-sensitive nondeterminism in COGNITION's
  self-model loop-detection, tracked separately as `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`
  (open). If the full `evaluate_simq.py --dry-run` sweep (flag OFF) flags a COGNITION delta, cross-check
  against that known signature (3 clean reproductions cited in that ticket's Completion Summary)
  before treating it as a regression this ticket introduced.
