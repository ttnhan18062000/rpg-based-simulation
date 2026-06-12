---
status: authoritative
layer: systems
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [town, buildings, economy, sabotage, contract]
---

# Town Engine Contract

**Source:** `src/town/` (10 files: blacksmith.py, buildings.py, class_hall.py, guild.py, home.py, home_storage.py, inn.py, sabotage.py, shop.py, town_navigation.py)  
**Authoritative status:** Town state IS authoritative — `BuildingState` participates in `AuthoritativeState` and its hash.  
**RPG economic laws:** `docs/mechanics/03_economic_laws.md` (atomic conservation — do not duplicate here).  
**System overview:** `docs/systems/buildings_and_economy.md` (do not duplicate here).

---

## Authoritative Pipeline Phases

The town layer participates in 9 of 17 authoritative pipeline phases:

| Phase | Name | Logic ID | Town responsibility |
|---|---|---|---|
| 2 | Actor Validity | `TOWN-001` | Rejects intents from dead, stunned, or incapacitated actors |
| 4 | Production Enforcement | `TOWN-155` | Validates crafting/blacksmithing requirements and resource costs |
| 5 | Action Routing | `TOWN-149` | Resolves combat, skills, and tactical ability interactions |
| 8 | Task Translation | `TOWN-164` | Converts high-level `ENTITY_ACT` tasks into low-level intents |
| 9 | World Interaction | `TOWN-165` | Enforces rules for harvesting, chest opening, and node usage |
| 11 | Infrastructure Sabotage | `LEG-RPG-006` | Resolves damage to buildings and town structures |
| 12 | Town Governance | `TOWN-147` | Updates regional influence, taxes, and town-level state |
| 15 | Economic Enforcement | `TOWN-166` | Enforces shop prices, trade legality, and inventory capacity |
| 17 | Final Integrity | `TOWN-167` | Resolves remaining occupancy conflicts and lifecycle status |

---

## Building System

`src/town/buildings.py` — `BuildingRegistry` defines static templates for each building type.

**Building types and base properties:**

| Type | Constant | max_hp | Services |
|---|---|---|---|
| Inn | `INN` | 1000 | `REST`, `HEAL_DEBT` |
| Guild | `GUILD` | 2000 | `QUEST`, `INTEL` |
| Shop | `SHOP` | 800 | `TRADE` |
| Blacksmith | `BLACKSMITH` | — | crafting |
| Home | `HOME` | — | private rest, storage |
| Church | `CHURCH` | — | — |

`BuildingState` (from `src/core/state.py`) carries: `id`, `kind`, `position`, `hp`, `max_hp`, `functional`.

**Functional rule:** A building is `functional` if `hp > 0`. All service interactions require the target building to be `functional`. Services from a non-functional building are rejected.

---

## Sabotage Pipeline (Phase 11 — `LEG-RPG-006`)

**Entry point:** `SabotageAction.apply(entity, building_id, state) → Optional[StateUpdate]`

**Preconditions (all must pass; any failure returns `None`):**
1. `building_id` exists in `state.buildings`
2. Building is `functional` (`hp > 0`)
3. Entity proximity: `√((ex-bx)² + (ey-by)²) < 5.0` (Euclidean distance)

**Resolution:**
- Damage = entity ATK (from `EntityState`)
- Returns `StateUpdate` with `BuildingUpdate(hp_delta=-damage)`
- If `hp - damage ≤ 0`: building becomes non-functional (`functional=False`)

**Applied by:** Phase 11 of the authoritative pipeline — not applied directly by `SabotageAction`.

---

## Shop / Trade Flow (Phase 15 — `TOWN-166`)

**Entry point:** `ShopService.buy_item(entity, item_id, quantity, state) → Optional[StateUpdate]`

**Preconditions:**
1. At least one functional building of `kind == "shop"` exists in `state.buildings`
2. Entity proximity to shop: Manhattan distance `|ex-sx| + |ey-sy| ≤ 2.0`
3. Entity gold ≥ item cost × quantity (per `ItemRegistry.get(item_id).cost`)
4. Item exists in `ItemRegistry`

**Compliance IDs in shop.py:** ECON-001 through ECON-012 (atomic conservation laws), COMBAT-083/084/085, SOC-012, STRAT-015/016/017/022/201, and others — these reference `docs/mechanics/03_economic_laws.md` for the underlying economic laws.

**Trade legality:** Governed by `TOWN-166` (phase 15). Transactions that violate atomic conservation (items appear without cost deduction, or gold deducted without item transfer) are rejected by the pipeline.

---

## Home Storage Lifecycle (Phase 9 / Phase 15)

**Entry point:** `HomeStorageService.transfer_to_home(entity, item_id, quantity, state) → Optional[StateUpdate]`

**Preconditions:**
1. Entity proximity to town center: Manhattan distance `|ex-tx| + |ey-ty| ≤ 2.0`
2. Entity inventory contains `quantity` of `item_id`
3. Home storage has capacity for the transfer

**Capacity:** Home storage capacity is bounded — transfer is rejected if the destination is full.

**HomeStorageService.transfer_from_home:** Reverse operation — moves items from home storage back to entity inventory. Same proximity rule applies.

**Retention:** Home storage persists indefinitely on `AuthoritativeState`. There is no expiry or overflow eviction — the capacity limit prevents unbounded growth.

---

## Home Rest (Phase 12)

**Entry point:** `HomeAction.rest(entity, state) → Optional[StateUpdate]`

Private rest reduces sleep debt by 40% of current value:
```
sleep_debt_delta = -(entity.biological.sleep_debt * 0.4)
```

Free (no gold cost). Contrast with Inn rest (`HEAL_DEBT` service) which fully restores sleep debt but costs gold.

---

## Town Navigation

**Entry point:** `TownNavigation.get_nearest_service(entity, service_kind, state) → Optional[BuildingState]`

Returns the nearest **functional** building that offers the requested service (Euclidean distance). Returns `None` if no functional building with the service exists.

Service kinds: `REST`, `HEAL_DEBT`, `QUEST`, `INTEL`, `TRADE`.

---

## Proximity Rules Summary

| Action | Distance metric | Max distance |
|---|---|---|
| Sabotage | Euclidean | < 5.0 |
| Shop buy/sell | Manhattan | ≤ 2.0 |
| Home storage transfer | Manhattan (to town_center) | ≤ 2.0 |

---

## Building Max HP by Type

| Building | max_hp |
|---|---|
| Guild | 2000 |
| Inn | 1000 |
| Shop | 800 |
| Others | per BuildingRegistry template |

A building whose `hp` is reduced to 0 or below via sabotage becomes non-functional (`functional=False`) and provides no services until repaired. Repair logic is governed by phase 12 (Town Governance — `TOWN-147`).
