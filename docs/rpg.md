# WorldLoop RPG: Authoritative Simulation Logic

This document is the consolidated, exhaustive source of truth for every RPG-based aspect and logic of the WorldLoop simulation. It excludes infrastructure, API, and frontend details, focusing entirely on the core simulation mechanics.

---

## 1. Simulation Core & Execution Flow

### 1.1 The Tick Cycle (4-Phase Pipeline)
The simulation operates on a deterministic, tick-based engine. Each simulation tick executes a strict 4-phase pipeline in `world_loop.py` to ensure determinism:

1.  **Scheduling & Snapshoting**:
    *   The engine identifies entities due to act (`next_act_at <= current_tick`).
    *   An immutable `Snapshot` of the world is created for AI workers to read.
    *   Tasks are fanned out to **RabbitMQ** (Distributed) or a **ThreadPool** (Local).
2.  **AI Decision Collection**:
    *   Worker daemons receive the snapshot once per tick (Fanout).
    *   Workers compute decisions (`AIBrain.decide`) for assigned entities and push `ActionProposals` to a results queue.
    *   The engine blocks until all results are collected or a hard timeout (e.g., 2s) is reached.
3.  **Conflict Resolution & Application**:
    *   Proposals are sorted deterministically (by `next_act_at`, then `entity_id`).
    *   Each action is validated against the *current* state (e.g., "is the target still reachable?").
    *   Valid actions are applied sequentially to the `WorldState`.
4.  **Post-Tick & Event Emission**:
    *   Subsystems update: XP gains, Level-ups, Stamina regen, Status effect ticks.
    *   State deltas are published to the **Redis Stream** for immediate SSE delivery.
    *   Periodic snapshots are pushed to **Kafka** for persistence.

### 1.2 Determinism
All randomness uses `DeterministicRNG` with `Domain`-specific hashing (`xxhash`). The same seed produces identical outcomes across any machine by seeding with `(Seed, Domain, EntityID, Tick)`.
*   **Domain.COMBAT**: Damage variance, crit rolls, evasion.
*   **Domain.AI**: Goal scoring variance, wander directions.
*   **Domain.MAP_GEN**: Biome placement, resource node yields.

---

## 2. World Generation & Biomes

The simulation world is a **512×512** 2D tile grid generated deterministically from `world_seed`.

### 2.1 Tile Materials (23 Types)
| Value | Name | Walkable | Description |
|-------|------|----------|-------------|
| 0 | FLOOR | Yes | Default open terrain |
| 1 | WALL | No | Impassable barrier |
| 2 | WATER | No | Impassable (currently) |
| 3 | TOWN | Yes | Hero safe zone |
| 4 | CAMP | Yes | Enemy stronghold |
| 5 | SANCTUARY | Yes | Debuff buffer around town |
| 6 | FOREST | Yes | Dense woodland — wolves |
| 7 | DESERT | Yes | Arid wasteland — bandits |
| 8 | SWAMP | Yes | Dark bogland — undead |
| 9 | MOUNTAIN | Yes | Rocky highlands — orcs |
| 10 | ROAD | Yes | Speed bonus (+30%) for movement |
| 11 | BRIDGE | Yes | Speed bonus, crosses water |
| 12 | RUINS | Yes | Explorable structures |
| 13 | DUNGEON_ENTRANCE | Yes | Future dungeon access point |
| 14 | LAVA | No | Impassable hazard |
| 15 | GRASSLAND | Yes | Open plains — centaurs |
| 16 | SNOW | Yes | Frozen tundra — frost kin |
| 17 | JUNGLE | Yes | Dense tropical canopy — lizardfolk |
| 18 | SHALLOW_WATER | Yes | Wading depth, slow movement |
| 19 | FARMLAND | Yes | Cultivated land, fast movement |
| 20 | CAVE | Yes | Underground passages |
| 21 | VOLCANIC | Yes | Ash and magma terrain — demons |
| 22 | GRAVEYARD | Yes | Haunted burial grounds |

### 2.2 Zone: Town & Sanctuary
*   **Town (13x13)**: Centered at (256, 256).
    *   **Hero Healing**: Heroes in `RESTING_IN_TOWN` heal `hero_heal_per_tick` (3) HP/tick.
    *   **Passive Heal**: Heroes in town regenerate `town_passive_heal` (1) HP/tick (blocked if adjacent hostile).
    *   **Town Aura Damage**: Hostile entities on TOWN tiles lose `town_aura_damage` (2) HP/tick.
*   **Sanctuary (25x25)**: Ring around town.
    *   Enemies receive territory debuffs (ATK/DEF reduction).
    *   Enemy AI triggers retreat behavior on sanctuary tiles.

### 2.3 Terrain Regions (Voronoi Biomes)
Eight biomes are placed via Voronoi tessellation to ensure 100% map coverage. Regions scale in difficulty by Manhattan distance from town.

| Distance from Town | Tier | HP/ATK/DEF Mult | XP/Gold Mult |
|-------------------|------|-----------------|---------------|
| ≤ 80 | 1 | 1.0× | 1.0× |
| ≤ 150 | 2 | 1.5×/1.3×/1.2× | 1.5× |
| ≤ 220 | 3 | 2.5×/2.0×/1.8× | 3.0× |
| > 220 | 4 | 4.0×/3.0×/2.5× | 5.0× |

### 2.4 Race & Faction Distribution
| Terrain | Race | Faction | Mob Tiers (Basic → Elite) |
|---------|------|---------|---------------------------|
| FOREST | Wolf | WOLF_PACK | wolf → dire_wolf → alpha_wolf |
| DESERT | Bandit | BANDIT_CLAN | bandit → bandit_archer → bandit_chief |
| SWAMP | Undead | UNDEAD | skeleton → zombie → lich |
| MOUNTAIN | Orc | ORC_TRIBE | orc → orc_warrior → orc_warlord |
| GRASSLAND | Centaur | CENTAUR_HERD | centaur → centaur_lancer → centaur_elder |
| SNOW | Frost | FROST_KIN | frost_wolf → frost_giant → frost_shaman |
| JUNGLE | Lizard | LIZARDFOLK | lizard → lizard_warrior → lizard_chief |
| VOLCANIC | Demon | DEMON_HORDE | imp → hellhound → demon_lord |

### 2.5 Road Networks
Generated from town center to the **8 nearest region centers** using L-shaped paths. 
*   **Speed Bonus**: Entities on ROAD or BRIDGE tiles receive a **+30% movement speed bonus**.
*   **Terrain Cost**: Pathfinding treats ROAD/BRIDGE as cost `0.7` (vs `1.0` baseline).

---

## 3. Resource Nodes & Harvesting

Harvestable nodes are scattered within terrain regions (4 per region).

### 3.1 Resource Registry (`TERRAIN_RESOURCES`)
| Terrain | Resource Type | Yields | Max Harvests | Respawn (ticks) | Channel (ticks) |
|---------|--------------|--------|-------------|-----------------|-----------------|
| **FOREST** | herb_patch / timber / berry_bush | herb / wood / wild_berries | 3 / 4 / 2 | 25 / 30 / 20 | 2 / 3 / 1 |
| **DESERT** | gem_deposit / cactus_fiber / sand_iron | raw_gem / fiber / iron_ore | 2 / 3 / 3 | 35 / 20 / 30 | 3 / 2 / 3 |
| **SWAMP** | mushroom_grove / bog_iron / dark_moss | glowing_mush / iron_ore / dark_moss | 3 / 3 / 2 | 25 / 30 / 20 | 2 / 3 / 2 |
| **MOUNTAIN** | ore_vein / crystal_node / quarry | iron_ore / ench_dust / stone_block | 4 / 2 / 3 | 30 / 40 / 35 | 3 / 4 / 3 |
| **SNOW** | ice_crystal / frozen_herb / bone | frost_shard / herb / bone | 2 / 2 / 3 | 40 / 30 / 35 | 3 / 3 / 3 |
| **JUNGLE** | exotic_plant / venom_gland / timber | herb / venom / wood | 3 / 2 / 4 | 25 / 30 / 30 | 2 / 2 / 3 |
| **VOLCANIC** | obsidian / sulfur / fire_crystal | obsidian / sulfur / ench_dust | 3 / 2 / 2 | 35 / 30 / 40 | 3 / 2 / 4 |

### 3.2 Node Lifecycle
1.  **Available**: (remaining > 0, cooldown = 0).
2.  **Depleted**: (remaining == 0). grey on map.
3.  **Respawning**: `cooldown_remaining` decrements each tick.
4.  **Respawned**: (remaining = max_harvests, cooldown = 0).

---

## 4. Entities & Factions

Every agent in the simulation is an `Entity`. Each entity belongs to exactly one **Faction**. 

### 4.1 Entity Model (`src/core/models.py`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique, monotonic, never reused |
| `kind` | str | Type name (e.g. "hero", "goblin", "wolf") |
| `pos` | Vector2 | Current grid position |
| `stats` | Stats | HP, ATK, DEF, SPD, level, gold, stamina, etc. |
| `ai_state` | AIState | Current FSM state |
| `next_act_at` | float | Absolute time this entity can act again |
| `alive` | bool | Gate for scheduling |
| `faction` | Faction | Which faction this entity belongs to |
| `tier` | int | Enemy difficulty tier (0–3) |
| `home_pos` | Vector2 \| None | Spawn/respawn position |
| `inventory` | Inventory \| None | Items carried + equipment slots |
| `home_storage` | HomeStorage \| None | Hero's persistent home storage |
| `attributes` | Attributes \| None | 9 primary attributes (STR, AGI, etc.) |
| `attribute_caps` | AttributeCaps \| None | Attribute growth limits |
| `death_count` | int | Incremented on respawn (perm-death at limit) |
| `generation` | int | Sequence number for replacements (1, 2, 3...) |
| `hero_familiarity` | dict[int, float] | Proximity-based bond scoring (0.0–1.0) |
| `hero_class` | int | HeroClass enum value (0=NONE) |
| `skills` | list[SkillInstance] | Learned skills with runtime state |
| `class_mastery` | float | 0.0–100.0 |
| `effects` | list[StatusEffect] | Active buffs/debuffs |
| `traits` | list[TraitType] | Personality traits (2–4 per entity) |
| `quests` | list[Quest] | Tracked quests (hero only) |
| `known_recipes` | list[str] | Recipe IDs learned from blacksmith |
| `craft_target` | str \| None | Current crafting goal |
| `terrain_memory` | set[tuple] | Explored tile positions |
| `entity_memory` | dict | Last-seen positions of other entities |
| `reputation` | float | Hero's world prestige (0.0–1.0+) |
| `facing` | Vector2 | Last movement direction (for Flanking) |
| `vision_range` | int | Perception radius (Manhattan distance) |
| `engaged_ticks` | int | Consecutive ticks adjacent to a hostile |

### 4.2 Faction Identities & Relations
| Faction | Value | Territory Tile | Kind Mapping |
|---------|-------|---------------|--------------|
| HERO_GUILD | 0 | TOWN | `hero` |
| GOBLIN_HORDE | 1 | CAMP | `goblin`, `goblin_scout`, `goblin_warrior`, `goblin_chief` |
| WOLF_PACK | 2 | FOREST | `wolf`, `dire_wolf`, `alpha_wolf` |
| BANDIT_CLAN | 3 | DESERT | `bandit`, `bandit_archer`, `bandit_chief` |
| UNDEAD | 4 | SWAMP | `skeleton`, `zombie`, `lich` |
| ORC_TRIBE | 5 | MOUNTAIN | `orc`, `orc_warrior`, `orc_warlord` |
| CENTAUR_HERD | 6 | GRASSLAND | `centaur`, `centaur_warrior`, `centaur_chief` |
| FROST_KIN | 7 | SNOW | `frost_wolf`, `frost_giant`, `frost_shaman` |
| LIZARDFOLK | 8 | JUNGLE | `lizard`, `lizard_warrior`, `lizard_chief` |
| DEMON_HORDE | 9 | VOLCANIC | `imp`, `hellhound`, `demon_lord` |

**Relations**: All factions are **HOSTILE** to each other by default. Same-faction entities are **ALLIED**.

### 4.3 Territory System & Debuffs
When an entity steps on hostile territory, `TERRITORY_DEBUFF` is applied.

| Faction | Tile | ATK Debuff | DEF Debuff | SPD Debuff | Alert Radius |
|---------|------|-----------|-----------|-----------|-------------|
| HERO_GUILD | TOWN | 0.6× | 0.6× | 0.8× | 6 |
| GOBLIN_HORDE | CAMP | 0.7× | 0.7× | 0.85× | 6 |
| WOLF_PACK | FOREST | 0.8× | 0.8× | 0.9× | 5 |
| BANDIT_CLAN | DESERT | 0.75× | 0.75× | 0.85× | 6 |
| UNDEAD | SWAMP | 0.7× | 0.7× | 0.8× | 7 |
| ORC_TRIBE | MOUNTAIN | 0.75× | 0.75× | 0.85× | 6 |
| CENTAUR_HERD | GRASSLAND | 0.8× | 0.8× | 0.9× | 8 |
| FROST_KIN | SNOW | 0.7× | 0.7× | 0.8× | 6 |
| LIZARDFOLK | JUNGLE | 0.75× | 0.75× | 0.85× | 5 |
| DEMON_HORDE | VOLCANIC | 0.65× | 0.65× | 0.75× | 7 |

---

## 5. Attributes, Classes & Skills

### 5.1 Primary Attributes
| Attribute | Field | Effect |
|-----------|-------|--------|
| **STR** | `str_` | Physical ATK (+2%/pt), carry weight |
| **AGI** | `agi` | SPD (+0.4/pt), crit (+0.4%/pt), evasion (+0.3%/pt) |
| **VIT** | `vit` | Max HP (+2/pt), physical DEF (+0.3/pt) |
| **INT** | `int_` | XP gain (+1%/pt), MATK (+0.2/pt), cooldown reduction |
| **SPI** | `spi` | MATK (+0.6/pt), MDEF (+0.15/pt) — primary magic offense |
| **WIS** | `wis` | MDEF (+0.4/pt), luck (+0.3/pt), XP gain (+0.5%/pt) |
| **END** | `end` | Max stamina (+2/pt), max HP (+0.5/pt), HP regen |
| **PER** | `per` | Vision range (+0.3/pt), loot quality, detection |
| **CHA** | `cha` | Trade prices (+1%/pt), interaction speed, social influence |

### 5.2 Derived Stat Formulas
*   **Max HP**: `base + VIT×2 + END×0.5`
*   **ATK**: `base + STR×0.5`
*   **DEF**: `base + VIT×0.3`
*   **MATK**: `base + SPI×0.6 + INT×0.2`
*   **MDEF**: `base + WIS×0.4 + SPI×0.15`
*   **SPD**: `base + AGI×0.4`
*   **Crit Rate**: `base + AGI×0.004`
*   **Evasion**: `base + AGI×0.003`
*   **Luck**: `base + WIS×0.3`
*   **Max Stamina**: `base + END×2`
*   **HP Regen**: `1.0 + END×0.15 + VIT×0.05`
*   **XP Multiplier**: `1.0 + INT×0.01 + WIS×0.005`

### 5.3 Attribute Training
| Action | Trained Attributes |
|--------|-------------------|
| `attack` | STR +0.015, AGI +0.008 |
| `magic_attack` | SPI +0.015, INT +0.008 |
| `move` | AGI +0.008, END +0.005, PER +0.003 |
| `harvest` | END +0.010, WIS +0.005, PER +0.004 |
| `skill` | INT +0.010, WIS +0.005, SPI +0.008 |
| `trade` | CHA +0.012, WIS +0.003 |
| `defend` | VIT +0.010, END +0.008 |

### 5.4 Hero Classes & Breakthroughs
| Class | Tier | Req | Primary Scaling | bonuses |
|-------|------|-----|----------------|---------|
| **Warrior** | 1 | Spawn | STR=S, VIT=A | STR+3, VIT+2, END+1 |
| **Ranger** | 1 | Spawn | AGI=S, END=A | AGI+3, WIS+2, END+1 |
| **Mage** | 1 | Spawn | SPI=S, WIS=A | INT+2, SPI+3, WIS+2 |
| **Rogue** | 1 | Spawn | AGI=S, STR=B | STR+2, AGI+2, WIS+1 |
| **Champion** | 2 | Lv10, STR 30+ | STR=SS, VIT=S | (Warrior → Champion) |
| **Archmage** | 2 | Lv10, INT 30+ | SPI=SS, INT=S | (Mage → Archmage) |

### 5.5 Mastery Benefits
| Tier | Mastery | Power | Cost | Cooldown |
|------|---------|-------|------|----------|
| **Novice** | 0–24% | 1.0x | 1.0x | 1.0x |
| **Apprentice** | 25–49% | 1.0x | 0.9x | 1.0x |
| **Adept** | 50–74% | 1.2x | 0.9x | 0.9x |
| **Expert** | 75–99% | 1.2x | 0.8x | 0.9x |
| **Master** | 100% | 1.35x | 0.8x | 0.8x |

---

## 6. AI System & Behavior (Hybrid Architecture)

Entity AI uses a **hybrid architecture** combining **Utility AI** for goal evaluation with a **State Machine** for execution. The goal evaluator picks *what* to do; the state handler executes *how* to do it.

### 6.1 Goal Evaluation (Utility AI)
Each goal is a `GoalScorer` subclass that returns a utility score (0.0–1.0+).

#### Goal Registry (9 Built-in Goals)
| Goal | Maps to State | Key Factors & Scoring Logic |
|------|---------------|----------------------------|
| **COMBAT** | HUNT | Enemy proximity, power comparison, HP ratio. Boosted by Aggressive trait. |
| **FLEE** | FLEE | HP ratio < flee threshold (default 30%, modified by Mood and Traits). |
| **EXPLORE** | WANDER | HP/stamina health, no enemies. Curiosity trait boosts this. |
| **LOOT** | LOOTING | Ground items nearby. Aborts if inventory is full (0.0 score). |
| **TRADE** | VISIT_SHOP | Sellable items, gold pouches. Urgency (+0.4) if bag > 80% full. |
| **REST** | RESTING_IN_TOWN | Low HP (< 50%) or low stamina (< 20%). High priority in town. |
| **CRAFT** | VISIT_BLACKSMITH | Check for learned recipes and material availability in inventory. |
| **SOCIAL** | VISIT_GUILD | Low intel on world map or lack of active quests. |
| **GUARD** | GUARD_CAMP | Non-hero mobs. Distance from home territory and intruder presence. |

#### Score Modifiers
Goals are filtered through a pipeline of `ScoreModifier` objects:
- **SocialModifier**: Boosts `SOCIAL` goals if the entity has not interacted with an ally for > 500 ticks.
- **SkirmishModifier**: Boosts `FLEE` or `MOVE` for ranged entities when an enemy is adjacent (Tactical Kiting).
- **EconomicModifier**: Boosts `TRADE` when total gold > 100 or redundant gear is detected.

### 6.2 AI State Machine (18 Handlers)
Each state uses a specialized `StateHandler` to propose actions.

| State | Logic & Transitions |
|-------|---------------------|
| **IDLE** | Re-evaluates goals via `GoalEvaluator`. Transitions to winning goal's `target_state`. |
| **WANDER** | Moves toward unexplored tiles (frontier). Mob `leash_radius` enforced (returns to camp if too far). |
| **HUNT** | Navigates to target via A*. Transitions to `COMBAT` when in range. Aborts if target lost or HP too low. |
| **COMBAT** | Attacks or uses `best_ready_skill()`. Uses potions if HP < 50%. Transitions to `FLEE` if HP < threshold. |
| **FLEE** | Moves away from nearest threat. Heroes flee toward town; mobs toward camp. |
| **RETURN_TO_TOWN** | Greedy navigation toward town center. Transitions to `RESTING` on arrival. |
| **RESTING_IN_TOWN** | Heals at `hero_heal_per_tick` (3). Triggers economy cycle (Shop -> Blacksmith -> Guild) once full. |
| **LOOTING** | Moves to item position. Channels `loot_progress`. Proposes `LOOT` action on completion. |
| **VISIT_SHOP** | Sells trash/materials. Buys upgrades and potions (if < 2). Handles rep-based discounts. |
| **VISIT_BLACKSMITH** | Learns recipes. Picks `craft_target` (best upgrade). Crafts if materials + gold available. |
| **VISIT_GUILD** | Reveals camp/node locations (Intel). Generates quests if slots available (< 3). |
| **VISIT_CLASS_HALL** | Learns skills (costs gold). Checks for breakthrough eligibility (Tier upgrade). |
| **VISIT_INN** | Rapid HP/Stamina recovery. Triggers "Gossip" events (Intel sharing). |
| **VISIT_HOME** | Upgrades storage. Deposits low-priority items (materials, excess consumables). |
| **HARVESTING** | Finds node within 8 tiles. Moves and channels harvest. Proposes `HARVEST` on completion. |
| **ALERT** | Triggered by territory intrusion. Seeks and engages intruder. Returns to `GUARD` if safe. |

### 6.3 Boredom & Tactical Nuances
*   **Boredom Penalty**: Every time a goal is selected, its base multiplier drops to **0.8**. It recovers by **+0.02** per tick. This forces behavioral variety.
*   **Diagonal Deadlock Prevention**: If two hostiles are at Manhattan distance 2 (diagonally), the higher-ID entity rests (waits) so the lower-ID entity can close the gap.
*   **Skill Selection**: `best_ready_skill()` prefers AoE if > 1 enemy nearby; else highest power single-target.
*   **Boss Ability Rotation**: Calamity bosses use a fixed sequence (e.g., Summon -> Slam -> Strike) instead of reactive scoring.

### 6.4 Perception & Memory
*   **Vision Range**: Limited by `vision_range` (Manhattan).
*   **Terrain Memory**: Persistent for heroes; mobs may forget after 1000 nodes.
*   **Entity Memory**: Expires after **200 ticks** if subject is unseen.
*   **Threat-Based Targeting**: Mobs prioritize targets with higher `damage_inflicted` (Threat).

---

## 7. Combat & Progression

### 7.1 Action Delay (The Speed Formula)
`delay = action_mult / (1.0 + ln(max(spd, 1)))`
*   **Min Delay**: 0.3s | **Max Delay**: 4.0s
*   **Action Mults**: Skill (2.5), Move (2.0), Attack/Rest (1.5), Loot/Harvest (1.2), Use Item (1.0).

### 7.2 Damage Pipeline
1.  **Dodge Check**: Skip if `RNG < defender.evasion`.
2.  **Accuracy/Block Check**: (Future implementation).
3.  **Base Damage**: `attacker.atk - (defender.def * 0.5)`. (Min 1).
4.  **Flanking Bonus**: `+20%` if `attacker` is behind `defender` (dot product < 0).
5.  **Multipliers**: 
    *   **Tier Diff**: `+10%` per tier higher than target.
    *   **Regional Debuff**: `0.7x` to `0.8x` if on enemy territory.
6.  **Stamina Penalty**: `0.8x` damage if `attacker.stamina < 10`.
7.  **Variance**: `±10%` (`0.9x` to `1.1x`).
8.  **Critical Hit**: `x1.5` if `RNG < attacker.crit_rate`.
9.  **Elemental Multiplier**: `x1.5` or `x0.5` based on `elem_vuln`.

### 7.3 Experience (XP) & Gold Scaling
XP/Gold rewards scale by enemy tier and region difficulty.
*   **Level Brackets**: 1-10 (Fast), 11-20 (Moderate), 21-30+ (Slow).
*   **XP Formula**: `base_xp * multiplier`.
    *   Tier 0 (Basic): 20 XP
    *   Tier 1 (Scout): 45 XP
    *   Tier 2 (Warrior): 100 XP
    *   Tier 3 (Elite): 250 XP
    *   Tier 4 (Boss): 1000+ XP

### 7.4 Respawning & Permadeath
*   **Mob Respawn**: 100–300 ticks (tier-dependent).
*   **Hero Respawn**: 50 ticks. Teleports to center, enters `RESTING_IN_TOWN`.
*   **Generation System**: When an entity hits `death_limit` (Life count), it is permanently removed and a "New Generation" entity of the same kind is spawned to maintain population.

---

## 8. Economy, Items & Buildings

As entities interact with the world, they generate an economy through looting, trading, and crafting.

### 8.1 Town Buildings & Functional Resilience
Buildings provide critical services but are vulnerable to sabotage.
- **Service Registry**:
  | Building | Type | AI State | Service |
  |----------|------|----------|---------|
  | General Store | `store` | VISIT_SHOP | Sell trash/mats, buy potions & equipment. |
  | Blacksmith | `blacksmith` | VISIT_BLACKSMITH | Crafting & recipe learning. |
  | Adventurer's Guild | `guild` | VISIT_GUILD | Map intel, quest generation. |
  | Class Hall | `class_hall` | VISIT_CLASS_HALL | Skill training & Tier breakthroughs. |
  | Traveler's Inn | `inn` | VISIT_INN | Rapid HP/stamina recovery & gossip. |
  | Hero's House | `hero_house` | VISIT_HOME | Long-term storage & item safety. |
- **Durability & Repair**:
  - Buildings starts with `500/500` durability.
  - **Damage**: Mobs in RAID state deal `50% of ATK` per strike.
  - **Disabling**: If `durability <= 0`, the building is non-functional and AI will skip its associated state.
  - **Repairing**: Heroes adjacent to a damaged building can propose a `REPAIR` action.
    - **Cost**: 10 Gold.
    - **Effect**: +50 Durability.
    - **Training**: Yields STR and END experience for the hero.

### 8.2 Items & Inventory (Exhaustive Registry)
Items are pre-defined in `data/items.json` and categorized by type and rarity.

#### Weapon Scaling (Sample)
| ID | Display Name | ATK | SPD | Crit | Range | Rarity |
|----|--------------|-----|-----|------|-------|--------|
| `wooden_club` | Wooden Club | +2 | 0 | 0% | 1 | Common |
| `iron_sword` | Iron Sword | +4 | 0 | 0% | 1 | Common |
| `steel_sword` | Steel Sword | +6 | +1 | 0% | 1 | Uncommon |
| `battle_axe` | Battle Axe | +8 | -1 | 0% | 1 | Uncommon |
| `enchanted_blade`| Enchanted Blade| +10 | +2 | 5% | 1 | Rare |
| `goblin_cleaver` | Goblin Chief Cleaver| +12 | 0 | 10% | 1 | Rare |
| `shortbow` | Shortbow | +3 | +1 | 0% | 3 | Common |
| `longbow` | Longbow | +5 | 0 | 4% | 4 | Uncommon |
| `windpiercer` | Windpiercer | +13 | +2 | 8% | 5 | Epic |

#### Materials & Sell Values
Common materials sell for **5-10g**, Rare for **20-40g**.
- **Materials**: Wood, Iron Ore, Steel Bar, Leather, Enchanted Dust, Herb, Wild Berries, Raw Gem, Fiber, Glowing Mushroom, Dark Moss, Stone Block, Wolf Pelt, Wolf Fang.
- **Loot Heuristic**: Entities prioritize looting items with a higher `gold_value` or rarity if inventory is low.

### 8.3 Crafting & Recipes
Crafting requires specific materials and a gold fee at the Blacksmith.
| Result | Cost | Required Materials |
|--------|------|--------------------|
| **Steel Sword** | 60g | 2× Iron Ore, 1× Wood |
| **Battle Axe** | 90g | 3× Iron Ore, 1× Steel Bar |
| **Iron Plate** | 70g | 3× Iron Ore, 1× Leather |
| **Enchanted Robe**| 150g | 2× Leather, 1× Enchanted Dust |
| **Wolf Cloak** | 50g | 2× Wolf Pelt, 1× Leather |
| **Enchanted Blade**| 200g | 2× Steel Bar, 2× Enchanted Dust |

---

## 9. Personality Traits (Exhaustive Registry)

Entities are assigned **2–4 traits** from the registry. Traits modify **Utility Goals** (additive) and **Passive Stats** (multiplicative).

### 9.1 Trait Definitions & Modifiers
| Trait | Category | Utility Bonuses | Stat Modifiers |
|-------|----------|-----------------|----------------|
| **Aggressive** | Combat | Combat +0.3, Flee -0.2 | ATK 1.05x, Flee Threshold -0.1 |
| **Cautious** | Combat | Combat -0.2, Flee +0.3, Rest +0.1 | DEF 1.05x, Flee Threshold +0.1 |
| **Brave** | Combat | Combat +0.15, Flee -0.3 | Flee Threshold -0.15 |
| **Cowardly** | Combat | Combat -0.3, Flee +0.4, Explore -0.1 | Flee Threshold +0.2 |
| **Bloodthirsty** | Combat | Combat +0.4, Flee -0.3, Rest -0.1 | Crit +5%, Flee Threshold -0.1 |
| **Greedy** | Social | Loot +0.4, Trade +0.2, Combat -0.1 | - |
| **Generous** | Social | Social +0.2, Loot -0.1, Trade -0.1 | - |
| **Charismatic** | Social | Trade +0.3, Social +0.3 | - |
| **Loner** | Social | Explore +0.2, Social -0.3 | - |
| **Diligent** | Work | Craft +0.2, Rest -0.15 | Interaction Speed 1.15x |
| **Lazy** | Work | Rest +0.3, Craft -0.2, Explore -0.1 | Interaction Speed 0.85x |
| **Curious** | Work | Explore +0.4, Loot +0.1 | - |
| **Berserker** | Style | Combat +0.2, Flee -0.2 | ATK 1.1x, DEF 0.9x |
| **Tactical** | Style | Combat +0.1 | - |
| **Resilient** | Style | Rest +0.1 | DEF 1.05x, HP Regen 1.2x |
| **Arcane Gifted**| Magic | - | MATK 1.1x |
| **Spirit Touched**| Magic | - | MDEF 1.1x |
| **Elementalist** | Magic | - | MATK 1.05x, Elem Dmg 1.15x |
| **Keen-Eyed** | Percept | Explore +0.15, Loot +0.1 | Vision +2 |
| **Oblivious** | Percept | Explore -0.15 | Vision -1, Interaction Speed 1.1x |

### 9.2 Inheritance & Incompatibility
- **Incompatible Pairs**: Aggressive/Cautious, Brave/Cowardly, Greedy/Generous, Diligent/Lazy, Keen-Eyed/Oblivious.
- **Race Bias**: Heroes are `2.0x` more likely to be Brave, Goblins `2.5x` more likely to be Greedy.

---

## 10. Strategic World Evolution

### 10.1 Global Scaling & Historical Legacy
- **Global Difficulty**: `1.0 + (world_age // 10000) * 0.1`. Multiplies all enemy base stats.
- **Monuments**: When a hero of Level 15+ dies, they spawn a static monument.
  - **Warrior**: 1.1x global HP multiplier for all future heroes.
  - **Mage/Ranger**: 1.1x global ATK multiplier for all future heroes.
  - Multipliers stack multiplicatively (Infinite scaling vs infinite threat).

### 10.2 Regional Influence & Conquest
- **Influence Calculation**: +5 per monster kill, -5 per hero death.
- **Safe Zones (>80 Influence)**: -50% monster spawn rate, Tier capped at SCOUT.
- **Conquered Zones (<-80 Influence)**:
  - **Stronghold**: Entity that spawns and must be destroyed.
  - **CONQUERED DEBUFF**: Heroes in region suffer **0.8x ATK and DEF**.

### 10.3 Faction Aggression & War
- **Aggression Growth**: +0.001 per tick. Accelerated by hero presence in territory.
- **War (Aggression > 80)**:
  - Entities prioritize the `RAID` state (attacking town).
  - +15% spawn weight for `WARRIOR` and `ELITE` tiers.
- **Calamities (World Bosses)**: Unique events at specific age milestones.
  - Bosess use `template_mult * world_difficulty`.
  - Guaranteed legendary loot drops (e.g., Gorath Cleaver: +50 ATK).

---

## 11. Individual Spirit & Combat Nuances

*   **Nemesis System**: Damage taken adds "grudge". If `grudge > 50`, the target becomes a Nemesis, overriding proximity targeting.
*   **Emotional Mood**:
    *   **Despair (Low Mood)**: Increases flee threshold by +0.15 (flee earlier).
    *   **Fury (High Mood)**: Reduces flee threshold by -0.15 (stay longer).
*   **Renown (Fame)**:
    *   `fame > 50`: Intimidates nearby mobs (reduces their `CombatGoal` score).
    *   `fame > 100`: Triggers fear in `BASIC` mobs, forcing them to `FLEE` immediately.

---

## 12. Pathfinding & Environment Costs

The A* pathfinder uses a grid of costs to bias movement:
| Tile Type | Movement Cost | Multiplier (SPD) |
|-----------|---------------|------------------|
| **Road / Bridge** | 0.7 | 1.5x |
| **TOWN / Floor** | 1.0 (Base) | 1.0x |
| **Grass / Forest**| 1.3 | 0.8x |
| **Swamp / Water** | 1.5 | 0.6x |
| **Mountain / Snow**| 1.4 | 0.7x |
| **Jungle** | 1.6 | 0.5x |

### 12.1 Simulation Constraints
- **Tick Rate**: Default 20 TPS (Ticks Per Second).
- **Snapshot Frequency**: Full state snapshot every 100 ticks for deterministic replay.
- **Cleanup**: Ground items have a TTL (Time-To-Live) of **1,000 ticks**.

---

## 13. Endgame Convergence (Terminal States)

The simulation terminates at **World Age 50,000** with a final verdict:
- **GOLDEN AGE (Victory)**: Age 50,000 reached with **all buildings functional** and average durability > 80%.
- **THE FALL (Defeat)**: **3 or more buildings destroyed** at any point after Age 10,000.
- **THE STRUGGLE (Draw)**: Age 50,000 reached but buildings are damaged or some are destroyed (< 3).

---

## 14. Mathematical & Algorithmic Foundations

This section provides the absolute mathematical source of truth for the core simulation logic.

### 14.1 Action Delay (The Speed Formula)
Calculates when an entity can take its next action. Higher speed reduces delay with diminishing returns.
- **Formula**: `delay = clamp(0.3, 4.0, base_delay * (action_mult / interaction_speed))`
- **Base Delay**: `1.0 / (1.0 + ln(max(spd, 1)))`
- **Action Multipliers (`action_mult`)**:
  | Action | Mult | Action | Mult |
  |--------|------|--------|------|
  | `use_item` | 1.0 | `loot / harvest` | 1.2 |
  | `attack / rest`| 1.5 | `move / building` | 2.0 |
  | `skill` | 2.5 | - | - |
- **Interaction Speed**: Stat derived from `CHA` and `INT` that specifically divides delay for `loot`, `harvest`, `use_item`, and `rest`.

### 14.2 The Damage Pipeline
Resolved sequentially in `CombatAction.apply()`:
1.  **Evasion Check**: Roll `RNG [0, 1)`. If `RNG < max(0.0, evasion - luck * 0.002)`, attack fails.
2.  **Base Damage Calculation**:
    - **Physical**: `raw_dmg = (atk_power * atk_mult) - (def_power * def_mult) // 2`
    - **Magical**: `raw_dmg = (matk_power * matk_mult) - (mdef_power * mdef_mult) // 2`
3.  **Variance**: `damage = int(max(raw_dmg, 1) * (1.0 + 0.1 * (rng_float - 0.5)))`
4.  **Elemental Modifier**: `damage = int(damage * defender.elem_vuln[element])`
5.  **Critical Hit**: Roll `RNG [0, 1)`. If `RNG < min(0.8, crit_rate + luck * 0.003)`:
    - `damage = int(damage * crit_dmg_mult)`

### 14.3 Experience & Progression Math
- **Kill XP**: `base_xp (20) * defender_level * (1.0 + defender_tier * 0.5)`
- **XP Multiplier**: `1.0 + (INT * 0.01) + (WIS * 0.005)`
- **Level Requirement**: `xp_to_next = int(100 * (level ** 1.5))`

### 14.4 Fractional Attribute Training
Attributes are not increased directly but through a fractional accumulator.
- **Formula**: `new_frac = old_frac + (base_rate * race_train_rate * aptitude * talent_mult * weakness_mult)`
- **Constants**: `talent_mult = 2.0`, `weakness_mult = 0.5`.
- **Increment**: If `new_frac >= 1.0`, integer attribute increases by 1 (clamped at `cap`) and `new_frac -= 1.0`.
- **Sample Rates (`base_rate`)**:
  - `attack`: STR +0.015, AGI +0.008
  - `move`: AGI +0.008, END +0.005, PER +0.003
  - `harvest`: END +0.010, WIS +0.005, PER +0.004

### 14.5 AI Selection Logic (Softmax)
When multiple goals are viable, the AI picks one using a temperature-controlled Softmax.
1.  **Goal Filtering**: Goals with `score <= 0.0` are discarded.
2.  **Top-N Selection**: Only the top 3 scoring goals are considered.
3.  **Softmax Weights**: `weight_i = exp((score_i - max_score) / temperature)`
4.  **Temperature**: `T = 0.05 + openness * 0.3`.
    - Low `T` (Low Openness) makes the AI nearly deterministic (picks max score).
    - High `T` (High Openness) makes the AI more probabilistic/creative.

### 14.6 Economic Formulas
- **Buy Price**: `base_price * (1.0 - min(0.3, reputation * 0.01))`
- **Sell Value**: `base_value * (1.0 + min(0.2, reputation * 0.005))`
- **Building Repair**: `durability += 50` at a flat cost of **10 Gold**.

### 14.7 Emotional & Mental Recovery
- **Mood Decay**: Mood returns to baseline (0.5) at a rate of `±0.01` per tick.
- **Boredom Recovery**: Each goal's multiplier recovers by `+0.02` per tick (max 1.0).
- **Hysteresis**: Active goal receives a **1.25x** score multiplier to prevent "shivering" between states.
