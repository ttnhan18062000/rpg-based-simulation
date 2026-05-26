# Implementation Plan - TCK-20260527-COG-GOAL-REGISTRY

The objective is to expand `GoalRegistry` with four new goal scorers: `combat_engage`, `combat_retreat`, `recover`, and `resolve_blocker`. We will make sure they are fully registered, support downstream strategic project selection, respect entity personality attributes, use deterministic tie-breaking, and are captured clearly in observability events.

## Proposed Changes

### Component: AI Goals

#### [MODIFY] [scorers.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/scorers.py)
- Implement `CombatEngageScorer`: evaluates hostile neighbors, uses `personality.bravery` and `hp_ratio`/stamina, returns utility and nearest hostile target.
- Implement `CombatRetreatScorer`: evaluates HP ratio and panic level, applies bravery penalty, returns utility and town center target.
- Implement `RecoverScorer`: evaluates missing HP and stamina debt, returns utility and inn/town center target.
- Implement `ResolveBlockerScorer`: checks for active unresolved blockers, returns utility and target coordinates or location of corresponding lead.

#### [MODIFY] [\_\_init\_\_.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/goals/__init__.py)
- Register the 4 new scorers with `GoalRegistry`.

### Component: Strategic Systems

#### [MODIFY] [intelligence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py)
- Add stable deterministic sorting: `modified_scores.sort(key=lambda x: (-x.utility, x.kind))` in `fused_strategic_pass()`.
- Add event emission / trace logging for chosen goals and rejected alternatives (tracing goal selection).
- Support downstream objective/action mapping for the new project kinds.

## Verification Plan

### Automated Tests
- Run strategic unit tests to verify existing features still pass.
- Write new unit tests specifically verifying:
  - Scorer utility values under varying HP, panic, stamina, and neighbor conditions.
  - Personality bias: brave entities select `combat_engage` more than cowardly entities; greedy entities prioritize profit/social more appropriately.
  - Deterministic tie-breaking behavior when multiple goals have the exact same score.
  - Projects are successfully created with correct target IDs and positions from these new goals.
