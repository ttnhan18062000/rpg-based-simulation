# Entities & Factions: The Aspect-Oriented Model

In the WorldLoop RPG, every agent (Heroes, Wolves, Goblins, etc.) is an `Entity`. Following the **Aspect-Oriented Architecture (AOA)**, entities are no longer monolithic objects but are composed of discrete, domain-specific **Aspects**.

---

## 1. The Entity Container

The `Entity` class (`src/core/entities/entity.py`) serves as a shell that coordinates lifecycle events (ticks) and enforces synchronization between its aspects.

### Core Properties
- **`id`**: A unique, monotonic integer assigned at spawn.
- **`kind`**: The archetype string (e.g., `"hero"`, `"bandit_archer"`, `"wolf"`).
- **`next_act_at`**: The absolute tick time when the entity is next allowed to act (Speed-based).

### Execution Guarantees
- **Phase-Locked Mutation**: Entities can only be mutated during the **Resolution** phase. any attempt to change an attribute during AI Deliberation will raise a `RuntimeError`.
- **Deep-Copy Snapshots**: When the engine creates a snapshot, it uses `model_copy(deep=True)` to ensure that the read-only view is 100% isolated from the simulation thread.

---

## 2. Aspect Decomposition

Each aspect encapsulates a specific domain of the entity's existence.

### 2.1 IdentityAspect
Handles the "soul" and social standing of the entity.
- **`display_name`**: User-facing name.
- **`faction`**: The `Faction` enum identifying alignment.
- **`role`**: `EntityRole` (HERO, MOB, BOSS, NPC).
- **`tier`**: Difficulty level (0=Basic, 3=Elite).
- **`traits`**: List of 2–4 `TraitType` enums (Aggressive, Greedy, etc.).
- **`life_directive`**: Permanent narrative goal (e.g., `"MONSTER_HUNTER"`).

### 2.2 SpatialAspect
Handles the entity's physical presence in the 2D grid.
- **`pos`**: `Vector2` location.
- **`facing`**: Direction of last movement (used for flanking math).
- **`vision_range`**: Perception radius (Manhattan distance).

### 2.3 CombatAspect
Handles health, damage throughput, and active status effects.
- **`hp` / `max_hp_base`**: Current and base maximum health.
- **`atk_base` / `def_base` / `spd_base`**: Authoritative base stats.
- **`matk_base` / `mdef_base`**: Magical base stats.
- **`crit_rate` / `crit_dmg` / `evasion`**: Secondary combat probabilities.
- **`elem_vuln`**: Dictionary of elemental multipliers (FIRE, ICE, etc.).
- **`effects`**: List of active `StatusEffect` objects.
- **`traces`**: A ring buffer of `CombatTraceRecord` for UI introspection.

### 2.4 ProgressionAspect
Handles RPG growth, currency, and skill mastery.
- **`level` / `xp` / `xp_to_next`**: Traditional leveling state.
- **`gold` / `fame`**: Economic and social currency.
- **`stamina` / `max_stamina`**: Resource for movement and skills.
- **`skills`**: List of `SkillInstance` objects with cooldown/mastery state.
- **`attributes`**: The 9 primary attributes (STR, AGI, VIT, INT, SPI, WIS, END, PER, CHA).
- **`aptitudes`**: Genetic multipliers (0.8x - 1.25x) affecting attribute training speed.

### 2.5 MindAspect
The most complex aspect, decomposed into cognitive sub-domains:
- **`decision`**: Current `AIState` (HUNT, FLEE, etc.) and Utility AI goal scores.
- **`perception`**: Sensory memory of seen entities (`entity_memory`) and territory (`terrain_memory`).
- **`emotion`**: Real-time emotional spikes (`panic`, `bravery`) and long-term `grudges`.
- **`navigation`**: A* path cache and movement history.
- **`narrative`**: A log of high-impact "Glory" and "Trauma" events.

### 2.6 InventoryAspect
Handles item management and equipment.
- **`equipment`**: Slots for weapon, armor, and accessories.
- **`bag`**: A list of `ItemInstance` objects (Clamped by weight/slots).

---

## 3. Factions & Territory

Factions define how entities perceive the world and each other.

### World Factions
| Faction | Dominant Race | Primary Territory | Relations |
| :--- | :--- | :--- | :--- |
| **HERO_GUILD** | Hero | Town / Sanctuary | Allied with all Heroes. |
| **GOBLIN_HORDE**| Goblin | Camp / Ruins | Hostile to all others. |
| **WOLF_PACK** | Wolf | Forest / Cave | Neutral to nature, Hostile to Town. |
| **UNDEAD** | Skeleton/Zombie | Swamp / Graveyard | Hostile to all life. |
| **ORC_TRIBE** | Orc | Mountain / Volcanic | Territorial, extremely aggressive. |

### Territory Debuffs
Stepping onto hostile territory (e.g., a Hero entering a Goblin Camp) applies immediate passive debuffs:
- **ATK/DEF Reduction**: ~20-30% penalty.
- **Alert Trigger**: Spawns in the area gain a perception boost toward the intruder.
- **Aggression Scaling**: Presence in a territory slowly builds faction-wide "War Ugency."

---

## 4. Trait Effects

Traits are multiplicative modifiers applied to an entity's AI and Stats.

- **Aggressive**: +5% ATK, -20% Flee utility, -10% Flee threshold.
- **Greedy**: +40% Looting utility, prioritizes High-Value items.
- **Arcane Gifted**: +10% MATK, +5% SPI training speed.
- **Cowardly**: +40% Flee utility, doubles morale loss on teammate death.

---

## 5. Genetic Seeds & Evolution

Every NPC and Hero is seeded with a `genetic_seed`. This seed determines:
1.  **Aptitudes**: Which stats the entity "learns" faster (e.g., a Warrior with high STR aptitude).
2.  **Longevity**: The maximum number of ticks before the entity naturally "retires" or reaches its `longevity_limit`.
3.  **Inheritance**: When an entity dies, its replacement (next `generation`) may inherit a portion of the predecessor's reputation or "World Fame."
