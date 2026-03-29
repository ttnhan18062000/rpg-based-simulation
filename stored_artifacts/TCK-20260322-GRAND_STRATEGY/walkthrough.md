# Walkthrough: Milestone 11 - Grand Strategy

I have implemented the Grand Strategy layer, introducing faction wars, territory conquest, and siege mechanics. This system adds a dynamic strategic layer where regional control shifts based on combat outcomes, affecting both hero performance and world evolution.

## Key Features Implemented

### 1. StrategySystem (`src/systems/strategy_system.py`)
The core of Milestone 11, responsible for:
- **Influence Processing**: Regional control shifts based on faction deaths. Hero deaths decrease influence (monster conquest), while monster deaths increase it (hero liberation).
- **War State Transitions**: Factions enter a `WAR` state when their aggression exceeds 80.0 and return to peace if it falls below 40.0.
- **Siege Mechanics**: Conquered regions (`influence <= -80.0`) spawn `Stronghold` entities. These fortifications must be destroyed by heroes to liberate the region.
- **Regional Debuffs**: Heroes in conquered regions with active strongholds receive a `CONQUERED_DEBUFF` status effect (0.8x ATK/DEF, 0.9x SPD).

### 2. Status Effects & Combat Integration
- **New Effect Type**: Added `CONQUERED_DEBUFF` to `EffectType` in `src/core/effects.py`.
- **Combat Tracking**: Modified `CombatAction.apply` in `src/actions/combat.py` to record faction deaths per region, providing the data needed for influence shifts.
- **Dynamic Stats**: Regional debuffs are automatically applied to heroes' effective stats through the status effect system.

### 3. World Loop & Generator Integration
- **Centralized Strategy**: Moved regional suppression logic from `WorldLoop` to `StrategySystem` for better modularity.
- **Strategic Spawning**: The `EntityGenerator` respects regional control, with safe zones (high hero influence) reducing spawn rates and capping enemy tiers.

## Verification Results

### Automated Tests
I implemented a comprehensive unit test suite in `tests/unit/systems/test_strategy.py` covering all core mechanics.

```bash
pytest tests/unit/systems/test_strategy.py
```

**Results:**
- `test_influence_shifts_on_monster_death`: PASSED (Monster deaths increase hero influence).
- `test_influence_shifts_on_hero_death`: PASSED (Hero deaths decrease influence).
- `test_war_state_transition`: PASSED (War declared at high aggression).
- `test_conquered_region_triggers_stronghold`: PASSED (Strongholds spawn in fallen regions).
- `test_stronghold_debuff_application`: PASSED (Heroes receive debuffs in conquered regions).

## Next Steps
- Implement **Regional Faction Objectives** (e.g., "Build a Trade Hub" or "Raid the Goblin Mine").
- Resolve any remaining **Milestone 12** planning tasks as the simulation evolves.
