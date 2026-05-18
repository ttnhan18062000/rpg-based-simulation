# Implementation Plan: Phase 5 Combat Legality Hardening

## Goal
Harden the combat legality matrix by fixing pipeline routing omissions, implementing LoS-restricted splash damage, and ensuring multi-kill reward atomicity.

## Proposed Changes

### Component: Engine Pipeline
#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Update `_route_combat_intent` to handle `SKILL` and `AOE_ATTACK`.
- Ensure `SKILL` actions are checked for cooldown and stamina legality before execution in the pipeline (or delegate to `SimulationDomainLogic` but ensure the pipeline respects the outcome).

### Component: Authoritative Application
#### [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Update `ApplyPath.apply_generation` splash damage loop to include a Line-of-Sight check.
- If a target is within `splash_radius` but LoS is obstructed from the `impact_pos`, no damage is applied.

### Component: Combat Resolution
#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py)
- Update `resolve_aoe_attack` to potentially identify and return rewards for all potential splash kills, or ensure rewards are handled consistently.
- *Self-Correction*: `ApplyPath` is currently where splash damage is applied. If an entity dies from splash damage, reward generation must be triggered. Since `ApplyPath` handles death (line 132), we should ensure splash-induced deaths also emit resource transfers or that they are handled in the next tick's reward processing (less ideal). 
- *Revised Strategy*: Rewards for AoE kills should be calculated in the `resolve` phase if possible.

### Component: Legality Service
#### [MODIFY] [legality.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py)
- Ensure `verify_aoe_legality` is robust and matches the requirements for both primary target and empty-tile targeting.

## Verification Plan

### Automated Tests
- Run `pytest tests/rpg/test_combat_legality_matrix.py`.
- Add `test_aoe_splash_obstruction` to verify walls block explosions.
- Add `test_skill_pipeline_integration` to verify skills work through the authoritative pipeline.
- Add `test_multi_kill_aoe_rewards` to verify multiple kills in one AoE grant cumulative rewards.

### Manual Verification
- Trace combat logs to ensure "OUT_OF_RANGE" and "LOS_OBSTRUCTED" are reported correctly for both skills and attacks.
