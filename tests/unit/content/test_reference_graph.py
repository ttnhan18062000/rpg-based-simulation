"""Tests for ContentReferenceGraph.add_module_edges and normalized module edge building."""
import pytest
from src.content.reference_graph import ContentReferenceGraph
from src.worldmodules.normalizer import NormalizedWorldModule


def _make_normalized_module(**kwargs) -> NormalizedWorldModule:
    """Build a minimal NormalizedWorldModule for testing."""
    defaults = dict(
        module_id="test_module",
        module_type="terrain",
        display_name="Test Module",
        description=None,
        version="1.0.0",
        requires=[],
        provides=[],
        parameters=[],
        regions=[],
        population_recipes=[],
        resource_recipes=[],
        building_recipes=[],
        biome_refs=(),
        ecology_refs=(),
        population_refs=(),
        relationship_refs=(),
        resources={},
        buildings={},
        services={},
        factions=[],
        quest_definitions=[],
    )
    defaults.update(kwargs)
    return NormalizedWorldModule(**defaults)


def _make_empty_graph() -> ContentReferenceGraph:
    """Build a ContentReferenceGraph struct without running _build_graph."""
    graph = ContentReferenceGraph.__new__(ContentReferenceGraph)
    graph.nodes = {}
    graph.edges = set()
    graph.adj = {}
    graph.reverse_adj = {}
    graph.edge_metadata = {}
    return graph


def test_add_module_edges_adds_biome_edges():
    """add_module_edges creates module→biome edges for each biome ID."""
    graph = _make_empty_graph()
    normalized = _make_normalized_module(
        module_id="mod_biome",
        biome_refs=("forest", "plains"),
    )
    graph.add_module_edges(normalized)
    assert ("module:mod_biome", "biome:forest") in graph.edges
    assert ("module:mod_biome", "biome:plains") in graph.edges


def test_add_module_edges_adds_ecology_population_relationship_edges():
    """add_module_edges creates edges for ecologies, populations, and relationships."""
    graph = _make_empty_graph()
    normalized = _make_normalized_module(
        module_id="mod_multi",
        ecology_refs=("temperate",),
        population_refs=("human_village",),
        relationship_refs=("allies",),
    )
    graph.add_module_edges(normalized)
    assert ("module:mod_multi", "ecology:temperate") in graph.edges
    assert ("module:mod_multi", "population:human_village") in graph.edges
    assert ("module:mod_multi", "faction_relationship:allies") in graph.edges


def test_add_module_edges_uses_normalized_ids_not_raw_dicts():
    """add_module_edges only reads string IDs from Tuple[str, ...] fields — no dict parsing.
    Count metadata is preserved on resource/building/service edges."""
    graph = _make_empty_graph()
    # Normalized module always contains string tuples after normalization
    normalized = _make_normalized_module(
        module_id="mod_ids_only",
        biome_refs=("biome_a", "biome_b"),
        resources={"wood_node": 3},
        buildings={"shop": 1},
        services={"healing": 2},
    )
    graph.add_module_edges(normalized)
    # Edges use string IDs directly
    assert ("module:mod_ids_only", "biome:biome_a") in graph.edges
    assert ("module:mod_ids_only", "biome:biome_b") in graph.edges
    assert ("module:mod_ids_only", "resource:wood_node") in graph.edges
    assert ("module:mod_ids_only", "building:shop") in graph.edges
    assert ("module:mod_ids_only", "service:healing") in graph.edges
    # Count metadata is preserved
    assert graph.edge_metadata.get(("module:mod_ids_only", "resource:wood_node")) == {"count": 3}
    assert graph.edge_metadata.get(("module:mod_ids_only", "building:shop")) == {"count": 1}
    assert graph.edge_metadata.get(("module:mod_ids_only", "service:healing")) == {"count": 2}
    # No raw dict edges should appear
    for edge in graph.edges:
        assert not edge[1].startswith("biome:{"), f"Raw dict appeared as edge target: {edge}"


def test_graph_build_uses_add_module_edges():
    """When ContentReferenceGraph is built with modules, biome/ecology edges appear in the graph."""
    from src.content.repository import CatalogRepository
    from src.worldmodules.schema import WorldModuleSpec

    # Build a minimal repo (no real content needed, just an empty one)
    repo = CatalogRepository.__new__(CatalogRepository)
    # Initialize all repository index attributes to empty dicts
    from src.content.repository import CANONICAL_FAMILIES
    for spec in CANONICAL_FAMILIES:
        setattr(repo, spec.repository_index, {})

    module_spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="graph_test_module",
        module_type="terrain",
        display_name="Graph Test Module",
        biomes=["meadow_biome"],
        ecologies=["grassland_ecology"],
        populations=["settler_pop"],
        relationships=["treaty_rel"],
    )

    graph = ContentReferenceGraph(repo, modules=[module_spec])

    assert ("module:graph_test_module", "biome:meadow_biome") in graph.edges
    assert ("module:graph_test_module", "ecology:grassland_ecology") in graph.edges
    assert ("module:graph_test_module", "population:settler_pop") in graph.edges
    assert ("module:graph_test_module", "faction_relationship:treaty_rel") in graph.edges
