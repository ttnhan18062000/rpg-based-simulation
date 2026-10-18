---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261018-COVER-WORDING-MATCHES-THE-CODE-GEOMETRY
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-COVER-WORDING-MATCHES-THE-CODE-GEOMETRY

## Title
The cover wording (Bible row, check_cover docstring, parity row) now says what the code does: an obstacle between attacker and defender.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Designer ruling 2026-10-18 (fiction of cover, D33 via rpg-planner): cover is an obstacle between attacker and defender; the code is right and the wording said "behind the target, away from the attacker". Fix the wording only.

## Scope
- docs/mechanics/02_combat_laws.md Cover row; the check_cover docstring (it is in src/engine/legality.py, not combat.py); parity row COMB-262 (v2_evidence, test_path); a stale comment in the forced-scenarios test.

## Out of Scope
- Any logic change; an intentional_divergences entry (behaviour did not change). Divergence 2.129's prose still says "behind the defender" in its legacy and measured text (historical record, left as written).

## Acceptance Criteria
- Docstring-only diff in src; combat tests green; parity ledger schema check green.

## Related Tickets
- TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND, TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT

## Related Docs
- docs/mechanics/02_combat_laws.md, docs/parity_ledger/combat_movement.yaml (COMB-262)

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- src/engine/legality.py (docstring)

## Assumptions / Open Questions
- Whether to also reword 2.129's historical text is the planner's call.

## Implementation Notes
Wording only.

## Test Summary
See the closing commit message and report.

## Files Changed
docs/mechanics/02_combat_laws.md, docs/parity_ledger/combat_movement.yaml, src/engine/legality.py (docstring), tests/unit/combat/test_terrain_mechanics_forced_scenarios.py (comment).

## Completion Summary
Done; no behaviour change.
