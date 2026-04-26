# PH6 M4: Economy Interactions

Implement deterministic town-based economy services: shopping, crafting, and repair.

## Proposed Changes

### [Recipe Registry] [NEW] [recipes.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/recipes.py)
- Implement `Recipe` dataclass: `output_id`, `output_qty`, `ingredients` (List[ItemStack]), `gold_cost`.
- Implement `RecipeRegistry` with standard recipes:
  - `iron_sword`: 5 iron_ore + 50 gold.
  - `leather_armor`: 5 leather (placeholder for now) + 40 gold.

### [Shop Action] [NEW] [shop.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/shop.py)
- Implement `ShopAction.buy(entity, item_id, qty, state)`:
  - Validates `entity.inventory.gold >= price * qty`.
  - Validates inventory capacity.
  - Returns `InventoryUpdate(items_add=[ItemStack(item_id, qty)], gold_delta=-(price*qty))`.
- Implement `ShopAction.sell(entity, item_id, qty, state)`:
  - Validates item presence.
  - Returns `InventoryUpdate(items_remove=[ItemStack(item_id, qty)], gold_delta=+(price*qty*0.5))`. (50% sell value).

### [Blacksmith Action] [NEW] [blacksmith.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/blacksmith.py)
- Implement `BlacksmithAction.craft(entity, recipe_id, state)`:
  - Validates ingredients and gold.
  - Returns `InventoryUpdate(items_remove=ingredients, items_add=[output], gold_delta=-gold_cost)`.

### [Verification Plan]

#### Automated Tests
- `tests/town/test_economy_contract.py`:
  - Verify shop buy/sell transactions.
  - Verify crafting consumes materials and produces items.
  - Verify transaction rejection on insufficient funds/materials.

#### Manual Verification
- Visual audit of gold and inventory snapshots after town visit cycles.
