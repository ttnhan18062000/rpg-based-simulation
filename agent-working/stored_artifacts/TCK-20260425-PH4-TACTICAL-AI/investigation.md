---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH4-TACTICAL-AI
artifact_type: investigation
tags: [ph4, tactical, ai]
---

# Investigation: Tactical AI Behavior

## Findings
- Legacy `src` uses implicit role logic based on class/faction.
- V2 `src` requires explicit `tactical_role` in `CombatComponent` for deterministic behavior.
- `CognitionProfile` contains capacity limits but they were not enforced in `StrategicIntelligenceSystem`.

## Implementation Strategy
- Use `SKIRMISHER` role for kiting behavior.
- Use `VANGUARD` role for closing behavior.
- Add `len(strat.projects)` check in `evaluate_strategic_intent`.
