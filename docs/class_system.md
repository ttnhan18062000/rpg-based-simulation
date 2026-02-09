# Class System — Complete Reference

Source: `src/core/classes.py` | Frontend: `frontend/src/components/ClassHallPanel.tsx`

---

## 1. Overview

Every hero is assigned a **class** at spawn. Classes provide attribute bonuses, scaling grades (E–SSS), learnable skills, and a breakthrough path to an elite class.

---

## 2. Progression Tiers

| Tier | Name | Level | Description |
|------|------|-------|-------------|
| 1 | Base Class | 1+ | Starting class at spawn |
| 2 | Breakthrough | 10+ | Elite class via level + attribute gate |
| 3 | Transcendence | 20+ | *(Future — not yet implemented)* |

```
Warrior  → Champion      → [Transcendence]
Ranger   → Sharpshooter  → [Transcendence]
Mage     → Archmage      → [Transcendence]
Rogue    → Assassin      → [Transcendence]
```

---

## 3. Attribute Scaling Grades

| Grade | Mult | Description |
|-------|------|-------------|
| E | 60% | Minimal benefit |
| D | 75% | Below average |
| C | 90% | Average |
| B | 100% | Baseline |
| A | 115% | Strong |
| S | 130% | Excellent — primary stat |
| SS | 150% | Outstanding — breakthrough tier |
| SSS | 180% | Legendary — reserved |

---

## 4. Base Classes (Tier 1)

### Warrior — Tank / Melee DPS

| STR | AGI | VIT | INT | WIS | END |
|-----|-----|-----|-----|-----|-----|
| **S** | D | **A** | E | D | B |

- **Bonuses:** STR +3, VIT +2, END +1 | Caps: STR +10, VIT +5, END +3
- **Breakthrough:** → Champion (Lv10, STR ≥ 30)

### Ranger — Ranged DPS / Scout

| STR | AGI | VIT | INT | WIS | END |
|-----|-----|-----|-----|-----|-----|
| D | **S** | D | D | **B** | **A** |

- **Bonuses:** AGI +3, WIS +2, END +1 | Caps: AGI +10, WIS +5, END +3
- **Breakthrough:** → Sharpshooter (Lv10, AGI ≥ 30)

### Mage — Ranged DPS / Support

| STR | AGI | VIT | INT | WIS | END |
|-----|-----|-----|-----|-----|-----|
| E | D | C | **S** | **A** | C |

- **Bonuses:** INT +3, WIS +2, VIT +1 | Caps: INT +10, WIS +5, VIT +3
- **Breakthrough:** → Archmage (Lv10, INT ≥ 30)

### Rogue — Melee DPS / Assassin

| STR | AGI | VIT | INT | WIS | END |
|-----|-----|-----|-----|-----|-----|
| **B** | **S** | D | D | C | C |

- **Bonuses:** STR +2, AGI +2, WIS +1 | Caps: STR +5, AGI +8, WIS +3
- **Breakthrough:** → Assassin (Lv10, AGI ≥ 25)

---

## 5. Breakthrough Classes (Tier 2)

### Champion (from Warrior)
- **Scaling:** STR=**SS**, AGI=C, VIT=**S**, INT=E, WIS=D, END=**A**
- **Bonuses:** STR +3, VIT +2 | Caps: STR +10, VIT +5
- **Talent — Unyielding:** Below 25% HP → +30% DEF, +20% ATK for 5 ticks

### Sharpshooter (from Ranger)
- **Scaling:** STR=D, AGI=**SS**, VIT=D, INT=C, WIS=**A**, END=**S**
- **Bonuses:** AGI +3, WIS +2 | Caps: AGI +10, WIS +5
- **Talent — Precision:** Crits deal +25% damage; Quick Shot range +1

### Archmage (from Mage)
- **Scaling:** STR=E, AGI=D, VIT=**B**, INT=**SS**, WIS=**S**, END=**B**
- **Bonuses:** INT +3, WIS +2 | Caps: INT +10, WIS +5
- **Talent — Arcane Mastery:** Skill durations +1 tick; cooldowns −1 tick

### Assassin (from Rogue)
- **Scaling:** STR=**A**, AGI=**SS**, VIT=D, INT=D, WIS=**B**, END=**B**
- **Bonuses:** STR +2, AGI +3 | Caps: STR +5, AGI +8
- **Talent — Lethal:** Guaranteed crit vs targets below 30% HP; Backstab → 2.8x

---

## 6. Class Skills

### Warrior
| Skill | Lv | Gold | Target | Power | CD | Sta | Effect |
|-------|----|------|--------|-------|----|-----|--------|
| Power Strike | 1 | 50 | Enemy | 1.8x | 4 | 12 | — |
| Shield Wall | 3 | 100 | Self | — | 8 | 15 | DEF +50%, 3t |
| Battle Cry | 5 | 200 | AoE Allies | — | 12 | 20 | ATK +20%, 3t |

### Ranger
| Skill | Lv | Gold | Target | Power | CD | Sta | Effect |
|-------|----|------|--------|-------|----|-----|--------|
| Quick Shot | 1 | 50 | Enemy | 1.5x | 3 | 8 | Range 3 |
| Evasive Step | 3 | 100 | Self | — | 7 | 10 | EVA +30%, 3t |
| Mark Prey | 5 | 200 | Enemy | — | 10 | 15 | DEF −25%, 4t |

### Mage
| Skill | Lv | Gold | Target | Power | CD | Sta | Effect |
|-------|----|------|--------|-------|----|-----|--------|
| Arcane Bolt | 1 | 50 | Enemy | 2.0x | 4 | 14 | Range 4 |
| Frost Shield | 3 | 100 | Self | — | 8 | 16 | DEF +40%, 3t |
| Mana Surge | 5 | 200 | Self | — | 12 | 22 | ATK +30%, 4t |

### Rogue
| Skill | Lv | Gold | Target | Power | CD | Sta | Effect |
|-------|----|------|--------|-------|----|-----|--------|
| Backstab | 1 | 50 | Enemy | 2.2x | 4 | 10 | CRIT +15% |
| Shadowstep | 3 | 100 | Self | — | 7 | 12 | EVA +40%, SPD +30%, 2t |
| Poison Blade | 5 | 200 | Enemy | 0.5x | 10 | 15 | DoT 4t |

### Race Skills (Hero — Innate, Free)
| Skill | Lv | Target | Effect |
|-------|----|--------|--------|
| Rally | 1 | AoE Allies | ATK +10%, DEF +10%, 3t, range 3 |
| Second Wind | 3 | Self | Heal 20% max HP, CD 20 |

---

## 7. Skill Mastery Tiers

| Tier | Mastery | Power | Stamina | Cooldown |
|------|---------|-------|---------|----------|
| Novice | 0–24% | — | — | — |
| Apprentice | 25–49% | — | −10% | — |
| Adept | 50–74% | +20% | −10% | — |
| Expert | 75–99% | +20% | −20% | −1 tick |
| Master | 100% | +35% | −25% | −1 tick |

Mastery is gained by using skills. Gain rate has diminishing returns.

---

## 8. Class Hall Building

The **Class Hall** is a town building (`building_type: "class_hall"`) where heroes:
1. Learn new class skills (costs gold)
2. Attempt breakthroughs when requirements are met

### 8.1 Class Hall UI (`ClassHallPanel.tsx`)

The panel features:
- **Class tabs** — Warrior, Ranger, Mage, Rogue with class-colored icons
- **Progression tree** — clickable nodes showing Base → Breakthrough → Transcendence(locked)
- **Class overview** — name, tier badge, role, lore, playstyle description
- **Attribute scaling grid** — 6 columns with color-coded grade badges and multiplier %
- **Base attribute bonuses** — stat bonuses and cap bonuses table
- **Attribute effects reference** — what each attribute does
- **Expandable skill cards** — click to reveal full details (requirements, stats, modifiers)
- **Breakthrough details** — requirements, bonuses, special talent description
- **Mastery tier reference table** — power/stamina/cooldown bonuses per tier

### 8.2 Hero AI Integration

`hero_should_visit_class_hall()` returns true when:
- Hero has unlearned skills available at their level + affordable gold
- Hero meets breakthrough requirements

`VisitClassHallHandler` in `src/ai/states.py`:
1. Hero walks to Class Hall
2. Learns available skills (deducts gold)
3. Attempts breakthrough if eligible (applies bonuses, changes class)

---

## 9. File Map

| File | Role |
|------|------|
| `src/core/classes.py` | Class/skill/breakthrough definitions, scaling grades, lore |
| `src/ai/states.py` | `VisitClassHallHandler` — AI logic for learning skills and breakthroughs |
| `frontend/src/components/ClassHallPanel.tsx` | Rich tabbed Class Hall UI panel |
| `frontend/src/components/BuildingPanel.tsx` | Routes `class_hall` to ClassHallPanel |
| `docs/class_system.md` | This document |
