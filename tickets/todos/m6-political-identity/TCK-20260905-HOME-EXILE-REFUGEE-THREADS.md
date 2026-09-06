---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
phase: open
date: 2026-09-05
tags: [strategy, world]
---

# TCK-20260905-HOME-EXILE-REFUGEE-THREADS

## Title
Home, Exile & Return + Named Refugee Threads (M6 ideas 59+65) — populate an existing field, not invent new state

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Idea 59 (Home, Exile & Return) and idea 65 (Named Refugee Threads) are the M6 epic's third and
final child (`TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`), consolidated into one ticket per the
epic doc's own Shared Implementation Opportunities finding (idea 65 folds into idea 59's ticket as
extra acceptance criteria, writing `home_region_id` at displacement time).

**The single largest correction found during this milestone's original investigation, confirmed
real, not assumed:** idea 59's central premise — "no per-entity place-attachment field exists" — was
flatly wrong. `StrategicComponent.home_region_id: Optional[str] = None`
(`src/core/strategic.py:414`) already exists, typed, with a live consumer already wired
(`RoutineService.evaluate_anchored_behavior()`, `src/systems/world_systems/routine.py:163`, called
from `src/systems/strategic_systems/intelligence.py:541,857`). This ticket is
populate-an-existing-field at the right moments (birth/settlement, displacement/exile), not
invent-new-state — materially cheaper than the epic doc's original scoping assumed.

## Scope
- Confirm and, if needed, wire `home_region_id`'s population at the moments the epic doc names:
  birth/settlement (an entity's home is set once, early) and displacement (idea 65 — a refugee's
  `home_region_id` is written or updated at the moment of forced displacement, distinct from their
  new, non-home current location).
- Confirm `RoutineService.evaluate_anchored_behavior()`'s existing "return home" concern correctly
  reflects a freshly-set or updated `home_region_id`, not just the birth-time value, once idea 65's
  displacement-time write lands.
- Add any missing observable event/telemetry for a displacement (exile/refugee) event, if none
  exists today (confirm during Investigate — not assumed either way here).
- Document the mechanism in a real, citable doc.

## Out of Scope
- Idea 39 (Affiliation's real change path) — `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`.
- Idea 56 (Drifting Loyalty) — `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`.
- Inventing any new per-entity place-attachment field — `home_region_id` already exists and is the
  correct target; this ticket populates and reads it correctly, it does not replace it.
- Any UI/API surface for home/exile/refugee status unless a future ticket asks for it.

## Acceptance Criteria
- [ ] `home_region_id` is correctly populated at birth/settlement for every new entity that should
      have one (confirm the exact population rule during Investigate — not assumed here).
- [ ] A real displacement/exile trigger writes or updates `home_region_id` per idea 65's "named
      refugee threads" requirement — confirmed via a test constructing a displacement scenario.
- [ ] `RoutineService.evaluate_anchored_behavior()`'s existing "return home" concern is confirmed
      (via a test) to correctly react to a post-displacement `home_region_id`, not just the
      birth-time value.
- [ ] The mechanism is documented in a real, citable doc.
- [ ] Parity-ledger entries added/updated for the affected file(s), each with a real `test_path`.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (parent epic)
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39, sibling child, no hard dependency)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56, sibling child, no hard dependency)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/strategic.py` (`StrategicComponent.home_region_id`)
- `src/systems/world_systems/routine.py` (`RoutineService.evaluate_anchored_behavior()`)
- `src/systems/strategic_systems/intelligence.py`

## Assumptions / Open Questions
- The exact displacement/exile trigger condition (calamity-driven, faction-conflict-driven, or both)
  is not decided here — real design work for this ticket's own Investigate/Plan phases.
- Whether this ticket can land in parallel with idea 39/56 or should wait, given it shares no hard
  code dependency with either — left to the implementer's own judgment at pickup time; the epic's
  SEQUENCE.md does not hard-block it behind the other two.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
