---
status: active
layer: systems
authority: P1
audience: developer
---

# World Design: Biomes, Regions & Towns

The world_dynamics.py simulation generates a 100x100 (default) grid-based world where terrain, difficulty, and resource placement are derived from a single `world_seed`.

---

## 1. Grid & Materials

The world is a 2D tile-map where each cell has a `Material` type that dictates movement cost, visibility, and possible resource yields.

| Material | Walkable | Description |
| :--- | :--- | :--- |
| **TOWN / SANCTUARY**| Yes | Permanent safe zones; no hostile spawns allowed. |
| **ROAD / BRIDGE** | Yes | Higher move speed; connects towns to regions. |
| **WALL / MOUNTAIN** | No | Blocks movement and Line of Sight (LoS). |
| **WATER / LAVA** | No | Blocks movement but allows LoS. |
| **FOREST / SWAMP** | Yes | Standard wilderness terrain. |
| **CAMP / RUINS** | Yes | Distinguishable terrain for enemy/resource centers. |

---

## 2. Regions & Procedural Generation

The `WorldGenerator` uses a **Voronoi-based Region Model** to partition the wilderness.

1.  **Seed Placement**: Random centers are picked for each biome type (Forest, Desert, etc.).
2.  **Voronoi Partitioning**: Every tile is assigned to the nearest region seed, creating jagged, natural-looking boundaries.
3.  **Naming**: Regions are named based on their terrain (e.g., "Whispering Woods", "Scorched Wastes").
4.  **Locations of Interest**: Within each region, 3-6 specific locations are spawned:
    - **Enemy Camps**: Highly fortified areas with "Guard" and "Elite" mobs.
    - **Resource Groves**: High-density zones for wood, ore, or herbs.
    - **Ruins**: Isolated spots containing `TreasureChest` nodes.
    - **Boss Arenas**: (Difficulty 3+) Large open areas containing a `WORLD_BOSS`.

---

### Historical Consequences and Scars [PHASE 4]

The WorldLoop simulation engine ensures that major events leave legible traces through the **RegionalConsequenceSystem**.

#### Local Scars
- **Persistence**: Authoritative actions like hero deaths or building sabotage generate `LocalScarRecord` entries.
- **Typing**: Scars are categorized into kinds like `BATTLE_FIELD` (high-casualty zones) or `RAID_DAMAGE`.
- **Decay**: Scars represent medium-term trauma. They decay over hundreds of ticks, reflecting natural recovery or restoration.
- **Behavioral Impact**: Entities can perceive nearby scars, inducing caution or panic (e.g., non-combatants fleeing battlefield zones).

#### Regional Danger and Stability
Each region tracks macro-tier metrics that influence long-term AI strategy:
- **Danger Level**: Aggregated from recent calamity, boss activity, and local casualties.
- **Stability**: A measure of institutional or social order, reflecting the success of local defenses.
- **Macro-Biases**: Regional danger shifts the "fleeing threshold" for all entities in the zone, making them more reactive to situational threats.

#### Recovery Mechanics
The world does not reset after each life. Recovery is a stateful process:
- **Repair**: Damaged buildings move through distinct recovery stages.
- **Normalization**: Regional danger slowly returns to base values if no new trauma is recorded, allowing for historical ebbs and flows.

---

## 3. Difficulty Zoning

Difficulty is determined by the **Manhattan Distance** from the town center (Primary Safe Zone).

| Distance (Tiles) | Tier | Level Range | Stat Multiplier |
| :--- | :--- | :--- | :--- |
| **0 - 15** | 1 | Lv 1 - 3 | 1.0x |
| **16 - 30** | 2 | Lv 3 - 6 | 1.5x HP, 1.3x ATK |
| **31 - 50** | 3 | Lv 5 - 10 | 2.5x HP, 2.0x ATK |
| **51+** | 4 | Lv 8 - 15 | 4.0x HP, 3.0x ATK |

---

## 4. Town & Functional Buildings

The Town center contains essential services for Hero progression.

- **Adventurer's Guild**: The hub where Heroes "check-in" to sync reputation and receive `World Fame`.
- **Blacksmith**: Forges and upgrades equipment. Heroes visit when they have enough gold and materials.
- **General Store**: Sells basic consumables (HP/Stamina Potions).
- **Class Hall**: Facilitates **Evolution** and skill training.
- **Traveler's Inn**: The primary `REST` location for Heroes after long expeditions.
- **Hero Houses**: Private residences where Heroes store excess items (`home_storage`).

- **Regions and Biomes**: Typed zones with distinct resource types, difficulty tiers, and macro-consequence layers.
- **Grids and Navigation**: Authoritative coordinate resolution and Bilinear Flow Field pathfinding.
- **World Objects**: Interactive nodes (Nodes, Chests, Buildings) with stateful persistence.
- **World Eras and Seasons**: Time-based difficulty scaling and event-driven day/night cycles.
- **Historical Consequences [PHASE 4]**: Persistent scars and regional danger levels that outlast single episodes.

---

## 5. Economic Ecosystem

The world economy is closed-loop:
1.  **Harvesting**: Heroes and some NPCs gather materials from `ResourceNode`s.
2.  **Looting**: Killing mobs or opening chests generates Gold and Items.
3.  **Expending**: Heroes spend Gold at shops (Store/Blacksmith), which cycles back into the "Town Wealth" (affecting building reinforcement and future stock).
4.  **Death**: When a Hero dies, 80% of their Gold is dropped in a `CorpseNode`, which can be recovered by the Hero or stolen by Goblins.
