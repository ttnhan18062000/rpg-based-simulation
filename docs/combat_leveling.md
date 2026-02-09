# Combat & Leveling System

Technical documentation for combat formulas, damage calculation, and the XP/leveling progression.

---

## Overview

Combat is resolved deterministically using the entity's effective stats (base + equipment bonuses). The system includes defense reduction, evasion rolls, critical hits, sanctuary debuffs, and automatic potion use. Killing an enemy awards XP and gold, with level-ups granting permanent stat growth.

**Primary files**: `src/actions/combat.py`, `src/engine/world_loop.py` (`_check_level_ups`)

---

## Combat Resolution

Each attack is processed in `CombatAction.apply()` with the following pipeline:

### Step 1: Evasion Check

```
effective_evasion = defender.effective_evasion() - attacker.stats.luck * 0.002
evasion_chance = clamp(effective_evasion, 0.0, 0.75)
if random_roll < evasion_chance → MISS (no damage)
```

- Attacker's `luck` stat reduces the defender's evasion
- Evasion is capped at 75%

### Step 2: Base Damage (Attribute-Enhanced)

```
atk_power = attacker.effective_atk() * sanctuary_atk_mult
def_power = defender.effective_def() * sanctuary_def_mult

# Attribute multipliers
str_mult = 1.0 + attacker.attributes.str_ * 0.02   (STR boosts attack)
vit_mult = 1.0 + defender.attributes.vit * 0.01     (VIT boosts defense)

damage = int(atk_power * str_mult) - int(def_power * vit_mult) // 2
damage = max(damage, 1)
```

- Effective ATK/DEF include equipment bonuses
- **STR** amplifies outgoing damage by 2% per point
- **VIT** amplifies defensive mitigation by 1% per point
- Sanctuary multipliers apply to non-hero entities on sanctuary tiles (default 0.5×)
- Minimum 1 damage guaranteed

### Step 2b: Stamina Cost

```
attacker.stats.stamina -= 3
```

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

- Base crit rate from stats + equipment bonuses
- Luck adds 0.3% per point
- Capped at 80%
- `crit_dmg` multiplier (default 1.5×, hero starts at 1.8×)

### Step 5: Apply Damage

```
defender.stats.hp -= int(damage)
attacker.next_act_at += 1.0 / max(attacker.stats.spd, 1)
```

Attack cooldown is inversely proportional to speed.

---

## Sanctuary Debuff

Non-hero entities fighting on `Material.SANCTUARY` tiles receive combat penalties:

| Multiplier | Default | Effect |
|------------|---------|--------|
| `sanctuary_debuff_atk` | 0.5 | ATK halved |
| `sanctuary_debuff_def` | 0.5 | DEF halved |

This makes the sanctuary zone dangerous for enemies, encouraging them to retreat.

---

## On-Kill Rewards

When a defender's HP reaches 0:

### XP Award (Attribute-Enhanced)
```
base_xp = xp_per_kill_base * defender.stats.level * (1 + defender.tier * 0.5)
xp_mult = 1.0 + attacker.attributes.int_ * 0.01 + attacker.attributes.wis * 0.005
xp_gained = int(base_xp * xp_mult)
attacker.stats.xp += xp_gained
```

- **INT** adds +1% XP per point
- **WIS** adds +0.5% XP per point

### Attribute Training from Combat
```
train_attributes(attacker.attributes, attacker.attribute_caps, "attack")
```
Combat trains **STR** (+0.015/action) and **VIT** (+0.005/action) fractionally.

| Config | Default | Description |
|--------|---------|-------------|
| `xp_per_kill_base` | 25 | Base XP per kill |

Example: Killing a Level 3 Warrior (tier 2) = `25 * 3 * (1 + 2*0.5)` = **150 XP**

### Gold Award
```
attacker.stats.gold += defender.stats.gold
defender.stats.gold = 0
```

All of the defender's gold is transferred to the attacker.

---

## Leveling System

Level-ups are checked each tick in `WorldLoop._check_level_ups()`.

### Level-Up Condition

```
while entity.stats.xp >= entity.stats.xp_to_next and level < max_level:
    level up
```

Excess XP carries over to the next level.

### Stat Growth Per Level

| Stat | Growth | Config Key |
|------|--------|------------|
| Max HP | +5 | `stat_growth_hp` |
| ATK | +2 | `stat_growth_atk` |
| DEF | +1 | `stat_growth_def` |
| SPD | +1 | `stat_growth_spd` |

Current HP is also increased by `stat_growth_hp` (capped at new max).

### Attribute Growth Per Level

On each level-up, `level_up_attributes()` is called:

```
All 6 primary attributes: +2 (capped at current cap)
All 6 attribute caps: +5
```

This ensures attributes scale alongside conventional stats as the entity progresses.

### XP Curve

```
xp_to_next = int(xp_to_next * xp_per_level_scale)
```

| Config | Default | Description |
|--------|---------|-------------|
| `xp_per_level_scale` | 1.5 | Multiplier per level |
| `max_level` | 50 | Level cap |

**XP progression example**:
| Level | XP Required |
|-------|-------------|
| 1 → 2 | 100 |
| 2 → 3 | 150 |
| 3 → 4 | 225 |
| 4 → 5 | 337 |
| 5 → 6 | 506 |
| 10 → 11 | 3,844 |

---

## Potion Use in Combat

When in the `COMBAT` AI state with HP below 50%:

1. Check inventory for potions (priority: large > medium > small)
2. If found, propose `USE_ITEM` action instead of `ATTACK`
3. Potion is consumed in `WorldLoop._process_item_actions()`
4. Entity heals by `template.heal_amount`, capped at `effective_max_hp()`
5. Action delay: 0.5 ticks (half a normal action)

| Potion | Heal Amount |
|--------|-------------|
| `small_hp_potion` | 20 HP |
| `medium_hp_potion` | 40 HP |
| `large_hp_potion` | 80 HP |

---

## Hero Death & Respawn

When the hero dies:

1. All **bag items** are dropped as ground loot at death position
2. **Equipment** is preserved (weapon, armor, accessory stay)
3. HP restored to `max_hp`
4. Teleported to `home_pos` (town center)
5. AI state set to `RESTING_IN_TOWN`
6. Action cooldown: `hero_respawn_ticks` (default 10 ticks)
7. Combat memory cleared

### Enemy Death

When a non-hero entity dies:

1. All items (bag + equipment) dropped as ground loot
2. Entity removed from the world permanently
3. Generator may spawn replacements on schedule

---

## Determinism

All combat calculations use `DeterministicRNG` with domain `Domain.COMBAT`:

- Damage variance: `rng.next_float(COMBAT, attacker_id, tick)`
- Crit roll: `rng.next_bool(COMBAT, attacker_id, tick + 1, chance)`
- Evasion roll: `rng.next_bool(COMBAT, attacker_id, tick + 2, evasion)`

This ensures identical combat outcomes given the same world seed, regardless of thread scheduling.
