import pytest
from src.core.builder import V2EntityBuilder
from src.core.strategic import BlockerState, BlockerKind
from src.core.models.inventory import ItemStack, EquipSlot
from src.world.providers.resources import ResourceOpportunityProvider
from src.world.providers.services import ServiceOpportunityProvider


from dataclasses import dataclass

@dataclass
class MockState:
    resource_nodes: dict


@pytest.fixture(autouse=False)
def minimal_service_registry():
    """Bootstrap ServiceRegistry with only a shop (buy affordance) at hometown and
    clear RecipeRegistry so craft opportunities do not crowd out buy_item in the top-5."""
    from src.core.registries import ServiceRegistry, ServiceDef, RecipeRegistry
    original_services = dict(ServiceRegistry._services)
    original_recipes = dict(RecipeRegistry._recipes)

    ServiceRegistry.bootstrap({
        "shop_hometown": ServiceDef("shop_hometown", "hometown", ("buy", "sell")),
    })
    RecipeRegistry.bootstrap({})

    yield

    ServiceRegistry.bootstrap(original_services)
    RecipeRegistry.bootstrap(original_recipes)

def test_resource_opportunities_basic():
    """Verify ResourceOpportunityProvider returns sorted, capped resource opportunities."""
    # Build entity in region near_forest where wood and herb are available
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "near_forest")

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="node_wood", position=(0.0, 0.0), yields_item="wood", remaining_charges=10, max_charges=10, required_ticks=5)
    node2 = ResourceNodeState(id=2, kind="node_herb", position=(0.0, 0.0), yields_item="herb", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1, 2: node2})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)
    
    # Verify we got some opportunities
    assert len(opportunities) > 0
    assert len(opportunities) <= 5
    
    # Verify sorted by estimated_reward descending
    for i in range(len(opportunities) - 1):
        assert opportunities[i].estimated_reward >= opportunities[i + 1].estimated_reward

    # Verify they carry requirements
    for opp in opportunities:
        assert opp.kind == "gather_resource"
        assert len(opp.requirements) >= 2
        # Requirements should include inventory_space and near_service
        req_kinds = [r.kind for r in opp.requirements]
        assert "inventory_space" in req_kinds
        assert "near_service" in req_kinds


def test_resource_opportunities_with_blocker():
    """Verify ResourceOpportunityProvider boosts reward for needed resources."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    # Place entity in old_mine where node_iron is located
    object.__setattr__(ent.navigation, "region_id", "old_mine")

    # Add active blocker for iron_ore
    blocker = BlockerState(id="bl_iron", kind=BlockerKind.MATERIAL, subject="iron_ore")
    object.__setattr__(ent.strategic, "blockers", {"bl_iron": blocker})

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="node_iron", position=(0.0, 0.0), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    # Find the iron_ore opportunity
    iron_opp = next((o for o in opportunities if o.subject == "iron_ore"), None)
    assert iron_opp is not None
    # Reward should be boosted to 50.0
    assert iron_opp.estimated_reward == 50.0


def test_service_opportunities_basic(minimal_service_registry):
    """Verify ServiceOpportunityProvider returns town service options."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "hometown")

    # Under baseline, rest/repair/ask_info won't yield high rewards unless fatigue or damage exists
    opportunities = ServiceOpportunityProvider.get_opportunities(ent, None)
    
    # We should have basic shop opportunity
    buy_opp = next((o for o in opportunities if o.kind == "buy_item"), None)
    assert buy_opp is not None
    assert buy_opp.subject == "small_potion"


def test_service_opportunities_rest_and_repair():
    """Verify ServiceOpportunityProvider handles rest and repair dynamically."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .biological(sleep_debt=45.0)  # Sleep debt > 40 triggers rest
        .equipment(durability={EquipSlot.MAIN_HAND: 30.0}) # Durability < 50 triggers repair
        .build())
    object.__setattr__(ent.navigation, "region_id", "hometown")

    opportunities = ServiceOpportunityProvider.get_opportunities(ent, None)

    # Rest opportunity should exist and have high reward equal to sleep_debt (45.0)
    rest_opp = next((o for o in opportunities if o.kind == "rest_inn"), None)
    assert rest_opp is not None
    assert rest_opp.estimated_reward == 45.0

    # Repair opportunity should exist
    repair_opp = next((o for o in opportunities if o.kind == "repair_gear"), None)
    assert repair_opp is not None
    assert repair_opp.estimated_reward == 80.0
