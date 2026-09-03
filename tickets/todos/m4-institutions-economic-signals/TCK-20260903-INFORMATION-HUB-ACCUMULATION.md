---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260903-INFORMATION-HUB-ACCUMULATION
phase: open
date: 2026-09-03
tags: [information, feature-flags, faction]
---

# TCK-20260903-INFORMATION-HUB-ACCUMULATION

## Title
Information hubs — knowledge accumulation and critical-information propagation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 41 — Information hubs: give InformationProviderState (Guides) a real knowledge-accumulation mechanism (e.g., increasing when a quest they assigned is reported back) and propagate 'critical' information City-to-City/City-to-Country. The M4 epic doc's premise that both feature flags are OFF is STALE: investigation confirms (direct read of feature_flags.py) ENABLE_BELIEF_ASSIMILATION now defaults ON (flipped by TCK-20260824-ROLLOUT-FLAG-DECISIONS) while ENABLE_INFORMATION_INTENT_EXECUTION remains OFF — no AC may assume both OFF. This is greenfield feature work (atlas marks idea 41 'Aspirational — design only'); InformationProviderState is frozen/immutable with no accumulation field today, so this is genuinely new mutation logic despite the atlas's 'no content risk' framing.

## Scope
- Add a real accumulation mechanism to InformationProviderState (or its typed update path) via a new typed field on StateUpdate.information_providers_update/merge(), following lead_contradiction.py's existing pattern (currently the only writer, only ever decrementing reliability_score).
- Trigger accumulation on a concrete event (e.g., a quest the Guide assigned being reported back).
- Implement City-to-City / City-to-Country propagation of 'critical' information using the EXISTING FactionState.territory/diplomatic_relations topology fields — no new topology type.
- Register any new gated behavior as a NEW flag in FeatureFlagManager._flags, defaulting OFF per DEV-002, with a test proving the flag-OFF path leaves information_providers/FactionState unchanged.
- State current flag reality explicitly in the ticket and any doc updates (BELIEF_ASSIMILATION ON, INFORMATION_INTENT_EXECUTION OFF).

## Out of Scope
- Any Conversation/entity-dialogue system — confirmed zero grep hits in src/; 'Guide-to-Guide exchange reusing Conversation' has nothing to reuse and must be reframed or explicitly scoped out.
- Any idea-66-dependent Place-model work (location_place_id) — propagation uses region/City-level FactionState.territory/diplomatic_relations, not a Place model.
- Redesigning InformationBeliefPhase's existing feature+content gating (ENABLE_BELIEF_ASSIMILATION AND non-empty pending_information_responses/self_model.knowledge.unknowns) beyond what's needed to read the new field.
- Repropagating the atlas's stale 'both flags OFF' premise or its stale line-number citations (feature_flags.py:18-19) into any new doc/ticket text.

## Acceptance Criteria
- [ ] InformationProviderState (or its typed update path) gains a real accumulation mechanism — verified via a before/after state assertion (not just an event firing) when a quest a Guide assigned is reported back.
- [ ] The ticket and any doc updates explicitly state current flag reality: ENABLE_BELIEF_ASSIMILATION ON, ENABLE_INFORMATION_INTENT_EXECUTION OFF — no AC assumes both OFF.
- [ ] Any new gated behavior registers a NEW flag in FeatureFlagManager._flags defaulting OFF (DEV-002), with a test asserting the flag-OFF path leaves information_providers/FactionState unchanged.
- [ ] City-to-City/City-to-Country propagation of 'critical' information walks FactionState.territory/diplomatic_relations (no new topology type), verified by a test where critical info at a City owned by Country A reaches sibling Cities under Country A but not an unrelated Country B.
- [ ] The mechanism for any Guide-to-Guide or hub-to-hub exchange is explicitly documented as NOT reusing a Conversation system (none exists in src/) — reframed at the state level or explicitly scoped out, not silently assumed.

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS
- TCK-20260824-LEAD-CONTRADICTION-WIRING
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
- TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION
- TCK-20260619-E42-INFO-SEEKING

## Related Docs
- docs/audits/D19_domain_phase_inventory.md
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/rpg_feature_atlas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/optimization/feature_flags.py
- src/domains/information/providers.py
- src/domains/information/schema.py
- src/domains/information/phase.py
- src/domains/information/assimilation.py
- src/engine/pipeline_phases/information_intent_execution.py
- src/engine/pipeline_phases/lead_contradiction.py
- src/core/state.py
- src/town/guild.py
- tests/unit/domains/information/test_phase5_information_source_profile.py
- tests/unit/domains/information/test_phase5_information_assimilation.py
- tests/unit/domains/information/test_phase5_information_belief_phase.py
- tests/integration/scenarios/test_phase5_information_belief_scenarios.py
- tests/unit/engine/test_information_intent_execution_phase.py
- tests/unit/strategic/test_belief_cycle.py
- tests/unit/strategic/test_belief_integration.py

## Assumptions / Open Questions
- The atlas's 'both flags OFF, no content risk' premise is stale — current reality (BELIEF_ASSIMILATION ON) means these changes carry real behavior risk on an already-live path; Plan phase should size accordingly.
- No Conversation/entity-dialogue system exists in src/ — Guide-to-Guide (or hub-to-hub) exchange must be designed fresh at the state/StateUpdate level, not assumed to reuse an existing dialogue system; open Plan-phase decision.
- City/Country 'critical information' classification has no existing concept wired to FactionState fields yet — despite reusing existing topology fields, the classification/propagation logic itself is new, not light wiring.
- `layer: strategy` was chosen because this work centers on knowledge accumulation/propagation (Mechanics Bible ch. 04 "Knowledge management, perception" territory) rather than a generic core-state change; no dedicated "information" layer exists in the registry and force-fitting `misc` was avoided since `strategy` genuinely fits the subsystem.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
