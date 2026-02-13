# Combat & Progression

Technical documentation for combat formulas, damage types, elements, leveling, death/respawn, and the speed/delay system.

---

## Overview

Combat is resolved deterministically using effective stats (base + equipment + attribute bonuses + status effects). The system supports dual damage types (physical/magical), elemental vulnerabilities, evasion, critical hits, potion use, and skill-based attacks. Killing enemies awards XP and gold, with level-ups granting permanent stat and attribute growth.

**Primary files:** `src/actions/combat.py`, `src/actions/damage.py`, `src/engine/world_loop.py`

---

## Damage Types (Strategy Pattern)

Each damage type is a `DamageCalculator` subclass registered in `DAMAGE_CALCULATORS`. Combat code calls `get_damage_calculator(damage_type)` and uses the returned `DamageContext` — no if/else branching.

| Type | Calculator | Stat Pair | Attribute Scaling |
|------|-----------|-----------|-------------------|
| **PHYSICAL** (0) | `PhysicalDamageCalculator` | ATK vs DEF | STR boosts attack (+2%/pt), VIT boosts defense (+1%/pt) |
| **MAGICAL** (1) | `MagicalDamageCalculator` | MATK vs MDEF | SPI boosts attack (+2%/pt), WIS boosts defense (+1%/pt) |

The weapon's `damage_type` field selects the calculator. Training action is `attack` for physical, `magic_attack` for magical.

---

## Combat Resolution Pipeline

Each attack is processed in `CombatAction.apply()`:

### Step 1: Evasion Check

```
effective_evasion = defender.effective_evasion() - attacker.stats.luck * 0.002
evasion_chance = clamp(effective_evasion, 0.0, 0.75)
if random_roll < evasion_chance → MISS (no damage)
```

- Attacker's `luck` reduces defender's evasion
- Evasion capped at 75%

### Step 2: Base Damage (Attribute-Enhanced)

```
atk_power = attacker.effective_atk() * sanctuary_atk_mult    # or effective_matk()
def_power = defender.effective_def() * sanctuary_def_mult     # or effective_mdef()

atk_mult = 1.0 + attacker_primary_attr * 0.02
def_mult = 1.0 + defender_primary_attr * 0.01

damage = int(atk_power * atk_mult) - int(def_power * def_mult) // 2
damage = max(damage, 1)
```

- Minimum 1 damage guaranteed
- Sanctuary multipliers apply to non-hero entities on sanctuary tiles (default 0.5×)

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

### Step 6: Apply Damage

```
defender.stats.hp -= int(damage)
attacker.next_act_at += speed_delay(attacker.effective_spd(), "attack")
```

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

## On-Kill Rewards

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

---

## Leveling System

Level-ups checked each tick in `WorldLoop._check_level_ups()`.

### Level-Up Condition

```
while entity.stats.xp >= entity.stats.xp_to_next and level < max_level:
    level up
```

Excess XP carries over.

### Stat Growth Per Level

| Stat | Growth | Config Key |
|------|--------|------------|
| Max HP | +5 | `stat_growth_hp` |
| ATK | +1 | `stat_growth_atk` |
| DEF | +1 | `stat_growth_def` |
| SPD | +1 | `stat_growth_spd` |

Current HP also increases by `stat_growth_hp` (capped at new max).

### Attribute Growth Per Level

On each level-up, `level_up_attributes()` is called:
- All **9** primary attributes: **+2** (capped at current cap)
- All **9** attribute caps: **+5**

### XP Curve

```
xp_to_next = int(xp_to_next * xp_per_level_scale)
```

| Config | Default |
|--------|---------|
| `xp_per_kill_base` | 30 |
| `xp_per_level_scale` | 1.5 |
| `max_level` | 20 |

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

## Chase Mechanics (epic-05)

Two systems that add depth to melee engagement and pursuit.

**Primary files:** `src/engine/world_loop.py`

### Opportunity Attacks

When an entity moves away from an adjacent hostile (Manhattan distance increases), the hostile gets a free reduced-damage hit:

```
damage = max(1, int(attacker_atk * opportunity_attack_damage_mult) - defender_def // 2)
```

- `opportunity_attack_damage_mult`: 0.5 (half-damage)
- No crit, no evasion check
- Generates threat on the mover
- Emits `"combat"` event with `verb=OPPORTUNITY_ATTACK`

### SPD-Based Chase Closing

Faster hunters periodically gain a bonus tile of movement when chasing slower prey:

```
interval = ceil(chase_spd_closing_base * target_spd / hunter_spd)
if chase_ticks % interval == 0 → bonus move toward target
```

- `chase_spd_closing_base`: 6
- Only triggers for HUNT-state entities with higher SPD than target
- Emits `"movement"` event with `verb=CHASE_SPRINT`

---

## Speed & Action Delay System

Defined in `src/core/attributes.py` via `speed_delay()`. Uses logarithmic diminishing returns with action-type multipliers.

### Formula

```
delay = action_mult / (1.0 + ln(max(spd, 1)))
```

Clamped to `[0.15, 2.0]` seconds.

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
| Move | ×1.0 | Baseline |
| Attack | ×0.9 | Slightly faster than moving |
| Skill | ×1.2 | Slower (powerful abilities) |
| Loot | ×0.7 | Fast pickup |
| Harvest | ×0.7 | Fast gathering |
| Use Item | ×0.6 | Fastest (potions should be quick) |
| Rest | ×1.0 | Same as baseline |

For non-combat actions, the `interaction_speed` derived stat further scales delay.

### Engagement Lock (Anti-Kite)

Tracked via `Entity.engaged_ticks`, incremented each tick adjacent (Manhattan ≤ 1) to a hostile. Reset to 0 when no hostiles adjacent.

When `engaged_ticks >= 2`, moving away costs **double** the normal delay:
- Slow tanky builds can pin down fast enemies
- Fast builds still act more often but can't kite indefinitely
- Penalty paid once per disengage, then `engaged_ticks` resets

---

## Death & Respawn

### Hero Death

1. All **bag items** dropped as ground loot at death position
2. **Equipment** preserved (weapon, armor, accessory stay)
3. HP restored to `max_hp`
4. Teleported to `home_pos` (town center)
5. AI state set to `RESTING_IN_TOWN`
6. Action cooldown: `hero_respawn_ticks` (10 ticks)
7. Combat memory cleared

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
