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

---

## 4. Commerce: The Market Law
Trading with shops (Buildings) is governed by liquidity and stock availability.

### Buying from Shops
*   **Rule**: The building must have the item in its stock.
*   **Cost**: `Price = Item_Base_Value * Market_Multiplier`.
*   **Outcome**: Gold is transferred from Entity to Building; Item is transferred from Building to Entity.

#### §4.1 Reputation Discount

**Relocated, 2026-09-07 (`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`):** this subsection reads a
Social-domain field (`SocialComponent.public_reputation`), not an Economic one — it now lives in
`docs/mechanics/07_social_political_dynamics.md` §6, the Social & Political Mechanics Bible chapter.
See that section for the full formula, notes, and reference — not duplicated here.

### Selling to Shops
*   **Rule**: The building must have enough **Gold (Liquidity)** to pay the entity.
*   **Benefit**: `Price = Item_Base_Value * 0.5` (static 50% of base value). Dynamic selling prices are out of scope (E5.6). In `ShopSystem.get_sell_price`, a regional trauma surcharge is applied: `price = base * (1.0 + region_trauma / 10.0)`, but this multiplies the item's pre-defined base value directly (not the 50% DynamicPriceService path).
*   **Outcome**: Item is transferred from Entity to Building; Gold is transferred from Building to Entity.

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
