# Investigation: Combat Legality Matrix Gaps

## 1. Pipeline Action Routing Omission
- `AuthoritativeApplyPipeline._route_combat_intent` currently only checks for `action_kind == "ATTACK"`.
- `SKILL` actions are implemented in `SimulationDomainLogic.execute_action` but are not reachable through the pipeline because they are filtered out in `_route_combat_intent`.
- **Action**: Modify `_route_combat_intent` to handle `SKILL` and `AOE_ATTACK`.

## 2. AoE Splash Line-of-Sight
- `ApplyPath.apply_generation` (Phase 16: Splash Damage Resolution) iterates over entities within `splash_radius`.
- It currently uses `LegalityServiceV2.get_manhattan_dist` but DOES NOT check for obstructions between the impact point and the other entities.
- This allows explosions to hit targets behind solid walls.
- **Action**: Add `LegalityServiceV2.has_line_of_sight(impact_pos, other_ent.position, prior_state)` to the splash loop.

## 3. Multi-Kill Reward Attribution
- If an AoE kills multiple monsters, the attacker should receive rewards for all of them.
- `CombatResolutionSystem.resolve_aoe_attack` currently only takes one `defender` and returns one `xp_gain`/`gold_gain`.
- The `ApplyPath` splash logic currently only applies damage (`extra_damage`), it doesn't seem to trigger rewards for splash kills.
- **Action**: Re-evaluate where rewards for splash kills should be generated. 
    - Option A: `ApplyPath` generates reward intents (Complex, `ApplyPath` is supposed to be simple).
    - Option B: `CombatResolutionSystem.resolve_aoe_attack` finds all targets and returns a list of reward intents (Better).
    - Option C: `SimulationDomainLogic.execute_action` for AoE finds all targets.

## 4. Friendly Fire Policy
- Current engine behavior:
    - Direct `ATTACK` on allies is rejected by `LegalityServiceV2.verify_attack_legality` (`FRIENDLY_FIRE_ILLEGAL`).
    - Splash damage hits allies (No faction check in `ApplyPath`).
- This matches "Hardcore RPG" laws where AoE is dangerous. We will preserve this but verify it with tests.
