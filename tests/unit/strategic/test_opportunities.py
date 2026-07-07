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


def test_resource_opportunities_hometown_wood_node():
    """TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP: a hero standing in hometown must
    now receive a gather_resource opportunity for wood_node (source_region_tags additively
    gained "hometown" in data/content/world/resources.yaml)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "hometown")

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="wood_node", position=(0.0, 0.0), yields_item="wood", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "wood" for opp in opportunities)


def test_resource_opportunities_hometown_herb_patch():
    """TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP: a hero standing in hometown must
    now receive a gather_resource opportunity for herb_patch (source_region_tags additively
    gained "hometown" in data/content/world/resources.yaml)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "hometown")

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="herb_patch", position=(0.0, 0.0), yields_item="herb", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "herb" for opp in opportunities)


def test_resource_opportunities_mountain_pass_zone_tag_gap():
    """TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY Step 2 finding: a hero standing in
    hero_guild_routing's mountain_pass_zone region gets zero gather_resource opportunities for
    either resource kind the mountain_pass module places there (iron_vein, frost_shard_cluster) --
    neither carries a "mountain_pass_zone" (or any) source_region_tags entry in
    data/content/world/resources.yaml. Same class of registry-omission gap
    TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP fixed for hometown/wood_node/herb_patch;
    found here but deliberately left unfixed (out of this ticket's scope) and flagged as a
    follow-up content-fix recommendation in docs/simulation_quality/eval_matrix_results.md instead.
    If this assertion starts failing, the tag gap has been closed and this test should be
    rewritten to assert coverage."""
    from src.core.state import ResourceNodeState

    for kind, item in (("iron_vein", "iron_ore"), ("frost_shard_cluster", "frost_shard")):
        ent = (V2EntityBuilder(1)
            .kind("hero")
            .build())
        object.__setattr__(ent.navigation, "region_id", "mountain_pass_zone")

        node = ResourceNodeState(id=1, kind=kind, position=(0.0, 0.0), yields_item=item, remaining_charges=10, max_charges=10, required_ticks=5)
        mock_state = MockState(resource_nodes={1: node})

        opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

        assert opportunities == [], (
            f"mountain_pass_zone/{kind}: expected zero gather_resource opportunities "
            f"(no source_region_tags coverage), got {opportunities!r}"
        )


def test_resource_opportunities_old_mine_iron_vein():
    """TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS Step 7: resource_dense_basin composes
    old_mine_resource_loop, whose old_mine region places iron_vein nodes. iron_vein has no
    explicit source_region_tags metadata in data/content/world/resources.yaml, but
    CatalogToResourceRegistryAdapter's legacy_id fallback (src/core/registries.py:435-436)
    infers source_region_tags=("old_mine",) for it — confirming a hero standing in old_mine
    does get a real gather_resource opportunity, unlike the orc_stronghold gap below."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "old_mine")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="iron_vein", position=(0.0, 0.0), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert any(opp.subject == "iron_ore" for opp in opportunities)


def test_resource_opportunities_orc_stronghold_tag_gap():
    """TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS Step 7 finding: a hero standing in
    resource_dense_basin's/frontier_marches's orc_stronghold region (from orc_clan_territory)
    gets zero gather_resource opportunities for either resource kind that module places there
    (iron_vein, wood_node) -- neither carries an "orc_stronghold" source_region_tags entry in
    data/content/world/resources.yaml (wood_node's explicit tags are ["near_forest", "hometown"];
    iron_vein's legacy_id-fallback tags are only ("old_mine",)). Same class of pre-existing
    registry-omission gap as test_resource_opportunities_mountain_pass_zone_tag_gap
    (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY) -- found here, deliberately left unfixed (out
    of this ticket's scope, and pre-dates it: orc_clan_territory is already composed by
    frontier_extended/frontier_living_world/generated_frontier_3_42), and flagged as a follow-up
    content-fix recommendation in docs/simulation_quality/eval_matrix_results.md instead. If this
    assertion starts failing, the tag gap has been closed and this test should be rewritten to
    assert coverage."""
    from src.core.state import ResourceNodeState

    for kind, item in (("iron_vein", "iron_ore"), ("wood_node", "wood")):
        ent = (V2EntityBuilder(1)
            .kind("hero")
            .build())
        object.__setattr__(ent.navigation, "region_id", "orc_stronghold")

        node = ResourceNodeState(id=1, kind=kind, position=(0.0, 0.0), yields_item=item, remaining_charges=10, max_charges=10, required_ticks=5)
        mock_state = MockState(resource_nodes={1: node})

        opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

        assert opportunities == [], (
            f"orc_stronghold/{kind}: expected zero gather_resource opportunities "
            f"(no source_region_tags coverage), got {opportunities!r}"
        )


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
