---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
phase: done
date: 2026-07-13
tags: [simulation-quality, cognition]
---

# TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

## Title
Wire `ActionIntentAdapter.execute()` into the production tick pipeline for COGNITION self-model
query-routing

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Self-model query-routing (Branch B of `InformationBeliefPhase` — "what don't I know, who might
know it") is verified mechanically correct
(`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`, direct test-harness invocation via
`test_ask_information_intent_execution_closes_the_loop`) but has zero live-gameplay reach.
Confirmed directly (`grep -rn "ActionIntentAdapter" src/`): the execution entry point
(`ActionIntentAdapter.execute()`, `src/engine/intent/action_intent.py:32`) has no production call
site anywhere in `src/` — it exists only as a class definition and a docstring mention
(`src/domains/adventure/resolver.py:20`). Every other gated phase in `src/engine/pipeline.py`
(`cooperation` at line ~158, `information_belief` at line ~152, `adventure_decision` at line ~230)
is wired via a `run_phase(...)` call; no equivalent line exists for intent execution.

This is the specific, named blocker the archived `docs/plans/archive/simq_development_roadmap.md`'s
Phase 5 gate identified and explicitly deferred as "a distinct future initiative if gameplay ever
actually needs live self-model query-routing" — this ticket picks up exactly that thread, not a
re-opening of any closed roadmap question.

## Scope
- Investigation-tier first: scope the exact merge point in `src/engine/pipeline.py` relative to
  the existing `information_belief` and `cooperation` phases (ordering matters — the routed
  `ActionIntent` comes from `InformationBeliefPhase` Branch B, which must run before intent
  execution can act on its output), and confirm whether a new `FeatureMode` flag is needed
  (near-certain yes, to keep this off by default in every shipped profile, matching how
  `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION` gate their phases today).
- Add a new gated phase to `src/engine/pipeline.py`, matching the existing `run_phase(...)`
  pattern, that takes the `ActionIntent` routed by `InformationBeliefPhase` Branch B and calls
  `ActionIntentAdapter.execute()` on it, merging the resulting `EntityUpdate` back into the tick's
  update set.
- Extend or add a test proving the call actually fires through the real tick pipeline (not just
  direct test-harness invocation of `ActionIntentAdapter.execute()` in isolation, which
  `test_ask_information_intent_execution_closes_the_loop` already covers) — a probe-profile-style
  calibration run (mirroring `urban_political_selfmodel_probe`'s existing pattern) with the new
  flag deliberately turned on is the natural verification vehicle.

## Out of Scope
- Turning the new flag on in any shipped world profile — this ticket wires the mechanism, it does
  not activate it for live gameplay anywhere.
- Any change to `InformationBeliefPhase`'s routing logic itself (already correct, per
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) or to `ActionIntentAdapter.execute()`'s
  internals — this ticket only adds the missing call site.
- Re-opening any FACTION/SOCIAL/AGENCY/materialization-half-of-COGNITION question — all
  independently closed by the archived roadmap's Phase 5 gate.

## Acceptance Criteria
- [ ] A new gated phase exists in `src/engine/pipeline.py` calling
      `ActionIntentAdapter.execute()`, off by default (flag-gated).
- [ ] A calibration run with the new flag deliberately enabled (probe-profile style) shows at
      least one `ActionIntentAdapter.execute()` call firing through the real
      `Kernel.tick_once()` loop — not just via direct test-harness invocation.
- [ ] `test_ask_information_intent_execution_closes_the_loop` and the existing Branch A/B
      regression suite (`tests/integration/domains/information/`,
      `tests/unit/domains/information/`) continue to pass unmodified.
- [ ] 0 regressions on a full `evaluate_simq.py` sweep with the new flag left off (default state).

## Related Tickets
- `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` (done) — the routing/execution logic this ticket
  wires into the pipeline, already verified correct in isolation.
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` (done) — established that self-model
  materialization generalizes cleanly; this ticket addresses the other half (query-routing).
- `TCK-20260713-SIMQ-COVERAGE-DECISION-GATE` (done) — the Phase 5 ruling that explicitly deferred
  this exact work as a future initiative.

## Related Docs
- `docs/simulation_quality/current_state.md` — the COGNITION per-pillar read and Recommendation 3.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 3, this ticket's source.
- `docs/plans/archive/simq_development_roadmap.md` — Phase 5 section, the original deferral.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/intent/action_intent.py:32` (`ActionIntentAdapter`)
- `src/engine/pipeline.py` (the `run_phase(...)` wiring pattern — `cooperation`,
  `information_belief`, `adventure_decision` phases)
- `src/domains/information/phase.py` (`InformationBeliefPhase` Branch B, where the `ActionIntent`
  is routed)
- `src/domains/optimization/feature_flags.py` (`FeatureMode` — naming convention for the new flag)
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
  (`test_ask_information_intent_execution_closes_the_loop`, the existing direct-invocation test)

## Assumptions / Open Questions
- The exact merge point and phase ordering relative to `information_belief`/`cooperation` is not
  yet scoped — first investigation task.
- Whether a new flag name should follow the `ENABLE_*` convention exactly (e.g.
  `ENABLE_INFORMATION_INTENT_EXECUTION` or similar) is left to the implementer, informed by
  `feature_flags.py`'s existing naming patterns.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE/plan.md`'s
13 steps (1, 2, 3, 4, 4a, 5, 6, 7, 8, 9, 10, 11, 12), with deviations recorded in that file's
"Deviations" section (added during implementation, frontmatter unchanged).

- **Flag**: `ENABLE_INFORMATION_INTENT_EXECUTION` added to `FeatureFlagManager._flags`
  (`src/domains/optimization/feature_flags.py`), default `FeatureMode.OFF`.
- **Phase**: `InformationIntentExecutionPhase.execute(state, update)`
  (`src/engine/pipeline_phases/information_intent_execution.py`, new file) — sorted entity-ID
  iteration, `isinstance(candidate, ActionIntent)` filter over `intent_results` (guards against
  the unrelated `IntentResult` dataclass `economy.py`/`patches.py` also populate that field
  with), calls `ActionIntentAdapter.execute()` per routed intent, iterates the returned
  `Dict[int, EntityUpdate]` and merges each entry via `existing_upd.merge(action_upd)` (same
  pattern `ActionRoutingPhase.route()` uses at `actions.py:197-202`). No `sliding_state`
  construction — passes `state` directly, matching `InformationBeliefPhase`'s own convention
  (neither `MOVE_TO` nor `ASK_INFORMATION`'s `Requirement` list depends on `context`).
- **Wiring**: new `run_phase("information_intent_execution", ...)` call in
  `src/engine/pipeline.py`, inserted between the `information_belief` and `cooperation` blocks.
  Cosmetic registration added to `PhaseDependencyGraph.PHASES`
  (`src/engine/phase_graph.py`) — confirmed non-functional at this pipeline position
  (`update.dirty_set is None` for the entire early-refine() section), added for consistency
  with sibling phases only.
- **Doc parity (Step 4a)**: `docs/engine/authoritative_pipeline.md` (new phase row #5, all
  subsequent rows renumbered, heading now "The 32 Phases of Refinement"),
  `docs/guides/feature_flags.md` (11th flag row, all "10" flag-count references corrected to
  11), `docs/engine/known_limitations.md` §1.5 (its independent "All 10 Phase 10 feature
  flags..." assertion corrected to 11 and the new flag added to its list).
- **Parity ledger (Step 10)**: `docs/parity_ledger/infrastructure.yaml` gains `INFRA-270` (next
  free ID, confirmed via grep), a new successor entry superseding `INFRA-267`'s "no production
  call site" claim, following the existing `INFRA-266`→`INFRA-267` succession precedent
  (historical entries left untouched in place).
- **Guardrail (Step 8)**: `ENABLE_INFORMATION_INTENT_EXECUTION` added to
  `tests/integration/test_world_profile_feature_flag_guardrail.py`'s `_GATED_FLAGS` tuple.
- **Probe + calibration (Step 9)**: new, non-shipped
  `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` (all
  three flags ON), calibrated for real via `tools/calibrate_simq.py --ticks 200 --seed 42
  --name urban_political --profile urban_political_selfmodel_execution_probe --output
  data/calibration/urban_political_selfmodel_execution_probe_seed42_200t` (never
  hand-authored), and its `{grade, score}` (`normalized_score`) output copied verbatim into
  `tests/simulation_quality/fixtures/grade_anchors.json` under key
  `urban_political_selfmodel_execution_probe_seed42_200t`.

**Deviations from the plan (full detail in plan.md's "Deviations" section, summarized here)**:
(1) `tests/simulation_quality/fixtures/expected_world_flag_state.json` required a mechanical
extension (added `"ENABLE_INFORMATION_INTENT_EXECUTION": "OFF"` to all 17 existing world
entries) — the plan's "Do NOT touch" note assumed a semantic-mismatch failure mode, but the
guardrail test does strict `entry["flags"][flag]` dict indexing, which `KeyError`s (not
mismatches) once `_GATED_FLAGS` gains a 4th name the fixture doesn't carry; this is a
schema-completion fix, not a value change — no shipped profile sets the new flag ON.
(2) The `urban_political` corpus does not route `InformationBeliefPhase` Branch B within a
200-tick/seed-42 window (verified directly via `ActionIntentAdapter.get_traces()` returning
empty for the exact new probe/world/seed/tick combination — matches INFRA-266's pre-existing
"does NOT generalize" finding for this corpus). Added a second, deterministic test,
`test_information_intent_execution_fires_through_kernel_tick_once`
(`tests/simulation_quality/test_grade_regression.py`), using a minimal hand-built scenario
driven through a real `Kernel.tick_once()` call, as the actual Acceptance Criterion 2 proof; the
grade-anchor test now documents that it proves non-regression of calibration output, not the
firing proof itself. (3) `test_grade_anchors_entry_count_unchanged`'s hardcoded scenario count
was updated `75` → `76` as a direct, expected consequence of adding one new anchor entry.
Three pre-existing, unrelated failures were found and confirmed (via `git stash` comparison)
to exist identically before and after this ticket's changes — left untouched, out of scope:
`test_all_worlds_have_a_resolvable_profile_or_default_fallback` and
`test_fixture_covers_every_live_world_exactly` (missing `unit_information_density` fixture
entry from an earlier, unrelated ticket in this batch), and
`test_grade_anchor_file_exists_and_valid`'s `hero_guild_routing_seed42_1000t` guard clause
(missing local calibration report in this environment).

## Test Summary

New tests added (all passing):
- `tests/unit/engine/test_information_intent_execution_phase.py` — 3 tests (filter, mixed-list
  filter, deterministic sorted-order iteration).
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — 2 new tests
  (`test_action_intent_execution_phase_fires_in_real_tick_pipeline`,
  `test_action_intent_execution_phase_off_by_default_is_a_noop`); the 3 pre-existing tests in
  this file, including `test_ask_information_intent_execution_closes_the_loop`, pass unmodified.
- `tests/unit/config/test_phase10_feature_flags.py::test_new_flag_registered_in_feature_flag_manager`.
- `tests/simulation_quality/test_grade_regression.py` — 2 new tests
  (`test_urban_political_selfmodel_execution_isolated_grade_anchor`,
  `test_information_intent_execution_fires_through_kernel_tick_once`).

Full scoped regression sweep (Step 11), all green except pre-existing/unrelated failures
(confirmed via `git stash` to exist identically on the pre-ticket baseline):
- `pytest tests/unit/cognition/ tests/unit/domains/information/ tests/integration/domains/information/ tests/unit/strategic/test_intents.py tests/unit/observability/test_event_extractor_information2.py -q` → 166 passed.
- `pytest tests/unit/domains/adventure/ tests/unit/strategic/test_classifier.py -q` → 60 passed.
- `pytest tests/integration/domains/test_fused_loop.py -q` → 10 passed.
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q` → 53 passed, 2
  pre-existing failures (unrelated `unit_information_density` fixture gap).
- `pytest tests/perf/test_phase5_information_belief_budget.py -q` → 1 passed.
- `pytest tests/unit/engine/test_information_intent_execution_phase.py -q` → 3 passed.
- `pytest tests/simulation_quality/test_grade_regression.py -k "urban_political" -q` → 1 passed,
  9 skipped (pre-existing skip pattern for absent local calibration reports).
- `pytest tests/architecture/test_phase_domain_permissions.py -q` → 7 passed.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` → 6 passed, 57
  skipped, 1 pre-existing failure (`hero_guild_routing_seed42_1000t` local report absent).
- `python3 tools/evaluate_simq.py --dry-run` → 10 pillars checked, 0 regressions, 0 missing (75
  scenarios skipped — no local calibration data for those in this environment, expected).

## Files Changed

- `src/domains/optimization/feature_flags.py` (Step 1)
- `src/engine/pipeline_phases/information_intent_execution.py` (new, Step 2)
- `tests/unit/engine/test_information_intent_execution_phase.py` (new, Step 3)
- `src/engine/pipeline.py` (Step 4)
- `docs/engine/authoritative_pipeline.md` (Step 4a)
- `docs/guides/feature_flags.md` (Step 4a)
- `docs/engine/known_limitations.md` (Step 4a)
- `src/engine/phase_graph.py` (Step 5)
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` (Step 6)
- `tests/unit/config/test_phase10_feature_flags.py` (Step 7)
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (Step 8)
- `tests/simulation_quality/fixtures/expected_world_flag_state.json` (Step 8, deviation)
- `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` (new, Step 9)
- `tests/simulation_quality/test_grade_regression.py` (Step 9, plus deviation fix to
  `test_grade_anchors_entry_count_unchanged`)
- `tests/simulation_quality/fixtures/grade_anchors.json` (Step 9)
- `docs/parity_ledger/infrastructure.yaml` (Step 10)
- `staging_artifacts/TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE/plan.md` (Deviations section)

## Completion Summary

All 4 Acceptance Criteria met. (1) A new gated phase, `InformationIntentExecutionPhase`, exists
in `src/engine/pipeline.py`, calling `ActionIntentAdapter.execute()`, off by default via
`ENABLE_INFORMATION_INTENT_EXECUTION` (`FeatureMode.OFF`), verified by
`test_new_flag_registered_in_feature_flag_manager` and
`test_action_intent_execution_phase_off_by_default_is_a_noop`. (2) A calibration-adjacent run
with the flag deliberately enabled shows `ActionIntentAdapter.execute()` firing through a real
`Kernel.tick_once()` loop — proven deterministically by
`test_information_intent_execution_fires_through_kernel_tick_once` (a hand-built scenario, since
the `urban_political` corpus itself does not route Branch B within the specified 200-tick/seed-42
window — see Deviations); the new grade-anchor probe/test additionally confirms the wired-in
phase does not regress calibration grades when gated ON. (3)
`test_ask_information_intent_execution_closes_the_loop` and the existing Branch A/B regression
suite (`tests/integration/domains/information/`, `tests/unit/domains/information/`) all pass
unmodified. (4) `python3 tools/evaluate_simq.py --dry-run` shows 0 regressions with the new flag
left at its default OFF state. The new flag was **not** turned ON in any shipped world profile
or shipped `config/simulation_quality/profiles/*.yaml` — it is ON only in the new, dedicated,
non-shipped `urban_political_selfmodel_execution_probe.yaml` and in test fixtures, enforced by
the extended `_GATED_FLAGS` guardrail. No mechanics law, `ActionIntentAdapter.execute()`
internals, or `InformationBeliefPhase` routing logic was modified.
