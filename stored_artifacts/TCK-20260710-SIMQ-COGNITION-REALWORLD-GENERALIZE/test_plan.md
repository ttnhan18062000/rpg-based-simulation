---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE
artifact_type: test_plan
tags: [cognition, self-model, simulation-quality, calibration, investigation]
---

# Test Plan — TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE

This ticket is investigation-only (per its own Scope/Out of Scope). No engine code changed. The
tests below are (1) the regression surface this investigation's real-compute runs must not have
broken (verified via `make evaluate --dry-run` and targeted pytest, below), and (2) the tests a
follow-up engine-fix ticket should add, scoped directly from this investigation's root-caused
findings, so Plan/Implementer do not need to re-derive them.

## Regression Surface

Existing tests that must keep passing (none of these were modified by this investigation):

**Unit — cognition:**
- `tests/unit/cognition/test_phase2_self_model_phase.py` — dirty check, first-tick full assessment,
  death skip
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` — `KnowledgeModelService.assimilate()`
  fact/unknown merge logic (directly exercised, unmodified, by this investigation's evidence)
- `tests/unit/cognition/test_phase2_self_assessment_service.py`
- `tests/unit/cognition/test_information_seeking.py`

**Unit — information domain:**
- `tests/unit/domains/information/test_phase5_information_query_router.py` — router scope/sort
  logic (confirmed current behavior via direct read, not modified)
- `tests/unit/domains/information/test_phase5_information_intent_resolver.py` — resolver
  MOVE_TO/ASK_INFORMATION logic (confirmed current behavior via direct read, not modified)
- `tests/unit/domains/information/test_phase5_information_assimilation.py`
- `tests/unit/domains/information/test_phase5_information_response_normalizer.py`
- `tests/unit/domains/information/test_phase5_belief_route_impact.py`
- `tests/unit/observability/test_event_extractor_information2.py`

**Integration:**
- `tests/integration/domains/test_fused_loop.py` —
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` and its
  sibling `test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist`
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (`INFRA-262`'s guardrail — must
  keep passing since no shipped profile's feature flags changed)

**Simulation-quality / calibration:**
- `tests/simulation_quality/test_grade_regression.py` — anchors for `urban_political_seed{42,123,456}_{200,500,1000}t`
  and `unit_selfmodel_pilot_*` must be unaffected (no anchor was touched by this investigation)
- `tests/simulation_quality/test_cognition_scorer.py`, `test_information_scorer.py`

**World compilation:**
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[urban_political]`

## Verification Already Performed By This Investigation

- `make evaluate --dry-run` (full corpus, `tools/evaluate_simq.py --dry-run`): **710 pillars
  checked, 3 pre-existing regressions, 0 missing.** Confirmed via `git status`/`git diff --stat`
  that zero tracked files were modified before this run — the 3 regressions
  (`dungeon_crawl_seed42_200t` COMBAT/PROGRESSION, `urban_political_seed42_200t` PROGRESSION) are
  **pre-existing corpus drift, not caused by this investigation**. AC7 as literally written ("exits
  0 with 0 regressions") is not currently satisfiable without a separate fix to that pre-existing
  drift — flagged to Plan as an open decision (re-scope AC7 to "0 new regressions," or file the
  pre-existing drift as its own ticket first). See investigation.md's Risks section.
- Direct `WorldCompiler.compile()` calls (seeds 42/123/456) against
  `data/worlds/urban_political/resolved/world.resolved.yaml` — zero compiler warnings, confirms
  UQ-2.
- Real `calibrate_simq.py` calibration runs (200 ticks each, `data/runs/run_1783873719_5169` and
  `run_1783874217_5169` — not committed, ephemeral run dirs) with `ENABLE_SELF_MODEL_COGNITION=ON`
  (both alone via a probe profile, and combined with `ENABLE_BELIEF_ASSIMILATION=ON` via the shipped
  `urban_political` profile) — see investigation.md for full grade/event-count evidence.
- Direct reproduction of `InformationQueryRouter.route()` → `InformationIntentResolver.resolve()`
  against the real compiled state, across all 3 anchor seeds — confirms `intent=None`,
  seed-invariant.

No new pytest tests were added by this investigation itself (investigation-only ticket, no code
change to make regression-testable yet). The "New Tests Required" section below is scoped for the
follow-up engine-fix ticket this investigation recommends.

## New Tests Required (for the follow-up engine-fix ticket, not this one)

1. **`test_branch_b_query_routing_fails_silently_on_real_urban_political_state`**
   - Category: integration / regression-guard (should currently be an `xfail` or a documented
     failing-state test if added *before* the fix lands, or a `PASS` confirmation test *after*)
   - Verifies: `InformationQueryRouter.route()` + `InformationIntentResolver.resolve()` against the
     real compiled `urban_political` state (actor_id 23, seed 42) currently returns `intent=None`
     due to the affordability gate on the certainty-ranked-first paid candidate — this is the
     regression guard that would catch the follow-up fix accidentally not fixing the real-world
     case (only fixing a synthetic one).
   - Location: `tests/integration/domains/information/test_phase5_information_belief_phase.py` or a
     new `tests/integration/domains/information/test_phase5_branch_b_realworld.py`

2. **`test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`**
   - Category: unit
   - Verifies: when `InformationIntentResolver.resolve()` returns `None` for `candidates[0]`,
     `InformationBeliefPhase.apply()` (or `InformationQueryRouter`) tries `candidates[1]` before
     giving up for the tick — the fix behavior for finding (2)/(3) in investigation.md.
   - Location: `tests/unit/domains/information/test_phase5_information_query_router.py` or
     `tests/integration/domains/information/test_phase5_information_belief_phase.py`

3. **`test_intent_resolver_insufficient_gold_produces_signal_not_silent_none`**
   - Category: unit
   - Verifies: the affordability gate at `resolver.py:65-69` produces a structured signal (e.g. an
     `"insufficient_gold"`-shaped response consumable by `KnowledgeModelService.assimilate()`'s
     existing branch at `knowledge_model.py:67-70`) instead of a bare `None` — closes the dead-code
     gap where that branch has no producer today.
   - Location: `tests/unit/domains/information/test_phase5_information_intent_resolver.py`

4. **`test_event_extractor_emits_route_new_query_event`**
   - Category: unit
   - Verifies: `event_extractor.py` gains an extractor branch for
     `last_routed_query_subject`/`last_routed_query_tick` (currently absent — confirmed by direct
     read of `event_extractor.py:276-299`), so a successful Branch B routing action becomes visible
     to SimQ scoring at all.
   - Location: `tests/unit/observability/test_event_extractor_information2.py` (extend) or a new
     `test_event_extractor_branch_b_routing.py`

5. **`test_ask_information_intent_execution_closes_the_loop`**
   - Category: integration
   - Verifies: a successfully executed `ASK_INFORMATION` intent
     (`action_intent.py:127-141`) eventually produces an `InformationResponse`/
     `pending_information_responses`-equivalent entry that a later tick's `InformationBeliefPhase`
     Branch A can re-assimilate — currently the execution path only deducts gold and stops.
   - Location: `tests/integration/domains/information/test_phase5_information_belief_phase.py`

6. **`test_urban_political_selfmodel_cognition_isolated_grade_anchor`** (optional — only if Plan
   decides to formalize `_investigation_probe_urban_political_selfmodel_only.yaml` as a permanent
   fixture rather than deleting it)
   - Category: simulation-quality / grade-regression anchor
   - Verifies: `urban_political` with `ENABLE_SELF_MODEL_COGNITION=ON` (materialization-only probe
     profile) anchors at COGNITION=S, INFORMATION=C, matching this investigation's measured values
     (5610 `self_model_updated` events, 0 `belief_*` events) — would need a new
     `grade_anchors.json` key (e.g. `urban_political_selfmodel_probe_seed42_200t`) and its own
     calibration data directory if committed.
   - Location: `tests/simulation_quality/fixtures/grade_anchors.json` (new key, if adopted) +
     `tests/simulation_quality/test_grade_regression.py`

## Scoped Pytest Commands

```bash
# Regression surface for this investigation's touched subsystem (cognition + information domain)
pytest tests/unit/cognition/ tests/unit/domains/information/ -v

# Integration-level Branch A/B coexistence and cross-tick behavior
pytest tests/integration/domains/test_fused_loop.py tests/integration/domains/information/ -v

# Grade-regression anchors (fast tier only; do not add -m slow here)
pytest tests/simulation_quality/test_grade_regression.py -v -k "urban_political or unit_selfmodel_pilot"

# Feature-flag guardrail (confirms this investigation didn't accidentally leave a shipped-profile change)
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v

# Full corpus dry-run comparison (already run manually during this investigation; re-run before Plan closes)
python3 tools/evaluate_simq.py --dry-run
```

Never `pytest tests/` — scope stays within `tests/unit/cognition/`,
`tests/unit/domains/information/`, `tests/integration/domains/`, and
`tests/simulation_quality/`, matching the affected subsystems.

## Anti-Drift Test Guards

- `tests/integration/test_world_profile_feature_flag_guardrail.py` — already the guard against this
  investigation's own biggest anti-drift risk (accidentally leaving `ENABLE_SELF_MODEL_COGNITION`
  or `ENABLE_BELIEF_ASSIMILATION` ON in a shipped profile). Must be re-run as part of closing this
  ticket to prove `urban_political.yaml` itself was never touched.
- `tests/simulation_quality/test_grade_regression.py` — must show 0 anchor drift for
  `urban_political_*` and `unit_selfmodel_pilot_*` keys specifically (not just corpus-wide) since
  those are the two worlds this investigation's evidence depends on being stable.
- A follow-up engine-fix ticket implementing the "New Tests Required" fixes above must re-run
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` and
  confirm it still passes unmodified — the fix must not require changing the hand-built test's
  narrower, already-passing scenario, only extend coverage to the real-world case this investigation
  found broken.
- Do not let a future ticket "fix" the routing gap by simply changing the router's sort order
  (`router.py:103`) without also fixing the no-fallback (`phase.py`) and missing-event-mapping
  (`event_extractor.py`) issues — investigation.md's three-point root cause is compound; a
  single-point fix would likely still leave the routing half unscoreable even if resolution
  succeeds. A regression test asserting `event_extractor.py` emits something for a routed query
  (test 4 above) is the guard against exactly this partial-fix trap.
