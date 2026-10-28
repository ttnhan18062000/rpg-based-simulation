---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-HUNGER-CAPACITY-DERIVATION-HAS-NO-LIVE-CALLER
phase: open
date: 2026-10-27
tags: []
---

# TCK-20261027-HUNGER-CAPACITY-DERIVATION-HAS-NO-LIVE-CALLER

## Title
The Bible's "Hungry halves cognitive capacity" law may have no live producer

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
rpg-implementer-ubuntu found this during U3, in TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS.
rpg-planner-ubuntu verified it at origin/main 3b5fab1e9. rpg-planner (u24) ruled on 2026-10-27,
relayed via lead-planner-u24 and lead-planner, that it is filed as its own ticket.

Bible ch01 `docs/mechanics/01_entity_anatomy.md:100` (Staged Starvation, SURV-02, owner decision 36)
says: "Hungry (hunger above 70): the cognitive capacity limits halve (`strategy/cognition_capacity.py`)".
`src/engine/starvation.py:10` and `docs/world_rules/foundations/capacity.md` cite the same
implementation. Parity STRAT-010 is related.

The derivation is `src/strategy/cognition_capacity.py::CapacityService.derive_profile`. It applies a
fatigue multiplier of 0.5 when hunger or sleep_debt is above 70, and 0.8 above 40 (lines 40-45). Its
only entry point is `StrategicIntelligenceSystem.derive_cognition_profile`
(`src/systems/strategic_systems/intelligence.py:1827`). A static search finds no caller of it in
`src/` or `tools/`; only tests call it. The live enforcer, `src/strategy/capacity.py::CapacityService`
via `CapacityEnforcementPhase`, reads the static `entity.strategic.profile` limits. So hunger may
never reduce capacity on a live tick. This is static evidence only: it has not been measured at
runtime, and dynamic dispatch has not been ruled out.

## Scope
**Part 1: measurement only, no code change. It can run now, in an ubuntu heavy slot (ask
lead-planner).**
1. Find out whether `derive_cognition_profile` or `CapacityService.derive_profile` runs on any live
   tick. Use a positive-controlled call counter: one probe arm that calls it deliberately, to prove
   the counter works, and one plain arm. Run it on frontier_living_world and crowded_frontier, seed
   42, 1000 ticks, in audit mode.
2. For entities with hunger above 40 and above 70, record their actual `strategic.profile` limits next
   to what `derive_profile` would give them.
3. Report to rpg-planner BEFORE any regrading of SURV-02 or STRAT-010, especially if the derivation
   never runs.

**Part 2: fix, or Bible and ledger regrading. Blocked.** It waits until both of these have landed:
u24's HUNGER step A, and TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
(u24, filed 2026-10-27; the winner lookup at intelligence.py:1610 takes a dead record of a kind
first). All three change capacity behaviour for the same entities, so each lands as its own paired
step. Part 2's design, whether that is wiring the derivation or changing the Bible, is rpg-planner's
call once Part 1's numbers are in.

## Out of Scope
- Any code change in Part 1.
- The capacity-gate winner lookup (u24's ticket) and HUNGER step A.
- Deleting or renaming either CapacityService. SAME-NAME-PAIRS keeps both, with an allowlist reason.

## Acceptance Criteria
1. Part 1 reports a call count per arm, with the positive control showing the counter fires, and a
   table of hungry entities' actual limits next to the derived ones.
2. rpg-planner rules on Part 2 from those numbers before anything is regraded.
3. Part 2 (later) brings the Bible, the ledger and the code into parity, with a paired proof
   attributing the change.

## Related Tickets
- TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS (where this was found)
- TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (u24)
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (HUNGER step A lineage)

## Related Docs
- docs/mechanics/01_entity_anatomy.md (Staged Starvation)
- docs/world_rules/foundations/capacity.md
- docs/parity_ledger/strategic_cognition.yaml (STRAT-010)

## Related Stored Artifacts

## Related Code Areas
- src/strategy/cognition_capacity.py, src/strategy/capacity.py
- src/systems/strategic_systems/intelligence.py (around L1827, and L1610 for u24's ticket)
- src/engine/starvation.py

## Assumptions / Open Questions
- Part 1 needs a heavy slot. Part 2 must not start before its two prerequisites land.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
