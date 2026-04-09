import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from src.core.entities.entity import Vector2
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.life_events import ReputationProfile
from src.core.models.enums import Faction as FactionEnum, AIState, ActionType, Material
from src.core.gameplay.buildings import item_sell_price, shop_buy_price
from src.actions.rest import RestAction
from src.core.logic.knowledge_propagation import KnowledgePropagationService
from src.ai.states.interaction import find_nearby_resource
from src.ai.states.navigation import propose_retreat_home
from src.ai.states.base import AIContext
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

class MockGrid:
    def __init__(self):
        self.width = 100
        self.height = 100
    def is_walkable(self, pos): return True
    def is_town(self, pos): return False
    def is_camp(self, pos): return False
    def get_region_id_at(self, x, y): return "test_region"
    def get(self, pos): return Material.GRASSLAND # Fixed for pathfinding tile_cost

class MockSnapshot:
    def __init__(self, entities=None, grid=None, resource_nodes=None, tick=1):
        self.entities = entities or {}
        self.grid = grid or MockGrid()
        self.resource_nodes = resource_nodes or []
        self.tick = tick
        self.camps = []
        self.regions = []
        self.ground_items = {}

    def nearby_entity_ids(self, x, y, radius):
        return []

    def nearby_ground_positions(self, x, y, radius):
        return []

class MockWorld:
    def __init__(self, tick=1):
        self.tick = tick
        self.entities = {}
        self.seed = 42

def test_pricing_reputation_scaling():
    # Heroism should increase sell price (bonus for heroes)
    # Trustworthiness should decrease buy price (friend discount)
    
    # 1. Sell Price (Entity selling to shop)
    from src.core.gameplay.items.item_registry import ITEM_REGISTRY, ItemTemplate
    from src.core.models.enums import Rarity, ItemType
    
    # Ensure item exists in registry for test
    ITEM_REGISTRY["test_repro_item"] = ItemTemplate(
        item_id="test_repro_item", name="Test Item", 
        item_type=ItemType.MATERIAL, rarity=Rarity.COMMON, sell_value=100
    )
    
    rep_neutral = ReputationProfile(heroism_score=0, trustworthiness=0)
    rep_hero = ReputationProfile(heroism_score=10, trustworthiness=0)
    
    price_neutral = item_sell_price("test_repro_item", rep_neutral)
    price_hero = item_sell_price("test_repro_item", rep_hero)
    
    assert price_hero > price_neutral, f"Hero should get better sell prices: {price_hero} vs {price_neutral}"
    
    # 2. Buy Price (Shop selling to entity)
    # small_hp_potion is 15 gold in SHOP_INVENTORY
    rep_trusted = ReputationProfile(heroism_score=0, trustworthiness=10)
    price_trusted = shop_buy_price("small_hp_potion", rep_trusted)
    price_untrusted = shop_buy_price("small_hp_potion", rep_neutral)
    
    assert price_trusted < price_untrusted, "Trusted entities should get better buy prices"

def test_rest_to_sleep_transition():
    rng = DeterministicRNG(42)
    
    # Case 1: Low stamina (< 20%) while resting at home -> Fall asleep
    actor = EntityBuilder(rng, 1).kind("hero").at(Vector2(10, 10)).build()
    actor.spatial.home_pos = Vector2(10, 10)
    actor.progression.stamina = 5 # 10%
    actor.mind.decision.ai_state = AIState.VISIT_HOME
    
    world = MockWorld(tick=1)
    world.entities = {1: actor}
    
    # Mock proposal
    from src.actions.base import ActionProposal
    proposal = ActionProposal(actor_id=1, verb=ActionType.REST)
    
    RestAction.apply(proposal, world)
    
    # Verify AIState transition via proposal attributes
    assert proposal.new_ai_state == AIState.SLEEPING, "Should fall asleep when stamina is low and at home"
    
    # Verify RoutineUpdate
    from src.actions.base import RoutineUpdate
    has_sleep_update = any(isinstance(u, RoutineUpdate) and u.is_sleeping for u in proposal.updates)
    assert has_sleep_update, "Should emit RoutineUpdate specifically marking sleeping start"

def test_gossip_distance_bounds():
    rng = DeterministicRNG(42)
    world = MockWorld(tick=1)
    
    sharer = EntityBuilder(rng, 1).kind("hero").at(Vector2(0, 0)).build()
    recipient = EntityBuilder(rng, 2).kind("hero").at(Vector2(1, 1)).build()
    
    # Target 1: Nearby (10 units)
    # Target 2: Far (100 units)
    
    # Mock memory
    from src.ai.beliefs import BeliefRecord
    from src.core.aspects.mind import ThreatEstimate
    sharer.mind.perception.entity_memory[3] = BeliefRecord(
        entity_id=3, pos=Vector2(5, 5), last_seen_tick=1, confidence=1.0, directness=1.0,
        threat=ThreatEstimate(overall=0.5)
    )
    sharer.mind.perception.entity_memory[4] = BeliefRecord(
        entity_id=4, pos=Vector2(100, 100), last_seen_tick=1, confidence=1.0, directness=1.0,
        threat=ThreatEstimate(overall=0.9)
    )
    
    update = KnowledgePropagationService.propagate_gossip(sharer, recipient, world)
    
    assert update is not None
    assert 3 in update.entity_memory, "Nearby target should be shared"
    assert 4 not in update.entity_memory, "Far target should NOT be shared (unless famous)"

def test_subjective_gathering_vision():
    rng = DeterministicRNG(42)
    actor = EntityBuilder(rng, 1).kind("hero").at(Vector2(0, 0)).build()
    actor.spatial.vision_range = 5
    
    from src.core.world.resource_nodes import ResourceNode
    
    # node_near pos is (2,2) -> manhattan distance is 4 (within vision 5)
    node_near = ResourceNode(
        node_id=1, name="Tree", resource_type="wood",
        pos=Vector2(2, 2), terrain=Material.FOREST, yields_item="wood"
    )
    
    # node_far pos is (10,10) -> manhattan distance is 20 (outside vision 5)
    node_far = ResourceNode(
        node_id=2, name="Rock", resource_type="ore",
        pos=Vector2(10, 10), terrain=Material.MOUNTAIN, yields_item="iron_ore"
    )
    
    snapshot = MockSnapshot(resource_nodes=[node_near, node_far])
    
    # Search radius 20, but vision is 5
    res = find_nearby_resource(actor, snapshot, radius=20)
    
    assert res is not None
    assert res.node_id == 1, "Should find nearby node"
    assert res.node_id != 2, "Should NOT find node outside vision even with large search radius"

def test_home_priority_retreat():
    rng = DeterministicRNG(42)
    # Actor at (50,50), Camp at (40,40), Home at (60,60)
    # Moving towards Camp(40,40) goes to (49,50)
    # Moving towards Home(60,60) goes to (51,50)
    actor = EntityBuilder(rng, 1).kind("monster").faction(FactionEnum.WOLF_PACK).at(Vector2(50, 50)).build()
    actor.spatial.home_pos = Vector2(60, 60)
    
    # Mock world with a closer camp
    snapshot = MockSnapshot()
    # nearest_camp expects list of (int, int) tuples!
    snapshot.camps = [(40, 40)]
    
    ctx = AIContext(
        actor=actor, snapshot=snapshot, config=SimulationConfig(), 
        rng=rng, faction_reg=None
    )
    
    state, proposal = propose_retreat_home(ctx, "Test retreat")
    
    assert state == AIState.RETURN_TO_CAMP
    # (51, 50) is one step towards (60, 60)
    assert proposal.target == Vector2(51, 50), f"Should move toward home_pos(60,60), got {proposal.target}"
