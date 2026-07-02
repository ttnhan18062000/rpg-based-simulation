---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-INFORMATION
phase: open
date: 2026-07-02
tags: [simulation_quality, information, belief, worldbuilder, feature_flag]
---

# TCK-20260702-SIMQ-UPLIFT2-INFORMATION

## Title
Activate INFORMATION pillar: enable belief assimilation + seed InformationSourceProfiles in urban_political

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
INFORMATION pillar grades C across all 30 calibration runs due to a dual gate:
(1) `ENABLE_BELIEF_ASSIMILATION=OFF` in `src/domains/optimization/feature_flags.py:18`
    → `InformationBeliefPhase` never runs (`src/engine/pipeline.py:152`)
(2) `AuthoritativeState.information_source_profiles = []` in all calibration worlds
    → even with the flag ON, no sources exist to query

Both gates must be lifted together to produce `belief_assimilated` / `lead_certainty_updated` events.

Fix: enable `ENABLE_BELIEF_ASSIMILATION=ON` in the `urban_political` calibration profile YAML,
and add two `InformationSourceProfile` entries to the `urban_political` world spec:
- A **town notice board** (`source_kind=GUIDE`, broad/low-accuracy public info)
- A **merchant rumour network** (tied to the existing `traveling_merchant` entity, `source_kind=TRAVELER`,
  trade-scoped, medium accuracy)

## Scope
1. Investigate: confirm how `information_source_profiles` is loaded into `AuthoritativeState` at
   compile time. Check `WorldAssemblyResolver`, `WorldCompiler`, and the world YAML for
   `urban_political` to understand where profiles are declared.
2. Schema: if `InformationSourceProfile` entries are not already declarable in world YAML, add the
   serialization path (world YAML → compile → `AuthoritativeState.information_source_profiles`).
3. World content: add two `InformationSourceProfile` entries to `urban_political` world spec:
   ```
   Profile 1 — town notice board:
     source_id: "town_notice_board"
     source_kind: "guide"           # InformationSourceKind.GUIDE
     knowledge_scopes: ["danger_rating", "material_source"]
     accuracy: 0.4
     freshness: 0.6
     bias: 0.1
     cost_gold: 0
     max_answers_per_query: 2

   Profile 2 — merchant rumour network:
     source_id: "traveling_merchant_rumors"
     source_kind: "traveler"        # InformationSourceKind.TRAVELER
     knowledge_scopes: ["material_source", "recipe_definition"]
     accuracy: 0.65
     freshness: 0.8
     bias: 0.2
     cost_gold: 5
     max_answers_per_query: 3
   ```
4. Feature flag: add `ENABLE_BELIEF_ASSIMILATION: "ON"` to
   `config/simulation_quality/profiles/urban_political.yaml` (same pattern as `ENABLE_SOCIAL_COOPERATION`
   added in TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO). Confirm `calibrate_simq.py` calls
   `_load_profile_feature_flags()` which already handles this injection.
5. Calibrate: re-run all `urban_political_*` scenarios; update `grade_anchors.json` for INFORMATION
   grade changes; verify 0 regressions elsewhere.
6. Update `docs/simulation_quality/event_type_coverage.md` with confirmed `calibration_hits` for
   `belief_assimilated`, `lead_certainty_updated`, `paid_information_transaction`.
7. Update parity ledger: `docs/parity_ledger/social_narrative.yaml` or `infrastructure.yaml` —
   add entry for INFORMATION pillar activation via belief assimilation.

## Out of Scope
- Activating INFORMATION in any world other than `urban_political` this ticket
- Adding new `InformationSourceKind` enum values (use existing: GUIDE, GUILD, BLACKSMITH, TRAVELER)
- Changing INFORMATION scoring weights
- Implementing a full information marketplace or NPC query-response loop (the phase already exists)

## Acceptance Criteria
- [ ] `ENABLE_BELIEF_ASSIMILATION=ON` injected for all `urban_political_*` calibration runs
- [ ] `AuthoritativeState.information_source_profiles` contains ≥2 profiles after compilation
      of `urban_political`
- [ ] At least one of `belief_assimilated` or `lead_certainty_updated` has `calibration_hits > 0`
      in at least one `urban_political_*` run
- [ ] `make evaluate --dry-run` exits 0 after anchors updated (0 regressions)
- [ ] `docs/simulation_quality/event_type_coverage.md` updated with confirmed hits
- [ ] Parity ledger updated

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — confirmed INFORMATION root cause (c3): dual-gate; deferred follow-up defined here
- TCK-20260702-SIMQ-UPLIFT2-FACTION — sibling ticket; both activate in urban_political

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — INFORMATION=C across all 30 runs
- `docs/audits/D20_simq_integration.md` §SimQ Uplift Batch — dual-gate follow-up noted
- `docs/simulation_quality/event_type_coverage.md` — `belief_assimilated`, `lead_certainty_updated` calibration_hits=0

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` — INFORMATION Deferral section

## Related Code Areas
- `src/domains/information/schema.py:24` — `InformationSourceProfile` dataclass (source_id, source_kind, knowledge_scopes, accuracy, freshness, bias, cost_gold, max_answers_per_query)
- `src/domains/information/schema.py:16` — `InformationSourceKind` enum: GUIDE, GUILD, BLACKSMITH, TRAVELER
- `src/domains/information/phase.py:15` — `InformationBeliefPhase.apply(state, source_profiles, …)`
- `src/domains/information/router.py:32` — router accepts `List[InformationSourceProfile]`
- `src/engine/pipeline.py:152` — `ENABLE_BELIEF_ASSIMILATION` gate for `InformationBeliefPhase`
- `src/domains/optimization/feature_flags.py:18` — `ENABLE_BELIEF_ASSIMILATION: FeatureMode.OFF`
- `src/core/state.py:1145` — `AuthoritativeState.information_source_profiles: List[Any]`
- `config/simulation_quality/profiles/urban_political.yaml` — calibration feature flag profile
- `tools/calibrate_simq.py` — `_load_profile_feature_flags()` injects flag into engine state
- `data/worlds/urban_political/` — world spec where profiles must be declared

## Assumptions / Open Questions
- UQ-1: How are `information_source_profiles` loaded into `AuthoritativeState` at compile time?
  Is there already a world YAML key for this, or does it need a new compiler/resolver code path?
  Check `WorldAssemblyResolver` and `WorldCompiler` for any `information_source_profiles` handling.
- UQ-2: Do the `knowledge_scopes` values need to match an enum, or are they free-form strings?
  Check `InformationBeliefPhase.apply()` to see how `knowledge_scopes` is used during query routing.
- UQ-3: Is `InformationBeliefPhase` already wired to emit `belief_assimilated` on every tick the
  phase runs, or only when a query is answered? Confirm the exact emission condition.

## Implementation Notes
Root cause from SOCIAL-ZERO investigation:
- Dual gate prevents ANY INFORMATION events: flag OFF means the phase never runs; even with flag ON,
  `state.information_source_profiles = []` means no source can answer queries.
- Fix pattern mirrors SOCIAL-ZERO: inject flag via profile YAML + add world-spec content.
- `_load_profile_feature_flags()` already exists in `calibrate_simq.py` and handles flag injection —
  no new tooling code needed, just add `ENABLE_BELIEF_ASSIMILATION: "ON"` to the profile YAML.
- The `InformationBeliefPhase` at `src/engine/pipeline.py:152` reads `source_profiles` from state
  directly — seeding them at compile time is sufficient.

## Test Summary
- Unit test: `InformationBeliefPhase.apply()` with a non-empty `source_profiles` list and flag ON
  produces at least one `belief_assimilated` event in a minimal scenario.
- Regression: existing worlds with `information_source_profiles=[]` still produce 0 INFORMATION events
  (confirming the gate-behavior is preserved for other worlds).
- Calibration: at least one `urban_political_*` run shows `calibration_hits > 0` for INFORMATION events.
- `make evaluate --dry-run` passes (0 regressions).

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
