from __future__ import annotations
from dataclasses import replace
import pytest
from src.core.state import AuthoritativeState, EntityState, ItemStack, ResourceNodeState, RegionState, IdentityComponent, InventoryComponent, CombatComponent, BuildingState, ChestState, InteractionComponent
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, InventoryUpdate, RewardUpdate, InteractionUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.domain_logic import SimulationDomainLogic

@pytest.fixture
def base_state():
    return AuthoritativeState(
        tick=10, seed=123,
        entities={
            1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0, active=True, 
                           identity=IdentityComponent(role=0, faction=0, known_recipes={"craft_steel_sword"}),
                           combat=CombatComponent(hp=100, max_hp=100, range=2, alive=True)), # Increased range
            2: EntityState(id=2, kind="monster", position=(1,1), readiness=100.0, active=True,
                           identity=IdentityComponent(role=2, faction=1), # Role.MONSTER
                           combat=CombatComponent(hp=1, max_hp=100, alive=True))
        },
        resource_nodes={
            101: ResourceNodeState(id=101, kind="MINE", yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5, position=(0,0))
        },
        buildings={
            1: BuildingState(id=1, kind="shop", position=(0,0), functional=True),
            2: BuildingState(id=2, kind="blacksmith", position=(0,0), functional=True)
        },
        terrain={},
        blocked_tiles=set(),
        town_tiles={(0,0), (1,1)},
        building_tiles={}
    )

def test_town_tax_refactor(base_state):
    """Verify that TownResolutionSystem uses ResourceTransferIntent for taxes."""
    region = RegionState(id="r1", name="Test Town", bounds=(0,0,10,10), owner_faction_id=1)
    state = replace(base_state, regions={"r1": region}, buildings={}) # Remove buildings to isolate entity tax
    
    # Hero has 100 gold
    hero = state.entities[1]
    state.entities[1] = replace(hero, inventory=replace(hero.inventory, gold=100))
    
    # Proposed update (empty)
    update = StateUpdate()
    
    # Refine
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    ent_upd = refined.entity_updates.get(1)
    assert ent_upd is not None
    # Tax is 2.0 (from town_resolution.py)
    assert ent_upd.inventory.gold_delta == -2.0
    
    # Check if faction gold was updated
    assert refined.resource_updates.get("faction_1_gold") == 2.0

def test_shop_sell_refactor(base_state):
    """Verify that ShopSystem uses ResourceTransferIntent."""
    hero = base_state.entities[1]
    # Hero has an item to sell
    item = ItemStack(item_id="iron_ore", quantity=1)
    base_state.entities[1] = replace(hero, 
        inventory=replace(hero.inventory, items=[item]),
        position=(0,0)
    )
    # Ensure building_tiles is "shop" and buildings exists
    base_state = replace(base_state, building_tiles={(0,0): "shop"})
    
    # ShopSystem reacts to inventory state
    update = StateUpdate()
    
    refined = AuthoritativeApplyPipeline.refine(base_state, update)
    
    ent_upd = refined.entity_updates.get(1)
    # iron_ore sell price is 10
    assert ent_upd.inventory.gold_delta == 10
    assert any(i.item_id == "iron_ore" for i in ent_upd.inventory.items_remove)

def test_blacksmith_craft_refactor(base_state):
    """Verify that BlacksmithSystem uses ResourceTransferIntent."""
    hero = base_state.entities[1]
    # Hero has materials for craft_steel_sword: 2 iron_ore, 1 wood, 60 gold
    mats = [ItemStack(item_id="iron_ore", quantity=2), ItemStack(item_id="wood", quantity=1)]
    base_state.entities[1] = replace(hero, 
        inventory=replace(hero.inventory, items=mats, gold=100),
        identity=replace(hero.identity, craft_target="craft_steel_sword", known_recipes={"craft_steel_sword"}),
        position=(0,0)
    )
    # Ensure building_tiles is "blacksmith"
    base_state = replace(base_state, building_tiles={(0,0): "blacksmith"})
    
    # BlacksmithSystem looks for craft_target in entity.identity
    update = StateUpdate()
    
    refined = AuthoritativeApplyPipeline.refine(base_state, update)
    
    ent_upd = refined.entity_updates.get(1)
    assert ent_upd is not None
    # craft_steel_sword cost 60
    assert ent_upd.inventory.gold_delta == -60
    assert any(i.item_id == "steel_sword" for i in ent_upd.inventory.items_add)
    # craft_target should be reset
    assert ent_upd.identity.craft_target == ""

def test_reward_update_hardening():
    """Verify that RewardUpdate no longer accepts gold_gain or items_gain."""
    reward = RewardUpdate(xp_gain=100)
    assert not hasattr(reward, "gold_gain")
    assert not hasattr(reward, "items_gain")

def test_combat_reward_via_intent(base_state):
    """Verify that combat rewards flow through ResourceTransferIntent."""
    from src.engine.domain_logic import SimulationDomainLogic
    attacker = base_state.entities[1] # range=2
    target = base_state.entities[2] # 1 HP monster
    
    # Mock context for attack
    class MockContext:
        def __init__(self, entities):
            self.entities = entities
            self.tick = 0
            self.terrain = {}
            self.regions = {}
            self.blocked_tiles = set()
            self.buildings = {}
    context = MockContext(base_state.entities)
    
    # Execute attack action
    updates = SimulationDomainLogic.execute_action(
        attacker, 
        payload={"action": "ATTACK", "target_id": target.id},
        context=context
    )
    
    attacker_up = updates[attacker.id]
    assert attacker_up.reward is None
    intent = attacker_up.resource_transfers[0]
    assert intent.source_kind == "COMBAT"
    assert intent.xp_reward == 10 # Monster level 1
    assert intent.xp_reward > 0
    assert intent.gold_delta >= 0

def test_recruitment_gold_handoff(base_state):
    """Verify that recruitment gold transfer uses ResourceTransferIntent."""
    from src.engine.domain_logic import SimulationDomainLogic
    recruiter = base_state.entities[1]
    recruit = base_state.entities[2]
    
    # recruiter has 1000 gold
    base_state.entities[1] = replace(recruiter, inventory=replace(recruiter.inventory, gold=1000))
    
    # recruiter offers 500 gold (should succeed)
    updates = SimulationDomainLogic.execute_action(
        base_state.entities[1],
        payload={"action": "RECRUIT", "target_id": recruit.id, "payout": 500},
        neighbor_view=[(recruit.id, recruit)],
        current_tick=0
    )
    
    # Both should have ResourceTransferIntent in the same group
    assert recruiter.id in updates, "Recruiter update missing"
    assert recruit.id in updates, "Recruit update missing"
    
    up1 = updates[recruiter.id]
    up2 = updates[recruit.id]
    
    assert up1.resource_transfers[0].gold_delta == -500
    assert up2.resource_transfers[0].gold_delta == 500

def test_class_hall_train_refactor():
    # Setup state
    hero = EntityState(id=1, kind="HERO", position=(1, 1), readiness=100.0)
    hero = replace(hero, 
        inventory=replace(hero.inventory, gold=100),
        identity=replace(hero.identity, known_recipes=set())
    )
    state = AuthoritativeState(entities={1: hero}, tick=0, seed=123)
    
    # Propose TRAIN action
    payload = {"action": "TRAIN", "skill_id": "STRIKE"}
    update_dict = SimulationDomainLogic.execute_action(hero, payload=payload)
    raw_update = StateUpdate(entity_updates=update_dict)
    
    # Refine through pipeline
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify: Intent generated and resolved
    ent_upd = refined.entity_updates[1]
    assert ent_upd.inventory.gold_delta == -50
    # Apply refined update manually to verify state transition
    from src.engine.apply import ApplyPath
    next_state = ApplyPath.apply_generation(state, refined)
    
    assert next_state.entities[1].inventory.gold == 50 # 100 - 50
    assert "STRIKE" in next_state.entities[1].identity.known_recipes

def test_chest_looting_and_cooldown():
    # Setup state
    hero = EntityState(id=1, kind="HERO", position=(1, 1))
    hero = replace(hero, interaction=InteractionComponent(target_node_id=10, progress=9.0))
    
    chest = ChestState(id=10, position=(1, 1), items=[ItemStack("iron_ore", 1)], respawn_tick=50)
    state = AuthoritativeState(entities={1: hero}, chests={10: chest}, tick=0, seed=123)
    
    # Propose progress
    raw_update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))})
    
    # Refine
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    # Verify: ChestUpdate created and intent created
    assert 10 in refined.chest_updates
    assert refined.chest_updates[10].cooldown_set == 50
    assert refined.chest_updates[10].items_set == []
    
    # Apply
    from src.engine.apply import ApplyPath
    next_state = ApplyPath.apply_generation(state, refined)
    
    assert next_state.entities[1].inventory.items[0].item_id == "iron_ore"
    assert next_state.chests[10].cooldown_remaining == 50
    assert next_state.chests[10].items == []
    
    # Verify Cooldown reduction in WorldDynamics
    # We need to refine again but with a dummy update to trigger Dynamics
    dummy_upd = StateUpdate()
    refined_dyn = AuthoritativeApplyPipeline.refine(next_state, dummy_upd)
    assert refined_dyn.chest_updates[10].cooldown_set == 49

def test_node_recharge_dynamics():
    # Setup state: node on its last tick of cooldown
    node = ResourceNodeState(id=20, kind="ORE", position=(2,2), yields_item="ORE", remaining_charges=0, max_charges=5, required_ticks=5, cooldown_remaining=1)
    state = AuthoritativeState(resource_nodes={20: node}, tick=0, seed=123)
    
    # Refine dummy update
    dummy_upd = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, dummy_upd)
    
    # Verify: Node recharged
    assert 20 in refined.node_updates
    assert refined.node_updates[20].cooldown_set == 0
    assert refined.node_updates[20].charges_delta == 5
    
    # Apply
    from src.engine.apply import ApplyPath
    next_state = ApplyPath.apply_generation(state, refined)
    assert next_state.resource_nodes[20].remaining_charges == 5
    assert next_state.resource_nodes[20].cooldown_remaining == 0
