---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79

## Title
Level-up no longer renames an entity's kind; the role stays the content role (D79 step 3).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`EvolutionSystem` renamed an entity's kind by name at level 10/25/50 (hero to LEGEND_HERO and so on) and wrote `kind_set` every tick. Remove the rename.

## Scope
- `src/engine/evolution.py`, five test conversions, a new test file, divergence 2.133, parity ledger PROG-125, the docs that described the rename.

## Out of Scope
- The other D79 steps; the dead goblin gear branch and its missing `chainmail` (after v1, D78); real advancement to a declared role.

## Acceptance Criteria
- No entity kind changes on level-up (tested at 10/25/50).
- Levels and stats still rise (tested).
- Divergence entry with the measurement, naming the calamity.py:99 change.

## Related Tickets
- TCK-20261014-NAME-LITERALS-IN-SRC-SCAN, TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79

## Related Docs
- docs/guidelines/intentional_divergences.md (2.133), docs/parity_ledger/progression.yaml (PROG-125)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79/

## Related Code Areas
- src/engine/evolution.py, src/world/calamity.py, src/observability/event_shapers.py

## Assumptions / Open Questions
- The goblin test conversion in test_recovery_gaps.py was not in the planner's approved list; it is the same kind of change and is disclosed.

## Implementation Notes
See plan.md and divergence 2.133. Hand-closed; the ticket file was written at close from the handover draft.

## Test Summary
tests/unit/progression, test_progression_regression.py, test_recovery_gaps.py: 148 passed; ledger/shaper/coverage -k subset: 150 passed. Paired measurement: 30 runs plus a base-vs-base repeat, behaviour identical (divergence 2.133).

## Files Changed
src/engine/evolution.py, tests (5 converted, 1 new), divergence log, parity ledger, three doc passages.

## Completion Summary
Done; measured 30 paired runs plus repeat, identical behaviour, rename path never live in the gate worlds.
