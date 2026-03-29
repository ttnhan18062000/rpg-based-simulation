# Epic 07: Reputation & Faction Diplomacy

## Summary

Expand the faction system with dynamic reputation, diplomacy, and inter-faction relations that evolve based on world events and entity actions. Factions can form alliances, declare war, negotiate truces, and shift between hostile/neutral/allied states over time.

Inspired by: Mount & Blade faction diplomacy, Crusader Kings relationship system, Fallout reputation system, Warcraft faction standings.

---

## Motivation

- Current faction relations are static (all hostile to everyone forever)
- No way for the hero to improve standing with enemy factions (e.g. become neutral with wolves by not hunting them)
- Static relations make the world feel rigid — real RPG worlds have shifting politics
- Dynamic diplomacy creates emergent narratives: "the orcs allied with the bandits against the undead"
- Aligns with "realistic RPG simulation" — factions respond to the hero's actions and to each other

---

## Features

### F1: Reputation System
- Each faction tracks a `reputation: int` score (-1000 to +1000) for the hero
- Reputation changes from:
  - Killing faction members: large negative
  - Killing faction enemies: positive (enemy of my enemy)
  - Trading with faction NPCs: small positive
  - Completing faction quests: moderate positive
  - Trespassing on territory without combat: small negative
- Reputation tiers: Hated → Hostile → Unfriendly → Neutral → Friendly → Honored → Exalted
- **Extensibility:** Reputation change amounts defined in a `ReputationEvent` registry, not hard-coded

### F2: Dynamic Faction Relations
- `FactionRelation` between any two factions can change at runtime
- Relation shifts triggered by:
  - One faction's entities repeatedly killing another faction's entities
  - World events (invasion triggers defensive alliances)
  - Hero actions (helping a faction fight a common enemy)
- Relation change thresholds configurable
- `FactionRegistry` becomes mutable at runtime (currently data-driven but static)
- **Extensibility:** Relation shift rules defined as `DiplomacyRule` entries in a registry

### F3: Faction Quests
- Faction-specific quest lines offered when reputation reaches Friendly+
- Example quest chains:
  - **Wolf Pack:** "Thin the orc numbers in the mountains" → reward: wolves ignore hero in forest
  - **Bandit Clan:** "Deliver supplies to our camp" → reward: access to black market
  - **Orc Tribe:** "Prove your strength in combat trials" → reward: orc weapons at discount
- Quest templates tagged with `required_reputation` threshold
- **Extensibility:** Faction quests use the existing `Quest` system with a `faction` filter

### F4: Cease-Fire & Alliance Mechanics
- When hero reputation with a faction reaches Neutral+, entities of that faction stop attacking the hero
- At Friendly+, faction members may assist the hero in combat against mutual enemies
- At Honored+, faction territory no longer applies debuffs to the hero
- Alliances between non-hero factions form dynamically (e.g. orcs + goblins vs undead)
- **Extensibility:** Reputation tier effects defined per tier in a `TierEffect` registry

### F5: Faction Territory Evolution
- Factions can expand or lose territory based on combat outcomes
- If a faction's camp is repeatedly raided, their territory shrinks
- If a faction dominates an area (no enemy presence), they slowly expand
- Territory changes reflected on the map (tile materials change)
- **Extensibility:** Territory expansion rules defined as configurable tick-based checks

### F6: Faction Economy
- Each faction has a `wealth` score that grows from member kills and resource harvesting
- Wealthy factions spawn stronger entities (better gear, higher tiers)
- Poor factions spawn weaker entities and may abandon territory
- Hero trading with faction shops affects faction wealth
- **Extensibility:** Wealth effects on spawn quality defined in `FactionEconomyConfig`

### F7: Frontend
- Reputation bars per faction in a new "Factions" tab on InspectPanel
- Faction territory boundaries drawn on overlay canvas (subtle colored borders)
- Diplomacy notifications in event log: "Orc Tribe and Bandit Clan formed an alliance"
- Minimap shows faction territory colors with dynamic borders
- Faction relations matrix viewable in a new panel

---

## Design Principles

- Reputation is stored per-faction on a global `ReputationTracker` in `WorldState`
- All reputation changes are deterministic (happen in WorldLoop, not in AI workers)
- `FactionRegistry` extended to support runtime relation changes while remaining thread-safe
- Territory evolution is gradual and tick-based — no sudden map changes
- All diplomacy is autonomous — hero's actions influence but don't directly control faction relations

---

## Dependencies

- Faction system with `FactionRegistry` (already exists)
- Territory system with debuffs (already exists)
- Quest system (already exists)
- Entity spawning system (already exists)

---

## Estimated Scope

- Backend: ~10 files new/modified
- Frontend: ~5 files modified
- Data: Reputation events, diplomacy rules, faction quest templates
