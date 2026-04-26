# Investigation: Tactical AI Behavior

## Findings
- Legacy `src` uses implicit role logic based on class/faction.
- V2 `src` requires explicit `tactical_role` in `CombatComponent` for deterministic behavior.
- `CognitionProfile` contains capacity limits but they were not enforced in `StrategicIntelligenceSystem`.

## Implementation Strategy
- Use `SKIRMISHER` role for kiting behavior.
- Use `VANGUARD` role for closing behavior.
- Add `len(strat.projects)` check in `evaluate_strategic_intent`.
