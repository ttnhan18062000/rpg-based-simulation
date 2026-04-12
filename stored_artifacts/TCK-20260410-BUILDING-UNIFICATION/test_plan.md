# Test Plan: TCK-20260410-BUILDING-UNIFICATION

## Functional Tests
- `tests/test_building_unification.py`:
    - **Guild Discovery**: Entity visits Guild hall. Verify `StrategicUpdate` contains expected `LeadRecord` and `CandidateZoneRecord`. Verify NO `MindUpdate(goals_add)` is present.
    - **Blacksmith Blocker**: Entity visits Blacksmith without materials. Verify `StrategicUpdate` contains a `BlockerRecord` for the missing material. Verify zero "Need X" strings in action reason or goal list.
    - **Detour Derivation**: 
        1. Inject a material blocker into an entity.
        2. Inject a corresponding material lead.
        3. Run `DetourSuggestionService.suggest_detours`.
        4. Verify an `ObjectiveRecord` is generated with the correct coordinates from the lead.

## Integration Tests
- **Simulation Loop**: Verify that entities can complete the "Blacksmith -> Guild -> Field -> Blacksmith" loop using only strategic records for detour navigation.
- **Snapshot Purity**: Verify that the new `LeadRecord` and `BlockerRecord` structures do not introduce aliasing bugs in `Snapshot.from_world`.

## Performance & Hysteresis
- Verify that multiple visits to the same building do not duplicate blockers.
- Verify that resolving a blocker at the blacksmith correctly updates the strategic state and allows the project to resume.
