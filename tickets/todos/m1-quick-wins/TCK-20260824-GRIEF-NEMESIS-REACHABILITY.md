---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-GRIEF-NEMESIS-REACHABILITY
phase: open
date: 2026-08-24
tags: [cognition, social, observability]
---

# TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Title
Extend Grief/Nemesis Triggers Past Episode Boundaries and Make Campaign Mode Reachable

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
GriefUrgencyImporter/NemesisRelationImporter only fire from CampaignOrchestrator._build_initial_state(); the author wants this extended to also fire on in-episode death. A depth-audit found this idea fails on 3 more axes: Campaign mode has zero scenario content wiring it in, no SimQ event type exists to measure it, and check_nemesis_promotion()/tick_place_attachment() have zero test coverage. Scope as make reachable, measurable, tested, then extend.

## Scope
- Establish a real production entry point that reaches CampaignOrchestrator.run_episode() -- new scenario content, CLI, or a documented API trigger (register_campaign() currently has zero callers anywhere)
- Add new event_type(s) (grief_urgency_triggered/nemesis_relation_formed) emitted via SimulationEvent following the existing pattern, queryable by a SimQ pillar
- Extend GriefUrgencyImporter/NemesisRelationImporter so an in-episode entity_death (not just the episode-boundary path in CampaignOrchestrator._build_initial_state()) causes the same grief-urgency concern injection within the same episode, via an authoritative-pipeline-compliant path
- Decide the event_category (social/strategy) and whether it counts toward the NARRATIVE pillar or needs a new one
- Reconcile GriefUrgencyImporter.apply()/NemesisRelationImporter.apply()'s 'return a new EntityState directly' mutation shape against the tick-time SocialUpdate pattern, as part of the in-episode trigger design

## Out of Scope
- check_nemesis_promotion()/tick_place_attachment() unit test coverage in src/systems/social_systems/memory.py -- completely unrelated code path, tracked separately as TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
- The broader 'Nemesis System overriding AI scoring' described in docs/engine/contracts/rpg_refinement_pillars.md -- current narrower FORM_PARTY-block-only implementation is a pre-existing possible divergence, noted but not resolved here

## Acceptance Criteria
- [ ] CampaignOrchestrator.run_episode() is reachable via a real production entry point, not just test scaffolding
- [ ] A new event_type (grief_urgency_triggered/nemesis_relation_formed) is emitted via SimulationEvent following the existing pattern and is queryable by a SimQ pillar
- [ ] An in-episode entity_death causes the same grief-urgency concern injection within the same episode via an authoritative-pipeline-compliant path

## Related Tickets
- TCK-20260628-E43F-GRIEF-URGENCY
- TCK-20260628-E43G-NEMESIS-RELATION
- TCK-20260628-E43H-NARRATIVE-OBS
- TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Related Docs
- docs/engine/contracts/rpg_refinement_pillars.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/campaigns/orchestrator.py
- src/domains/campaigns/grief_urgency.py
- src/domains/campaigns/state.py
- src/api/routes/campaigns.py
- src/observability/event_extractor.py
- src/observability/events.py
- src/core/updates.py

## Assumptions / Open Questions
- What 'reachable' means (new CLI script vs scenario content vs API route) needs an explicit author decision before implementation
- Independent of TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS (C9b) -- no shared code, data model, or callers between the two halves of the original concern
- `layer: strategy` was chosen because grief/nemesis concern injection feeds the strategic goal-hierarchy/concern layer (docs/mechanics/04_strategic_cognition.md); no registered layer covers "campaigns" or "social narrative" specifically -- revisit if a dedicated layer is registered later

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
