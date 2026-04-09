# World Evolution & Town Resilience

Technical documentation for the global difficulty scaling, faction aggression, building durability, and historical legacy systems introduced in Epic 19.

---

## Overview

As the simulation progresses, the world undergoes "Evolution" (becoming more dangerous) and "Pressure" (factions attacking the town). To counter this, "Resilience" mechanics allow heroes to defend and repair the town, and "Historical Legacy" ensures that fallen legends empower future generations.

**Primary files:** `src/engine/world_loop.py`, `src/core/world_state.py`, `src/core/buildings.py`, `src/core/monuments.py`, `src/actions/raid.py`, `src/actions/repair.py`

---

## 1. World Evolution

### Global Difficulty Scaling
The world age determines the overall threat level.
- **World Age**: Incremented every tick (`WorldState.world_age`).
- **Difficulty Modifier**: Calculated as `1.0 + (world_age // 10000) * 0.1`.
- **Stat Scaling**: `EntityGenerator.spawn()` multiplies base monster HP and ATK by this modifier.
  - *Example*: At World Age 20,000, a newly spawned goblin will have 1.2x base stats.

### Faction Aggression & War Status
Factions (Goblins, Wolves, Bandits, etc.) grow more hostile based on their proximity to town and hero activity.
- **Aggression Tracking**: `WorldState.faction_aggression` (0.0 to 100.0).
- **Growth**: Increments by `0.001` per tick. Attacks on faction members accelerate this.
- **War Declaration**: If aggression reaches **80.0**, the faction enters a **WAR** state with the town.
  - **Tier Escalation**: During WAR, the `EntityGenerator` has a `+15%` increased probability of spawning higher-tier entities (Warriors/Elites) to target the town.
  - **Aggression Decay**: Aggression only drops (truce) if it falls below **50.0**.

---

## 1.5 Strategic Resilience (Milestone 11)

The world's regions dynamically shift between Hero and Monster control based on the **Influence Index**.

### Regional Influence
- **Shift Calculation**:
  - **Hero Death**: `-5.0` Influence (favors Monsters).
  - **Monster Death**: `+5.0` Influence (favors Heroes).
- **Safe-Zones** (`Influence > 80.0`):
  - **Population Suppression**: `50%` reduction in monster spawn rates.
  - **Tier Cap**: Spawns are capped at **SCOUT** tier or lower.
- **Conquered Regions** (`Influence < -80.0`):
  - **Stronghold Spawning**: A static **Stronghold** entity is spawned at the region center.
  - **`CONQUERED_DEBUFF`**: Heroes in the region suffer **0.8x ATK/DEF** as long as the stronghold stands.

---

---

## 2. Town Resilience

### Building Durability & Sabotage
Buildings are fixed targets in the town.
- **Durability**: Attributes added to `Building` class (`durability`, `max_durability`).
- **Functional State**: `is_functional` remains `True` if `durability > 0`. If 0, the building services are disabled.
- **Sabotage Damage**: `CombatAction` handles attacks on buildings. 
  - Buildings take **50% of attacker's raw ATK** as damage.
  - Attacks cost 5 stamina and trigger standard global cooldown.
- **Raid Targeting**: `RaidAI` logic:
  1. Target closest hero if within range 5.
  2. If no heroes near, target closest **functional** building for sabotage.

### Repair System (`src/actions/repair.py`)
Heroes can maintain the town's integrity.
- **RepairAction**: A hero adjacent (Manhattan distance ≤ 1) to a damaged building can perform a repair.
- **Requirements**: Hero must have at least 10 gold.
- **Effect**: Restores **50 Durability** for a flat cost of **10 Gold**.
- **Yields**: Standard attribute training (STR/END).

---

## 3. Historical Legacy (Monuments)

To provide a sense of continuity, legendary heroes are immortalized.

### Monument Spawning
In `WorldLoop._phase_cleanup()`, when a hero suffers **Permanent Death**:
- **Requirement**: `entity.stats.level >= 15`.
- **Creation**: A `Monument` is added to `WorldState.monuments`.
- **Data**: Records hero name, class, level, and home position.
- **Buff Type**: Assigned dynamically by class:
  - **Warrior**: `hp` buff.
  - **Mage/Ranger**: `atk` buff.

### Global Buff Application
`WorldLoop._apply_monument_buffs()` runs when a new hero is replacement-spawned:
- **HP Buff**: Each HP monument provides a **1.1x multiplier** (multiplicative stacking).
- **ATK Buff**: Each ATK monument provides a **1.1x multiplier** (multiplicative stacking).
- These buffs help later generations survive the increased difficulty of an older world.

---

## 3.5 The Legend's Legacy: Succession and Inheritance [PHASE 4]

While Monuments provide global stat buffs, Phase 4 introduces **Direct Continuity** between specific individuals and their homes.

### Successor and Heirloom Transfer
- **Successor Assignment**: Upon the permanent death of a "Legend" (Tier 2 or Level 15+), a successor may be designated.
- **Inheritance Records**: The `SuccessorRecord` maps the authoritative transfer of identity fragments.
- **Transfer Channels**:
    - **Gear**: Heirlooms and legendary equipment can be recovered by the designated heir.
    - **Reputation**: A portion of the predecessor's public standing (Heroism/Notoriety) is carried over.
    - **Motive Fragments**: Unresolved long-term goals or grudges are inherited, driving multi-generational storylines.

### Household and Home Continuity
- **Persistent Anchors**: The `HouseholdRecord` ties entities to a shared home building (`home_building_id`).
- **Group Memory**: Households retain collective reputation and storage levels, ensuring that a home remains a sanctuary even as its occupants change.
- **Generational Tracking**: The `generation` field on entities tracks their ancestral depth within a specific household or lineage.

---

---

## 4. Endgame Convergence

The simulation identifies clear win/loss states based on the town's survival.

### Victory (The Golden Age)
- **Condition**: `world_age >= 50,000` AND **All buildings** are functional with `durability > 80%` max.
- **Result**: Simulation stops with a success state.

### Defeat (The Fall)
- **Condition**: `world_age >= 50,000` AND **3 or more buildings** are destroyed (0 durability).
- **Result**: Simulation stops with a failure state.
