import pytest
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState, InventoryComponent, ItemStack, InteractionComponent, GroundItemState, CorpseState
from src.systems.harvest_system import HarvestSystem
from src.systems.loot_system import LootSystem
from src.engine.apply import ApplyPath

@pytest.fixture
def base_state():
    # Setup a simple state
    node = ResourceNodeState(
        id=101,
        kind="IRON_NODE",
        position=(1, 0),
        yields_item="iron_ore",
        remaining_charges=5,
        max_charges=5,
        required_ticks=1
    )
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .inventory(max_slots=1)
        .interaction(target_node_id=101, progress=0)
        .properties({"interaction_kind": "harvest", "harvest_duration": 1})
        .build()
    )
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={101: node},
        terrain={(0,0): "FLOOR", (1,0): "FLOOR"}
    )

def test_harvest_full_inventory_does_not_deplete_node(base_state):
    # 1. Fill inventory with something else
    from src.core.state import ItemStack
    full_inventory = InventoryComponent(max_slots=1, items=[ItemStack("wood", 1)])
    from dataclasses import replace
    base_state = replace(base_state, entities={1: replace(base_state.entities[1], inventory=full_inventory)})
    
    # 2. Run HarvestSystem
    # Entity is at (0,0), node is at (1,0), dist=1. Progress 0, required 1.
    update = HarvestSystem.update(base_state)
    
    # 2.5 Refine (Enforce Conservation)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(base_state, update)
    
    # 3. Apply updates
    final_state = ApplyPath.apply_generation(base_state, update)
    
    # VIOLATION CHECK:
    # Item was NOT added (InventoryService skips it)
    assert len(final_state.entities[1].inventory.items) == 1
    assert final_state.entities[1].inventory.items[0].item_id == "wood"
    
    # Node SHOULD NOT be depleted (but currently it is)
    assert final_state.resource_nodes[101].remaining_charges == 5, "Node should not be depleted if item cannot be added"

def test_loot_ground_item_full_inventory_does_not_remove_item(base_state):
    # 1. Setup ground item
    ground_item = GroundItemState(id=201, item_id="iron_ore", quantity=1, position=(1, 0))
    from dataclasses import replace
    base_state = replace(base_state, 
        ground_items={201: ground_item},
        entities={1: replace(base_state.entities[1], 
            interaction=replace(base_state.entities[1].interaction, target_node_id=201, progress=9),
            identity=replace(base_state.entities[1].identity, properties={**base_state.entities[1].identity.properties, "interaction_kind": "ground_item"})
        )}
    )
    
    # 2. Fill inventory
    full_inventory = InventoryComponent(max_slots=1, items=[ItemStack("wood", 1)])
    base_state = replace(base_state, entities={1: replace(base_state.entities[1], inventory=full_inventory)})
    
    # 3. Run LootSystem
    update = LootSystem.update(base_state)
    
    # 3.5 Refine (Enforce Conservation)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(base_state, update)
    
    # 4. Apply updates
    final_state = ApplyPath.apply_generation(base_state, update)
    
    # VIOLATION CHECK:
    # Item SHOULD NOT be removed from ground
    assert 201 in final_state.ground_items, "Ground item should not be removed if pickup fails"

def test_loot_corpse_full_inventory_does_not_remove_corpse(base_state):
    # 1. Setup corpse
    corpse = CorpseState(id=301, original_entity_id=99, position=(1, 0), items=[ItemStack("iron_ore", 1)], decay_tick=100)
    from dataclasses import replace
    base_state = replace(base_state, 
        corpses={301: corpse},
        entities={1: replace(base_state.entities[1], 
            interaction=replace(base_state.entities[1].interaction, target_node_id=301, progress=9),
            identity=replace(base_state.entities[1].identity, properties={**base_state.entities[1].identity.properties, "interaction_kind": "corpse"})
        )}
    )
    
    # 2. Fill inventory
    full_inventory = InventoryComponent(max_slots=1, items=[ItemStack("wood", 1)])
    base_state = replace(base_state, entities={1: replace(base_state.entities[1], inventory=full_inventory)})
    
    # 3. Run LootSystem
    update = LootSystem.update(base_state)
    
    # 3.5 Refine (Enforce Conservation)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(base_state, update)
    
    # 4. Apply updates
    final_state = ApplyPath.apply_generation(base_state, update)
    
    # VIOLATION CHECK:
    # Corpse SHOULD NOT be removed
    assert 301 in final_state.corpses, "Corpse should not be removed if loot fails"

def test_crafting_full_inventory_does_not_consume_materials():
    from src.engine.blacksmith import BlacksmithSystem, V2Recipe
    from src.core.state import InventoryComponent, ItemStack, IdentityComponent, AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, EntityUpdate
    from dataclasses import replace
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .inventory(gold=100, items=[ItemStack("iron_ore", 2), ItemStack("wood", 1)])
        .properties({"known_recipes": {"craft_steel_sword"}, "craft_target": "craft_steel_sword"})
        .build()
    )
    # Fix the inventory max_slots separately if needed or just use the builder
    entity = replace(entity, inventory=replace(entity.inventory, max_slots=1))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, building_tiles={(0,0): "blacksmith"})
    # Need to add a functional building too
    from src.core.state import BuildingState
    state = replace(state, buildings={501: BuildingState(id=501, kind="blacksmith", position=(0,0))})
    
    # 2. Run BlacksmithSystem
    update = BlacksmithSystem.enforce(state, StateUpdate())
    
    # 3. Refine (Enforce Conservation)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(state, update)
    
    # 4. Apply
    final_state = ApplyPath.apply_generation(state, update)
    
    # CHECK: Materials and Gold should NOT be consumed because 1 slot cannot hold the result 
    # even if materials are removed (since materials themselves were already violating the 1-slot limit)
    # Actually, can_add_items_with_removals(inv(1 slot, 2 items), add(1), remove(2)) ->
    # remove 2 -> 0 items. add 1 -> 1 item. 1 <= 1. SUCCESS!
    
    # Wait, so even with 1 slot it succeeds if results <= max_slots.
    # To FAIL, we need result > max_slots.
    # Let's use max_slots=0 (impossible but works for test) or 1 and make the recipe output 2 items.
    
    # I'll update the test to use a recipe that outputs 2 items or just set max_slots to 0.
    inv_invalid = replace(entity.inventory, max_slots=0)
    state_invalid = replace(state, entities={1: replace(entity, inventory=inv_invalid)})
    
    update_invalid = BlacksmithSystem.enforce(state_invalid, StateUpdate())
    update_invalid = AuthoritativeApplyPipeline.refine(state_invalid, update_invalid)
    final_state_invalid = ApplyPath.apply_generation(state_invalid, update_invalid)
    
    assert final_state_invalid.entities[1].inventory.gold == 100
    assert len(final_state_invalid.entities[1].inventory.items) == 2
    assert "steel_sword" not in [i.item_id for i in final_state_invalid.entities[1].inventory.items]

def test_quest_completion_full_inventory_does_not_grant_reward():
    from src.systems.quest_system import QuestSystem
    from src.core.quests import QuestState, QuestStatus, QuestKind, RewardState
    from src.core.state import StrategicComponent
    
    # 1. Setup entity with a near-complete explore quest
    quest = QuestState(
        id="q1", kind="QUEST", quest_kind=QuestKind.EXPLORE, 
        goal_value=10.0, current_value=9.0,
        quest_status=QuestStatus.ACTIVE,
        reward=RewardState(xp=100, gold=50, items=["iron_sword"]),
        metadata={"target_position": (0,0)}
    )
    
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .inventory(max_slots=1, items=[ItemStack("wood", 1)])
        .strategic(projects={"q1": quest})
        .build()
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Run QuestSystem
    update = QuestSystem.update(state)
    
    # 2.5 Refine (Enforce Conservation)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(state, update)
    
    # 3. Apply
    final_state = ApplyPath.apply_generation(state, update)
    
    assert final_state.entities[1].inventory.gold == 0
    assert len(final_state.entities[1].inventory.items) == 1
