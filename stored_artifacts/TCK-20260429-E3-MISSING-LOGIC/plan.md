# Plan: E3 Missing Logic Implementation

## Completed Work

### 1. Stamina System (Checklist Part 6 Section E)
- `StaminaComponent` on EntityState with current/max/regen/exhaustion fields
- `StaminaUpdate` typed update on EntityUpdate
- `StaminaService` in rpg_depth.py: drain_attack/move/harvest/skill, can_use_skill, tick_regen
- Passive regen per tick in apply_generation (rest/active rates)
- Exhaustion penalty integrated into CombatResolutionSystem.resolve_attack
- Movement stamina drain via StaminaUpdate in MovementSystem

### 2. Wound/Scar System (Checklist Part 6 Section E)
- `WoundState` and `ScarState` on EntityState
- `WoundUpdate` typed update on EntityUpdate
- `WoundService` in rpg_depth.py: should_inflict_wound (40% threshold), create_wound, heal_wound→scar
- Wound stat penalties (atk/def/speed/max_hp)
- Scar permanence (30% of original wound penalties)
- Apply path processes wounds/scars and triggers recalculation gate

### 3. Mob Leash (Checklist Section 8)
- NavigationComponent extended with home_position, leash_radius, chase_ticks, max_chase_ticks
- `LeashService` in rpg_depth.py: is_beyond_leash, should_give_up_chase, return_home, is_at_home
- Leash distance check + chase timeout (1.5x leash radius, max_chase_ticks)

### 4. Terrain Cost (Checklist Section 7)
- `TERRAIN_COST` constant table in state.py (ROAD=0.5, PLAIN=1.0, SWAMP=3.0, etc.)
- `TerrainCostService` in rpg_depth.py: get_tile_cost, get_path_cost
- Movement readiness cost now terrain-weighted in MovementSystem
- `terrain` field added to WorkerPacket

### 5. Target Stickiness (Checklist Z5)
- `TargetStickinessService` in rpg_depth.py: should_switch_target
- Margin-based switching (30% improvement needed)
- Loyalty factor increases with ticks on current target

### 6. Skill Scaling (Checklist Z10)
- `SkillScalingService` in rpg_depth.py: calculate_skill_damage
- Physical (STR), Magical (INT), Elemental (SPI+INT) formulas
- `get_effective_stats` integrates gear + wounds + scars + passives
- Replaces raw LevelingService.recalculate_combat_stats in apply gate

### 7. Attribute Caps
- `ATTRIBUTE_CAP = 99` and enforce_attribute_caps() in rpg_depth.py
- Evasion capped at 0.95

## Files Changed
- src/core/state.py (StaminaComponent, WoundState, ScarState, NavigationComponent leash, TERRAIN_COST, EntityState)
- src/core/updates.py (StaminaUpdate, WoundUpdate, EntityUpdate, merge)
- src/core/worker_protocol.py (WorkerPacket terrain field)
- src/engine/rpg_depth.py (NEW - all services)
- src/engine/combat.py (exhaustion integration)
- src/engine/movement.py (terrain cost, stamina drain)
- src/engine/apply.py (stamina/wound apply + recalculation gate)
- src/engine/executor.py (terrain in packet)
- tests/rpg/test_rpg_depth.py (NEW - 54 tests)
