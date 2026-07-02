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
    *   **Regular Nodes** (e.g., Iron Vein): Lose **1 charge** per harvest tick.
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

Entities with positive public reputation receive a proportional discount at all shops.

**Formula:**

    entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalized [0, 1]
    discount    = entity_rep × 0.20                            # up to 20% at max rep
    discounted  = floor(base_cost × (1 − discount))
    final_cost  = max(1, discounted)                           # floor: never free

**Notes:**
- `public_reputation` sourced from `SocialComponent.public_reputation` (range 0.0–2.0, default 1.0).
- At default reputation (1.0): 10% discount.
- At maximum reputation (2.0): 20% discount.
- At zero or negative reputation: 0% discount (no penalty, no bonus).
- Faction cross-check is not applied in this release (DEV-001). Discount is universal across all shops.
- Conservation law satisfied: buyer pays less, shop receives less; net world gold unchanged.

**Reference:** TCK-20260619-E33D-REP-DISCOUNTS, `src/systems/economy_systems/reputation_discount.py`.

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
