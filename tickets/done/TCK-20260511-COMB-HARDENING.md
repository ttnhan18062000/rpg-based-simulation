# TCK-20260511-COMB-HARDENING

## Title
Hardening Tactical Combat Logic & Anti-Stalemate Audit

## Status
DONE

## Request Summary
Hardening of tactical combat logic to ensure skill-aware decision making, target stickiness, and 100% compliance with COMB subsystem laws.

## Scope
- Implement skill-aware target selection in TacticalDecisionSystem
- Implement target stickiness logic (COMB-270/271)
- Add strategic update support to CombatUpdate (COMB-282)
- Annotate codebase with Logic ID markers
- Update logic_checklist_exhaustive.md

## Out of Scope
- INFRA series (distributed replay)
- SOC series (social cooperation)

## Acceptance Criteria
- [x] All COMB laws in checklist marked as verified
- [x] TacticalDecisionSystem evaluates learned skills
- [x] Target stickiness verified with tests
- [x] Full pass on combat legality matrix integration tests
- [x] Graphify updated

## Related Tickets
None

## Related Docs
- logic_checklist_exhaustive.md

## Related Stored Artifacts
- walkthrough.md

## Related Code Areas
- src/engine/tactical.py
- src/engine/apply.py
- src/core/updates.py
- src/engine/legality.py

## Implementation Notes
- Used TaskComponent(payload=...) for runtime state and TaskUpdate(payload_set=...) for proposed updates.
- Added strategic_upd field to CombatUpdate to allow combat results to trigger strategic shifts (e.g. boss death).

## Test Summary
- tests/integration/pipeline/test_combat_legality_matrix.py (14/14 Passed)
- tests/unit/tactical/test_target_stickiness.py (3/3 Passed)

## Files Changed
- src/engine/tactical.py
- src/engine/apply.py
- src/core/updates.py
- logic_checklist_exhaustive.md

## Completion Summary
All objectives for the COMB series audit are complete. The engine now correctly enforces skill costs and ranges during tactical evaluation and prevents "flip-flopping" targets through stickiness constraints.
