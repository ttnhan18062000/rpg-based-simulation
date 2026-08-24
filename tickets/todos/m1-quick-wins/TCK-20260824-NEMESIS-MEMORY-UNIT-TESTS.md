---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
phase: open
date: 2026-08-24
tags: [social, testing]
---

# TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Title
Add Unit Test Coverage for check_nemesis_promotion()/tick_place_attachment()

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
A depth-audit of the Grief/Nemesis trigger idea found that check_nemesis_promotion()/tick_place_attachment() in src/systems/social_systems/memory.py have zero test coverage. The author's scoping intent (make reachable, measurable, tested) requires this pair to be given standalone unit tests, tracked separately since they are a completely unrelated code path from the Campaign-mode grief/nemesis work.

## Scope
- Add unit tests covering the branch conditions of check_nemesis_promotion() (src/systems/social_systems/memory.py)
- Add unit tests covering the branch conditions of tick_place_attachment() (src/systems/social_systems/memory.py)

## Out of Scope
- Any change to CampaignOrchestrator/GriefUrgencyImporter/NemesisRelationImporter reachability, event wiring, or in-episode triggering -- tracked separately as TCK-20260824-GRIEF-NEMESIS-REACHABILITY; confirmed completely unrelated code path

## Acceptance Criteria
- [ ] check_nemesis_promotion() has unit tests covering each of its branch conditions
- [ ] tick_place_attachment() has unit tests covering each of its branch conditions

## Related Tickets
- TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/memory.py

## Assumptions / Open Questions
- Independent of TCK-20260824-GRIEF-NEMESIS-REACHABILITY (C9a) -- testing these orphaned functions doesn't unblock or interact with the Campaign-mode work
- layer set to `systems` (src/systems/social_systems/memory.py) since no dedicated `social` layer is registered in registries/layer_registry.jsonl; `systems` is the closest registered fit for this file's location.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
