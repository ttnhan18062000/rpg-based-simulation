---
name: systems-economy
description: Work in src/systems/ — economy, crafting, harvest, market, quest, guild. Sourced from the Mechanics Bible's Economic Laws chapter and the buildings/guild/quest technical doc. Use when editing atomic conservation, inventory, market, crafting, harvesting, or quest logic.
source: project
date_added: "2026-08-05"
---

# Systems / Economy (This Repo)

Covers `src/systems/` (25 top-level files: `economy.py`, `crafting.py`, `harvest_system.py`,
`market.py`, `quest_system.py`, `guild_system.py`, `town_service.py`, etc., plus 5
`*_systems/` subdirectories). Sourced from `docs/mechanics/03_economic_laws.md` (Mechanics Bible
ch.3, P0 authoritative) and `docs/simulation/town_contract.md` (authoritative, `src/town/`).
This is the largest single
domain gap found in this repo's skill-catalog sweep — 32+ tickets reference this subsystem, zero
prior skill or agent coverage.

## Atomic Conservation Law

Source: ch.3 §1. Every resource transfer requires: the **source** has the resource available, the
**sink** has capacity to receive it, and **both** updates happen in a single atomic step — either
side failing rolls back the entire transaction. This is the load-bearing invariant underneath
everything else in this skill.

## Inventory Limits

Source: §2. Default slot limit: **16 slots** (each unique item type = 1 slot). Default weight
limit: **50.0 kg** (sum of all item weights). Movement cost scales with total inventory weight
(more weight = more stamina drain per move). Failure outcome for either limit: `INVENTORY_FULL`,
action aborted.

## Resource Harvesting & Regeneration

Source: §3/§3.1. `ResourceNodes` have finite charges — regular nodes (Iron Vein, Stone Outcrop)
lose 1 charge per harvest; loot nodes (Treasure Chest) are fully consumed on first interaction.
Depleted nodes are removed and enter regeneration (if `regen_rate_per_tick > 0`).

Regen runs via the **Resource Ecology Service** on a fixed cadence: `ECOLOGY_INTERVAL = 200`
ticks. Each ecology tick: skip if `regen_rate_per_tick <= 0`; skip if already full; skip if
`cooldown_remaining > 0`; otherwise `new_charges = min(max_charges, remaining_charges +
regen_rate_per_tick)`. Emits `RESOURCE_DEPLETED` (once per tick, dedup set) and
`RESOURCE_RECOVERED` (first time a fully-depleted node goes above 0) via
`StateUpdate.world_events_add`. `GATHER_RESOURCE` adventure-route benefit scales by
`remaining_charges / max_charges` at decision time (see the cognition-strategy skill's
`docs/mechanics/04_strategic_cognition.md` §6.2 citation for the consuming side).

## Market: Buying, Selling, Reputation Discount

Source: §4/§4.1.
- **Buying**: building must have the item in stock. `Price = Item_Base_Value * Market_Multiplier`.
- **Reputation discount** (real formula, `src/systems/economy_systems/reputation_discount.py`):
  ```
  entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalized [0, 1]
  discount    = entity_rep × 0.20                            # up to 20% at max rep
  discounted  = floor(base_cost × (1 − discount))
  final_cost  = max(1, discounted)                           # floor: never free
  ```
  At default reputation (1.0): 10% discount. At max (2.0): 20%. At zero/negative: 0% (no penalty).
  Conservation-law-consistent: buyer pays less, shop receives less, net world gold unchanged.
- **Selling**: building must have enough gold (liquidity). `Price = Item_Base_Value * 0.5` (static
  50%, dynamic selling out of scope per E5.6). `ShopSystem.get_sell_price` applies a regional
  trauma surcharge — `price = base * (1.0 + region_trauma / 10.0)` — directly on the item's
  pre-defined base value, **not** on the 50% dynamic-price path; don't conflate the two formulas.

## Crafting

Source: §5 + `buildings_and_economy.md` §3. Requirements: exact recipe material counts, a gold
cost, and sometimes a specific station (e.g. Forge/Blacksmith). Source materials are destroyed and
the product created in the same tick. Real recipe example (Blacksmith, Steel Sword): 60g, 2× Iron
Ore + 1× Wood. Crafting flow: hero visits blacksmith → learns recipes → picks best upgrade as
`craft_target` → gathers materials/gold → returns → blacksmith consumes materials+gold, produces
item → auto-equips if better → `craft_target` cleared.

## Quest System

Source: `buildings_and_economy.md` §6. **Note the file split**: the quest *model*
(`Quest`/`QuestType` dataclass, templates) lives in `src/core/quests.py`; the runtime system that
consumes it is `src/systems/quest_system.py` — these are two different files, don't conflate them.

3 quest types: **HUNT** (kill `target_count` of an enemy kind), **EXPLORE** (move within 2 tiles
of `target_pos`), **GATHER** (collect `target_count` of an item via loot/harvest). 9 real built-in
templates (`hunt_goblin`, `hunt_wolf`, `hunt_bandit`, `hunt_undead`, `hunt_orc`, `gather_herbs`,
`gather_ore`, `gather_pelts`, `explore_region`), each with a min level and target list. Rewards
scale with `count` and `hero_level` (×1.0 + level×0.1). Limits: `MAX_ACTIVE_QUESTS = 3` per hero,
completed quests pruned every 50 ticks.

## Adventurer's Guild

Source: `buildings_and_economy.md` §4. Camp Intel reveals enemy camp locations
(`terrain_memory`). Resource Node Intel reveals harvestable node locations. Material Hints (if the
hero has a `craft_target`) add tips to the hero's `goals` list about where to find required
materials. Terrain Tips: Forests→wolves→pelts/fangs, Deserts→bandits→fiber/gems,
Swamps→undead→bone/ectoplasm, Mountains→orcs→stone/iron.

## Home Storage

Source: §6. Private, persistent storage at the entity's home position: **32 slots**, **200.0 kg**
(double a standard inventory). Only the owning entity can deposit/withdraw. Only accessible when
physically present at home coordinates.

## The Authoritative Pipeline Phases This Domain Executes Inside

Source: `docs/engine/authoritative_pipeline.md` (the 39-phase `AuthoritativeApplyPipeline`, the
sole mechanism allowed to mutate `AuthoritativeState`). This domain's operations are NOT free-form
— they execute as specific named phases, in this fixed order, and this skill's logic must not
contradict that ordering:

| Phase # | Name | What it does | Compliance ID |
|---|---|---|---|
| 8 | `blacksmith` | Validates crafting/blacksmithing requirements and resource costs | `TOWN-155` |
| 23 | `quest_rewards` | Authoritatively delivers quest rewards and completion markers | `PROG-084` |
| 25 | `shop` | Enforces shop prices and trade legality | `TOWN-166` |
| 27 | `resource_transactions` | Enforces resource conservation and atomic transaction integrity | — |

## What This Skill Does NOT Cover

`guild_system.py`'s own deeper internals beyond what `buildings_and_economy.md` §4 documents (Camp
Intel / Resource Node Intel / Material Hints / Terrain Tips / Quest Generation) are out of scope
for this skill — no Mechanics Bible chapter or contract doc goes deeper than that today. Stated
explicitly rather than silently assumed covered.
