---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261031-MECHANISM-NOTE-CAPACITY-TIE-TRIM-ORDER
phase: open
date: 2026-10-31
tags: [determinism]
---

# TCK-20261031-MECHANISM-NOTE-CAPACITY-TIE-TRIM-ORDER

## Title
Append rpg-planner's binding note about the capacity trim's tie rule to the cognition_capacity_fatigue entry in registries/mechanisms.yaml.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The mechanism changed-code advisory at TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED's close listed 6 mechanisms. rpg-planner's ruling (2026-10-31, relayed via lead-planner-u24 and lead-planner), word for word:

"Non-blocking: (B)'s push of b8701d330 goes ahead unchanged.
- Only ONE entry needs a note: cognition_capacity_fatigue. (B) changed which concern survives a tie at the cap, which is a real rule. The other five, including tactical_decision and strategic_intelligence_core, are hygiene sorts and order stabilization with no semantic change, so they get no note.
- Binding text, appended to cognition_capacity_fatigue's verified.note:
'**Note, added 2026-10-31 (TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED, divergence 2.144, Stabilized):** when concerns tie at the capacity trim, the kept set is ordered by (urgency desc, concern id) with ids compared as strings, so the trim no longer follows the process hash seed. The id key exists for determinism only and carries no meaning about which concern matters more.'
- Delivery: a hotfix follow-up after (B) merges, under S4. This message is rpg-planner's plan OK. One file, plus the regenerated verification view if its test requires it. The ubuntu lead dispatches it."

lead-planner's note: its role doesn't dispatch, so S4's dispatch is rpg-planner-ubuntu's, citing this ruling.

## Scope
1. Append the binding text exactly to cognition_capacity_fatigue's verified.note in registries/mechanisms.yaml.
2. Regenerate every view the registry's tests require.

## Out of Scope
The other five mechanisms. Any src change.

## Acceptance Criteria
1. The appended text is byte-identical to the binding text, and the diff touches only that note plus regenerated views.
2. The full tests/tools directory passes, not a -k subset. generate_registry --check is in sync.

## Related Tickets
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED

## Related Docs
- docs/guidelines/intentional_divergences.md 2.144

## Related Stored Artifacts
- none

## Related Code Areas
- registries/mechanisms.yaml

## Assumptions / Open Questions
- Dispatch after B merges, under S4 (#715 6473439661). If B is still unmerged when this is ready, fold it into B's open PR; the push ask stays separate (lead-planner).

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
