# Entities & Factions: The Aspect-Oriented Model (v2)

In the WorldLoop RPG, every agent (Heroes, Mobs, NPCs) is an `Entity`. Following the **Resource-Safe Engine (v2)** architecture, entities are composed of discrete **Aspects** and governed by strict authoritative mutation laws.

---

## 1. The Entity Shell

The `Entity` class (`src_v2/core/entities/entity.py`) coordinates lifecycle events and enforces synchronization between its aspects.

### Core Properties
- **`id`**: A unique, monotonic integer.
- **`kind`**: The archetype string (e.g., `"hero"`, `"wolf"`).
- **`next_act_at`**: The absolute tick when the entity is next allowed to act.

### Authoritative Execution Laws
1.  **Generation-Based Apply**: In v2, entities are never deep-cloned during a standard tick. Instead, they are updated through the `ApplyPath`, which creates the next "Generation" of the entity state. This ensures that shared references remain read-only for observers.
2.  **Phase-Locked Mutation**: Entities can only be mutated during the **RESOLUTION** phase of the kernel. Any attempt to modify a field during AI Deliberation results in a simulation halt.
3.  **Shallow Packetization**: For AI workers, entities are wrapped in a `WorkerPacket` which provides a shallow, read-only view of the actor and its immediate surroundings.

---

## 2. Aspect Decomposition

### 2.1 IdentityAspect
The "Social Fingerprint" and personality of the entity.
- **`faction`**: One of the five primary world factions.
- **`role`**: `HERO`, `MOB`, `BOSS`, or `NPC`.
- **`traits`**: Discrete behavioral modifiers (e.g., `Greedy`, `aggressive`).

### 2.2 SpatialAspect
Physical presence in the 100x100 grid.
- **`pos`**: `Vector2` location.
- **`vision_range`**: Maximum radius for sensory perception.

### 2.3 CombatAspect
Authoritative health and damage state.
- **`hp` / `max_hp_base`**: Authoritative health pools.
- **`atk` / `def` / `spd`**: Derived combat stats based on genetics and level.
- **`status_effects`**: List of active `StatusEffect` objects.

### 2.4 ProgressionAspect
RPG growth and genetic potential.
- **`level` / `xp`**: Progression state.
- **`aptitudes`**: Genetic multipliers (0.8x - 1.2x) that determine how many stats are gained per level. This ensures that two heroes of the same level can have radically different builds.

### 2.5 MindAspect
The cognitive stratum, composed of:
- **`strategic`**: Stores current `Projects` and `Objectives`.
- **`perception`**: Subjective memory of seen threats and terrain.
- **`emotion`**: Persistent `panic` and `bravery` levels.
- **`narrative`**: Log of "Glory" and "Trauma" events.

---

## 3. Factions & Relations

Factions dictate sensory saliency and targeting priority:
- **HERO_GUILD**: Allied with all Heroes.
- **GOBLIN_HORDE**: Hostile to all life.
- **WOLF_PACK**: Neutral to nature, hostile to non-nature intruders.
- **UNDEAD**: Hostile to all life.
- **ORC_TRIBE**: Territorial defenders.

---

## 4. Genetic Seeds

Every entity is initialized with a `deterministic_seed`. This seed generates the unique `Aptitude` pool, ensuring that every entity's career is unique but perfectly reproducible if the world is replayed.

> [!IMPORTANT]
> All Entity state changes MUST flow through the `ApplyPath`. Do not attempt many-to-many mutations or ad-hoc field updates outside the resolution phase.
