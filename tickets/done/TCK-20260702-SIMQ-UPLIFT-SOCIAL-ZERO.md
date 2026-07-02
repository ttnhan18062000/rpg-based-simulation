---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO
phase: done
date: 2026-07-02
tags: [simulation_quality, faction, social, information, emission, diagnostic]
---

# TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO

## Title
Investigate and fix zero-activation of FACTION / SOCIAL / INFORMATION pillars across entire calibration corpus

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
FACTION, SOCIAL, and INFORMATION pillar scores show **0 calibration_hits across all 25 calibration runs** — every world (sandbox_world, urban_political, dungeon_crawl, frontier, highland, wilderness, swamp), every seed, every tick count including 2000t. These pillars always grade C with raw_score=0.0, event_count=0.

This is not a world-specific gap. Per `docs/simulation_quality/event_type_coverage.md`, 0 engine_emission_gaps and 0 translation_gaps were declared as of 2026-07-01 — the scorers and EventExtractor emitters are wired. Yet no calibration run has ever scored a FACTION, SOCIAL, or INFORMATION event. The root cause is that the underlying **engine-level mechanics** (diplomatic activity, contract negotiation, cooperation decisions, information purchase, belief formation) either do not trigger in practice or do not pass through the emission path at sufficient rate to register in quality_scores.jsonl.

## Scope
1. Confirm root cause by running a diagnostic calibration (200–500t) on sandbox_world or urban_political with DEBUG observability and scanning the raw event log for event_types: `diplomatic_transition`, `faction_tension_delta`, `cooperation_event`, `social_memory_created`, `contract_offer_created`, `contract_completed`, `belief_assimilated`, `lead_certainty_updated`.
2. Determine whether the gap is:
   - (a) Events fire at the engine level but are not being emitted by EventExtractor
   - (b) Events are emitted and translated but scored at 0 due to weight misconfiguration
   - (c) The underlying engine mechanics never trigger (factions passive, no contract gameplay, no NPC cooperation)
3. Fix the identified gap: if (a), repair the EventExtractor emission path. If (b), fix the weights. If (c), determine which worlds are capable of hosting this activity and what configuration unlocks it, then propose the minimal world spec or engine activation change.
4. Verify: at least one of FACTION / SOCIAL / INFORMATION scores ≥1 calibration_hit in ≥1 world at ≥1 tick count post-fix.
5. Update `docs/simulation_quality/event_type_coverage.md` with confirmed calibration_hits.

## Out of Scope
- Achieving A or B grade on any of these pillars in this ticket (grade improvement is a follow-up)
- Changing the scoring weight configuration unless (b) is confirmed
- The AGENCY routing-gate gap (separate; tracked under P0-A follow-up)

## Acceptance Criteria
- [x] Diagnostic run confirms whether engine-level events for FACTION/SOCIAL/INFORMATION actually fire (with evidence from observability log or structured diagnostic output)
- [x] Root cause classified as (a), (b), or (c) with supporting evidence in investigation.md
- [x] Fix implemented and verified: ≥1 calibration run shows non-zero event_count for at least one of the three pillars (SOCIAL: 1891 events, grade S in urban_political_seed42_500t)
- [x] `docs/simulation_quality/event_type_coverage.md` updated with revised calibration_hits
- [x] If root cause is (c) (engine mechanics inactive), document which worlds and configurations would activate the mechanics, and open a follow-up ticket for engine-level enablement if scope exceeds this ticket

## Related Tickets
- TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION — added FactionScorer and SocialScorer emitters (declared as fixing emission gap)
- TCK-20260701-SIMQ-EMIT-SOCIAL2 — closed remaining SOCIAL/FACTION/INFORMATION stubs
- TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS — added InformationScorer emitters
- TCK-20260702-SIMQ-EVAL-MATRIX — produced the 25-run calibration corpus revealing zero-activation

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` — §1.1 table: all FACTION/SOCIAL/INFORMATION events show calibration_hits=0
- `docs/simulation_quality/quality_scoring_contract.md` — §5 (SOCIAL), §7 (FACTION), §9 (INFORMATION) scorer contracts
- `docs/plans/audit_fix_plan.md` — Finding 1: "Systemic C ceiling on 5 pillars is confirmed engine-structural"

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `src/simulation_quality/scorers/social.py` — SocialScorer, EVENT_TYPES: cooperation_event, group_joined, contract_*, reputation_delta, social_memory_created
- `src/simulation_quality/scorers/faction.py` — FactionScorer, EVENT_TYPES: diplomatic_transition, alliance_proposed, alliance_accepted, war_declared, military_conflict_resolved, territory_ownership_changed, resource_seized, faction_tension_delta, faction_extinct
- `src/simulation_quality/scorers/information.py` — InformationScorer
- `src/systems/event_extractor/phase.py` — EventExtractor emission path for all three pillars
- `src/simulation_quality/quality_hub.py` — _translate() routing table
- `data/calibration/*/quality_scores.jsonl` — zero rows for FACTION/SOCIAL/INFORMATION in all 25 runs

## Assumptions / Open Questions
- **AQ1**: Do diplomatic_transition and faction_tension_delta events appear anywhere in raw observability output for worlds with multiple factions (dungeon_crawl has 16 factions, urban_political has multiple)? Unknown until diagnostic.
- **AQ2**: Are contracts and cooperation decisions behaviorally available to NPC agents in all worlds, or gated behind a feature flag or specific NPC class?
- **AQ3**: Does the fix require world spec changes (e.g., adding inter-faction tension triggers), engine mechanic activation, or EventExtractor repair?

## Implementation Notes

Root cause confirmed as (c): engine mechanics never triggered. Three independent sub-causes:

**SOCIAL (c2 — resolved):**
- `ENABLE_SOCIAL_COOPERATION=OFF` by default in `FeatureFlagManager`. CooperationPhase never ran.
- Fix: added `feature_flags: ENABLE_SOCIAL_COOPERATION: "ON"` to `config/simulation_quality/profiles/urban_political.yaml`.
- Added `_load_profile_feature_flags()` to `tools/calibrate_simq.py` to read the `feature_flags:` block from the scoring profile YAML and inject into `state.feature_flags` before engine startup, with env vars as higher-priority override.
- **Critical bug found and fixed:** `ApplyPath.apply_generation()` in `src/engine/apply.py` reconstructed `AuthoritativeState` each tick without passing `feature_flags`, silently dropping all overrides after tick 0. Added `feature_flags=dict(getattr(prior_state, "feature_flags", None) or {})` to carry the field across ticks.
- **Serialization bug found and fixed:** `CooperationPhase` stored a raw `CooperationDecisionResult` object in `property_updates["last_cooperation_decision"]`, which leaked into `entity.identity.properties` via `IdentityPatch` and broke `CanonicalStateHasher` JSON serialization. Fixed by storing `decision.selected_posture.value` (a string) instead — `EventExtractor` only checks `is not None`.
- Result: `cooperation_event` fires 1657 times in urban_political_seed42_500t. SOCIAL grade: C → S.
- `stagnation_window=100` (detection_params.yaml) — confirmed safe: cooperation events fire at tick ~1 (well before tick 100), so dormancy penalty never fires.

**FACTION (c1 — deferred):**
- `WorldCompiler.compile()` does not construct `FactionState` objects from world spec. All factions start with `tension_level=0.0`, `territory=()`. `compute_transitions()` requires `pair_tension > 0.4` to fire. Never satisfied.
- Requires: (1) `FactionStateSpec` schema extension, (2) compiler code path to construct FactionState from spec, (3) world content seeding. Out of scope for this ticket.
- Follow-up ticket: extend WorldCompiler + WorldSpec, seed bandit_company/town_council tension_level=0.5 in urban_political world.

**INFORMATION (c3 — deferred):**
- Dual gate: `ENABLE_BELIEF_ASSIMILATION=OFF` AND `state.information_source_profiles=[]` in all calibration worlds. Enabling the flag alone produces no events.
- Follow-up ticket: add InformationSourceProfile to world spec, enable flag in calibration profile.

**stagnation_window (R4 check):** `stagnation_window=100` in detection_params.yaml. First cooperation event fires at tick ~1 (group-member entities in urban_political world). Gate not crossed → dormancy penalty never fires → positive scoring on first event. Safe.

## Test Summary
- Run diagnostic calibration (200–500t) with `SIM_OBS_MODE=DEBUG` on urban_political or sandbox_world; grep observability event log for FACTION/SOCIAL/INFORMATION event_types
- Post-fix: add or extend test in `tests/simulation_quality/` that asserts ≥1 FACTION or SOCIAL or INFORMATION event fires in a targeted scenario
- Verify `make evaluate --dry-run` still shows 0 regressions after anchors are updated

## Files Changed
- `config/simulation_quality/profiles/urban_political.yaml` — added `feature_flags: ENABLE_SOCIAL_COOPERATION: "ON"` block
- `tools/calibrate_simq.py` — added `_load_profile_feature_flags()`, patched `_run_engine()` to accept `extra_flags`, wired profile flags into engine state; refactored env-var injection to shared `_parse_flag_value()` helper
- `src/engine/apply.py` — carry `feature_flags` across ticks in `apply_generation()` (bug fix: field was silently dropped each tick)
- `src/domains/cooperation/phase.py` — store `decision.selected_posture.value` (string) instead of raw `CooperationDecisionResult` in `property_updates["last_cooperation_decision"]` (serialization bug fix)
- `tests/unit/domains/cooperation/test_cooperation_phase.py` — created; 3 tests: flag ON sets last_cooperation_decision, flag OFF skips, inactive entities produce no output
- `tests/simulation_quality/fixtures/grade_anchors.json` — updated `urban_political_seed42_500t` SOCIAL anchor from C → S
- `docs/simulation_quality/event_type_coverage.md` — updated cooperation_event calibration_hits to 1657, contract_expired_offer to 234; added last-updated note
- `staging_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` — added FACTION Deferral and INFORMATION Deferral sections

## Completion Summary
SOCIAL pillar activated in urban_political calibration by enabling ENABLE_SOCIAL_COOPERATION via profile YAML. Two engine bugs fixed: (1) apply_generation dropped feature_flags each tick, and (2) CooperationPhase stored a non-serializable object in property_updates. With both bugs fixed, cooperation_event fires 1657 times in urban_political_seed42_500t (SOCIAL grade C→S). FACTION and INFORMATION remain deferred — root causes documented with follow-up ticket scope defined. 76 regression tests pass. evaluate_simq --dry-run exits 0.
