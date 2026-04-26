# tests/parity/test_economy_scarcity.py
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState, BuildingState, ResourceNodeState
from src.core.enums import EntityRole, Faction
from src.core.builder import V2EntityBuilder
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from tests.parity.test_parity_rpg_recovery import create_test_profile

@pytest.mark.v2_contract
def test_dynamic_pricing():
    """Verifies that regional trauma increases shop prices."""
    # Hero with 1 wood
    hero = (V2EntityBuilder(1).at((10, 10))
            .role(EntityRole.HERO)
            .with_inventory(items=["wood"])
            .build())
    
    # Shop at (10, 10)
    shop = BuildingState(id=1, kind="shop", position=(10, 10))
    region = RegionState(id="wilds", name="Wilds", bounds=(0,0,100,100), trauma_score=0.0)
    
    state = AuthoritativeState(
        tick=1, seed=42, 
        entities={1: hero}, 
        buildings={1: shop}, 
        building_tiles={(10, 10): "shop"},
        regions={"wilds": region}
    )
    
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    
    # Case 1: Baseline price (trauma=0)
    kernel_a = Kernel(profile, state, rng)
    kernel_a.tick_once()
    assert kernel_a.state.entities[1].inventory.gold == 5
    assert not any(item.item_id == "wood" for item in kernel_a.state.entities[1].inventory.items)
    
    # Case 2: Scarcity price (trauma=10)
    region_b = replace(region, trauma_score=10.0)
    state_b = replace(state, regions={"wilds": region_b})
    kernel_b = Kernel(profile, state_b, rng)
    kernel_b.tick_once()
    # Price = 5 * (1 + 10/10) = 10
    assert kernel_b.state.entities[1].inventory.gold == 10

@pytest.mark.v2_contract
def test_resource_depletion():
    """Verifies that harvesting consumes charges and triggers cooldown."""
    # Hero at node
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).build())
    # Node with 1 charge left
    node = ResourceNodeState(
        id=1, kind="TREE", position=(5, 5), 
        yields_item="WOOD", remaining_charges=1, 
        max_charges=5, required_ticks=1, respawn_cooldown=100
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero}, resource_nodes={1: node})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Hero reaches readiness at tick 11
    for _ in range(11): kernel.tick_once()
    
    # Tick 12: Hero starts harvesting (INTERACT)
    # Note: V2 hero auto-interacts if idle at node? No, worker proposes it.
    # We'll just run it.
    kernel.tick_once()
    
    # Verify node is depleted
    n1 = kernel.state.resource_nodes[1]
    assert n1.remaining_charges == 0
    assert n1.cooldown_remaining == 100
    # Verify hero got wood
    h1 = kernel.state.entities[1]
    assert any(item.item_id == "WOOD" for item in h1.inventory.items)
