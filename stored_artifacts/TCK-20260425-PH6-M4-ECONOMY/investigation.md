---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M4-ECONOMY
artifact_type: investigation
tags: [ph6, m4, economy]
---

# Investigation — PH6 M4: Economy Interactions

## Goal
Implement deterministic economic interactions in town: shopping (buy/sell), blacksmith services (crafting/repair), and the recipe substrate.

## Requirements
- **Authoritative Transactions**: Gold and items must be exchanged atomically.
- **Recipe Substrate**: Define required materials and gold for crafting items.
- **Bounded Interactions**: Entities must be in a town or near a specific building to access these services.
- **Service Mapping**: Building tiles in `AuthoritativeState` map to services (Shop, Blacksmith).

## Proposed Architecture

### 1. Recipe Registry (`core/recipes.py`)
- `Recipe`: `output_item_id: str`, `output_quantity: int`, `ingredients: List[ItemStack]`, `gold_cost: int`.
- `RecipeRegistry`: Storage for all known recipes (e.g., `iron_sword`, `leather_armor`).

### 2. Shop Service (`town/shop.py`)
- `ShopAction.buy(entity, item_id, quantity, state)`:
  - Validates gold and inventory capacity.
  - Returns `InventoryUpdate`.
- `ShopAction.sell(entity, item_id, quantity, state)`:
  - Validates item existence in inventory.
  - Returns `InventoryUpdate`.

### 3. Blacksmith Service (`town/blacksmith.py`)
- `BlacksmithAction.craft(entity, recipe_id, state)`:
  - Validates materials and gold.
  - Returns `InventoryUpdate`.

### 4. Integration
- These actions should probably be "instant" or very short channels if we want town interactions to feel snappy. For M4, we'll start with instant authoritative updates triggered by proximity to the building.

## Questions
- How do we define which building is a shop?
  `AuthoritativeState.building_tiles` maps coordinates to building types.
- What are the default prices?
  Defined in `ItemRegistry` (implemented in M1).
