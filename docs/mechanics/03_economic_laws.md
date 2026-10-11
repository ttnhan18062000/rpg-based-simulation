---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-27
---

# Chapter 3: Economic Laws

This chapter defines the laws of resource conservation, trade, and industry within the simulation. Every item and gold coin follows the **Atomic Conservation Law**.

---

## 1. Atomic Conservation Law
The simulation enforces a strict "Source and Sink" balance. A resource transfer only succeeds if:
1.  **The Source** has the resource available.
2.  **The Sink (Destination)** has the capacity to receive it.
3.  **Both** updates happen in a single atomic step. If either fails, the entire transaction is rolled back.

---

## 2. Inventory & Logistics
Entities are constrained by physical limits. Inventory management is a core survival mechanic.

| Constraint | Law | Failure Outcome |
| :--- | :--- | :--- |
| **Slot Limit** | Default: **16 slots**. Each unique item type occupies 1 slot. | `INVENTORY_FULL` (Action Aborted) |
| **Weight Limit** | Default: **50.0 kg**. Sum of all item weights. | `INVENTORY_FULL` (Action Aborted) |
| **Mobility** | Movement Cost scales with total inventory weight. | Increased Stamina drain per move. |

---

## 3. Resource Harvesting
Resources exist in the world as `ResourceNodes`.

*   **Node Charges**: Nodes have finite energy.
    *   **Regular Nodes** (e.g., Iron Vein, Stone Outcrop): Lose **1 charge** per harvest tick.
    *   **Loot Nodes** (e.g., Treasure Chest): Are **fully consumed** on the first successful interaction.
*   **Depletion**: Once charges reach 0, the node is removed from the world and enters a regeneration phase (if applicable).
*   **A Held Gather Ends When Its Node Cannot Yield**: an `INTERACT` on a node that is missing or has no charges left spends nothing, gathers nothing and fails with `SOURCE_MISSING` or `SOURCE_DEPLETED` (`CoreActions.execute_interact`). That is an unrecoverable failure, so the held task is cleared (`ActionRoutingPhase.route()`, `src/engine/pipeline_phases/actions.py`, the same reset as a held `ATTACK`, Bible 02) and the scheduler hands the entity back to the brain. Without it the entity was re-dispatched the same no-op, annotated `SUCCESS`, every tick for hundreds of ticks (`TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED`). The brain may pick the node again once regeneration (section 3.1) refills it.
*   **Wild Food Is Part of the Land** (SURV-06, owner decision 29): a food node (`berry_thicket`, yielding `wild_berries`, 30 hunger per item) stands only in wild land, never in town land, which holds owned food. Each biome declares how much wild food its land holds (a forest or sacred grove 10 charges, the swamp border 8, deep or cursed land and the frontier-village biome none) and how fast it regrows (the schema default, one charge per ecology interval, through the process in 3.1); the amounts are never sized to demand. Every recipe node (any kind, unless its kind opts out with `placement: uniform`) is placed on a tile its declared region OWNS by region precedence (up to 64 draws of the node's seeded stream; none found means no node and a compile warning), so a node declared in wild land never lands on a tile a town or another region owns. Eating what a subject carries consumes the item together with the meal (`CARRIED_FOOD`, 30 hunger per item); core `EAT` with nothing carried keeps its old relief of 40 while the free-meal removal is parked (`d27-free-meal-removal`).

### 3.1 Resource Regeneration

Regenerating nodes carry a `regen_rate_per_tick` field (integer ≥ 0). Nodes with
`regen_rate_per_tick > 0` are processed by the **Resource Ecology Service** on a
fixed cadence:

| Constant | Value | Meaning |
| :--- | :--- | :--- |
| `ECOLOGY_INTERVAL` | **200 ticks** | Number of ticks between ecology checks |
| `regen_rate_per_tick` | per-node field | Charges restored per ecology interval |

**Regen rules** (applied at each ecology tick):
1. Skip if `regen_rate_per_tick <= 0`.
2. Skip if `remaining_charges >= max_charges` (already full).
3. Skip if `cooldown_remaining > 0`.
4. Otherwise: `new_charges = min(max_charges, remaining_charges + regen_rate_per_tick)`.

**Bare wait** (declared `regrowth_mode: regrow`, memo row 59): the harvest that empties such a node starts `respawn_cooldown` ticks of waiting
(the typed `RESOURCE_DEPLETED` record site, `economy._record_depletion`); the wait ends with no charges added and rules 1 to 4 resume from zero.
The default mode `none` starts no wait. (A finished wait on a `none` node adds `max_charges`, a latent path no kind reaches today.)

**Events emitted** (via `StateUpdate.world_events_add` → `recent_world_events`):

| Event | When |
| :--- | :--- |
| `RESOURCE_DEPLETED` | A harvest reduces `remaining_charges` to 0 (emitted once per tick via dedup set). |
| `RESOURCE_RECOVERED` | Ecology regen brings a fully-depleted node (`remaining_charges == 0`) above 0 charges for the first time. |

**Depletion-aware adventure scoring** (from Epic 2.1C): `GATHER_RESOURCE` route
benefit is scaled by `remaining_charges / max_charges` at decision time, so agents
naturally deprioritize exhausted nodes. See `docs/mechanics/04_strategic_cognition.md` §6.2.

*Sources: `src/world/ecology.py` (`ResourceEcologyService.process_ecology`),
`src/engine/economy.py` (RESOURCE_DEPLETED emitter),
`src/domains/world_emergence/schema.py` (`WorldEventCategory`).*

### 3.2 Meat from Bodies (Decision 44)
A dead body is a source of food, and the only one that is not a resource node.

*   **Source**: at death, whatever the cause, a body whose kind declares `edible_as: [meat]` leaves `meat_yield` units of `raw_meat` on its corpse
    (the typed source `BODY_AT_DEATH`; `src/engine/carcass.py`). A kind that feeds nobody leaves none.
*   **Sink**: meat leaves a corpse only by being eaten there (an `EAT` transfer whose source kind is `CORPSE_FOOD` and whose source id is the
    corpse id, so every meal is traceable to the body it came from), by being looted (`CORPSE`), or when the corpse decays (the typed sink
    `CORPSE_DECAY`).
*   **Diet gate**: an eater may eat an item only if the item's `food_class` (`plant`, `meat`, `prepared`) is in its body's `diet`. An undeclared
    diet keeps the legacy "eats any food". Raw meat fills less than a prepared meal (20 against 30: raw flesh is harder to digest).
*   **Exclusions**: a kind never regards its own species as food, and a faction never hunts its own members.
*   **Yield by size** (owner row 60, band anchors not targets): small 2, medium 5, large 12 to 15 units of 20 hunger each: a small body is one meal
    for a meat-eater, a medium one about a day's food for a same-size meat-eater, a large one several days or a pack's day. A meat-eater's hunger
    rate is the `very_low` need level (0.3 of the base, 0.03 per tick), so a full meal lasts at least a day to the starvation line. With no
    spoilage until M3 a carcass keeps until it decays (`CORPSE_DECAY`).
*   **Plant cover** (memo row 59): wild land of a biome that declares `grazing_cover` carries patches of a `regrow` resource kind (one kind per
    fertility band: 6 / 12 / 20 charges, regrowing 1 / 2 / 3 per ecology check, a patch emptied stays bare 4800 / 2400 / 1200 ticks and regrows
    from zero). It yields `grass_cover`, food class `graze` (20 hunger), eaten only by a diet that includes `graze`.
*   **Wild creatures and factions** (decision 47): a faction verdict never decides a fight with a wild creature (a body with a diet whose faction
    has the `wild` alignment). Appraisal decides, in both directions: hunt if hungry and able to overcome, defend or flee if threatened.

*Sources: `src/engine/carcass.py`, `src/core/conservation.py` (`_corpse_food_result`), `src/engine/domain/core_actions.py` (`corpse_meal`),
`src/engine/appraisal.py` (`can_eat_item`), `data/content/living/body_models.yaml`, `data/content/world/items.yaml`.*

---

## 4. Commerce: The Market Law
Trading with shops (Buildings) is governed by liquidity and stock availability.

### Buying from Shops
*   **Rule**: The building must have the item in its stock.
*   **Cost**: `Price = Item_Base_Value * Market_Multiplier`.
    *   **Pressure term removed (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`)**: `DynamicPriceService.calculate_buy_price(base_value)` returns `max(1, int(base_value))`. The former `min(3.0, 1 + global_salience)` multiplier is gone, so a buy price never depends on host timing or on a pressure signal. `Market_Multiplier` is only what `MarketSystem` derives from region and building modifiers. Recorded in `docs/guidelines/intentional_divergences.md` §2.75.
*   **Outcome**: Gold is transferred from Entity to Building; Item is transferred from Building to Entity.

#### §4.1 Reputation Discount

**Relocated, 2026-09-07 (`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`):** this subsection reads a
Social-domain field (`SocialComponent.public_reputation`), not an Economic one — it now lives in
`docs/mechanics/07_social_political_dynamics.md` §6, the Social & Political Mechanics Bible chapter.
See that section for the full formula, notes, and reference — not duplicated here.

### Selling to Shops
*   **Rule**: The building must have enough **Gold (Liquidity)** to pay the entity.
*   **Benefit**: one sell law (EXCH-01/EXCH-02, `TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02`): `Price = MarketSystem.calculate_price(is_buy=False)` per UNIT, i.e. base value x region modifier x building modifier x 0.8 (the sell factor; a buy uses 1.2), at least 1 gold, times the quantity sold. The base value is `MarketSystem`'s table, else the item's catalog value. Regional trauma no longer moves the sell price (the old `ShopSystem.get_sell_price` surcharge `base * (1 + trauma / 10)` is gone ON PURPOSE: one law; EXCH-01 allows more price factors, so trauma can return later as a declared factor). The shop pays only out of its own purse, so a sale never takes more units than the purse covers.
*   **Who sells**: selling is a chosen act (AGENCY-01): a subject whose task is the SELL action at a shop sells what it can spare; standing beside a shop sells nothing. The gathered materials (wood, ore, iron ore, fish, leather, fiber, herb) sell; the last unit of a weapon or armor stack and any item an equipment slot names stay with their owner; food sells only as surplus, keeping at least one meal's worth (60 hunger of recovery).
*   **Paid work** (EXCH-02, owner decision 34): a subject that cannot afford a meal and has nothing to sell works a shift at an inn: the `WORK` action is held for 200 ticks (a two-hour kitchen and yard shift at 36 seconds a tick) beside the inn, then the inn pays 6 gold (a meal and a coin) out of its OWN purse as one typed `WAGE` transfer, once per shift. A short purse pays nothing: the worker is unpaid and no coin appears. Only a kind authored with the `keeps_coin_and_trades` trait sells or works for a wage, and only while the controlling faction of the building's region is not hostile to it (owner decisions 42 and 43). While the free meal stands (owner decision 44) the sale and the shift are dormant in the measured worlds. The public wage for town work (decision 37) is that same shift at a building a treasury keeps: see Section 4.1.
*   **Outcome**: Item is transferred from Entity to Building; Gold is transferred from Building to Entity.

### 4.1 Treasuries, Tax and Rewards (EXCH-02, owner decisions 37, 38, 51 and 58)
*   **Treasury**: each region-owner bucket has one treasury (`global_resources`, key via `src/core/treasury.py`), started with the sum of its member factions' declared starting gold. It is coin like any purse: it pays only what it holds and never goes negative by a transfer.
*   **Tax**: there is no periodic levy. A sale or a wage pays a tenth of the proceeds (declared content, rounded down per transaction, the same for outsiders) to the treasury of the faction holding the building's region, in the same transaction.
*   **Upkeep**: on the upkeep tick each functional building meets 5 gold of upkeep from its OWN purse (nothing is paid out to a payee: coin leaves a building only as wages and tax); the holder's treasury pays its debts oldest first, then tops up only a building's shortfall; a building neither can pay is disabled and reopens when it can. No coin is minted. A shift at a treasury-backed WORK kind pays the inn rate from the building's purse, topped up by the treasury (declared, not yet reachable in play).
*   **Rewards**: a kill grants experience only; the dead entity's coin and goods move to its body and a looter takes them; a body that decays leaves its coin where it fell, as a purse on the ground (with the body it fell from and the tick) that a looter can take. A quest reward's gold is paid by its one real giver (the posting building's ground holder or the offering faction); a short giver records an owed debt, paid oldest first; a quest with no giver pays experience only. There is no gold sink: no wealth levy, surcharge or repair fee.
*   **Inheritance and repair**: an heir takes the dead entity's items and coin atomically; a repair is charged once into the smith's purse, or uses a carried repair kit away from one.
*   **Conservation**: the total of entity purses, building purses, bodies, purses on the ground and treasuries changes only by declared world-creation coin.

---

## 5. Industry: Crafting & Conversion
Entities can transform raw materials into finished goods.

*   **Requirements**:
    1.  **Recipe Materials**: The exact item counts specified.
    2.  **Gold Cost**: Labor and processing fees.
    3.  **Station**: Some crafts require a specific building type (e.g., Forge).
*   **Conversion**: The source materials are **destroyed** and the product is **created** in the same tick.

---

## 6. Private Wealth: Home Storage
Every entity has a private, persistent storage unit located at their home position.

*   **Capacity**: **32 slots** and **200.0 kg** (double a standard inventory).
*   **Security**: Only the owning entity can deposit or withdraw from their home storage.
*   **Sync**: Storage is only accessible when the entity is physically present at their home coordinates.

---

## 7. Per-Physical-Item Identity: `ItemInstance` Ownership History

Added by TCK-20260831-ITEM-INSTANCE-HISTORY. `ItemStack` (Section 2) tracks *quantity by
`item_id`* only — it has no notion of a specific physical object's provenance, and this Chapter
had zero prior mentions of item identity/instance concepts before this section. `ItemInstance`
introduces a strictly additive, opt-in layer on top of it for items whose individual history
matters.

*   **Scope**: Only items explicitly flagged `significant=True` at creation receive an
    `ItemInstance` record. All other items continue through the ordinary `ItemStack` path
    unchanged — this law does not apply to the general case.
*   **Additivity Law**: `ItemInstance` never replaces or substitutes for a significant item's
    `ItemStack` entry. Both representations coexist: `ItemStack` still governs quantity/weight/
    slot conservation (Sections 1–2); `ItemInstance` separately tracks that one physical item's
    ownership lineage. A stack-merge of same-`item_id` `ItemStack`s (e.g. two same-`item_id`
    significant items ending up in one inventory) must never collapse their distinct
    `ItemInstance` records into one.
*   **Ownership Transfer Law**: Transferring a significant item (sale, gift, loot pickup by a new
    owner) appends the new owner's entity id to `owner_history` — **append-only**; prior owners
    are never overwritten or dropped. This is a typed `ItemInstanceUpdate`, and the append may
    only be committed by `ApplyPath.apply_generation` — no other code path may mutate a live
    `ItemInstance`.
*   **No Automatic Classification**: `significant` is a caller-supplied boolean with no default
    and no rarity/tier/value heuristic behind it. As of this writing, zero production call sites
    set `significant=True` — the trigger criteria for what makes an item "significant" is an
    explicit open design decision, not defined by this law. The feature is gated by
    `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF).
