import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, BuildingState, 
    InventoryComponent, ItemStack, RegionState, CombatComponent
)
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.core.enums import ReasonCode
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.systems.market import MarketSystem

@pytest.fixture
def economic_state():
    # Setup a region with a shop
    region = RegionState(
        id="village",
        name="The Village",
        bounds=(0, 0, 10, 10),
        price_modifiers={"MATERIAL": 1.5} # Materials are expensive here
    )
    
    # Shop with limited stock and gold
    shop = BuildingState(
        id=501,
        kind="shop",
        position=(5, 5),
        inventory=InventoryComponent(
            items=[ItemStack("iron_ore", 2)], # Only 2 iron ore
            gold=100
        )
    )
    
    # Entity with gold
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .position(5, 5)
        .gold(200)
        .readiness(100.0)
        .build()
    )
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        buildings={501: shop},
        regions={"village": region},
        terrain={(5,5): "FLOOR"},
        building_tiles={(5,5): "shop"}
    )

def test_shop_stock_depletion(economic_state):
    # RPG-ECON-200: Shop stock enforcement
    # 1. Proposal: Buy 3 iron ore (Shop only has 2)
    price = MarketSystem.calculate_price(economic_state, economic_state.buildings[501], "iron_ore", is_buy=True)
    # 2 * 1.5 (region) * 1.2 (buy) = 3.6 -> 3 gold per unit? 
    # Actually Base(5) * 1.5 * 1.2 = 9 gold per unit.
    
    intent = ResourceTransferIntent(
        source_id=501,
        source_kind="SHOP_BUY",
        items_add=[ItemStack("iron_ore", 3)],
        gold_cost=price * 3,
        transfer_kind="BUY"
    )
    
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    # 2. Authoritative Resolution
    refined = AuthoritativeApplyPipeline.refine(economic_state, update)
    
    # 3. Verify Rejection
    res = next((r for r in refined.entity_updates[1].intent_results if r.source_id == 501), None)
    assert res is not None
    assert not res.accepted
    assert res.reason == ReasonCode.OUT_OF_STOCK
    
    # 4. Proposal: Buy 2 iron ore (Valid)
    intent_valid = ResourceTransferIntent(
        source_id=501,
        source_kind="SHOP_BUY",
        items_add=[ItemStack("iron_ore", 2)],
        gold_cost=price * 2,
        transfer_kind="BUY"
    )
    update_valid = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent_valid])})
    refined_valid = AuthoritativeApplyPipeline.refine(economic_state, update_valid)
    
    # 5. Apply and Verify State
    final_state = ApplyPath.apply_generation(economic_state, refined_valid)
    
    # Entity has items, lost gold
    assert len(final_state.entities[1].inventory.items) == 1
    assert final_state.entities[1].inventory.items[0].quantity == 2
    assert final_state.entities[1].inventory.gold == 200 - (price * 2)
    
    # Shop lost items, gained gold
    assert len(final_state.buildings[501].inventory.items) == 0
    assert final_state.buildings[501].inventory.gold == 100 + (price * 2)

def test_shop_liquidity_depletion(economic_state):
    # RPG-ECON-201: Shop liquidity enforcement
    # Shop has 100 gold.
    # 1. Give entity expensive items to sell
    from dataclasses import replace
    expensive_items = [ItemStack("iron_sword", 5)] # Base 50 each
    new_entity = (V2EntityBuilder(1)
        .kind("HERO")
        .position(5, 5)
        .gold(0)
        .items(expensive_items)
        .readiness(100.0)
        .build()
    )
    economic_state = replace(economic_state, entities={1: new_entity})
    
    price = MarketSystem.calculate_price(economic_state, economic_state.buildings[501], "iron_sword", is_buy=False)
    # Base(50) * 1.0 (region mod for GEAR) * 0.8 (sell) = 40 gold each.
    # Selling 3 would cost shop 120 gold. Shop has 100.
    
    intent = ResourceTransferIntent(
        source_id=501,
        source_kind="SHOP_SELL",
        items_remove=[ItemStack("iron_sword", 3)],
        gold_delta=price * 3,
        transfer_kind="SELL"
    )
    
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    refined = AuthoritativeApplyPipeline.refine(economic_state, update)
    
    # 2. Verify Rejection
    res = next((r for r in refined.entity_updates[1].intent_results if r.source_id == 501), None)
    assert res is not None
    assert not res.accepted
    assert res.reason == ReasonCode.LIQUIDITY_EXHAUSTED

def test_regional_price_modifiers(economic_state):
    # RPG-ECON-202: Regional price modifiers
    # Region 'village' has MATERIAL mod 1.5.
    # Default region (none) has 1.0.
    
    # 1. Price in Village
    price_village = MarketSystem.calculate_price(economic_state, economic_state.buildings[501], "iron_ore")
    assert price_village == int(5 * 1.5 * 1.2) # 9
    
    # 2. Price in Wild (No region)
    from dataclasses import replace
    wild_state = replace(economic_state, regions={})
    price_wild = MarketSystem.calculate_price(wild_state, wild_state.buildings[501], "iron_ore")
    assert price_wild == int(5 * 1.0 * 1.2) # 6
    assert price_village > price_wild

def test_scarcity_aware_ai(economic_state):
    # RPG-ECON-203: Strategic intelligence response to non-functional buildings
    from src.systems.strategic import StrategicIntelligenceSystem
    from src.core.strategic import ProjectState, ProjectStatus, ObjectiveState
    from src.core.updates import EntityUpdate
    
    # 1. Entity has an active shopping project for iron_ore
    obj = ObjectiveState(id="shopping_501", kind="reach_location", target="501", status="ACTIVE")
    project = ProjectState(id="p1", kind="shopping", status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    
    entity = economic_state.entities[1]
    entity = replace(entity, strategic=replace(entity.strategic, projects={"p1": project}, current_project_id="p1"))
    
    # 2. Shop is sabotaged (non-functional)
    shop = economic_state.buildings[501]
    shop = replace(shop, functional=False)
    economic_state = replace(economic_state, entities={1: entity}, buildings={501: shop})
    
    # 3. Run Strategic Intelligence
    economic_state = replace(economic_state, tick=9)
    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(economic_state, economic_state.entities[1])
    
    # 4. Verify project ABANDONED
    p_upd = next((p for p in strat_upd.projects_add_or_update if p.id == "p1"), None)
    assert p_upd is not None
    assert p_upd.status == ProjectStatus.ABANDONED
