---
status: active
layer: systems
authority: P1
audience: developer
---

# Combat & Progression

> [!NOTE]
> **Compliance Status**: This system is 95% certified. See the [Gap Analysis](../compliance/gap_analysis.md) for known logic issues regarding `status_sleeping` and dead actor rejection.

Technical documentation for combat formulas, damage types, elements, leveling, death/respawn, and the speed/delay system.

---

## Overview

Combat is resolved deterministically using effective stats (base + equipment + attribute bonuses + status effects). The system supports dual damage types (physical/magical), elemental vulnerabilities, evasion, critical hits, potion use, and skill-based attacks. Killing enemies awards XP and gold, with level-ups granting permanent stat and attribute growth. All logic is encapsulated in **Aspects** (`CombatAspect`, `ProgressionAspect`, `MindAspect`).

**Primary files:** `src/actions/combat.py`, `src/actions/damage.py`, `src/engine/world_dynamics.py`, `src/actions/base.py` (Proposals)

### Global Scaling
As the world ages, the difficulty scales globally. All spawned entities receive a stat multiplier based on the current world age. See [World Evolution & Resilience](../systems/world_evolution_and_resilience.md) for the scaling formula.

---

## Damage Types (Strategy Pattern)

Each damage type is a `DamageCalculator` subclass registered in `DAMAGE_CALCULATORS`. Combat code calls `get_damage_calculator(damage_type)` and uses the returned `DamageContext` — no if/else branching.

| Type | Calculator | Stat Pair | Attribute Scaling |
|------|-----------|-----------|-------------------|
| **PHYSICAL** (0) | `PhysicalDamageCalculator` | ATK vs DEF | STR boosts attack (+2%/pt), VIT boosts defense (+1%/pt) |
| **MAGICAL** (1) | `MagicalDamageCalculator` | MATK vs MDEF | SPI boosts attack (+2%/pt), WIS boosts defense (+1%/pt) |

The weapon's `damage_type` field selects the calculator. Training action is `attack` for physical, `magic_attack` for magical.

---

## 2.5 Regional Conquest Debuffs

Strategic control of a region directly impacts combat efficacy through the **Regional Conquest** system.

| Condition | Effect | Multipliers |
|-----------|--------|-------------|
| **Safe Zone** (`influence > 80`) | **Resource Bounty** | `+10%` Loot/Harvest speed |
| **Conquered** (`influence < -80`) | **`CONQUERED_DEBUFF`** | `0.8x` ATK, `0.8x` DEF, `0.9x` SPD |

- **Stronghold Requirement**: The debuff is only active in a conquered region if a monster **Stronghold** entity is present.
- **Application**: Applied to all `HERO_GUILD` entities in the region during the world tick.

---

## Combat Resolution Pipeline

Each attack is processed in `CombatAction.apply()`:

### Step 1: Evasion Check

```
effective_evasion = defender.effective_evasion() - attacker.stats.luck * 0.002
evasion_chance = max(0.0, effective_evasion)
if random_roll < evasion_chance → MISS (no damage)
```

- Attacker's `luck` reduces defender's evasion
- Evasion capped at 75%

### Step 2: Base Damage Calculation
Damage is calculated using the **Fractional Armor Mitigation** formula (Pillar 3):

```
atk_final = attacker.combat.atk * attacker_primary_mult * skill_power
def_final = defender.combat.def * defender_primary_mult

# Pillar 3: Non-linear mitigation
raw_damage = int(atk_final * (atk_final / (atk_final + def_final * 2.0 + 1.0)))
damage = max(raw_damage, 1)
```

- Minimum 1 damage guaranteed
- Sanctuary multipliers apply to non-hero entities on sanctuary tiles (default 0.5×)

### Step 2c: Flanking Bonus
If the attacker is behind the defender (attacker.pos is opposite to defender.facing), a **1.5x damage multiplier** is applied.
- Calculated in `PhysicalDamageCalculator.resolve()`.
- Facing is based on the target's last movement direction.

### Step 2b: Stamina Cost

Each attack costs 3 stamina. If stamina reaches 0, the entity can still attack but gains no attribute training.

### Step 3: Damage Variance

```
variance_roll = rng.next_float(Domain.COMBAT, attacker.id, tick)
damage = damage * (1.0 + damage_variance * (variance_roll - 0.5))
```

- `damage_variance` defaults to 0.3 (±15% spread)
- Uses deterministic RNG seeded by attacker ID and tick

### Step 4: Critical Hit

```
crit_chance = attacker.effective_crit_rate() + attacker.stats.luck * 0.003
crit_chance = clamp(crit_chance, 0.0, 0.80)
if random_roll < crit_chance:
    damage = damage * attacker.stats.crit_dmg
```

- Luck adds 0.3% per point; capped at 80%
- `crit_dmg` default: 1.5× (hero starts at 1.8×)

### Step 5: Elemental Vulnerability

```
element = weapon_element or skill_element  (default NONE)
vulnerability = defender.stats.elem_vuln.get(element, 1.0)
damage = damage * vulnerability
```

- Values > 1.0 = weakness, < 1.0 = resistance, 0.0 = immune

### Step 6: Authoritative Application
Since the **AOA Stabilization**, the engine does not mutate HP directly in the resolution service. Instead, it emits a **`CombatTraceUpdate`**:

```python
# In CombatAction.apply()
proposal.updates.append(CombatTraceUpdate(
    result=CombatTraceRecord(
        attacker_id=attacker.id, 
        defender_id=defender.id,
        damage=damage,
        details=CombatTraceDetails(is_crit=is_crit, ...)
    )
))
```

The **`ActionSystem`** later processes these updates authoritatively, applying the damage, generating threat/grudges, and recording the memory log in the same tick.

---

## Elements

| Element | Value |
|---------|-------|
| NONE | 0 |
| FIRE | 1 |
| ICE | 2 |
| LIGHTNING | 3 |
| DARK | 4 |
| HOLY | 5 |

Each entity has an `elem_vuln` table on `Stats` (dict mapping Element → float). Default is 1.0 for all.

---

## On-Kill Rewards (Pillar 1 Stabilization)

Reward logic is precomputed in the **`KillRewardService`** but applied authoritatively.

### XP Award

```
base_xp = xp_per_kill_base * defender.level * (1 + defender.tier * 0.5)
xp_mult = 1.0 + attacker.attributes.int_ * 0.01 + attacker.attributes.wis * 0.005
xp_gained = int(base_xp * xp_mult)
```

- **INT** adds +1% XP per point; **WIS** adds +0.5% XP per point

### Gold Transfer

All of the defender's gold is transferred to the attacker.

### Attribute Training

Combat trains STR (+0.015/action) and AGI (+0.008/action) for physical attacks, SPI (+0.015) and INT (+0.008) for magical attacks. 
- **Stamina Requirement**: If an entity's stamina is **0**, they can still attack but receive **no attribute training**.

---

## 4. Tactical AI Logic

Combat behavior is driven by state-based logic in `src/ai/states.py`.

### 4.1 Target Prioritization
Entities select targets using a hierarchical priority:
1.  **Personal Nemesis**: Visible hostile with `grudge > 50.0` (highest grudge wins).
2.  **Highest Threat**: Non-hero mobs target whoever has the highest value in their `threat_table`.
3.  **Nearest Enemy**: Heroes and mobs without threat/grudges target the closest hostile.

### 4.2 Mood & Fleeing
The decision to retreat (`should_flee`) is sensitive to the entity's **Mood**:
- **Base Threshold**: 15% - 20% HP.
- **Despair (Low Mood)**: Threshold shifts **up** (retreats at ~30% HP).
- **Fury (High Mood)**: Threshold shifts **down** (stays until ~5% HP).

### 4.3 Tactical Maneuvers (Pillar 3: Action)
- **Decision Inertia (Hysteresis):** Entities commit to their current goal for `GOAL_LOCK_TICKS` (5) to prevent behavioral jitter between two high-utility options.
- **Ranged Skirmishing:** Ranged classes maintain a `min_dist` (3 tiles) and will reposition if hostiles close in, utilizing tactical hints from the AI context.
- **Support Priorities:** Agreeable entities (Agreeableness > 0.7) prioritize assisting allies who are at low HP or requested support via the tactical intent phase.

## 5. Nemesis System & Emotional Combat

The Mood system (see 4.2) introduces persistent psychological effects triggered by combat.

### 5.1 Grudges

Every hit received in combat generates a **Grudge** against the attacker.
- **Formula**: `grudge_gain = (damage / max_hp) * 50.0`
- **Effect**: Grudges are stored in the defender's `MindAspect`. If a grudge exceeds **50.0**, the attacker is marked as a **Nemesis**.
- **Behavior**: AI will prioritize targeting their Nemesis even if other closer or higher-threat enemies are visible.

### 5.2 Emotional Mood

Entities possess a dynamic `mood` value (0.2 to 1.0) that reflects their current morale.
- **Morale Loss**: Each hit taken reduces mood: `mood_drop = (damage / max_hp) * 0.2`.
- **Combat Efficacy**: Low mood increases the likelihood of fleeing. At minimum mood (0.2), an entity may flee at **30% HP** (compared to the baseline 15-20%).
- **Recovery**: Mood is reset to a baseline of 0.2 upon respawn.

### 5.3 Bad Memories

When an entity dies, it records a "Bad Memory" of the current region.
- **Sentiment**: A negative sentiment (-1.0) is stored for the region in `memory_locations`.
- **Avoidance**: During future exploration, the entity will treat tiles in "Bad Memory" regions as being much further away, naturally biasing them to explore elsewhere.

---

## 6. Fame & Reputation (Epic 19)

Fame tracks a hero's prestige across the world. It is primarily earned by completing **Calamity Bounties**.
- **Bounty Completion**: +100 Fame.
- **Usage**: Required for Tier 3 Breakthroughs (Level 20 + 100 Fame).

---

## Leveling System

Level-ups checked each tick in `WorldLoop._check_level_ups()`.

### Level-Up Condition

Each entity is bound to a specific `RACE_PROFILE` defining their `train_rate`, `level_cap`, and `evolves` logic.
- Entities without a profile or a `train_rate=0.0` (like `skeleton`) earn 0 XP.

```python
while entity.stats.xp >= entity.stats.xp_to_next and level < profile.level_cap:
    level up
```

Excess XP carries over.

### Stat Growth Per Level

Base dimishing returns stat growth based on the current level bracket:
- Levels 1-10: HP +5, ATK/DEF/SPD +1
- Levels 11-20: HP +3, ATK/DEF/SPD +1
- Levels 21-30: HP +2, ATK/DEF/SPD +0

**Milestone Levels (5, 10, 15, 20, 25, 30)**:
Whenever these levels are crossed, instead of base growth, the entity receives roughly **3x massive stat spikes** (+15 HP, +3 ATK/DEF/SPD). An event is emitted highlighting the milestone.

### Attribute Growth & Genetic Evolution (Pillar 2: Body)

On each level-up, attributes grow based on the entity's **Genetic Aptitudes**:
- **Aptitudes:** Every entity spawns with unique multipliers (e.g., `str_aptitude: 1.2`) for each attribute.
- **Growth Formula:** `attribute += 2 * aptitude`. This ensures that two entities of the same class can develop significantly different power levels over time.
- **Caps:** Attribute caps increase by **+5** per level.

### 2.2 Breakthrough Milestones & Pillar Traits

When an entity crosses major level thresholds, they unlock **Pillar Traits**—massive global multipliers that define their late-game role:

| Level | Milestone | Trait Example | Effect |
| :--- | :--- | :--- | :--- |
| **50** | **Ascension** | **Colossus** | `+50% HP`, `+20% DEF` |
| **75** | **Mastery** | **Archmage** | `+40% MATK`, `-20% Mana Cost` |
| **100** | **Divinity** | **Juggernaut**| `+100% HP`, `CC Immunity` |

These milestones trigger unique world-events and are color-coded in the simulation UI.

### XP Curve

XP to next level dynamically scales by the current level:

- Levels 1-10: `xp_to_next *= 1.4`
- Levels 11-20: `xp_to_next *= 1.6`
- Levels 21-30: `xp_to_next *= 2.0`

---

## Class Breakthroughs & Tier 3 (Transcendence)

Heroes can evolve into more powerful classes once they hit level and stat thresholds.

### Tier 2 (Mastery)
- **Requirement**: Level 10 + Primary Stat 30+.
- **Examples**: Warrior -> Champion, Mage -> Archmage.

### Tier 3 (Transcendence) - Locked by Calamity

- **Requirement**: Level 20 + Primary Stat 50+ + **100 Fame** + **Calamity Remnant** (Legendary material).
- **Process**: Visit the Class Hall with a `Calamity Remnant` in inventory to transcend.
- **Classes**:
    - **WARLORD** (from Champion): Focus on massive HP and ATK. Indomitable passive grants CC immunity.
    - **STORM_CALLER** (from Archmage): Massive AoE magical damage. Tempest passive allows dual-casting.
    - **GHOST_STALKER** (from Sharpshooter): Ultimate ranged precision. Ethereal passive provides high evasion.
    - **NIGHTSHADE** (from Assassin): High crit and poison utility. Venomous passive adds DoT to all hits.

---

## 7. World Boss (Calamity) Combat

Calamities are regional threats that spawn via `world_loop._check_calamity_spawns()`. They require multiple heroes to defeat and use unique mechanics.

### Calamity Auras

Live Calamities apply a **Calamity Aura** within a 15-tile radius via `world_loop._apply_calamity_auras()`.

| Target | Effect | Description |
|--------|--------|-------------|
| **Heroes** | -10% Evasion | Multiplicative debuff for any hero within the radius. |
| **Minions** | +5% ATK | Flat attack boost for allied mobs in range (capped at 3x base). |

*Note: The planned "Void Fluctuations" (Mana Static, Terror, etc.) are currently slated for future enhancement.*

### Combat Mechanics

- **Massive HP**: Calamities have `stat_multiplier` (5.0x - 15.0x) and ignore standard execution thresholds.
- **Regional Lock**: Calamities will not leave their home region and will rapidly heal if kited to a boundary.
- **Final Blow**: The hero who deals the killing blow to a Calamity receives a massive Fame bonus (+100) and the title "Calamity Slayer".

### Loot & Rewards

- **Calamity Remnant**: A mandatory material for Tier 3 Transcendence. Guaranteed drop (1-2 per boss).
- **Legendary Gear**: Unique items (`gorath_cleaver`, `vexira_staff`) with special modifiers.
- **Calamity Essence**: Used for high-tier crafting at the Blacksmith.

---

## Veterancy & Innate Talents

### Veterancy Ranks
Entities earn veterancy points in combat (+1 per hit dealt, +1 survived hit, +5 to +10 per kill). This grants multiplier bonuses over time.
- **GREEN**: 1.0x (0 points)
- **BLOODED**: 1.03x ATK/DEF (25 points)
- **VETERAN**: 1.06x ATK/DEF, 1.05x HP (80 points)
- **ELITE**: 1.1x ATK/DEF/HP, 1.05x SPD (200 points)
- **LEGEND**: 1.15x All Stats (500 points)

### Innate Talents
Every entity generates with 2 random `talents` and 1 `weakness` across the 9 core attributes.  
- Attacking, taking damage, and working adds fractional EXP to `attributes`.
- **Talented** attributes train at `2.0x` speed.
- **Weaknesses** train at `0.5x` speed.

### Near-Death Hardening
When an entity survives a hit with **HP ratio < 0.15**:
- **Max HP permanently increases by +1**.
- This simulates "hardening" through combat survival.
- Veteran NPCs and long-lived heroes often have significantly boosted Max HP from this mechanic.

---

## Potion Use in Combat

When in `COMBAT` state with HP below 50%:

1. Check inventory for potions (priority: large > medium > small)
2. Propose `USE_ITEM` action instead of `ATTACK`
3. Potion consumed, entity heals by `template.heal_amount` (capped at `effective_max_hp()`)
4. Action delay: 0.5 ticks (half a normal action)

| Potion | Heal |
|--------|------|
| `small_hp_potion` | 20 HP |
| `medium_hp_potion` | 40 HP |
| `large_hp_potion` | 80 HP |

---

## Skill-Based Attacks

Skills are used via `USE_SKILL` action when:
- Skill is off cooldown
- Entity has enough stamina
- Target is in range

Skill damage uses `power` multiplier on base damage, skill-specific `damage_type` and `element`, and applies buff/debuff effects based on skill modifiers. See `attributes_and_classes.md` for skill details.

### Status Effect Combos
Certain status effect combinations trigger reactive "Combos" when damage is applied:

| Combo | Requirements | Effect |
|-------|--------------|--------|
| **SHATTER** | Frozen + Physical Damage | **3.0x Damage** + Consumes Frozen effect |
| **OVERLOAD**| Wet + Magical Damage | **2.0x Damage** + Applies Shocked effect |

- Combos are processed in `ActionSystem._apply_skill_effect()`.
- They reward tactical positioning and skill sequencing.

---

## Ranged Combat (epic-05 F4)

Ranged weapons and skills can hit targets beyond melee range, with line-of-sight and cover mechanics.

**Primary files:** `src/core/items.py`, `src/core/grid.py`, `src/actions/combat.py`, `src/ai/states.py`

### Weapon Range

Each weapon has a `weapon_range` field on `ItemTemplate` (default 1 = melee). Ranged weapons:

| Weapon | Range | Type |
|--------|-------|------|
| Swords/Daggers | 1 | Melee |
| Shortbow | 3 | Ranged |
| Longbow/Hunting Bow | 4 | Ranged |
| Staves/Wands | 3 | Ranged (magical) |
| Windpiercer | 5 | Ranged |

### Line of Sight

Ranged attacks require clear LoS via Bresenham's line algorithm (`Grid.has_line_of_sight()`). Any WALL tile between attacker and defender blocks the attack.

### Cover System

Defenders adjacent to a WALL tile get **+10% evasion** against ranged attacks. Checked via `Grid.has_adjacent_wall()`.

### AI Kiting

Ranged entities (weapon_range ≥ 3) kite when:
- Adjacent to enemy (dist ≤ 1)
- HP > 60%
- Propose `MOVE` away instead of attacking

---

## AoE Attacks & Skills (epic-05 F1)

Skills with `AREA_ENEMIES` or `AREA_ALLIES` target types hit multiple entities in a radius.

**Primary files:** `src/core/classes.py` (SkillDef), `src/engine/world_loop.py` (resolution)

### SkillDef Fields

| Field | Type | Description |
|-------|------|-------------|
| `radius` | int | AoE spread from impact point (0 = single target) |
| `aoe_falloff` | float | Damage reduction per tile from center (default 0.15) |

### AoE Skills

| Skill | Class | Range | Radius | Falloff | Power | Type |
|-------|-------|-------|--------|---------|-------|------|
| Whirlwind | Warrior | 1 | 1 | 0.0 | 1.5 | Physical |
| Rain of Arrows | Ranger | 4 | 2 | 0.15 | 1.4 | Physical |
| Fireball | Mage | 4 | 2 | 0.20 | 1.8 | Magical |

### AoE Resolution

1. Impact point = nearest hostile within cast range
2. Collect all valid targets within `radius` of impact point
3. Per target: `damage *= max(0, 1.0 - dist_from_center * aoe_falloff)`
4. Crits only on center target (`dist_from_center == 0`)
5. Damage variance uses unique seed per target (`tick + 5 + eid`)

### AI AoE Preference

`best_ready_skill()` scores AoE skills as `power * nearby_enemies` when multiple enemies are clustered (nearby_enemies > 1), preferring AoE over single-target.

---

## Aggro & Threat System (epic-05 F3)

Enemies track threat per attacker and target the highest-threat entity instead of nearest.

**Primary files:** `src/core/models.py`, `src/actions/combat.py`, `src/engine/world_loop.py`, `src/ai/perception.py`, `src/ai/states.py`

### Threat Table

Each entity has `threat_table: dict[int, float]` mapping attacker IDs to accumulated threat scores.

### Threat Generation

| Source | Formula |
|--------|---------|
| Basic attack damage | `damage * threat_damage_mult` (1.0) |
| Skill damage | `damage * threat_damage_mult` (1.0) |
| Opportunity attack | `damage * threat_damage_mult` (1.0) |
| Tank class bonus | Warrior/Champion get `threat_tank_class_mult` (1.5×) |

### Threat Decay

`_tick_threat_decay()` runs every core tick:
- All threat entries decay by `threat_decay_rate` (10%) per tick
- Entries below 1.0 are pruned
- Dead attacker entries removed

### AI Targeting

- **Mobs** (non-HERO_GUILD): use `highest_threat_enemy()` — target visible hostile with highest threat score, fallback to nearest
- **Heroes**: always use `nearest_enemy()` for intuitive behavior

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `threat_decay_rate` | 0.10 | 10% decay per tick |
| `threat_damage_mult` | 1.0 | Threat per point of damage |
| `threat_heal_mult` | 0.5 | Threat per point of healing (future) |
| `threat_tank_class_mult` | 1.5 | Multiplier for Warrior/Champion |

---

---

## Chase Mechanics (epic-05)

Two systems that add depth to melee engagement and pursuit.

### Opportunity Attacks

When an entity moves away from an adjacent hostile (Manhattan distance increases), the hostile gets a free reduced-damage hit via `_process_opportunity_attacks`:
- **Damage**: `max(1, int(attacker_atk * 0.5) - defender_def // 2)`
- **Properties**: No crit, no evasion check.
- **Threat**: Generates threat on the mover.
- **Event**: Emits `"combat"` with `verb=OPPORTUNITY_ATTACK`.

### SPD-Based Chase Closing

Faster hunters periodically gain a "sprint" move when chasing slower prey via `_process_chase_closing`:
- **Calculated Interval**: `ceil(6.0 * target_spd / hunter_spd)`
- **Effect**: Gains 1 bonus tile of movement toward the target every `interval` ticks.
- **Requirement**: Hunter SPD > Target SPD.

---

## Speed & Action Delay System

Defined in `src/core/attributes.py` via `speed_delay()`. Uses logarithmic diminishing returns with action-type multipliers.

### Formula

```
delay = action_mult / (1.0 + ln(max(spd, 1)))
```

Clamped to `[0.3, 4.0]` ticks.

### SPD → Delay Table (move action)

| SPD | Delay | Actions/tick |
|-----|-------|-------------|
| 1 | 1.00 | 1.0 |
| 5 | 0.53 | 1.9 |
| 10 | 0.38 | 2.6 |
| 20 | 0.31 | 3.2 |
| 50 | 0.24 | 4.2 |

### Action-Type Multipliers

| Action | Multiplier | Effect |
|--------|-----------|--------|
| Move | ×2.0 | Baseline |
| Attack | ×1.5 | Slightly faster than moving |
| Skill | ×2.5 | Slower (powerful abilities) |
| Loot | ×1.2 | Standard interaction |
| Harvest | ×1.2 | Standard interaction |
| Use Item | ×1.0 | Fastest (potions should be quick) |
| Rest | ×1.5 | Same as attack |

For non-combat actions, the `interaction_speed` derived stat further scales delay.

### Engagement Lock (Anti-Kite)

Tracked via `Entity.engaged_ticks`, incremented each tick adjacent (Manhattan ≤ 1) to a hostile. Reset to 0 when no hostiles adjacent.

When `engaged_ticks >= 2`, moving away costs **double** the normal delay:
- Slow tanky builds can pin down fast enemies
- Fast builds still act more often but can't kite indefinitely
- Penalty paid once per disengage, then `engaged_ticks` resets

---

## Death & Respawn

### Hero Death & Permadeath (The Death Tier System)

Heroes follow a tiered death system that escalates with each subsequent defeat.

| Death Count | Consequences |
|-------------|--------------|
| **1st Death** | Drops **Bag Items** only. Respawn at home. |
| **2nd Death** | Drops **Bag Items + Accessory**. Respawn at home. |
| **3rd Death** | Drops **Bag Items + Accessory + Armor**. Respawn at home. |
| **Permadeath** | `death_count >= max`. Drops **ALL gear**. Removed from world. |

**Permadeath Details**:
- **Monuments**: If a hero is Level 15+ upon permadeath, a **Monument** is spawned at their home position, providing localized buffs (+10% HP/ATK) to passing heroes.
- **Generational Replacement**: A new hero of the same generation + 1 is scheduled to spawn at the same house after 50 ticks.
- **Cleanup**: AI memory and active effects are cleared upon every death.

### Enemy Death

1. All items (bag + equipment) dropped as ground loot
2. Entity removed from the world permanently
3. Generator may spawn replacements on schedule

---

## Determinism

All combat calculations use `DeterministicRNG` with domain `Domain.COMBAT`:

- Damage variance: `rng.next_float(COMBAT, attacker_id, tick)`
- Crit roll: `rng.next_bool(COMBAT, attacker_id, tick + 1, chance)`
- Evasion roll: `rng.next_bool(COMBAT, attacker_id, tick + 2, evasion)`

Identical outcomes given the same world seed, regardless of thread scheduling.
