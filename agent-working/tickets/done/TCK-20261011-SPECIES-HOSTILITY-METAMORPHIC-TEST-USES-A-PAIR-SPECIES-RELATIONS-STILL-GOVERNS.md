---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261011-SPECIES-HOSTILITY-METAMORPHIC-TEST-USES-A-PAIR-SPECIES-RELATIONS-STILL-GOVERNS
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-SPECIES-HOSTILITY-METAMORPHIC-TEST-USES-A-PAIR-SPECIES-RELATIONS-STILL-GOVERNS

## Title
The species-hostility metamorphic test uses a pair whose hostility species_relations still governs, and guards that the 'high' variant really changes the hostility input.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
After Q3 (B), `is_wild_creature` (src/engine/hostility.py) means wild creatures regard others by appraisal and ignore species_relations. So tests/integration/lab/test_species_relations_metamorphic_validation.py::test_species_hostility_increase_does_not_decrease_combat_engagement_rate now holds TRIVIALLY for wolves: its 'high' variant gives the same wolf-human engagements as the baseline (Lane A, 2026-10-11). testing-planner watches it hourly as a "species must not appear" item, so it is green for the wrong reason.

## Scope
- Move the metamorphic relation to a people-kind pair where species_relations still sets hostility.
- NON-VACUITY GUARD (testing-planner, 2026-10-11): before comparing engagement rates, assert that the 'high' variant changes the hostility input the kernel reads for the chosen pair: species_relations is consulted, and the hostility value differs from the baseline. If a later rule takes the pair out of species_relations, the test fails loudly.
- Keep the hungry-wolf layout as a separate appraisal check: hungry wolves engage people; sated wolves don't.

## Out of Scope
- Any change to hostility rules.

## Acceptance Criteria
- The relation is non-trivial: the guard passes, and engagements are compared on a pair species_relations governs.
- The wolf appraisal check is separate and green.

## Related Tickets
Lane A hunting (Q3 (B), divergence 2.107); M1 monster-drive child (D62).

## Related Docs
docs/mechanics/02_combat_laws.md; designer memo Q3.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/hostility.py; tests/integration/lab/test_species_relations_metamorphic_validation.py.

## Assumptions / Open Questions
The people-kind pair is town_council human vs merchant_league human in unit_faction_tension: neutral at faction level, species_relations upgrade-only escalates it with a human_to_human high row (found by probing the semantics service; goblin/orc/undead rows need a world with those populations).

## Implementation Notes
Metamorphic test moved to the human pair; baseline is the authored file, variant appends a human_to_human high row; engagements counted for the pair only; non-vacuity guard _pair_hostility_input asserts (False, True) for the kernel's faction-semantics verdict and that neither is a wild creature. Wolf appraisal check split into tests/unit/engine/test_hungry_wolf_hunts_prey_it_out_bands.py.

## Test Summary
Metamorphic test passes (454 s): per-seed pair engagements baseline 0 in all 10 seeds, high 89 in total (9,6,7,10,10,12,0,7,10,18). Unit test: 2 passed. Tests only, no rule change.

## Files Changed
tests/integration/lab/test_species_relations_metamorphic_validation.py; tests/unit/engine/test_hungry_wolf_hunts_prey_it_out_bands.py.

## Completion Summary
Done. The relation is now exercised by a pair species_relations governs and fails loudly if that stops being true.
