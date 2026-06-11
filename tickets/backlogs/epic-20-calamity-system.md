# epic-20: Calamity (World Boss) System

**Status**: 🗓️ Draft (design-04 / epic-20)

## Epic Summary
Introduce high-stakes "Calamity" events—dynamic World Boss encounters that spawn in the simulation's endgame. These events anchor the "Progression Spine" (Epic 17) by providing the ultimate challenge for high-level heroes, yielding legendary loot, world-wide fame, and unique "Transcendence" class transformations.

## Rationale
As heroes reach the level cap and the "Long-Story Spine" (Epic 17) matures, the world requires a high-stakes mechanism to cycle power and reward absolute mastery. Calamities provide a dynamic endgame threat that prevents stagnation, forces high-level hero cooperation, and provides the only path for **Transcendence Class** transformations and **Legendary-tier** gear acquisition.

## Scope & Affected Systems
- **Core Engine**: `src/engine/world_loop.py` (Calamity check & aura application)
- **Data Models**: `src/core/calamities.py` (Templates)
- **Generation**: `src/systems/generator.py` (Spawning logic)
- **Progression**: `src/core/hero_attributes.py` (Transcendence classes & Fame)

---

## 🏗️ Phase 1: The Incarnation (Core Spawning)
The Calamity System uses a "Destiny Check" to trigger boss arrivals. Every 10,000 ticks, a weighted roll is performed to determine if a Calamity manifests.

- **Trigger Weights**: The spawn probability increases based on a combination of:
    - **World Evolution**: Flat increase per 50,000 ticks of world age.
    - **Hero Concentration**: Exponential increase if 3+ high-level heroes are within the same tile radius (50x50).
    - **Metaphysical State**: Randomized "Blood Moon" events that multiply the current spawn weight by 2x.
- **Dynamic Scaling**: Boss stats (HP/ATK) are calculated at the moment of spawn, scaling linearly with the number of high-level heroes (Level 15+) currently active in the simulation.
- **The Omen**: A 1,000-tick warning period where the target region enters a "Pre-Calamity" state. Local common monsters receive a +25% stat buff ("Touch of the Void").

## 🌪️ Phase 2: The Calamity Aura (Regional Impact)
Calamities project a regional aura that fundamentally alters simulation rules within their domain. Upon manifestation, a Calamity randomly selects 2-4 **Void Fluctuations** from the global table:

- **Mechanical Fluctuations**: 
    - *Mana Static*: Hero Skills have a 50% failure rate (consumes stamina but no effect).
    - *Slowdown*: All move/act delays are multiplied by 1.5x.
    - *Terror*: Defensive evasion stats for all non-legendary entities are halved.
- **Environmental Fluctuations**:
    - *Stamina Drain*: Passive -2 stamina per tick for all heroes in the region.
    - *Fog of War*: Hero vision range is hard-capped to 2 tiles.
    - *Economic Freeze*: Resource nodes and treasure chests cease regeneration.
- **Metaphysical Fluctuations**:
    - *Void Corruption*: Fallen heroes have a 10% chance per tick to rise as hostile Shadow Spirits.
    - *Guild Unity (Positive)*: Heroes gain +10% ATK for each ally within a 5-tile radius.

## ⚔️ Phase 3: The Slaying (Combat & Rewards)
The battle flow is designed to force high-level engagement and tactical coordination.

- **Combat Mechanics**:
    - **Enrage (30% HP)**: The boss gains +50% SPD and doubles the potency of its active Void Fluctuations.
    - **The Immortal Veil (60% HP)**: Upon reaching this threshold, the boss becomes immune to damage. Three **Void Pylons** spawn within 10 tiles; all must be destroyed to break the shield.
    - **Summoner Presence**: Every 1,000 ticks, a wave of Void Minions spawn. These minions prioritize healing the boss if they reach its melee range.
- **Victory & Rewards**:
    - **The Final Blow**: The hero who lands the killing blow gains a unique permanent title and a massive Fame multiplier (2x).
    - **Legendary Loot Pool**: Guaranteed drop of a unique "Named" item (e.g., *The Void-Render*) with stats exceeding Standard Epic-tier gear by 30%.
    - **The World-Sigh**: Upon victory, the global world-age "Difficulty Scaling" is suspended for 10,000 ticks as the world "heals."

## 🎓 Phase 4: The Legacy (Transcendence & Fame)
Victory against a Calamity leaves a permanent mark on both the world and the participants.

- **Transcendence Class Induction**: Heroes who participate significantly in the fight (dealing >5% total HP damage) unlock a **Transcendence** upgrade for their class:
    - **Void Reaver (Warrior)**: Basic attacks ignore 50% defense and can "Silence" targets (preventing skills).
    - **Star-Gazer (Mage)**: Vision range extends to 15; skills can reach any target in sight.
    - **Spectral Stalker (Ranger)**: Evasion is doubled for the first 3 ticks of any combat encounter.
    - **Blood-Oath Knight (Champ)**: Gains +1 HP per monster killed in the world (legacy scaling).
- **The Hall of Fame**:
    - **Monument Spawning**: A static "Monument of Victory" is placed in the Hero Guild town, displaying the slayer's name and the Calamity's type.
    - **Aura of the Victor**: Legendary heroes project a subtle passive buff (+5% XP) to all lower-level allies within a 10-tile radius.
    - **Legendary Merchant**: Reaching "Master" Fame unlocks a hidden vendor who trades in high-tier reagents found only in Calamity regions.

---

## 🛠️ Technical Implementation Details
For developers implementing this system:

- **Simultaneous Final Blows**: If multiple entities reduce the boss to <= 0 HP on the same tick, the "Final Blow" goes to the entity that dealt the highest total damage *during that tick*.
- **Calamity Concurrency**: Only one Calamity can be active in the world at a time. A new spawns check will not trigger until the previous one is defeated or despawned.
- **Void Pylon Entities**: Pylons are spawned as `kind="prop"` with fixed HP (10,000) and no AI. They must be added to the `WorldState` spatial index.
- **Fame Attribute**: Add `fame: float = 0.0` to the `Stats` model.
- **Effect Mapping**: Void Fluctuations should be implemented as a new `EffectType.VOID_AURA` that is applied globally to all entities in the target region during the `_apply_calamity_auras` phase.

**Tier:** epic
**Type:** feature
**Priority:** P2
