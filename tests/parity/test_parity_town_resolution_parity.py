import json
import pytest
from dataclasses import replace
from typing import Dict, Any

from src.core.state import AuthoritativeState, EntityState, InventoryComponent, IdentityComponent
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.town_resolution import TownResolutionSystem
from src.engine.shop import ShopSystem
from src.engine.blacksmith import BlacksmithSystem

def load_oracle():
    with open("tests/parity/town_oracle/results.json", "r") as f:
        return json.load(f)

@pytest.mark.differential
@pytest.mark.parametrize("scenario", load_oracle())
def test_town_resolution_scenario_parity(scenario):
    """
    Verify V2 Town Resolution produces identical resource deltas as V1 Oracle.
    """
    scenario_id = scenario["scenario"]
    inputs = scenario["input"]
    expected = scenario # Flat structure
    
    # 1. Setup V2 State
    e_id = 1
    initial_items = inputs.get("inventory", [])
    initial_gold = inputs.get("gold", 0)
    
    building_tiles = {}
    town_tiles = set()
    pos = (255, 255)
    town_tiles.add(pos)
    
    if "blacksmith" in scenario_id:
        building_tiles[pos] = "blacksmith"
    elif "shop" in scenario_id:
        building_tiles[pos] = "shop"

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            e_id: EntityState(
                id=e_id,
                kind="hero",
                position=pos,
                inventory=InventoryComponent(
                    items=initial_items,
                    gold=initial_gold
                ),
                identity=IdentityComponent(
                    known_recipes=set(inputs.get("recipes", [])),
                    craft_target=inputs.get("craft_target")
                ),
                properties={"hp": 100, "max_hp": 100}
            )
        },
        town_tiles=town_tiles,
        building_tiles=building_tiles
    )
    
    # 2. Execute V2 Resolution
    update = StateUpdate(entity_updates={})
    update = TownResolutionSystem.resolve(state, update)
    update = ShopSystem.enforce(state, update)
    update = BlacksmithSystem.enforce(state, update)
    
    # 3. Extract and Verify Outcome
    ent_upd = update.entity_updates.get(e_id)
    
    if not ent_upd:
        assert expected["gold_delta"] == 0
        assert not expected["items_removed"]
        assert not expected["items_added"]
        return

    inv_upd = ent_upd.inventory
    
    # Gold Delta Parity
    actual_gold_delta = inv_upd.gold_delta if inv_upd else 0
    assert actual_gold_delta == expected["gold_delta"], f"Gold parity failed in {scenario_id}"
    
    # Inventory Item Parity
    actual_removed = []
    for i in (inv_upd.items_remove if inv_upd else []):
        item_id = i.item_id if hasattr(i, "item_id") else i
        quantity = i.quantity if hasattr(i, "quantity") else 1
        actual_removed.extend([item_id] * quantity)
    actual_removed.sort()
    
    expected_removed = sorted([i for i in expected["items_removed"] if i != "gold"])
    assert actual_removed == expected_removed, f"Removed items parity failed in {scenario_id}. Expected {expected_removed}, got {actual_removed}"
    
    actual_added = []
    for i in (inv_upd.items_add if inv_upd else []):
        item_id = i.item_id if hasattr(i, "item_id") else i
        quantity = i.quantity if hasattr(i, "quantity") else 1
        actual_added.extend([item_id] * quantity)
    actual_added.sort()
    
    expected_added = sorted([i for i in expected["items_added"] if i != "gold"])
    assert actual_added == expected_added, f"Added items parity failed in {scenario_id}. Expected {expected_added}, got {actual_added}"
    
    # Recipe Parity
    if "blacksmith" in scenario_id and expected.get("recipes_learned"):
        actual_learned = sorted(ent_upd.identity.recipes_learned) if ent_upd.identity else []
        assert actual_learned == sorted(expected["recipes_learned"]), f"Recipe parity failed in {scenario_id}"
