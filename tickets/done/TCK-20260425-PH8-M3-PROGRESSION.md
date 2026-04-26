# TCK-20260425-PH8-M3-PROGRESSION

## Title
Implement Authoritative Leveling and Attribute Growth

## Status
DONE

## Request Summary
Implement the core growth mechanics: converting XP (Evolution Points) into Levels and updating derived attributes (HP, ATK, DEF).

## Scope
- Define `LevelingService` with XP curve and stat scaling logic.
- Implement authoritative auto-leveling in `ApplyPath.apply_generation`.
- Add contract tests for growth and healing surges.

## Out of Scope
- Veterancy and milestones (Milestone 7).
- Attribute points/distribution (Milestone 5).

## Acceptance Criteria
- Entities level up automatically upon meeting XP requirements.
- Stats scale multiplicatively (10% per level).
- Level up triggers a proportional heal + 20% bonus surge.

## Related Tickets
- `TCK-20260425-PH8-M1-QUESTS`
- `TCK-20260425-PH8-M2-GENERATION`

## Related Docs
- `resource_v2_e_phases.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260425-PH8-M3-PROGRESSION/`

## Related Code Areas
- `src/progression/leveling.py`
- `src/engine/apply.py`
- `tests/progression/test_leveling.py`

## Implementation Notes
- XP Curve: `100 * (level ** 1.5)`
- Scaling: Iterative 1.1x multiplier for Max HP, ATK, DEF.
- Integrated into `ApplyPath._apply_entity_update` for automatic promotion.

## Test Summary
- `test_automatic_level_up`: PASS
- `test_multi_level_up`: PASS

## Files Changed
- `src/progression/leveling.py` [NEW]
- `src/engine/apply.py` [MODIFY]
- `tests/progression/test_leveling.py` [NEW]

## Completion Summary
- Successfully implemented the V2 growth engine.
- Verified deterministic promotion and attribute scaling across multiple levels.
