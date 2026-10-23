---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID

## Title
Faction squad group_id uses Python's salted hash() of a str region id, so the state hash depends on PYTHONHASHSEED (#593 F4)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
#593 F4 (verified on main by rpg-planner 2026-10-22). `src/engine/military_conflict.py:339`: `group_id = abs(hash((contested_region_id, attacker_id, state.tick))) % (2 ** 31)`; `contested_region_id` is `Optional[str]` (str region ids, state.py:1348), so the tuple hash is salted per process. `groups` is in CanonicalStateHasher, so two processes with different PYTHONHASHSEED get different state hashes once a faction squad forms. Only the measurement tools pin PYTHONHASHSEED; compose, the Makefile and live/API runs do not. Same pattern at `src/domains/perception/filter.py:88,97` (`hash(signal.signal_id)` for a str id; whether it reaches hashed state is unverified).

## Scope
1. Replace with a stable digest (e.g. blake2b of the tuple) or an allocator-issued id; same for perception/filter.py:88,97 if it reaches state.
2. PROBE A0 first: does any shipped world (unit_faction_tension W5, urban_political W2) form a FACTION_SQUAD within its tick count? If none, add a small purpose-built world following the `data/worlds/mechanic_scenario_*` pattern (e.g. mechanic_scenario_faction_attack), declared as a test scenario, not a gate/benchmark world.
3. Cross-PYTHONHASHSEED test: two processes (hashseed 0 and 1) on that world give equal final hashes and equal squad ids.

## Out of Scope
Other salted-hash sites not reaching state (list them in investigation).

## Acceptance Criteria
- Final state hash equal across PYTHONHASHSEED=0 and =1 on a world where a faction squad forms.
- perception/filter.py:88,97 resolved or shown not to reach hashed state.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/engine/military_conflict.py; src/domains/perception/filter.py; data/worlds/

## Assumptions / Open Questions
Changes squad ids, so a world-changing hash difference is expected on any run where a squad forms; needs a paired step and a gate check (V-rows unchanged). Probe A0 answered on #593 6347182683 (not yet run).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
