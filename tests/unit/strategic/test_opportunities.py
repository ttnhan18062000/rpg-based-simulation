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


def test_resource_opportunities_mountain_pass_zone_iron_vein():
    """TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP: a hero standing in
    hero_guild_routing's mountain_pass_zone region must now receive a gather_resource
    opportunity for iron_vein (source_region_tags additively gained "mountain_pass_zone" in
    data/content/world/resources.yaml, alongside the pre-existing "old_mine" legacy-fallback
    tag verified by test_resource_opportunities_old_mine_iron_vein). Supersedes the former
    test_resource_opportunities_mountain_pass_zone_tag_gap, which documented this as a zero-
    opportunity gap before the fix (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY Step 2 finding)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "mountain_pass_zone")

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="iron_vein", position=(0.0, 0.0), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "iron_ore" for opp in opportunities)


def test_resource_opportunities_mountain_pass_zone_frost_shard_cluster():
    """TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP: a hero standing in
    hero_guild_routing's mountain_pass_zone region must now receive a gather_resource
    opportunity for frost_shard_cluster (source_region_tags gained "mountain_pass_zone" in
    data/content/world/resources.yaml -- frost_shard_cluster previously carried no
    source_region_tags entry at all). Supersedes the former
    test_resource_opportunities_mountain_pass_zone_tag_gap, which documented this as a zero-
    opportunity gap before the fix (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY Step 2 finding)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "mountain_pass_zone")

    from src.core.state import ResourceNodeState
    node1 = ResourceNodeState(id=1, kind="frost_shard_cluster", position=(0.0, 0.0), yields_item="frost_shard", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node1})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "frost_shard" for opp in opportunities)


def test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes():
    """TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP Scope item 2: goblin_camp
    (goblin_camp_conflict module) and haunted_battlefield (ruins_mystery_quest module) place no
    resource nodes at all in hero_guild_routing -- confirmed via both modules' YAML (no
    `resources:` key in data/content/world_modules/goblin_camp_conflict.yaml or
    data/content/world_modules/ruins_mystery_quest.yaml) and the compiled
    data/worlds/hero_guild_routing/resolved/world.resolved.yaml (only wood_node/herb_patch in
    hometown and iron_vein/frost_shard_cluster in mountain_pass_zone are listed under
    `resources:`). There is therefore nothing to tag for these two regions -- no
    source_region_tags addition was made for either, and this test documents that finding rather
    than silently skipping it. A hero standing in either region with no resource nodes present in
    live state correctly receives zero gather_resource opportunities."""
    from src.core.state import ResourceNodeState

    for region_id in ("goblin_camp", "haunted_battlefield"):
        ent = (V2EntityBuilder(1)
            .kind("hero")
            .build())
        object.__setattr__(ent.navigation, "region_id", region_id)

        mock_state = MockState(resource_nodes={})

        opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

        assert opportunities == [], (
            f"{region_id}: expected zero gather_resource opportunities (no resource node is "
            f"physically placed in this region by its composing module), got {opportunities!r}"
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
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: a hero standing in
    orc_stronghold (placed by orc_clan_territory.yaml, composed by
    resource_dense_basin/frontier_marches/frontier_extended/frontier_living_world/
    generated_frontier_3_42/crowded_frontier) now receives gather_resource opportunities for
    both resource kinds that module places there (iron_vein, wood_node) -- both gained an
    "orc_stronghold" source_region_tags entry in data/content/world/resources.yaml. Supersedes
    the former version of this test (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS Step 7), which
    documented this as a zero-opportunity gap before the fix."""
    from src.core.state import ResourceNodeState

    for kind, item in (("iron_vein", "iron_ore"), ("wood_node", "wood")):
        ent = (V2EntityBuilder(1)
            .kind("hero")
            .build())
        object.__setattr__(ent.navigation, "region_id", "orc_stronghold")

        node = ResourceNodeState(id=1, kind=kind, position=(0.0, 0.0), yields_item=item, remaining_charges=10, max_charges=10, required_ticks=5)
        mock_state = MockState(resource_nodes={1: node})

        opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

        assert len(opportunities) > 0
        assert all(opp.kind == "gather_resource" for opp in opportunities)
        assert any(opp.subject == item for opp in opportunities)


def test_resource_opportunities_sacred_grove_healing_flower_patch():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: forest_warden_grove.yaml places
    healing_flower_patch nodes in sacred_grove. healing_flower_patch previously had no metadata
    block at all (falling through to the node_flower legacy_id heuristic, which only names
    near_forest); it now carries an explicit metadata.source_region_tags entry naming
    sacred_grove (and re-including near_forest so that prior coverage is preserved)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "sacred_grove")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="healing_flower_patch", position=(0.0, 0.0), yields_item="healing_flower", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "healing_flower" for opp in opportunities)


def test_resource_opportunities_sacred_grove_spirit_wisp():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: forest_warden_grove.yaml places
    spirit_wisp nodes in sacred_grove. spirit_wisp previously had no metadata block at all and
    resolved to zero source_region_tags; it now carries an explicit
    metadata.source_region_tags entry naming sacred_grove (mirroring its own
    preferred_biomes, which already named this region)."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "sacred_grove")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="spirit_wisp", position=(0.0, 0.0), yields_item="spirit_essence", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "spirit_essence" for opp in opportunities)


def test_resource_opportunities_swamp_border_territory_wood_node():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: sunken_swamp_border.yaml places
    wood_node nodes in swamp_border_territory. wood_node's source_region_tags gained an
    additive "swamp_border_territory" entry in data/content/world/resources.yaml."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "swamp_border_territory")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="wood_node", position=(0.0, 0.0), yields_item="wood", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "wood" for opp in opportunities)


def test_resource_opportunities_swamp_border_territory_herb_patch():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: sunken_swamp_border.yaml places
    herb_patch nodes in swamp_border_territory. herb_patch's source_region_tags gained an
    additive "swamp_border_territory" entry in data/content/world/resources.yaml."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "swamp_border_territory")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="herb_patch", position=(0.0, 0.0), yields_item="herb", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "herb" for opp in opportunities)


def test_resource_opportunities_haunted_battlefield_spirit_wisp():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: undead_battlefield.yaml places
    spirit_wisp nodes in haunted_battlefield, in worlds composing that module
    (frontier_extended, wilderness_survival). spirit_wisp's source_region_tags gained an
    additive "haunted_battlefield" entry. This only applies where a node is actually placed --
    worlds using only ruins_mystery_quest (dungeon_crawl, hero_guild_routing,
    frontier_marches) place no node in haunted_battlefield at all, and
    test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes (which
    tests that "no live node in mock state" case) remains valid and unmodified alongside this
    new test -- they exercise different mock-state shapes for the same region, not
    contradictory outcomes."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "haunted_battlefield")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="spirit_wisp", position=(0.0, 0.0), yields_item="spirit_essence", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "spirit_essence" for opp in opportunities)


def test_resource_opportunities_trading_hometown_iron_vein():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: trading_company_hub.yaml's
    resource_recipes places an iron_vein node in region "hometown", which
    src/worldassembly/resolver.py:335's namespace-prefixing remaps to "trading_hometown" for
    any world composing it under the "trading" namespace (e.g. urban_political). This is a
    distinct region id from plain "hometown" (already closed by
    TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP) -- iron_vein's source_region_tags
    gained an additive "trading_hometown" entry, independent of that prior fix."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "trading_hometown")

    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="iron_vein", position=(0.0, 0.0), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=5)
    mock_state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

    assert len(opportunities) > 0
    assert all(opp.kind == "gather_resource" for opp in opportunities)
    assert any(opp.subject == "iron_ore" for opp in opportunities)


def test_resource_opportunities_bandit_road_and_wolf_den_no_resource_nodes():
    """TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT: bandit_road and wolf_den carry
    zero resource-node content corpus-wide (neither scalable_bandit_camp.yaml nor
    bandit_road_trade_pressure.yaml declares any resources for bandit_road; wolf_den_near_forest.yaml
    declares resources but its first-declared region is near_forest, so the compiler places all of
    that module's nodes there, not in wolf_den). This is an intentional hazard-zone gap, decided by
    human review 2026-07-08 -- not an authoring oversight (see
    docs/guidelines/intentional_divergences.md #2.29). No source_region_tags addition was made for
    either region; a hero standing in either region correctly receives zero gather_resource
    opportunities regardless of resource kind. Mirrors
    test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes's existing
    pattern for goblin_camp (already covered there)."""
    from src.core.state import ResourceNodeState

    for region_id in ("bandit_road", "wolf_den"):
        ent = (V2EntityBuilder(1)
            .kind("hero")
            .build())
        object.__setattr__(ent.navigation, "region_id", region_id)

        mock_state = MockState(resource_nodes={})

        opportunities = ResourceOpportunityProvider.get_opportunities(ent, mock_state)

        assert opportunities == [], (
            f"{region_id}: expected zero gather_resource opportunities (intentional hazard-zone "
            f"gap, no resource node placed corpus-wide), got {opportunities!r}"
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
