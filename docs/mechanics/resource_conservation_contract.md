---
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-06-13
tags: [resource-conservation, atomic-law, crafting, economy, loot, home-storage]
related_chapter: 03_economic_laws.md
---

# Resource Conservation Contract

Companion sub-contract to `03_economic_laws.md`. That chapter names the Atomic Conservation Law; this doc gives the complete formula depth, gate sequence, failure codes, and edge cases needed for agents to safely implement or modify resource transfer logic.

---

## Purpose

Define the exact enforcement mechanism for the Atomic Conservation Law: every resource transfer in the simulation is fully accepted or fully rejected as an indivisible unit. No partial transfers are permitted.

---

## RPG Meaning

Items, gold, and node charges in the world obey strict conservation. An entity cannot harvest a node, receive a crafted item, or buy from a shop unless every precondition passes atomically. If any check fails, the world state is unchanged — no item vanishes, no charge is consumed, no gold is spent.

---

## Inputs

| Field | Type | Description |
|---|---|---|
| `intent` | `ResourceTransferIntent` | The proposed transfer: source_kind, source_id, items_add, items_remove, gold_delta, transaction_id |
| `state` | `WorldState` | Read-only snapshot of world (nodes, inventories, buildings, ground_items, corpses, home_storage) |
| `reservations` | `Dict[tuple[str, str\|int], int]` | Optional — tick-level concurrent reservation counts per (source_kind, source_id) |

---

## Core Rules

1. **Idempotency gate (Gate 1):** If `intent.transaction_id` is in `state.processed_transaction_ids`, immediately reject with `IDEMPOTENCY_VIOLATION`. No further checks run.

2. **Destination capacity check (Gate 2):** `InventoryService.can_add_items_with_removals(inventory, items_add, items_remove)`. This accounts for simultaneous removals so that a swap or craft does not over-count slots. Runs before source validation for every `source_kind`.

3. **Source existence / stock check (Gate 3):** The specific guard depends on `source_kind`:
   - `NODE`: node must exist in `state.resource_nodes`; remaining charges > 0 (accounting for `node_overrides` from same-tick sliding updates and `reservations` dict for concurrent actors)
   - `GROUND_ITEM`: item must exist in `state.ground_items`; not reserved by another actor
   - `CORPSE`: corpse must exist in `state.corpses`; not reserved
   - `CRAFTING`: entity must own all materials; gold >= `gold_cost`; capacity check already done
   - `SHOP_BUY`: building functional, has stock, entity has gold
   - `SHOP_SELL`: building functional, has liquidity (gold), entity has items
   - `HOME_STORAGE`: withdraw → storage has items; deposit → storage has capacity AND entity has items

4. **Atomicity (Gate 4):** On success, a single `TransactionResult` is returned that bundles all updates (`inventory_update`, `node_update` / `ground_item_remove` / `corpse_remove` / `building_update` / `home_storage_update`). The apply path commits all fields together. On failure, `TransactionResult(accepted=False, reason=<ReasonCode>)` is returned and nothing is mutated.

---

## Formula / Decision Logic

### Gate Execution Order

```
resolve(intent, state, reservations):
  1. if intent.transaction_id in state.processed_transaction_ids:
       return TransactionResult(accepted=False, reason=IDEMPOTENCY_VIOLATION)

  2. if not InventoryService.can_add_items_with_removals(inventory, intent.items_add, intent.items_remove):
       return TransactionResult(accepted=False, reason=INVENTORY_FULL)

  3. [source_kind dispatch — Gate 3 checks per source_kind]
     if any Gate 3 check fails:
       return TransactionResult(accepted=False, reason=<specific_code>)

  4. return TransactionResult(accepted=True, inventory_update=..., <source_update>=...)
```

### Market Pricing Formulas

Buy price (`DynamicPriceService.calculate_buy_price`):
```
multiplier = 1.0 + global_salience          # salience in [0.0, 2.0]
multiplier = min(multiplier, 3.0)            # Fair Trade Law hard cap
final_price = max(1, int(base_value * multiplier))
```

Sell price (`DynamicPriceService.calculate_sell_price`):
```
final_price = max(1, int(base_value * 0.5))  # always 50%, no salience modifier
```

`MarketSystem.calculate_price` applies region and building modifiers on top:
```
final = base_val * region_mod * building_mod * type_bias
type_bias = 1.2 (buy) | 0.8 (sell)
return max(1, int(final))
```

### Loot vs Regular Node

Both share the NODE code path in `resolve()`. Distinction is `charges_delta`:

| Node Kind | charges_delta | Effect |
|---|---|---|
| Regular (e.g. `iron_vein`) | `-1` | One charge consumed per harvest |
| Loot (e.g. `treasure_chest`) | `-node.remaining_charges` | All charges consumed in one interaction |

Determined at: `src/core/conservation.py` line 91 — `node.kind == "LOOT"`.

---

## Lifecycle

Runs during **Phase 5 (Resolution)** of the 6-phase deterministic loop (`kernel.md`). Specifically within the authoritative pipeline's resource-transfer resolution phase. The resolver is read-only relative to `WorldState`; mutations are returned as typed update objects and committed by the apply path (Phase 6 / Persistence).

---

## Mutation Rules

**What can change on success:**
- `entity.inventory` (items added/removed, gold delta)
- `resource_node.remaining_charges` (decremented)
- `ground_item` (removed from state)
- `corpse` (removed from state)
- `building.inventory` / `building.gold` (stock and liquidity updated)
- `home_storage` (items added or removed)
- `state.processed_transaction_ids` (transaction_id registered)

**What must never change on failure:**
- Source item/node/corpse is not touched
- Entity inventory is not changed
- Building inventory is not changed
- Home storage is not changed

This is enforced structurally — the authoritative `apply` path only processes updates from an `accepted=True` result.

---

## Failure Codes

| Code | Condition |
|---|---|
| `IDEMPOTENCY_VIOLATION` | Duplicate transaction_id |
| `INVENTORY_FULL` | Destination slot or weight capacity exceeded |
| `TARGET_INVALID` | Node / building does not exist or not functional |
| `SOURCE_DEPLETED` | Node charges <= 0 |
| `SOURCE_MISSING` | Ground item / corpse not found |
| `TARGET_LOCKED` | Source reserved by another actor this tick |
| `INSUFFICIENT_GOLD` | Entity gold < cost |
| `INSUFFICIENT_RESOURCES` | Entity missing recipe materials or sell items |
| `OUT_OF_STOCK` | Building has no stock of requested item |
| `LIQUIDITY_EXHAUSTED` | Building lacks gold to pay sell price |
| `INSUFFICIENT_CAPACITY` | Home storage full on deposit |
| `UNKNOWN_SOURCE_KIND` | Unrecognised `source_kind` string |
| `ACTION_EXHAUSTION` | Gold short for TOWN_SERVICE/TAX or home storage item missing |

---

## Home Storage Rules

- Capacity: 32 slots / 200.0 kg (double standard entity inventory)
- Only accessible when entity is physically present at home coordinates — enforced at the strategic/interaction layer, **not** inside `conservation.py`
- The resolver receives `entity.id` as the storage key (owner security enforced upstream)
- Withdraw path: storage must hold at least the requested quantity of each item
- Deposit path: storage must have capacity AND entity must own the items
- Transfer is symmetric: `inventory_update` adds items entity gains / removes items entity gives; `home_storage_update` does the inverse

---

## Crafting Atomicity

`CraftingSystem` (`src/systems/economy_systems/crafting.py`) runs 7 sequential gate checks before emitting an `InventoryUpdate`:

1. Recipe known in `RecipeRegistry`
2. Entity has `recipe_id` in `identity.known_recipes`
3. Entity role matches `recipe.required_role` (if set)
4. All material quantities present in inventory
5. Gold >= `recipe.gold_cost`
6. Capacity for output (slot count, stacking exemption if item already present)
7. If all pass: emit `InventoryUpdate(items_remove=materials, items_add=[result_item], gold_delta=-recipe.gold_cost)`

The conservation path (`source_kind="CRAFTING"`) then re-checks materials, gold, and capacity atomically. Materials are removed and product added in the same `InventoryUpdate`. This double-check prevents TOCTOU drift between CraftingSystem evaluation and conservation resolution.

---

## Concurrent Actor Protection

The resolver accepts an optional `reservations` dict (`Dict[tuple[str, str|int], int]`). Before committing a NODE, GROUND_ITEM, CORPSE, QUEST, CHEST, or RECRUIT source, the resolver checks `reservations.get((source_kind, source_id), 0)`. If > 0, the second actor receives `TARGET_LOCKED`.

This mechanism prevents duplication when two actors complete the same loot target in the same tick.

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| Craft output would fill inventory, but craft also removes materials that free slots | `can_add_items_with_removals` accounts for removals — slot freed by material removal counts toward capacity for output |
| Two actors harvest same node in same tick | First actor gets `TransactionResult(accepted=True)`; `reservations` marks it; second actor gets `TARGET_LOCKED` |
| LOOT node picked up by one actor while another targets it | Same concurrent protection via reservations |
| Entity sells all items and then tries to deposit gold (zero-item transfer) | Gate 2 passes trivially; Gate 3 checks gold amount; succeeds if transfer is valid |
| `source_kind` not in known set | Returns `UNKNOWN_SOURCE_KIND` immediately after Gate 2 |

---

## Examples

### Successful mineral harvest

```
intent: source_kind=NODE, source_id="iron_vein_3", items_add=[iron_ore×1], gold_delta=0
Gate 1: transaction_id not in processed → pass
Gate 2: inventory has 1 free slot → pass
Gate 3: node exists, remaining_charges=3, not reserved → pass
Result: accepted=True, node_update={remaining_charges: 2}
```

### Failed craft (insufficient gold)

```
intent: source_kind=CRAFTING, recipe_id="iron_sword", gold_delta=-50
Entity gold: 30
Gate 1: unique transaction_id → pass
Gate 2: capacity for sword → pass
Gate 3: CRAFTING path → gold 30 < 50 → fail
Result: accepted=False, reason=INSUFFICIENT_GOLD
```

---

## Source Areas

| Module | Role |
|---|---|
| `src/core/conservation.py` | `ResourceTransactionResolver.resolve()` — primary gate logic |
| `src/systems/economy_systems/crafting.py` | `CraftingSystem` — 7-gate pre-check before conservation |
| `src/systems/economy_systems/loot.py` | Loot resolution before conservation call |
| `src/systems/economy_systems/market.py` | `MarketSystem`, `DynamicPriceService` — pricing |
| `src/systems/economy_systems/chests.py` | Chest/loot node interaction |
| `src/core/models/inventory.py` | `InventoryService.can_add_items_with_removals` |

---

## Regression Tests

| Test / Group | Verified Law |
|---|---|
| `tests_v2/parity/test_resource_conservation_parity.py` | Atomic acceptance/rejection gate sequence |
| `tests_v2/test_crafting_atomicity.py` | 7-gate crafting pre-check and conservation double-check |
| `tests_v2/test_market_pricing.py` | Buy/sell price formulas including salience cap |
| `tests_v2/test_loot_no_duplication.py` (COMB-089) | Concurrent actor reservation prevents loot duplication |
| `tests_v2/test_home_storage.py` | Home storage capacity and withdraw/deposit symmetry |
| Parity ledger entries `town_resource.yaml` | TOWN-121 through TOWN-125 cover concurrent loot protection |

---

## Extension Rules

To add a new `source_kind`:
1. Add the enum value to `SourceKind` in `src/core/conservation.py`
2. Implement the Gate 3 check in the `_check_source_*` dispatch method
3. Add a corresponding failure code to `ReasonCode` if needed
4. Add a `TransactionResult` update field for the source mutation
5. Update the apply path to handle the new update field
6. Add regression tests covering: success path, each new failure code, concurrent reservation if applicable
7. Update this doc and `03_economic_laws.md` if the new source_kind is visible gameplay behavior
