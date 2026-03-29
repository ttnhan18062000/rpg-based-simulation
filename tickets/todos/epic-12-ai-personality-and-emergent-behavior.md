# Epic 12: AI Personality & Emergent Behavior

## Summary

Deepen the trait and AI systems to produce truly distinct entity personalities with long-term memory, grudges, preferences, fears, and emergent behavioral patterns. Each entity becomes a unique individual whose history shapes their future decisions.

Inspired by: Rimworld pawn stories, Dwarf Fortress personality system, The Sims needs/wants, Shadow of Mordor Nemesis system.

---

## Motivation

- Current traits modify goal scores but don't create memorable individual behavior
- Entities have no long-term memory of past encounters (only current-tick entity memory)
- No grudge system — an entity that nearly died to a specific enemy doesn't remember the threat
- No preference learning — a hero doesn't learn to avoid dangerous terrain after repeated deaths there
- Aligns with "realistic RPG simulation" — individuals shaped by their experiences

---

## Features

### F1: Long-Term Memory
- Extend `entity_memory` with persistent event records:
  - `combat_history`: list of `(tick, enemy_id, enemy_kind, outcome, hp_lost)`
  - `death_locations`: list of `(tick, pos)` — where the hero died
  - `profitable_areas`: list of `(pos, gold_gained, items_gained)` — where good loot was found
- Memory influences goal scoring: avoid death locations, prefer profitable areas
- Memory decays over time (older entries weighted less)
- **Extensibility:** Memory types defined as `MemoryEntry` subclasses in a registry

### F2: Nemesis System
- When an entity survives a near-death encounter (HP < 10%) against a specific enemy, that enemy becomes a **nemesis**
- Nemesis tracking: `entity.nemesis_id`, `nemesis_encounters: int`, `nemesis_threat: float`
- Behavioral changes:
  - Aggressive entities seek out their nemesis for revenge
  - Cautious entities actively avoid their nemesis
  - Brave entities gain a combat bonus against their nemesis (+10% ATK)
- Nemesis relationship is mutual — the enemy also tracks the hero
- **Extensibility:** Nemesis effects defined per trait combination, not per entity

### F3: Fear & Confidence System
- Each entity has a `confidence: float` (0.0 to 1.0) that shifts based on combat outcomes
- Winning fights → confidence increases → more aggressive goal scoring
- Losing fights or fleeing → confidence decreases → more cautious behavior
- Confidence recovers slowly during rest
- High confidence: willing to engage tougher enemies, explore further from safety
- Low confidence: sticks to safe areas, hunts only weak enemies, rests more often
- **Extensibility:** Confidence thresholds and effects configurable per trait

### F4: Preferred Hunting Grounds
- Heroes develop preferences for terrain types based on success rate
- After multiple successful hunts in FOREST, hero gains `terrain_preference: FOREST`
- Preferred terrain gets +0.1 explore utility bonus; non-preferred gets no change
- Preferences shift over time as the hero gains experience in different terrains
- **Extensibility:** Preference system is trait-influenced (Curious heroes shift preferences faster)

### F5: Entity Mood System
- Each entity has a `mood: float` (-1.0 to +1.0)
- Mood affected by: combat outcomes, health, inventory fullness, time in town, weather, nearby allies/enemies
- Mood modifies global goal scoring:
  - High mood (+0.5 to +1.0): bonus to explore, combat, craft goals
  - Neutral mood (-0.5 to +0.5): normal behavior
  - Low mood (-1.0 to -0.5): bonus to rest, flee goals; penalty to combat
- Mood events logged: "Hero is feeling confident after defeating the goblin chief"
- **Extensibility:** Mood triggers defined in `MoodEvent` registry

### F6: Behavioral Learning
- Over time, entities adjust their base goal scoring weights based on outcomes
- Example: if a hero repeatedly fails at combat with orcs → orc combat score decreases
- If a hero consistently profits from trading → trade goal score gets a persistent bonus
- Learning rate is slow (tiny adjustments per event) and capped
- **Extensibility:** Learning targets defined as `(event_type, goal_name, adjustment)` entries

### F7: Personality Expression in Events
- Event log messages flavored by personality:
  - Aggressive hero: "Hero charges at the goblin with fury!"
  - Cautious hero: "Hero carefully approaches the goblin..."
  - Greedy hero: "Hero's eyes light up at the pile of gold"
- Personality-flavored messages selected from template pools per trait
- **Extensibility:** Message templates tagged by `(event_type, trait)` in a lookup table

### F8: Frontend
- InspectPanel AI tab expanded with:
  - Confidence bar (red to green)
  - Mood indicator (emoji or color)
  - Nemesis section (if any) with encounter history
  - Terrain preferences visualization
  - Combat history summary (wins/losses/flees)
- Entity tooltip on canvas shows mood icon
- Event log messages show personality-flavored text

---

## Design Principles

- All memory and personality state stored on the `Entity` dataclass — snapshottable
- Confidence and mood are updated in WorldLoop Phase 4 (deterministic)
- Learning adjustments are tiny per-event to prevent oscillation
- All personality effects flow through existing goal evaluation pipeline
- Nemesis system uses existing entity ID tracking — no new relationship graph
- Event message flavoring is purely cosmetic — doesn't affect simulation logic

---

## Dependencies

- Trait system (already exists)
- Goal evaluation system (already exists)
- Entity memory system (already exists)
- Event log system (already exists)
- Combat system (already exists)

---

## Estimated Scope

- Backend: ~8 files modified (models.py, states.py, scorers.py, brain.py, world_loop.py, traits.py)
- Frontend: ~3 files modified (InspectPanel AI tab, EventLog, useCanvas tooltips)
- Data: Mood event registry, personality message templates, nemesis effect definitions
