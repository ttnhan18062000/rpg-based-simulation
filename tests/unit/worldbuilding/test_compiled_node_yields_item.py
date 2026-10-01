"""Compiled resource nodes must yield a registered ITEM id, not the module's resource KIND.

`resource_type` in module authoring names a resource kind (`herb_patch`); the node must yield the
catalog item (`herb`). Regression for the collision that made herb harvesting silently never
complete (ItemRegistry.get miss -> can_add_items False -> interaction reset every tick).
"""
from pathlib import Path

import pytest

from src.core.items import ItemRegistry
from src.core.registries import ResourceRegistry
from src.worldassembly.context import CompileContext
from src.worldassembly.models import ResolvedResourceProfile
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.schema import WorldSpec

WORLDS_DIR = Path("data/worlds")
CORPUS_WORLDS = sorted(p.name for p in WORLDS_DIR.iterdir() if (p / "world.yaml").exists() or (p / "world.json").exists())

EXPECTED_ITEM_BY_KIND = {"herb_patch": "herb", "wood_node": "wood", "iron_vein": "iron_ore"}


def _spec(resource_type: str) -> WorldSpec:
    return WorldSpec.model_validate({
        "schema_version": "worldspec.v1",
        "world_id": "yield_item_probe",
        "name": "Yield Item Probe",
        "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
        "regions": [{"id": "wilds", "type": "wilderness", "bounds": [0, 0, 40, 40], "terrain": "FOREST"}],
        "factions": [{"id": "villagers", "type": "civilian"}],
        "entities": [{"id": "g", "count": 1, "role": "citizen", "faction": "villagers", "spawn_region": "wilds"}],
        "resources": [{"id": "node_a", "resource_type": resource_type, "count": 3, "region": "wilds"}],
        "buildings": [],
    })


@pytest.mark.parametrize("kind,item", sorted(EXPECTED_ITEM_BY_KIND.items()))
def test_context_resolved_yield_item_is_the_catalog_item(kind, item):
    ctx = CompileContext()
    ctx.register_resource("node_a", ResolvedResourceProfile(required_ticks=8, resource_type=kind, yield_item=item))
    state, _ = WorldCompiler.compile(_spec(kind), seed=1, context=ctx)
    (node,) = state.resource_nodes.values()
    assert node.kind == kind
    assert node.yields_item == item


@pytest.mark.parametrize("kind,item", sorted(EXPECTED_ITEM_BY_KIND.items()))
def test_no_context_falls_back_to_resource_registry(kind, item):
    state, _ = WorldCompiler.compile(_spec(kind), seed=1)
    (node,) = state.resource_nodes.values()
    assert node.kind == kind
    assert node.yields_item == ResourceRegistry.get(kind).yield_item == item


def test_unknown_kind_keeps_declared_string():
    state, _ = WorldCompiler.compile(_spec("not_a_catalog_kind"), seed=1)
    (node,) = state.resource_nodes.values()
    assert node.yields_item == "not_a_catalog_kind"


@pytest.mark.parametrize("world_id", CORPUS_WORLDS)
def test_every_corpus_node_yields_a_registered_item(world_id):
    spec, context = WorldRepository(str(WORLDS_DIR)).load_world_with_context(world_id)
    state, _ = WorldCompiler.compile(spec, seed=42, context=context)
    bad = {n.kind: n.yields_item for n in state.resource_nodes.values()
           if ItemRegistry.get(n.yields_item) is None}
    assert not bad, f"{world_id}: nodes yield unregistered item ids {bad}"
    for n in state.resource_nodes.values():
        if n.kind in EXPECTED_ITEM_BY_KIND:
            assert n.yields_item == EXPECTED_ITEM_BY_KIND[n.kind]


@pytest.mark.parametrize("world_id", CORPUS_WORLDS)
def test_compiled_nodes_obey_the_registry_kind_to_item_law(world_id):
    """The law ecology-spawned nodes already obey (test_resource_ecology.py): a node's `yields_item` is
    its kind's `ResourceRegistry` yield item. Asserted here over every compiler-produced node, so the
    kind/item collision cannot return for any kind, observed harvested or not."""
    spec, context = WorldRepository(str(WORLDS_DIR)).load_world_with_context(world_id)
    state, _ = WorldCompiler.compile(spec, seed=42, context=context)
    violations = {
        n.kind: (n.yields_item, ResourceRegistry.get(n.kind).yield_item)
        for n in state.resource_nodes.values()
        if ResourceRegistry.contains(n.kind) and ResourceRegistry.get(n.kind).yield_item != n.yields_item
    }
    assert not violations, f"{world_id}: kind -> (node yields_item, registry yield_item) {violations}"
