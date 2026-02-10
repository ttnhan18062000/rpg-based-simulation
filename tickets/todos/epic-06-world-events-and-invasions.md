# Epic 06: World Events & Invasions

## Summary

Introduce dynamic world events that periodically alter the simulation: faction invasions, resource booms, plagues, wandering bosses, and festivals. Events create unpredictable challenges and opportunities that force the hero (and all entities) to adapt their behavior.

Inspired by: Rimworld random events, Terraria invasions, Dwarf Fortress sieges, MMORPG world boss spawns, Kenshi world state changes.

---

## Motivation

- The current world is static after generation — same enemies in same places forever
- No external pressure drives emergent narrative (e.g. "the goblins attacked the town")
- World events create memorable moments and force adaptive AI behavior
- Invasions test the hero's combat readiness and create urgency
- Aligns with "fully automated world" — events happen whether or not the hero is ready

---

## Features

### F1: Event System Framework
- `WorldEvent` dataclass: `event_id`, `event_type`, `start_tick`, `duration`, `severity`, `affected_area`, `active`
- Events tracked in `WorldState.active_events: list[WorldEvent]`
- Event scheduler in `WorldLoop` — checks each tick for event triggers
- Event triggers: tick-based probability (configurable frequency), world state conditions (e.g. hero reaches level 10)
- **Extensibility:** `EventDef` registry — new events = register a definition + handler class

### F2: Faction Invasions
- A hostile faction sends a wave of enemies toward the town
- Invasion types:
  - **Goblin Raid** — 8–15 goblins march from camps toward town
  - **Wolf Pack Hunt** — wolves swarm from forests toward nearest entity cluster
  - **Undead Rising** — skeletons and zombies spawn on SWAMP tiles and spread outward
  - **Orc War Party** — elite orcs push from mountains toward camps and town
- Invasion severity scales with game progress (hero level, ticks elapsed)
- Town NPCs (future) flee to buildings; hero AI prioritizes defense
- **Extensibility:** Invasion definitions in a registry with faction, wave composition, path, and trigger conditions

### F3: Wandering World Bosses
- Unique powerful entities that spawn periodically and roam the map
- Examples: `Ancient Dragon`, `Lich King`, `Giant Troll`, `Shadow Assassin`
- World bosses have: unique skills, massive HP, special loot tables, territory-agnostic movement
- Boss presence announced via event log; nearby entities react (flee or engage based on power comparison)
- Defeating a world boss drops legendary loot and grants bonus XP
- **Extensibility:** `WorldBossDef` registry — stats, skills, loot table, patrol behavior

### F4: Resource Events
- **Resource Boom** — specific resource nodes yield double for N ticks
- **Blight** — resource nodes in a terrain region become depleted and don't respawn for N ticks
- **Treasure Rain** — gold pouches and rare items drop randomly across the map
- **Merchant Caravan** — temporary wandering merchant with rare stock (ties into Epic 02)
- **Extensibility:** Resource events modify `ResourceNode` fields temporarily via the event system

### F5: Environmental Disasters
- **Earthquake** — WALL tiles collapse in an area, opening new paths; entities in area take damage
- **Flood** — FLOOR tiles near WATER temporarily become impassable
- **Wildfire** — spreads across FOREST tiles, damaging entities and depleting resources
- Disasters use `Domain.WEATHER` RNG for determinism
- **Extensibility:** Disaster effects defined as tile transformation rules + entity damage patterns

### F6: Positive Events
- **Festival** — town NPCs celebrate, shop prices reduced, hero heals faster in town
- **Blessing** — random hero receives a temporary buff (TERRITORY_BUFF-style)
- **Discovery** — a hidden area is revealed on the map (new resource node or chest)
- Positive events reward the hero for surviving negative events

### F7: Event AI Integration
- New `GoalScorer`: `DefendGoal` — high score when invasion is active and enemies are near town
- Existing goals modified: `FleeGoal` scores higher during invasions for low-level heroes
- Enemy AI during invasions: coordinated movement toward town center, ignore normal territory behavior
- **Extensibility:** Event influence on goal scoring via `EventUtilityBonus` typed dataclass

### F8: Frontend
- Event banner notification at top of screen (animated slide-in)
- Active events shown in sidebar Events tab with countdown timer
- Invasion enemies rendered with a special glow or marker
- World boss has unique canvas rendering (larger sprite, aura effect)
- Event history preserved in event log with `[EVENT]` category

---

## Design Principles

- Events are properties of `WorldState`, snapshottable and deterministic
- Event handlers are `EventHandler` subclasses registered in an `EVENT_HANDLERS` dict
- All event effects flow through existing systems (spawn, status effects, resource nodes)
- Event scheduling uses `Domain.WEATHER` or a new `Domain.EVENTS` for determinism
- Events are data-driven — adding new events = registering definitions, not modifying core loop

---

## Dependencies

- Entity spawning system (already exists)
- Status effect system (already exists)
- Resource node system (already exists)
- Event log system (already exists)
- Faction system (already exists)

---

## Estimated Scope

- Backend: ~8 files new/modified
- Frontend: ~4 files modified (event banner, rendering, event log)
- Data: Event definitions, invasion compositions, world boss definitions
