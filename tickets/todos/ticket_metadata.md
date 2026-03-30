# Ticket Metadata

Master index of all active tickets with priority, effort estimate, dependencies, and status.

**Last updated:** 2026-03-11

---

## Legend

| Column | Values |
|--------|--------|
| **Priority** | P0 (critical) · P1 (high) · P2 (medium) · P3 (low) |
| **Effort** | XS (< 1h) · S (1–4h) · M (4–16h) · L (2–5d) · XL (1–2w) · XXL (2w+) |
| **Status** | `needs-decision` · `ready` · `in-progress` · `done` |
| **Type** | bug · enhance · adjust · design · epic · infra |

---

## Completed Work

All bugs, enhancements, adjustments, design reviews, and infrastructure tickets are **done**.

| ID | Ticket | Type | Summary |
|----|--------|------|---------|
| bug-01 | Diagonal HUNT Move Conflict | bug | Higher-ID entity yields at Manhattan 2 |
| bug-02 | Hero Looting Full Bag | bug | `is_effectively_full` checks slots + weight |
| enhance-01 | Enrich Event Information | enhance | Metadata on SimEvent, enriched combat/loot/death/level_up/skill events |
| enhance-02 | Bag Max Capacity UI | enhance | Slot + weight bars with color coding |
| enhance-03 | Extend Max Tick to 50000 | enhance | EventLog ring buffer (10k cap) |
| enhance-04 | Mob Roaming Leash | enhance | Radius 15, chase cap 1.5×, give-up 20 ticks, 5% HP/tick heal on return |
| adjust-01 | Action Speed Balance | adjust | Doubled delay multipliers, SPD stat meaningful |
| design-01 | Skill Stat Scaling | design | DamageCalculator routing, crit/variance/evasion on skills |
| design-02 | Revise Ticking Mechanism | design | Fixed empty-tick stall, subsystem rate divisors |
| infra-01 | Automated Testing | infra | `make test`, deterministic replay, 575+ tests |
| infra-02 | Performance Profiling | infra | `make profile`, per-tick timing, memory profiling |
| infra-03 | Telemetry & Observability | infra | Prometheus mapping, automated docker deployment, Grafana dashboards via containerized stack, test automation |
| infra-04 | Realtime State Streaming | infra | Shifted 80ms HTTP polling to highly optimized unidirectional SSE delta payloads, heavily reducing network burden |
| infra-05 | Distributed AI Workers | infra | Integrated RabbitMQ to distribute AI evaluations to scalable daemon processes bypassing the GIL |
| infra-07 | Redis Streams Event Bus | infra | Replaced local asyncio.Queues with a Redis Stream for system-wide event broadcasting and delta state distribution |

**Automation commands:**

| Command | What it does |
|---------|-------------|
| `make test` | Run all 575+ Python tests |
| `make test-quick` | Run fast tests only (skip `@slow`) |
| `make test-cov` | Run tests with coverage report |
| `make profile` | 500-tick performance report (timing, phases, entity counts) |
| `make profile-full` | 2000-tick profile + cProfile `.prof` dump |
| `make profile-memory` | 500-tick profile with tracemalloc memory snapshot |

---

## Completed Epics

| ID | Ticket | Effort | Summary |
|----|--------|--------|---------|
| epic-15 | Region & World Overhaul | XL | Voronoi tessellation, 512×512 map, 8 biomes, 9 factions, tier 1–4 difficulty, loot scaling, region events, hero AI awareness |
| epic-16 | Performance Audit | L | Backend: 43% faster ticks (49.8ms→28.4ms), 70% fewer function calls. Frontend: 256× smaller overlay, drag-skip, minimap caching, 98% API payload reduction |
| epic-19 | [Kafka Event-Sourcing](epic-19-event-sourcing-persistence.md) | XL | Long-term durability via Apache Kafka; append-only event-sourcing allows infinite rewinds and ML data pipelines. |

## Partially Completed Epics

| ID | Ticket | Done | Remaining | Status |
|----|--------|------|-----------|--------|
| epic-18 | [Entity Progression Depth](epic-18-entity-progression-depth.md) | Leveling Curve, Racial Profiles, Phase D Evolution, Veterancy | Skill Discovery, Milestones, Battle Marks | partial — core evolution and veterancy are functional |
| epic-09 | [Pathfinding & Movement](epic-09-improved-pathfinding-and-movement.md) | F1 (A*), F2 (Terrain Costs), F4 (Path Cache), F6 (Obstacle Avoidance), F9 (Terrain Detail), F10 (Tile Tooltip) | F3 (Hazard Avoidance), F5 (Formations), F7 (Speed Mods), F8 (Path Viz) | partial — core pathfinding complete, remaining features are polish |

---

## Open Epics — Prioritized by Emergent Storytelling Impact

Epics re-ordered by how much they contribute to **emergent narrative moments** — the core vision of the project.

### Priority 0 — Progression Spine (build this first)

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-17 | [Long-Story Progression Spine](epic-17-long-story-progression.md) | **P0** | XXL | Fixes the level-20 ceiling. Multi-hero, death stakes, world evolution, raids, world boss, dungeon, transcendence, hall of fame. Subsumes slimmed-down parts of E01, E04, E06, E08. Without this, the simulation stalls at tick 10,000. |
| epic-18 | [Entity Progression Depth](epic-18-entity-progression-depth.md) | **P0** | XL | Deepens micro-level growth for ALL entities. Veterancy, evolution, innate talent, toughness, revised leveling curve, skill discovery, attribute milestones, racial growth profiles, battle marks. Every living thing in the world grows through experience. |

### Tier 1 — High-Impact Narrative

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-12 | [AI Personality & Emergent Behavior](epic-12-ai-personality-and-emergent-behavior.md) | **P1** | XXL | Nemesis system, grudges, confidence, mood — turns entities into *individuals* whose history shapes decisions. Highest storytelling ROI. |
| epic-07 | [Reputation & Faction Diplomacy](epic-07-reputation-and-faction-diplomacy.md) | **P1** | XL | Shifting alliances and faction wars — the political map evolves, creating geopolitical narrative. |
| epic-20 | [Calamity (World Boss) System](epic-20-calamity-system.md) | **P1** | XL | Prototype with auras and spawning integrated; full randomized spec in progress. |

### Tier 2 — World Richness (deepen the world)

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-03 | [Day/Night & Weather](epic-03-day-night-and-weather.md) | **P2** | XL | Natural rhythm drives behavior cycles — night raids, storm shelter, visibility tension. |
| epic-02 | [NPC & Social System](epic-02-npc-and-social-system.md) | **P2** | XXL | Living town with schedules, relationships — the town becomes a character in the story. |
| epic-13 | [Ruins Exploration & Lore](epic-13-ruins-exploration-and-lore.md) | **P3** | XXL | Discovery and world history — rewards curiosity, adds narrative depth. |

### Tier 3 — Depth & Polish (enrich existing systems)

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-05 | [Advanced Combat (remaining)](epic-05-advanced-combat-mechanics.md) | **P2** | L | Status ailments, combos, environmental combat — richer tactical combat moments. |
| epic-10 | [Enchantment & Item Progression](epic-10-enchantment-and-item-progression.md) | **P3** | XL | Gear becomes meaningful and personal — socketing, enhancement, item sets. |
| epic-14 | [Frontend UX Improvements](epic-14-frontend-ux-improvements.md) | **P2** | XL | Smooth animations, combat numbers, keyboard shortcuts — better watching experience. |
| epic-11 | [Replay & Observation Tools](epic-11-replay-and-observation-tools.md) | **P2** | XXL | Timeline scrubbing, heatmaps, stat graphs — tools for studying emergent behavior. |
| epic-09 | [Pathfinding (remaining)](epic-09-improved-pathfinding-and-movement.md) | **P3** | M | Hazard avoidance, formations, speed modifiers, path visualization — polish. |

### Subsumed by Epic-17 (slimmed-down versions included)

| ID | Ticket | What E17 Takes | What Remains |
|----|--------|----------------|-------------|
| epic-04 | [Multi-Hero Party System](epic-04-multi-hero-party-system.md) | Multi-hero spawning, naming, familiarity | Full party formation, shared XP/loot, coordinated tactics |
| epic-06 | [World Events & Invasions](epic-06-world-events-and-invasions.md) | Faction raids, wandering world boss | Event framework, resource events, environmental disasters |
| epic-08 | [Transcendence & Endgame Classes](epic-08-transcendence-and-endgame-classes.md) | **P4 of Epic-20** | Trial quests, visual identity, post-transcendence growth |
| epic-01 | [Dungeon System](epic-01-dungeon-system.md) | Single dungeon instance | Full dungeon generation, traps, loot tables, cooldowns |

---

## Open Architecture & Tech Stack Improvements

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| design-03 | [Data-Driven Registries](design-03-data-driven-registries.md) | **P1** | M | Foundation for Epic-18; decouples configs from Python logic. |
| infra-06 | [Hardening & Chaos Testing](infra-06-hardening-and-chaos-testing.md) | **P3** | M | Property-Based Testing (Hypothesis) and fault injection. |

---

## Recommended Next Steps

1. **epic-18 Phase A** (Leveling Curve + Racial Profiles) — fix the flat growth first; every entity benefits immediately
2. **epic-18 Phase B** (Veterancy + Talent) — make every entity an individual that grows through combat
3. **epic-17 Phase 1** (Multi-Hero + Death Stakes) — multiple heroes with the new progression = divergent stories
4. **epic-18 Phase C+D** (Toughness + Evolution) — mobs evolve organically; the world grows alongside heroes
5. **epic-17 Phase 2** (World Evolution) — world age, raids, world boss, camp reinforcement
6. **epic-18 Phase E+F** (Skill Discovery + Milestones + Marks) — entities earn identity through experience
7. **epic-12** (AI Personality) — nemesis system on top of marked, veteran, evolved entities = rich stories
8. **epic-17 Phase 3** (Endgame) — level cap 30, transcendence, dungeon, legendary items, hall of fame
9. **epic-07** (Faction Diplomacy) — dynamic alliances make the faction map a living story
