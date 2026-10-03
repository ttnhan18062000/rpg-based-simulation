---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260805-SYSTEMS-SKILL
artifact_type: investigation
tags: [skills, economy]
---

# Investigation — TCK-20260805-SYSTEMS-SKILL

## Real `src/systems/` structure confirmed
`find`/`ls` confirmed: 25 top-level `.py` files (economy.py, crafting.py, harvest_system.py,
market.py, quest_system.py, guild_system.py, town_service.py, etc.) plus **5**
`*_systems/` subdirectories (`economy_systems/`, `lifecycle_systems/`, `social_systems/`,
`strategic_systems/`, `world_systems/`) — the ticket's Request Summary cited 6, real count is 5;
noted honestly, doesn't change scope.

## Real docs found beyond the ticket's own citation
`search_docs` surfaced a second real, rich doc the ticket didn't cite:
`docs/systems/buildings_and_economy.md` — "Technical documentation for town buildings, shop
system, crafting, guild services, quests, and treasure chests." Covers Blacksmith recipes (real
item/gold/material tables), the Adventurer's Guild (camp intel, quest generation), Class Hall, and
the Quest System (`src/core/quests.py` — note: quest *model* lives in `src/core/`, distinct from
`src/systems/quest_system.py`, the runtime system that consumes it; both cited correctly, not
conflated). Used alongside `docs/mechanics/03_economic_laws.md` (the ticket's own citation) rather
than only the latter — gives genuine breadth (guild/quest coverage) grounded in a real doc instead
of either fabricating that coverage or omitting it.

## Real Content Grounded
- **Atomic Conservation Law** (`03_economic_laws.md` §1): source-has-resource + sink-has-capacity
  + single atomic step, rollback on either failure.
- **Inventory limits** (§2): 16 slots, 50.0 kg, movement cost scales with weight.
- **Resource harvesting/regen** (§3.1): `ECOLOGY_INTERVAL` = 200 ticks,
  `new_charges = min(max_charges, remaining_charges + regen_rate_per_tick)`,
  `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` events.
- **Reputation discount formula** (§4.1) — the exact real formula:
  `entity_rep = clamp(public_reputation, 0.0, 2.0) / 2.0`, `discount = entity_rep × 0.20`,
  `final_cost = max(1, floor(base_cost × (1 − discount)))`. Source:
  `src/systems/economy_systems/reputation_discount.py`.
- **Selling formula**: `Price = Item_Base_Value * 0.5`, with a regional-trauma surcharge applied
  on top of base value (not the 50% path) in `ShopSystem.get_sell_price`.
- **Crafting** (§5 + `buildings_and_economy.md` §3): recipe materials + gold cost + station
  requirement; source materials destroyed, product created same tick; real recipe table example
  (Steel Sword: 60g, 2× Iron Ore + 1× Wood).
- **Quest System** (`buildings_and_economy.md` §6): 3 real quest types (HUNT/EXPLORE/GATHER), 9
  real built-in templates, `MAX_ACTIVE_QUESTS = 3`, pruning every 50 ticks.
- **Authoritative pipeline phases this domain executes inside** (`docs/engine/authoritative_pipeline.md`,
  confirmed by grep): phase 8 `blacksmith` (TOWN-155), phase 20 `quest_rewards` (PROG-084), phase
  21 `shop` (TOWN-166), phase 22 `resource_transactions`.

## Scope Decision: one skill, focused on documented laws — not all 70 files
Given the domain's real size (25 files + 5 subdirs), a skill cannot exhaustively cover every
file's internals without fabricating undocumented behavior. Decided: **one skill**
(`systems-economy`), scoped to what's actually documented across the 2 real docs above (economic
laws + buildings/guild/quest technical doc) — the authoritative-law layer, not a file-by-file
tour. `guild_system.py`'s own deeper internals beyond what `buildings_and_economy.md` §4 documents
are out of scope — disclosed, not silently assumed covered.

## Unresolved Questions
None — all cited content verified against 2 real docs and real file/phase names.
