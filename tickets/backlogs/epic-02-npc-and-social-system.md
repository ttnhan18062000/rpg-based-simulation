# Epic 02: NPC & Social System

## Summary

Introduce non-player characters (NPCs) as a new entity role that populates the town and world. NPCs have daily routines, relationships, dialogue, and provide services beyond static buildings. This transforms the town from a set of utility points into a living settlement.

Inspired by: Stardew Valley NPC schedules, Dwarf Fortress social simulation, Elder Scrolls NPC routines, Rimworld colonist interactions.

---

## Motivation

- `EntityRole.NPC` exists in the enum but is unused
- Town buildings are currently static interaction points with no personality
- A living town with NPCs dramatically increases simulation realism
- NPCs create emergent social dynamics: friendships, rivalries, merchant competition
- Aligns with "fully automated world" — NPCs act autonomously alongside the hero

---

## Features

### F1: NPC Entity Type
- NPCs use the existing `Entity` model with `EntityRole.NPC`
- Each NPC has: name, profession, personality traits, home position, schedule
- NPC professions: Shopkeeper, Blacksmith, Guildmaster, Innkeeper, Guard, Farmer, Healer, Wandering Merchant
- **Extensibility:** `NPCDef` dataclass defines profession, schedule template, dialogue pool — new NPC types = new data

### F2: Daily Schedules
- NPCs follow time-of-day schedules (tied to tick ranges or a day/night cycle)
- Schedule phases: Wake → Work → Break → Work → Rest
- During Work: NPC stands at their assigned building/post
- During Break: NPC wanders town, visits other NPCs
- During Rest: NPC returns to home position
- Schedules defined as data (list of `(tick_range, location, activity)`)
- **Extensibility:** New schedule types added without code changes

### F3: Relationship System
- Each NPC tracks a `relationship_score` (-100 to +100) with the hero and other NPCs
- Score changes from: trading, quests completed, gifts, proximity time
- Relationship tiers: Stranger → Acquaintance → Friend → Close Friend → Rival → Enemy
- Higher relationship unlocks: better trade prices, exclusive quests, crafting discounts, unique dialogue
- **Extensibility:** Relationship effects defined in a `RelationshipTier` registry

### F4: NPC AI States
- New AI states: `NPC_WORKING`, `NPC_BREAK`, `NPC_RESTING`, `NPC_FLEEING`
- NPCs flee to town center or buildings when enemies approach town
- NPCs with Guard profession engage enemies (use combat system)
- NPC AI uses the same hybrid goal/state architecture
- **Extensibility:** New NPC behaviors = new `StateHandler` subclass + register

### F5: Dialogue System
- NPCs have context-aware dialogue lines based on: relationship, hero state, time of day, recent events
- Dialogue displayed in InspectPanel when clicking an NPC
- Dialogue pools are data-driven (JSON/dataclass arrays)
- Special dialogue for quest-giving, shop tips, world lore
- **Extensibility:** Dialogue templates with conditional triggers, not hard-coded strings

### F6: Wandering Merchants
- Special NPC type that travels between towns/camps on roads
- Carries rare/unique items not available in the General Store
- Appears periodically (configurable spawn interval)
- Can be attacked by enemies while traveling (hero can escort for relationship bonus)

### F7: NPC Needs & Morale
- NPCs have basic needs: food, rest, safety
- Unmet needs reduce morale → slower service, worse prices, may leave town
- Hero can help NPCs (bring food, clear nearby threats) to boost morale
- Town prosperity score derived from aggregate NPC morale

### F8: Frontend
- NPCs rendered on canvas as distinct shapes (e.g. square with profession icon)
- InspectPanel shows: NPC name, profession, relationship bar, current activity, dialogue
- Relationship history visible in a new panel section
- NPC schedule visualized as a timeline bar

---

## Design Principles

- NPCs use the same `Entity` model — no parallel entity system
- NPC AI plugs into existing `AIBrain` with NPC-specific `GoalScorer` subclasses
- Relationships stored on the NPC entity (not a global graph) for snapshot safety
- All NPC behavior deterministic via `DeterministicRNG`
- Schedule system is data-driven — not a time-of-day hardcode

---

## Dependencies

- `EntityRole.NPC` enum (already exists)
- `EntityBuilder` pattern (already exists)
- Status effect system for morale debuffs (already exists)
- Faction system — NPCs belong to `HERO_GUILD` faction

---

## Estimated Scope

- Backend: ~10 files new/modified
- Frontend: ~4 components new/modified
- Data: NPC definitions, schedules, dialogue pools
