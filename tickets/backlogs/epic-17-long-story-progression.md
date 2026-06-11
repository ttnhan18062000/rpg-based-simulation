# Epic 17 — Long-Story Progression Spine

**Priority:** P1  
**Effort:** XXL  
**Status:** design  
**Dependencies:** None (self-contained, replaces/subsumes parts of E01, E04, E06, E08)

---

## Problem Statement

The simulation hits a progression wall around tick 10,000. A single hero reaches level 20, acquires Epic gear, masters all skills, and then loops fight/sell/rest indefinitely with no meaningful goal. The world is static — same camps, same factions, same difficulty. There is no reason to watch past the first 10,000 ticks.

**Goal:** Make the simulation produce compelling, watchable stories for 50,000+ ticks through layered progression, multiple protagonists, world evolution, and endgame content.

---

## Current Progression Timeline (before this epic)

```
Tick 0        → Hero spawns in town (level 1, class gear)
Tick ~200     → Explored tier 1, killed wolves/goblins, level 3-4
Tick ~800     → Tier 2 regions, crafted first weapon, level 6-7
Tick ~2000    → Breakthrough at level 10 (Warrior → Champion)
Tick ~5000    → Tier 3/4 regions, Epic gear, level 15+
Tick ~10000   → Level 20 cap, best gear, all skills mastered
Tick 10000+   → STALL. Hero loops endlessly with no growth or goals.
```

## Target Progression Timeline (after this epic)

```
Tick 0        → 3-5 heroes spawn with different classes/traits/names
Tick ~500     → Heroes diverge: cautious mage in tier 1, brave warrior pushes tier 2
Tick ~1500    → First hero death. New hero ("2nd generation") spawns at level 1.
Tick ~2500    → First breakthrough. Camps that weren't cleared have grown stronger.
Tick ~4000    → Faction raid on town! Heroes rush back to defend.
Tick ~7000    → World boss appears. Only the strongest hero attempts it.
Tick ~10000   → First hero hits level 20. World enemies have scaled up.
Tick ~15000   → Dungeon attempt by level 22 hero — fails, retreats.
Tick ~20000   → Transcendence achieved by one hero. Dungeon cleared.
Tick ~25000   → 2nd-gen heroes catching up. World boss 3rd spawn = very strong.
Tick ~35000   → Faction raid + world boss simultaneously = crisis event.
Tick ~50000   → Multiple hero generations. Hall of fame has 5+ entries.
```

---

## 5 Progression Walls Addressed

| # | Wall | Root Cause | Solution |
|---|------|-----------|----------|
| 1 | **Level 20 cap** | `max_level=20`, XP meaningless after cap | Extend to 30, halved growth after 20, Tier 3 class at 25 |
| 2 | **Single hero** | 1 protagonist = 1 story, plateaus at max | Spawn 3-5 heroes with different classes/traits/names |
| 3 | **Static world** | Nothing changes; camps/factions frozen | Camp reinforcement, world age scaling, periodic raids |
| 4 | **Gear ceiling** | Epic is the top rarity, no aspirational drops | Legendary rarity, unique named items from bosses/dungeons |
| 5 | **No long-term goals** | No dungeons, no bosses, no milestones | World boss, dungeon instance, transcendence trial, hall of fame |

---

## Phase 1 — Multiple Heroes + Death Stakes

**Effort:** L  
**Impact:** Multiplies narrative surface area. Every other feature becomes more interesting with multiple heroes.

### F1: Multi-Hero Spawning

Spawn **3–5 heroes** at game start instead of 1.

**Changes:**
- `config.py`: add `hero_count: int = 4`
- `engine_manager.py` `_build()`: loop hero spawning, assign different classes round-robin (Warrior, Ranger, Mage, Rogue), randomize traits per hero
- Each hero gets a unique spawn offset within the town square (avoid stacking)
- All heroes share the same buildings (shop, blacksmith, guild)

**AI behavior:**
- Heroes are independent — each runs its own goal evaluation
- No party system yet (that's E04) — they operate solo but may end up in the same region
- Existing goal scorers work unchanged — each hero evaluates its own HP, inventory, nearby enemies

**Frontend:**
- Entity list shows all heroes at the top (already sorted by kind)
- Spectating one hero shows fog-of-war for that hero only (already works)

### F2: Hero Naming

Auto-generate names for heroes at spawn time.

**Changes:**
- `core/models.py`: add `display_name: str = ""` field on Entity
- Name tables (deterministic via RNG):
  - First names: 20 per gender/style (e.g. Kael, Lyra, Thorne, Sera, Aldric, Mira, ...)
  - Titles: drawn from traits (e.g. "the Brave", "the Cautious", "the Greedy")
  - Format: `"{first_name} the {trait}"` → "Kael the Brave"
- Names appear in:
  - Event log: `"Kael the Brave killed Goblin Chief (Lv12)"`
  - Entity list sidebar
  - Hover tooltip
  - Inspect panel header
- Mob entities keep `kind` as display (no naming for mobs)

### F3: Hero Death Escalation

Progressive death penalties that raise stakes over time.

**Changes:**
- `core/models.py`: add `death_count: int = 0` on Entity
- Death penalty tiers:

| Deaths | Penalty |
|--------|---------|
| 1st | Bag items dropped (current behavior) |
| 2nd | Bag + accessory dropped |
| 3rd | Bag + accessory + armor dropped |
| 4th+ | **Permadeath** — hero removed permanently. New hero spawns at town after 50 ticks. |

- New hero inherits nothing from the dead hero — fresh level 1, new class (round-robin from alive heroes), new name, new traits
- `engine/world_loop.py` `_process_death()`: check `death_count`, apply escalated drops
- New hero spawns via `_process_hero_replacement()` in cleanup phase

### F4: Hero Generation Tracking

Track hero "generations" for narrative context.

**Changes:**
- `core/models.py`: add `generation: int = 1` on Entity
- When a new hero replaces a permadead one: `generation = max(all_hero_generations) + 1`
- Events: `"A new hero arrives: Sera the Curious (Generation 3)"`
- Frontend inspect panel shows generation number
- Stat tracking per hero: total kills, deaths, ticks alive, highest level reached

### F5: Hero Familiarity (Lightweight)

Heroes that spend time near each other develop familiarity.

**Changes:**
- `core/models.py`: add `hero_familiarity: dict[int, float] = {}` mapping hero_id → score (0.0–1.0)
- `world_loop.py` cleanup phase: for each pair of alive heroes within vision range, increment familiarity by +0.002/tick (caps at 1.0), decay by -0.0005/tick when apart
- High familiarity (>0.5): +10% ATK/DEF when within 3 tiles of familiar hero (applied as status effect, refreshed per tick)
- Low familiarity (<0.2): no effect
- Displayed in inspect panel under a "Bonds" section
- Events: `"Kael and Lyra have become allies"` at familiarity 0.5+

---

## Phase 2 — World Evolution + External Pressure

**Effort:** L  
**Impact:** The world becomes a living antagonist. Heroes can't just grind in peace.

### F6: World Age Clock

A tick-based world age counter that drives scaling and events.

**Changes:**
- `core/world_state.py`: add `world_day: int` property → `tick // 100`
- Used as input for:
  - Enemy scaling (F8)
  - Raid scheduling (F7)
  - World boss spawning (F9)
- Displayed in frontend header: `"Day 42"` alongside tick counter

### F7: Faction Raids on Town

Periodic invasion events that create defensive drama.

**Changes:**
- `config.py`: add `raid_interval_days: int = 20` (every 2000 ticks), `raid_base_strength: int = 5`
- `world_loop.py` cleanup phase: at tick `raid_interval_days * 100`:
  1. Pick a random faction (weighted by nearest region proximity)
  2. Spawn `raid_base_strength + world_day // 10` enemies at the border of the town sanctuary
  3. All spawned enemies have `ai_state = HUNT` targeting town center
  4. Emit event: `"The Goblin Horde raids the town! (8 attackers)"`
- Raid enemies don't leash — they push until dead or town aura kills them
- Heroes in town or nearby auto-engage via existing ALERT/COMBAT AI
- If raid enemies reach town center and no heroes are nearby: damage town buildings (reduce shop stock, break blacksmith for N ticks)
- Raid strength scales with `world_day`: early raids are trivial, later ones are dangerous

**Raid Strength Scaling:**

| Day | Enemies | Enemy Level | Difficulty |
|-----|---------|-------------|-----------|
| 20 | 5 | 3-5 | Easy |
| 50 | 8 | 6-10 | Medium |
| 100 | 12 | 10-15 | Hard |
| 200 | 18 | 15-25 | Deadly |

### F8: Enemy Scaling by World Age

Respawned enemies grow stronger as the world ages, preventing permanent safety.

**Changes:**
- `systems/generator.py`: enemy stat multiplier includes `world_age_mult`:
  ```
  world_age_mult = 1.0 + (world_day / 200) * 0.5
  ```
  (At day 100: enemies are 1.25× stronger. At day 200: 1.5×. At day 400: 2.0×.)
- Applied on top of existing region difficulty multipliers
- Enemy level range also shifts up: `level_min += world_day // 50`, `level_max += world_day // 30`
- Effect: tier 1 regions that were safe at day 1 become challenging by day 100

### F9: Wandering World Boss

A single named boss entity that roams the map, providing an aspirational combat goal.

**Changes:**
- `config.py`: `world_boss_spawn_day: int = 50`, `world_boss_respawn_days: int = 50`
- `core/models.py`: new entity role `WORLD_BOSS` (or just a flag `is_world_boss: bool = False`)
- Boss properties:
  - Named (deterministic from name table): "Gorath the Destroyer", "Vexira the Cursed", etc.
  - Stats: 5× region tier 4 stats, scales with spawn count (`1.3^n` per respawn)
  - Unique AI: `WANDER` state but covers large distances, attacks anything in range, doesn't leash
  - Drops: Legendary item (unique, one copy only) + large gold + large XP
- Spawn: random tile in tier 3+ region, announced via event: `"Gorath the Destroyer has appeared in Stormcrag Heights!"`
- Despawn: does NOT despawn. Roams until killed.
- Respawn: `world_boss_respawn_days` days after death, at a new location, 1.3× stronger
- Frontend: world boss shown as a large red diamond on minimap (always visible regardless of fog)

### F10: Camp Reinforcement

Camps that are left alone grow stronger over time.

**Changes:**
- `core/regions.py` or `world_state.py`: per-camp `reinforcement_level: int = 0`
- `world_loop.py` cleanup phase: every 500 ticks, for each camp location:
  - If camp has <50% of original guard count → spawn 1 replacement guard at `original_tier + reinforcement_level`
  - If camp is at full guards → increment `reinforcement_level` (cap at 3)
- Effect: camps left alone for 2000+ ticks have tier+3 guards = very dangerous
- Camps that are actively raided by heroes stay at base difficulty
- Heroes must choose: clear camps proactively, or risk them becoming threats later

---

## Phase 3 — Endgame Content + Extended Progression

**Effort:** XL  
**Impact:** Gives max-level heroes meaningful goals and creates climactic story moments.

### F11: Extended Level Cap (20 → 30)

Simple but effective — extend the growth curve.

**Changes:**
- `config.py`: `max_level: int = 30`
- Level 21–30: half stat growth (HP+2, ATK/DEF/SPD+0 alternating levels)
- XP curve continues at 1.5× scale — level 30 requires ~50× more XP than level 20
- Attribute growth continues (caps still increase by +5/level)
- Effect: heroes have 10 more levels of slow growth. Level 25 is a significant achievement. Level 30 is rare.

### F12: Transcendence (Tier 3 Class)

The ultimate class advancement for heroes who reach the endgame.

**Changes:**
- `core/classes.py`: add Tier 3 classes:

| Tier 3 | From | Requirement | Ultimate Skill |
|--------|------|-------------|---------------|
| **Warlord** | Champion | Level 25, STR≥60, kill world boss | Earthquake (AoE radius 3, 3.0× power, 1-tick stun) |
| **Deadeye** | Sharpshooter | Level 25, AGI≥60, kill world boss | Piercing Shot (ignores DEF, range 6, 2.5× power) |
| **Archon** | Archmage | Level 25, SPI≥60, kill world boss | Meteor (AoE radius 4, 4.0× power, fire element) |
| **Phantom** | Assassin | Level 25, AGI≥50, clear dungeon | Death Mark (target takes 3× damage for 3 ticks) |

- Transcendence event: `"Kael the Brave has transcended! Warlord Kael emerges!"`
- Visual: transcended heroes get a distinct color/glow on the canvas
- Only ~1 in 3-4 heroes will ever reach this in a typical run

### F13: Dungeon Instance

A single challenging dungeon that provides endgame content.

**Changes:**
- Place one `dungeon_entrance` location in a tier 4 region (already exists as a location type)
- Dungeon has 3 rooms + 1 boss room:

| Room | Content | Difficulty |
|------|---------|-----------|
| 1 | 3 elite guards | Tier 4 × 1.5 |
| 2 | 5 warriors + 1 chief | Tier 4 × 2.0 |
| 3 | Trap room (damage per tick while inside) + 2 elites | Tier 4 × 2.0 |
| Boss | Named dungeon boss (unique) | Tier 4 × 4.0 |

- Hero AI: `DungeonGoal` scorer activates when hero is level 18+, has good gear (weapon rarity ≥ RARE), and HP is full. Score starts low (0.2) and grows with level.
- State: `DUNGEON_DIVE` — hero enters, fights room by room. If HP drops below 20%, hero flees (exits dungeon, rooms reset after 1000 ticks).
- Dungeon clear event: `"Kael the Brave has cleared the Abyssal Dungeon!"`
- Reward: Legendary weapon + massive XP + transcendence prerequisite
- Dungeon resets 1000 ticks after clear (new boss, same layout)

### F14: Legendary Items

Aspirational items that only drop from endgame content.

**Changes:**
- `core/enums.py`: add `Rarity.LEGENDARY = 5` (above EPIC)
- `core/items.py`: add 6-8 legendary items:

| Item | Type | Source | Special |
|------|------|--------|---------|
| Gorath's Cleaver | Weapon (melee) | World boss | +30% ATK, lifesteal 10% |
| Vexira's Fang | Weapon (ranged) | World boss | +25% ATK, poison on hit |
| Crown of Ages | Accessory | Dungeon boss | +20% all stats |
| Dragonscale Mail | Armor | Dungeon boss | +40% DEF, fire resist |
| Band of the Fallen | Accessory | World boss (3rd kill) | +15% XP, +10% gold |
| Worldbreaker | Weapon (melee) | World boss (5th kill) | +50% ATK, AoE on basic attack |

- Legendary items are unique — only one copy exists. If the holder dies, it drops as loot (other heroes can pick it up).
- Frontend: legendary items shown in gold text with a special border in inspect panel

### F15: Hall of Fame

Permanent record of hero achievements for narrative closure.

**Changes:**
- `core/world_state.py`: add `hall_of_fame: list[HallOfFameEntry]`
- `HallOfFameEntry`: hero name, class, generation, ticks_alive, max_level, total_kills, cause_of_death, notable_achievements (list of strings)
- Entry added when:
  - Hero dies permanently (permadeath after 4th death)
  - Hero reaches transcendence
  - Simulation ends
- Notable achievements auto-detected:
  - "Slayer of Gorath" (killed world boss)
  - "Dungeon Conqueror" (cleared dungeon)
  - "Transcended" (reached Tier 3)
  - "Lone Survivor" (last hero alive during a raid)
  - "First Blood" (first kill in the simulation)
- Frontend: new "Hall of Fame" tab in sidebar showing all entries
- API: `GET /api/v1/hall_of_fame` endpoint

---

## Implementation Plan

| Phase | Features | Effort | Dependencies |
|-------|----------|--------|-------------|
| **1A** | F1 (multi-hero) + F2 (naming) | M | None |
| **1B** | F3 (death escalation) + F4 (generation tracking) | M | F1 |
| **1C** | F5 (familiarity) | S | F1 |
| **2A** | F6 (world age) + F8 (enemy scaling) | M | None |
| **2B** | F7 (faction raids) | L | F6 |
| **2C** | F9 (world boss) + F14 (legendary items) | L | F6 |
| **2D** | F10 (camp reinforcement) | S | None |
| **3A** | F11 (level cap 30) | S | None |
| **3B** | F12 (transcendence) | M | F9 or F13 |
| **3C** | F13 (dungeon) | L | F11 |
| **3D** | F15 (hall of fame) | M | F3 |

**Recommended order:** 1A → 2A → 1B → 2D → 2B → 2C → 1C → 3A → 3C → 3B → 3D → F14

Total estimated effort: **XXL** (4-6 weeks)

---

## Design Principles

- **Deterministic:** All new systems use `DeterministicRNG` with appropriate domain separation. World boss spawn location, raid composition, hero names — all seeded.
- **Data-driven:** Legendary items, raid configs, boss stats — all registry/config based.
- **Backward-compatible:** Existing single-hero simulations still work (`hero_count=1` disables multi-hero features).
- **Incremental:** Each phase is independently valuable. Phase 1 alone makes the simulation 3× more interesting.
- **Observable:** Every progression milestone emits an event. The frontend doesn't need changes beyond displaying new event types and the hall of fame tab.

---

## Files Affected (estimated)

**New files:**
- `src/core/hero_names.py` — Name tables + generation logic
- `src/core/hall_of_fame.py` — HallOfFameEntry dataclass

**Backend (modified):**
- `src/config.py` — hero_count, raid_interval, world_boss_spawn_day, etc.
- `src/core/models.py` — display_name, death_count, generation, hero_familiarity, is_world_boss
- `src/core/world_state.py` — hall_of_fame list, world_day property
- `src/core/enums.py` — Rarity.LEGENDARY
- `src/core/items.py` — legendary item templates
- `src/core/classes.py` — Tier 3 class definitions + ultimate skills
- `src/engine/world_loop.py` — death escalation, hero replacement, raid spawning, boss spawning, camp reinforcement, familiarity ticking
- `src/systems/generator.py` — world_age_mult scaling, world boss spawning
- `src/ai/goals/scorers.py` — DungeonGoal scorer
- `src/ai/states.py` — DUNGEON_DIVE state handler
- `src/api/schemas.py` — HallOfFameSchema, world_day in stats
- `src/api/routes/state.py` — hall_of_fame endpoint

**Frontend (modified):**
- `frontend/src/types/api.ts` — HallOfFameEntry, world_day, display_name
- `frontend/src/components/Header.tsx` — world day display
- `frontend/src/components/Sidebar.tsx` — Hall of Fame tab
- `frontend/src/components/InspectPanel.tsx` — generation, bonds, death count
- `frontend/src/components/EntityList.tsx` — hero names
- `frontend/src/hooks/useCanvas.ts` — world boss minimap marker, transcended hero glow
- `frontend/src/constants/colors.ts` — legendary item color, world boss color

**Tier:** epic
**Type:** feature
**Priority:** P2
