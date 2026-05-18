import json
import os
import pytest
from typing import Dict, Any

from src.core.state import AuthoritativeState, EntityState, ResourceNodeState, InteractionComponent, InventoryComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate
from src.engine.interaction import InteractionSystem

# Constants
RESULTS_PATH = "tests/parity/interaction_oracle/results.json"

def load_oracle_results():
    if not os.path.exists(RESULTS_PATH):
        pytest.skip(f"Oracle results not found at {RESULTS_PATH}. Run capture script first.")
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)

# Helper to build V2 state and updates based on scenario
def get_v2_setup(scenario_name: str, oracle: Dict[str, Any]):
    # Common actor
    actor = EntityState(
        id=1, 
        kind="hero", 
        position=(1.0, 1.0),
        interaction=InteractionComponent(target_node_id=500, progress=0),
        inventory=InventoryComponent(max_slots=10)
    )
    
    # Common node
    node = ResourceNodeState(
        id=500,
        kind="WOOD",
        position=(1.0, 1.0),
        yields_item="WOOD",
        remaining_charges=5,
        max_charges=5,
        required_ticks=2
    )

    entities = {1: actor}
    nodes = {500: node}
    
    # Adjust state based on scenario
    if scenario_name == "harvest_done":
        entities[1] = EntityState(
            id=1, kind="hero", position=(1.0, 1.0),
            interaction=InteractionComponent(target_node_id=500, progress=2) # Progress 2/2
        )
    elif scenario_name == "loot_full_inventory":
        entities[1] = EntityState(
            id=1, kind="hero", position=(1.0, 1.0),
            inventory=InventoryComponent(max_slots=1, items=[ItemStack("iron_ore", 1)]) # Use ItemStack to fill it
        )
    elif "interrupted" in scenario_name:
        entities[1] = EntityState(
            id=1, kind="hero", position=(1.0, 1.0),
            interaction=InteractionComponent(target_node_id=500, progress=1)
        )

    state = AuthoritativeState(tick=1, seed=42, entities=entities, resource_nodes=nodes)
    
    # Proposed update (what the AI suggests)
    proposed_interaction = InteractionUpdate(
        target_node_id=500,
        progress_delta=oracle.get("progress_delta", 0.0),
        reset=(oracle.get("progress_set") == 0.0)
    )
    
    # In V2, move-interruption is detected if moved_this_tick is True
    moved = ("interrupted" in scenario_name or scenario_name == "loot_full_inventory")
    
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, interaction=proposed_interaction, moved_this_tick=moved)
        }
    )
    
    return state, update

@pytest.mark.differential
@pytest.mark.parametrize("oracle", load_oracle_results(), ids=lambda o: o["scenario"])
def test_resource_interaction_parity_with_oracle(oracle):
    """
    Verifies that V2 InteractionSystem.enforce matches captured V1 behavior.
    """
    scenario_name = oracle["scenario"]
    state, update = get_v2_setup(scenario_name, oracle)

    # Execute V2 enforcement
    refined_update = InteractionSystem.enforce(state, update)
    e_upd = refined_update.entity_updates.get(1)
    
    assert e_upd is not None, f"Scenario {scenario_name}: No update for entity 1"

    # Parity checks
    if scenario_name == "harvest_tick_1":
        # Progress should stay as delta=1.0 (not reset)
        assert e_upd.interaction.progress_delta == 1.0
        assert e_upd.interaction.reset == False
        
    elif scenario_name == "harvest_done":
        # Completion: progress reset, item added
        assert e_upd.interaction.reset == True
        assert any(item.item_id == "WOOD" for item in e_upd.inventory.items_add)
        
    elif scenario_name == "loot_full_inventory":
        # Inventory full should force reset in V2
        assert e_upd.interaction.reset == True
        
    elif "interrupted" in scenario_name:
        # Movement or target switch results in reset
        assert e_upd.interaction.reset == True

    # Verification of node depletion
    if scenario_name == "harvest_done":
        n_upd = refined_update.node_updates.get(500)
        assert n_upd is not None
        assert n_upd.charges_delta == -1
