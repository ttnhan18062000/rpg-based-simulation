# Epic 04: Multi-Hero & Party System

## Summary

Expand the simulation from a single hero to multiple heroes that can form parties, specialize in roles, and coordinate tactics. Each hero is fully autonomous with its own class, inventory, and AI — but heroes can choose to group up for harder content.

Inspired by: Final Fantasy party system, Baldur's Gate companion AI, Rimworld colonist management, MMORPG holy trinity (tank/healer/DPS).

---

## Motivation

- Currently only one hero exists — the simulation's "protagonist" bottleneck
- Multiple heroes create emergent group dynamics: who leads, who tanks, who heals
- Party formation enables harder content (dungeon bosses, elite camps) that a solo hero can't handle
- Different classes in a party create tactical synergy (Warrior tanks while Mage deals AoE damage)
- Aligns with "fully automated world" — multiple autonomous agents cooperating without player input

---

## Features

### F1: Multiple Hero Spawning
- Configurable `num_heroes` in `SimulationConfig` (default: 1, expandable to 2–6)
- Each hero spawned with a different class (round-robin or random)
- Each hero has independent: inventory, home storage, quests, craft target, memory
- Heroes share the `HERO_GUILD` faction — allied to each other
- **Extensibility:** Hero count and class assignment via config, not hard-coded

### F2: Party Formation
- New data structure: `Party` dataclass with `leader_id`, `member_ids[]`, `formation`
- Heroes evaluate a `PartyGoal` scorer — high score when nearby allies exist and hard content is nearby
- Party formation triggered when: multiple heroes are near each other and a high-difficulty target exists
- Party dissolves when: objective completed, member HP critical, or members wander apart
- **Extensibility:** Party strategies defined as `PartyStrategy` subclasses (Aggressive, Defensive, Balanced)

### F3: Party AI Coordination
- Party leader selects the target; members follow leader's chosen goal
- Role-based behavior within party:
  - **Tank (Warrior/Champion):** Engages first, draws aggro
  - **DPS (Ranger/Rogue):** Attacks from flanking positions
  - **Support (Mage):** Uses buff skills on allies, attacks from range
- New AI states: `PARTY_FOLLOW`, `PARTY_COMBAT`, `PARTY_SUPPORT`
- Members maintain formation (configurable spacing around leader)
- **Extensibility:** Role behaviors defined per class, not per entity — new classes automatically get role assignments

### F4: Shared XP & Loot
- Kill XP split among party members within a radius (configurable split: equal vs proportional to damage)
- Loot distribution: round-robin or need-before-greed (priority to members who need the item type)
- Gold shared equally
- **Extensibility:** Loot distribution strategies as pluggable `LootDistributor` classes

### F5: Hero Differentiation
- Each hero develops differently based on: class, traits, combat experience, explored terrain
- Heroes that explore different regions accumulate different materials and recipes
- Trading between heroes at the General Store (one sells, another buys)
- Indirect cooperation: one hero clears a camp, another loots the area afterward

### F6: Hero Rivalry & Competition
- When not in a party, heroes may compete for the same loot or quest targets
- Greedy-trait heroes prioritize personal gain over cooperation
- Brave heroes more likely to join parties; Loner heroes avoid them
- Competition creates natural variety in hero progression paths

### F7: Frontend
- Multiple hero diamonds on the canvas, each with a unique color tint
- Party lines drawn between grouped heroes (dashed line connecting members)
- Entity list shows all heroes with individual stats
- Spectate any hero independently
- Party info section in InspectPanel when spectating a party member

---

## Design Principles

- Each hero is a fully independent `Entity` — no shared state between heroes
- Party coordination happens through AI goal scoring, not through a centralized controller
- All party logic runs through the standard `ActionProposal` → `WorldLoop` pipeline
- Party formation/dissolution is emergent from individual AI decisions
- No "player control" — all heroes are fully autonomous

---

## Dependencies

- Hero class system (already exists)
- Faction system — all heroes in `HERO_GUILD` (already exists)
- Goal evaluation system (already exists)
- Building/economy system (already exists)

---

## Estimated Scope

- Backend: ~12 files new/modified
- Frontend: ~6 files modified
- Config: `num_heroes`, party size limits, XP split ratios
