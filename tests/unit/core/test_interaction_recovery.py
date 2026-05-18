import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, InventoryComponent, InteractionComponent, ResourceNodeState, ItemStack, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate
from src.engine.interaction import InteractionSystem
from src.engine.town_resolution import TownResolutionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction

def test_weight_pressure_enforcement():
    # Setup state: Entity with limited weight capacity
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .inventory(items=[ItemStack("wood", 1), ItemStack("wood", 1)])
              .combat(readiness=100.0)
              .build())
    
    # max_weight=5.0 override (Default is 50)
    entity = replace(entity, inventory=replace(entity.inventory, max_weight=5.0))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={10: ResourceNodeState(id=10, kind="ORE", position=(0,0), yields_item="ore", remaining_charges=1, max_charges=1, required_ticks=1)}
    )
    
    # Interaction: Finish harvest of ORE (Weight 5.0)
    # Total weight would be 4.0 + 5.0 = 9.0 > 5.0
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0, target_node_id=10))}
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, upd)
    ent_upd = refined.entity_updates[1]
    
    # Should have been reset due to weight pressure
    assert ent_upd.interaction.reset is True
    assert ent_upd.inventory is None

def test_channeled_looting_one_shot():
    # Setup state: LOOT node
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .combat(readiness=100.0)
              .build())
    
    # Set interaction state
    entity = replace(entity, interaction=InteractionComponent(progress=9, target_node_id=10))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        resource_nodes={10: ResourceNodeState(id=10, kind="LOOT", position=(0,0), yields_item="gold", remaining_charges=10, max_charges=10, required_ticks=10)}
    )
    
    # Interaction: Finish looting
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))}
    )
    
    refined = AuthoritativeApplyPipeline.refine(state, upd)
    
    # Node update should have charges_delta = -10 (ALL charges consumed for LOOT)
    node_upd = refined.node_updates[10]
    assert node_upd.charges_delta == -10
    
    # Entity should get the item
    actual_added = [i.item_id if hasattr(i, "item_id") else i for i in refined.entity_updates[1].inventory.items_add]
    assert "gold" in actual_added

def stack(item_id: str, quantity: int = 1) -> ItemStack:
    return ItemStack(item_id=item_id, quantity=quantity)


def test_shop_sell_refactor():
    """
    Verify that shop auto-sell is converted into an authoritative InventoryUpdate.

    Important pipeline rule:
        ShopSystem.enforce(...) creates ResourceTransferIntent.
        AuthoritativeApplyPipeline.refine(...) then runs resource transaction
        resolution and converts the intent into InventoryUpdate.

    Therefore this test must call the full pipeline, not ShopSystem.enforce(...)
    directly, if it wants to assert ent_upd.inventory.

    Important map rule:
        In the latest source/tests, building_tiles maps tile -> building kind,
        not tile -> building id.

        Correct:
            building_tiles={(0, 0): "shop"}

        Wrong for this path:
            building_tiles={(0, 0): 100}

    Fraud this catches:
        - shop tile is not detected
        - auto-sell intent is not generated
        - resource transaction resolver does not convert sell intent
        - inventory update is missing after full refinement
    """
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction
    from src.core.models.inventory import ItemStack
    from src.core.state import (
        AuthoritativeState,
        BuildingState,
        InventoryComponent,
    )
    from src.core.updates import StateUpdate
    from src.engine.pipeline import AuthoritativeApplyPipeline

    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
        )
        .inventory(
            items=[
                ItemStack(item_id="iron_ore", quantity=1),
            ],
            gold=0,
        )
        .combat(
            hp=100,
            max_hp=100,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: entity,
        },
        buildings={
            100: BuildingState(
                id=100,
                kind="shop",
                position=(0, 0),
                functional=True,
                inventory=InventoryComponent(gold=1000),
            ),
        },
        town_tiles={
            (0, 0),
        },

        # Latest source/test convention:
        # tile -> building kind string.
        # Do not use 100 here.
        building_tiles={
            (0, 0): "shop",
        },
    )

    refined = AuthoritativeApplyPipeline.refine(
        state,
        StateUpdate(force_full_scan=True),
    )

    ent_upd = refined.entity_updates.get(1)

    assert ent_upd is not None
    assert ent_upd.inventory is not None, (
        f"Expected InventoryUpdate after full pipeline refinement. "
        f"Got entity update: {ent_upd}"
    )

    assert ent_upd.inventory.gold_delta == 10
    assert any(
        item.item_id == "iron_ore"
        for item in ent_upd.inventory.items_remove
    )

def test_movement_interruption():
    # Setup state: Channelling interaction
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .combat(readiness=100.0)
              .build())
    entity = replace(entity, interaction=InteractionComponent(progress=5, target_node_id=10))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Update: Move while channelling
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, moved_this_tick=True, interaction=InteractionUpdate(progress_delta=1.0))}
    )
    
    refined = InteractionSystem.enforce(state, upd)
    assert refined.entity_updates[1].interaction.reset is True
