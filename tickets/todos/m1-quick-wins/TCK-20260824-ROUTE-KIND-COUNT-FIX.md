---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260824-ROUTE-KIND-COUNT-FIX
phase: open
date: 2026-08-24
tags: [adventure, documentation]
---

# TCK-20260824-ROUTE-KIND-COUNT-FIX

## Title
Fix Stale Route/Activity Kind Count in Adventure Routing Docs

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
docs/mechanics/adventure_routing_contract.md's table of route/activity kinds is stale by exactly 3 entries (documents 13, actual is 16). This is a straightforward doc correction.

## Scope
- Update docs/mechanics/adventure_routing_contract.md's Route Family Taxonomy table to contain exactly 16 rows matching the RouteFamily enum
- Add the 3 missing rows (QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL) with accurate Meaning descriptions
- Correct the prose "All 13 families" to "All 16 families"

## Out of Scope
- The Regression Tests section's reference to a nonexistent tests_v2/ directory (separate staleness issue)
- The Source Areas table's omission of src/domains/adventure/mapper.py (separate staleness issue)
- Implying all 16 families map to a project -- RouteToProjectMapper._MAP intentionally has only 15 entries (DEFER_WITH_REASON excluded by design)

## Acceptance Criteria
- [ ] Route Family Taxonomy table contains exactly 16 rows matching the RouteFamily enum
- [ ] QUEST_OPPORTUNITY, PROTECT_TARGET, and OWN_SURVIVAL rows are added with accurate Meaning descriptions
- [ ] Prose is corrected from "All 13 families" to "All 16 families"
- [ ] No src/ file is modified; tests/unit/domains/adventure/test_phase3_route_families.py::test_route_family_definitions_are_unique continues to pass unchanged, confirming 16 as ground truth

## Related Tickets
- TCK-20260619-E23D-HERO-MATCHING
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Related Docs
- docs/mechanics/adventure_routing_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/mechanics/adventure_routing_contract.md
- src/domains/adventure/schema.py
- src/domains/adventure/mapper.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
