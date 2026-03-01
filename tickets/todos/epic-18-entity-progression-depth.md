# Epic 18 — Entity Progression Depth

**Priority:** P0 (implement alongside or before epic-17)  
**Effort:** XL  
**Status:** design  
**Dependencies:** None  
**Applies to:** ALL entities (heroes, goblins, wolves, orcs, undead, bandits, centaurs, demons — everyone)

---

## Design Philosophy

In the real world and in the best fantasy, **everything that lives, grows.** A wolf that survives a hundred hunts is not the same wolf. A goblin warrior who's defended its camp against three hero raids is battle-hardened. An orc who's swung an axe ten thousand times has arms like tree trunks.

This epic makes every entity a **living individual** that grows through experience. The same systems apply universally: a hero and a goblin both get tougher by taking hits, faster by running, stronger by fighting. The difference is in their **innate nature** — how fast they learn, how high they can reach, and what they're naturally gifted at.

### Inspirations

- **Kenshi** — Toughness grows by taking damage. Every NPC uses the same progression.
- **Mount & Blade** — Troops evolve through combat (peasant → militia → veteran).
- **Battle Brothers** — Innate talent stars determine growth potential.
- **Pokemon / Progression Fantasy** — Monsters evolve through accumulated experience.
- **Elder Scrolls** — "Learn by doing." Universal for all NPCs.
- **Dwarf Fortress** — Every creature shares the same attribute system.
- **Wuxia / Cultivation** — Body tempering through suffering. Beasts cultivate alongside humans.
- **Tolkien** — Age = power. Different races mature at fundamentally different rates.
- **Rimworld** — Skills decay without use. Passion affects learning rate.

---

## Features

### F1: Veterancy (Combat Experience Ranks)

Every entity that participates in combat accumulates veterancy points — the difference between a green recruit and a grizzled veteran.

**Point Sources:**

| Action | Points |
|--------|--------|
| Deal damage | +1 per hit |
| Take damage and survive | +1 per hit taken |
| Kill an enemy | +5 |
| Kill a higher-level enemy | +10 |
| Survive below 25% HP | +3 (once per fight) |

**Ranks:**

| Rank | Points | Bonus |
|------|--------|-------|
| Green | 0 | — |
| Blooded | 25 | +3% ATK, +3% DEF |
| Veteran | 80 | +6% ATK, +6% DEF, +5% HP |
| Elite | 200 | +10% ATK/DEF, +10% HP, +5% SPD |
| Legend | 500 | +15% all stats |

- `core/models.py`: add `veterancy: int = 0`
- Bonuses via `effective_*()` methods
- Event on rank-up: `"Wolf #42 has become a Veteran"`

---

### F2: Entity Evolution (Mobs Promote Through Experience)

Mobs evolve into their next racial tier through accumulated experience — not at spawn, but through survival.

**Evolution Requirements:**

| From → To | Veterancy | Ticks Alive | Level |
|-----------|-----------|-------------|-------|
| wolf → dire_wolf | Veteran | 800 | ≥5 |
| dire_wolf → alpha_wolf | Elite | 1500 | ≥8 |
| goblin → goblin_warrior | Blooded | 500 | ≥4 |
| goblin_warrior → goblin_chief | Veteran | 1200 | ≥8 |
| orc → orc_warrior | Veteran | 1000 | ≥6 |
| orc_warrior → orc_warlord | Elite | 2000 | ≥12 |
| imp → hellhound | Veteran | 800 | ≥7 |
| hellhound → demon_lord | Legend | 3000 | ≥15 |

On evolution: kind changes, race stat mods applied, HP restored, new innate skills learned, major event emitted.

---

### F3: Innate Talent (Aptitude at Birth)

Every entity is born with **2 talented attributes** (2× training rate) and **1 weak attribute** (0.5× rate).

**Selection:**
- Trait-influenced: Brave → STR/VIT. Cautious → PER/WIS. Greedy → CHA/WIS. Curious → INT/PER. Resilient → VIT/END.
- Race-influenced: Wolves → AGI always talented. Orcs → STR always talented.
- 3rd factor: random via `DeterministicRNG`

- `core/models.py`: add `talent_strong: list[str]`, `talent_weak: list[str]`
- Applied as multiplier in `train_attributes()`
- Inspect panel: `"Talented: STR ★, AGI ★ | Weak: SPI ▼"`

---

### F4: Toughness (Body Tempering)

Taking damage and surviving makes entities physically harder. The body adapts.

- **Passive:** Every hit taken → train VIT +0.003, END +0.002
- **Near-death (HP < 15%):** Permanent +1 max HP, +0.05 VIT (once per combat)
- **Scar tissue:** Track `total_damage_taken`. Every 100 damage → +0.5% DEF (caps +15%)
- Event: `"Kael was hardened by a near-death experience (+1 max HP)"`
- `core/models.py`: add `total_damage_taken: int = 0`

---

### F5: Leveling Curve Revision

Replace flat growth with **milestone power spikes** and **diminishing returns**.

**XP Scale:** Levels 1–10: 1.4× | Levels 11–20: 1.6× | Levels 21–30: 2.0×. Base: 80 XP.

**Milestone Levels (3× normal growth):**

| Level | HP | ATK | DEF | SPD | Unlock |
|-------|----|-----|-----|-----|--------|
| 5 | +15 | +3 | +2 | +2 | 2nd skill slot |
| 10 | +20 | +4 | +3 | +3 | Breakthrough eligible |
| 15 | +15 | +3 | +2 | +2 | 4th skill slot |
| 20 | +20 | +4 | +3 | +2 | Soft cap (was hard cap) |
| 25 | +15 | +3 | +2 | +2 | Transcendence eligible |
| 30 | +10 | +2 | +1 | +1 | Hard cap |

**Normal levels:** +4-5 HP, +1 ATK at low levels → +2 HP, +0 ATK at high levels.

**Mob Leveling:** Mobs gain XP from kills at 0.5× hero rate. Mob level caps by race (F8).

---

### F6: Skill Discovery (Learn Through Experience)

Entities learn abilities through specific gameplay conditions — not menus.

| Skill | Condition | Effect | Who |
|-------|-----------|--------|-----|
| Desperate Strike | Survive < 15% HP, 3× | +50% ATK when HP < 20% | Any melee |
| Iron Skin | Take 500+ total damage | +5% DEF permanent | Any |
| Race Slayer | Kill 10+ of same race | +15% dmg vs that race | Any |
| Pack Tactics | Fight with ally within 3 tiles, 10× | +10% ATK when ally adjacent | Any |
| Hit and Run | Kite successfully 10× | No opportunity attack penalty | Ranged |
| Last Stand | Survive outnumbered 3:1+ | +20% DEF when outnumbered | Any |
| Predator's Instinct | Kill 5 enemies without resting | +1 vision range | Any |
| Berserker Rage | Kill attacker after dropping < 30% HP, 3× | +30% ATK / -15% DEF when HP < 30% | Melee |
| Ambush Mastery | Kill on first hit, 5× | +25% first-strike damage | Rogue/Bandit/Wolf |

- `core/models.py`: add `discovery_progress: dict[str, int]`
- Check conditions in cleanup phase. Emit event on discovery.

---

### F7: Attribute Milestones (Threshold Bonuses)

When an attribute crosses 15/25/40/60, unlock a passive bonus and emit an event.

**Examples (each attribute has 4 tiers):**

| Attr | 15 (Capable) | 25 (Exceptional) | 40 (Superhuman) | 60 (Legendary) |
|------|-------------|-------------------|-----------------|-----------------|
| STR | +5% melee dmg | +10% melee dmg | +20% melee dmg | +30%, stagger on hit |
| AGI | +3% evasion | +5% evasion, +5% crit | +10% both | Guaranteed dodge 1/combat |
| VIT | +5% max HP | +10% max HP | +20% max HP | +30%, regen 1 HP/tick |
| PER | +1 vision | +2 vision | +3 vision | See through adjacent fog |

- `core/models.py`: add `milestone_unlocks: set[str]`
- Event: `"Kael's STR reached 25 — Exceptional Strength!"`

---

### F8: Racial Growth Profiles

Different races grow at different rates and have different ceilings.

| Race | Train Rate | Level Cap | Evolves? | Special |
|------|-----------|-----------|----------|---------|
| Human (hero) | 1.0× | 30 | Class advancement | Balanced, highest skill ceiling |
| Goblin | 1.3× | 12 | Yes | Fast learners, low ceiling |
| Wolf | 0.7× | 8 | Yes | AGI always talented |
| Bandit | 1.0× | 15 | Yes | Human-like, CHA/AGI talented |
| **Undead** | **0.0×** | **—** | **No** | **Cannot train/level/evolve/decay. Frozen in time.** |
| Orc | 0.6× | 15 | Yes | Slow but STR/VIT talented, highest non-hero ceiling |
| Centaur | 0.9× | 12 | Yes | AGI/SPD talented |
| Frost Kin | 0.5× | 10 | No | Innately powerful, slow growth |
| Lizardfolk | 0.8× | 12 | Yes | VIT/END talented, 1.5× toughness rate |
| Demon | 0.4× | 20 | Yes | Very slow, very high ceiling. Ancient demon = terrifying |

**Undead** are the exception: frozen, eternal, unchanging. Thematic and strategic — they're predictable threats.

---

### F9: Battle Marks (Permanent Feat-Based Identity)

Significant achievements permanently mark an entity with bonuses and AI effects.

| Mark | Condition | Bonus | AI Effect |
|------|-----------|-------|-----------|
| Blooded | First kill | +2% ATK | — |
| Survivor | Survive < 5% HP, 3× | +5% HP | Lower flee threshold |
| Hero-Slayer | Kill a hero (mobs) | +10% ATK vs heroes | Confident vs heroes |
| Camp Destroyer | Clear a camp (heroes) | +5% ATK in enemy territory | Weak mobs flee earlier |
| Apex Predator | Evolve to highest tier | +10% all stats | Same-race mobs defer |
| Ancient | Survive 5000+ ticks | +5% all stats, +2 vision | — |
| Giant-Killer | Kill enemy 5+ levels higher | +10% dmg vs higher-level | — |
| Unbreakable | Take 2000+ total damage | +10% DEF | — |

- `core/models.py`: add `battle_marks: list[str]`
- Events on earning marks. Shown in inspect panel and tooltip.

---

### F10: Stat Decay (Use It or Lose It)

Attributes slowly decay without use — an idle blade grows dull.

- **Rate:** -0.001 per tick for attributes not trained in the last 200 ticks
- Can't decay below spawn-time base value
- **Undead exempt** (they don't grow OR decay)
- Very slow: ~1000 ticks to lose 1 point. Not punishing — just maintenance pressure.
- Forces entities to stay active to maintain their edge

---

## Implementation Plan

| Phase | Features | Effort |
|-------|----------|--------|
| **A** | F5 (leveling curve) + F8 (racial profiles) | M |
| **B** | F1 (veterancy) + F3 (talent) | M |
| **C** | F4 (toughness) + F10 (decay) | S |
| **D** | F2 (evolution) | L |
| **E** | F6 (skill discovery) + F7 (attribute milestones) | L |
| **F** | F9 (battle marks) | M |

**Recommended:** A → B → C → D → E → F

---

## Files Affected

**Modified:**
- `src/config.py` — XP curve params, milestone config, racial caps
- `src/core/models.py` — veterancy, talent, total_damage_taken, battle_marks, discovery_progress, milestone_unlocks
- `src/core/attributes.py` — milestone bonuses, talent multiplier in train_attributes(), decay logic
- `src/core/classes.py` — milestone skill slot unlocks
- `src/core/enums.py` — VeterancyRank enum
- `src/systems/generator.py` — assign talents at spawn, racial train_rate
- `src/engine/world_loop.py` — veterancy tracking, evolution checks, toughness, discovery checks, mark checks, decay
- `src/actions/combat.py` — veterancy point accumulation, toughness damage tracking
- `src/ai/goals/scorers.py` — mark-based AI score adjustments
- `src/api/schemas.py` — veterancy, marks, talents in entity schemas

**Frontend:**
- Inspect panel: veterancy rank, talents, marks, milestones, discovery progress
- Entity list: veterancy rank indicator
- Tooltip: marks and veterancy
- Canvas: visual veterancy indicators (ring thickness/color)
