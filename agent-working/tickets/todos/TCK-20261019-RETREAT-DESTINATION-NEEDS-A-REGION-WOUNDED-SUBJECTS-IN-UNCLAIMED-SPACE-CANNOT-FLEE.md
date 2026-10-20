---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261019-RETREAT-DESTINATION-NEEDS-A-REGION-WOUNDED-SUBJECTS-IN-UNCLAIMED-SPACE-CANNOT-FLEE
phase: open
date: 2026-10-19
tags: []
---

# TCK-20261019-RETREAT-DESTINATION-NEEDS-A-REGION-WOUNDED-SUBJECTS-IN-UNCLAIMED-SPACE-CANNOT-FLEE

## Title
retreat_destination needs a region: wounded subjects in unclaimed space cannot flee.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`retreat_destination` (src/engine/tactical_destinations.py:80+) computes the away vector only when `containing_region` (:38, strict bounds) finds a region around the subject, then falls back to the subject's home region, else None (a hold, tactical.py:107 `_destination_or_hold`). Unclaimed space between regions is legitimate (docs/mechanics/06_worldbuilding_foundation.md:42; the compiler must not refuse it), so a wounded subject standing there, with no home region, can never flee. Found at frontier_living_world seed 42, tile (41,31): hometown ends at x=40 and trading_hometown starts at x=45. The designer's ruling: flight must not depend on region membership.

## Scope
Fix after v1, as its own measured step: the away vector is computed from the appraised threat (D47) and the walkable ground. A region clamp may limit it but is never required.

## Out of Scope
- The merchants' missing home_region_id (M1 home-range item).
- The v1 step that stops a held panic from freezing a hungry subject (TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL).

## Acceptance Criteria
- A wounded subject in unclaimed space with a perceived threat gets a real retreat destination; a region clamp, when present, only limits it.
- Before-number to measure first: the count of PANIC_RETREAT holds with subject region None, on the paired 3 worlds (not yet measured; merchant 37 at tile (41,31) on frontier seed 42 is the known example).

## Related Tickets
- TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/tactical_destinations.py:38, :80+; src/engine/tactical.py:107.

## Assumptions / Open Questions
- Whether the away vector should use walkable-ground search or stay a clamped vector is the designer's call.

## Implementation Notes
None yet.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
