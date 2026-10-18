---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND
phase: done
date: 2026-10-17
tags: []
---

# TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND

## Title
Forced scenarios for the three terrain mechanics the gate worlds never exercise: cover, chokepoints, high ground.

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Owner ruling 2026-10-17 (via rpg-planner): the three terrain mechanics are dormant in the gate worlds, so staged fights must prove them through the real kernel and resolver, each failing when the mechanic's read is switched off. Test-only.

## Scope
- One new test file, six tests, each through Kernel.tick_once: cover (damage drops, COVER_REDUCTION in the trace), high ground (damage rises, HIGH_GROUND in the trace), chokepoint (finder returns the gap tile, a VANGUARD decides HOLD_CHOKEPOINT and keeps the tile); control arms with the precondition absent.
- Path probe answering the designer's question (attacks per path in the gate worlds).

## Out of Scope
- Any src change. The skill and AoE bypass of the multipliers (disclosure item only). The cover geometry wording (reported to rpg-planner).

## Acceptance Criteria
- Each mechanic is reached through the kernel and real resolver and has a control arm.
- With the cover read, the high-ground read, or the chokepoint finder switched off in a scratch copy, the matching test fails and the others pass.

## Related Tickets
- TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT, TCK-20261014-CHOKEPOINTS-ARE-FOUND-FROM-BLOCKED-TILES

## Related Docs
- docs/guidelines/intentional_divergences.md (2.129, 2.130)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND/

## Related Code Areas
- src/engine/combat.py, src/engine/legality.py, src/engine/positioning.py (read only)

## Assumptions / Open Questions
- Finding for rpg-planner: check_cover reads the tile adjacent to the defender on the ATTACKER's side, not "behind the target, away from the attacker" as the Bible (02_combat_laws) and the docstring say. Tests pin the code's behaviour.

## Implementation Notes
See plan.md and investigation.md.

## Test Summary
New file 6 passed. Scratch mutations: cover read off -> 1 failed (cover test); high-ground read off -> 1 failed (high-ground test); finder off -> 1 failed (chokepoint test). tests/unit/combat run below.

## Files Changed
tests/unit/combat/test_terrain_mechanics_forced_scenarios.py (new).

## Completion Summary
Done; test-only. Output on /mnt/data/scratch-rpg-implementer (path probe pp_*.json, mutation copy mut/).
