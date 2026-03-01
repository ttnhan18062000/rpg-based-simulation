# RPG Simulation Engine — Project Pitch

## One-Liner

**An RPG world that plays itself** — a deterministic, concurrent simulation engine where hundreds of autonomous entities explore, fight, craft, and form factions across a living 2D world — while you watch the stories emerge.

---

## What Is This?

A **fully autonomous 2D RPG simulation engine** built on three pillars:

1. **A living world** — heroes explore, fight, loot, craft, and level up on their own. Monsters guard territory, form factions, and fight back. The economy runs itself. Every entity has personality traits that shape its decisions.
2. **Emergent storytelling** — nobody writes the plot. Stories emerge from the collision of AI, combat, economy, and faction systems interacting in ways that create *narrative as a side effect of mechanics*.
3. **Serious engineering** — deterministic concurrency, immutable snapshots, domain-separated RNG, shared pydantic schemas, 575+ tests, and performance-optimized rendering. The same seed produces the exact same story on any machine.

Think of it as an **ant farm meets Final Fantasy** — a living world you observe rather than control, built on an engine you can trust.

---

## Why Is It Interesting?

### 🌍 A Complete Living World

This isn't a toy simulation. The systems are deep enough to produce real RPG gameplay:

| System | What It Does |
|--------|-------------|
| **8 biomes** | Forest, desert, swamp, mountain, grassland, snow, jungle, volcanic — each with unique races, resources, and terrain features |
| **9+ factions** | Hero Guild, Goblin Horde, Wolf Pack, Bandit Clan, Undead, Orc Tribe, Centaur Herd, Frost Kin, Lizardfolk, Demon Horde — with territory, hostility, and faction-aware AI |
| **4 hero classes** | Warrior → Champion, Ranger → Sharpshooter, Mage → Archmage, Rogue → Assassin — each with unique skills, scaling, and playstyle |
| **30+ item types** | Weapons, armor, accessories, potions, crafting materials — with rarity tiers (Common → Epic) and stat bonuses |
| **AoE & ranged combat** | Whirlwind, Rain of Arrows, Fireball — with weapon range, line of sight, cover, threat/aggro, kiting AI |
| **A* pathfinding** | Terrain-cost-aware routing with road preference, path caching, and greedy fallback |
| **Full economy** | Shop, blacksmith, guild — heroes sell loot, buy potions, learn recipes, craft gear |
| **Personality traits** | Brave, Cautious, Greedy, Curious, Resilient — each modifies AI goal scoring differently |
| **Region difficulty** | Tier 1–4 scaling by distance from town — stat multipliers, loot quality, and mob composition increase |

### 📖 Emergent Stories, Not Scripted Ones

Nobody writes the plot. Instead, stories emerge from the collision of simple rules:

- A cautious hero avoids a goblin camp for 500 ticks, slowly grinding wolves in the forest. It levels up, crafts a sword at the blacksmith, and finally raids the camp — only to find the goblin chief has leveled too.
- A brave, greedy ranger charges deep into orc territory for rare loot. It kites enemies at range, narrowly survives with 3 HP, and flees back to town to sell everything at the shop.
- Two factions clash at a border. The undead push from the swamp, skeletons shambling slowly but tanking massive damage. The bandits in the desert scatter — they're fast but fragile.

These aren't handcrafted scenarios. They happen because the systems interact in ways that create *narrative* as a side effect of *mechanics*.

### ⚙️ Engineered for Correctness and Performance

The engine is built with the rigor of production systems software:

- **Absolute determinism** — all randomness via `Hash(Seed, Domain, EntityID, Tick)` using xxhash. Same seed = same world = same story, on any machine, every run.
- **Single-writer concurrency** — AI workers run in parallel on immutable `Snapshot` objects. Only the `WorldLoop` thread mutates `WorldState`. No locks on the hot path.
- **Shared schemas** — core data models (`ItemTemplate`, `SkillDef`, `ClassDef`, `TraitDef`) are `pydantic_dataclass(frozen=True)` — the single source of truth for both the game engine and the REST API. No duplicate schemas.
- **575+ automated tests** — combat, AI, pathfinding, inventory, economy, deterministic replay verification, API payload tests.
- **Performance-optimized** — backend: 28ms/tick for 200 entities on 512×512 (43% improvement after audit). Frontend: 256× smaller fog overlay, offscreen minimap caching, drag-skip rendering, 98% API payload reduction.

### 🔭 Built to Watch

The web-based viewer isn't an afterthought — it's designed for observation:

- **Spectate any entity** — see the world through its eyes with fog of war, vision range, and ghost markers for remembered enemies
- **Three fog levels** — visible (clear), explored (dimmed), and unseen (completely dark)
- **Rich tooltips** — hover any tile to see terrain, entities, buildings, loot, and resources — fog-gated when spectating
- **Minimap** with terrain caching, entity dots, and viewport indicator
- **Event log** tracking combat, deaths, level-ups, loot, and skill usage
- **6-tab inspector** showing stats, equipment, skills, AI goals, memory, and events for any entity

---

## Architecture

### Tick Cycle

```
Every tick (configurable speed):
  1. SCHEDULE  — find entities whose next_act_at ≤ current_tick
  2. COLLECT   — parallel AI workers decide actions (read immutable snapshots)
  3. RESOLVE   — single thread validates & applies all actions atomically
  4. CLEANUP   — respawn, decay, territory effects, threat decay
```

### Concurrency Model

| Thread | Role | Reads | Writes |
|--------|------|-------|--------|
| **Main** (uvicorn) | HTTP requests | `latest_snapshot` | Control signals |
| **Engine** (`WorldLoop`) | Tick cycle | `WorldState` | `WorldState`, `Snapshot` |
| **Workers** (ThreadPool) | AI computation | `Snapshot` (immutable) | `ActionQueue` (thread-safe) |

Workers never see partial updates. The `ActionQueue` is the only shared mutable structure.

### Data-Driven Design

Adding content means adding data, not code:

- **Items** → register in `ITEM_REGISTRY`
- **Skills** → add `SkillDef` to class definition
- **Factions** → extend `Faction` enum + register relationships
- **Terrain costs** → add entry to `TERRAIN_MOVE_COST`
- **Traits** → register `TraitDef` with utility bonuses
- **Races** → add to `RACE_TIER_KINDS` + `RACE_STAT_MODS`

All game definitions are pydantic dataclasses — `IntEnum` at runtime for fast logic, lowercase strings in JSON for the API.

---

## Current State

### What's Built (production-ready)

**Simulation:**
- 200+ autonomous entities on a 512×512 Voronoi-tessellated world with 8 biomes
- Hybrid AI: Utility AI for goal selection + State Machine for execution
- Full combat: AoE skills, ranged weapons, threat/aggro, opportunity attacks, kiting, cover
- A* pathfinding with terrain costs, path caching, greedy fallback
- Economy loop: loot → sell → buy potions → gather materials → craft gear
- 9+ factions with territory, hostility, alert states, town aura

**Engineering:**
- Deterministic replay: same seed = same world on any machine (verified by SHA-256 fingerprint test)
- 575+ automated tests (combat, AI, pathfinding, inventory, economy, API, replay)
- Backend: 28ms/tick (43% improvement after profiling audit)
- Frontend: 98% API payload reduction, 256× smaller fog overlay, drag-skip rendering
- Shared pydantic schemas — zero duplicate API models

**Frontend:**
- Triple-layer canvas (grid + entities + fog overlay) with CSS-scaled tile-resolution fog
- Spectate mode with 3-level fog of war, ghost markers, vision border
- Rich tile tooltips (fog-gated), minimap with terrain caching, 6-tab entity inspector
- Interactive API documentation page with Try It Out

---

## Roadmap

Epics are ordered by **impact across all three pillars** — emergent storytelling, world depth, and engineering challenge.

### Tier 1 — High-Impact Features

| Epic | Name | Impact |
|------|------|--------|
| **E12** | AI Personality & Emergent Behavior | Nemesis system, grudges, confidence, mood — entities become *individuals* with history. Highest storytelling ROI. |
| **E04** | Multi-Hero Party System | Multiple autonomous heroes cooperating and competing — multiplies narrative surface area and AI complexity. |
| **E06** | World Events & Invasions | Goblin raids, wandering bosses, plagues — external pressure creates dramatic stakes. New event scheduling subsystem. |
| **E07** | Reputation & Faction Diplomacy | Shifting alliances, cease-fires, faction wars — the political landscape evolves at runtime. |

### Tier 2 — World Richness

| Epic | Name | Impact |
|------|------|--------|
| **E03** | Day/Night & Weather | Natural rhythm drives behavior cycles. Weather effects + visibility modifiers add strategic depth. |
| **E02** | NPC & Social System | Living town with schedules, relationships, merchants — NPCs as autonomous agents. |
| **E01** | Dungeon System | Instanced multi-room challenges — heroes autonomously gauge readiness before entering. |
| **E13** | Ruins Exploration & Lore | Discovery loop, lore collection, hidden caches — rewards exploration with permanent bonuses. |

### Tier 3 — Depth & Polish

| Epic | Name | Impact |
|------|------|--------|
| **E05** | Advanced Combat (remaining) | Status ailments, combos, environmental combat, formations — tactical depth. |
| **E08** | Transcendence & Endgame Classes | Tier 3 class advancement, ultimate skills — late-game power fantasy. |
| **E10** | Enchantment & Item Progression | Gem socketing, +1–+10 enhancement, item sets — gear investment. |
| **E14** | Frontend UX Improvements | Smooth interpolation, damage numbers, keyboard shortcuts, camera follow. |
| **E11** | Replay & Observation Tools | Timeline scrubbing, heatmaps, stat graphs — tools for studying emergent behavior. |
| **E09** | Pathfinding (remaining) | Hazard avoidance, formations, speed modifiers, path visualization. |

---

## Try It

```bash
git clone <repo-url>
cd rpg-based-simulation
make install    # Python + Node dependencies
make serve      # Open http://localhost:8000
```

Click any entity to spectate. Press play. Watch the world unfold.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Engine** | Python 3.11+, xxhash, ThreadPoolExecutor |
| **API** | FastAPI, Pydantic 2, uvicorn |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, HTML5 Canvas |
| **Testing** | pytest (575+ tests), deterministic replay verification |
