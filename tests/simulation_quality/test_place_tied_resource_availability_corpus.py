"""Idea 49 (Place-Tied Crafting Materials) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

REFINEMENT, found during Investigate: the real "place-tied" constraint is resource-node placement,
not a live crafting-time proximity check -- confirmed via grep, no such gate exists anywhere in
`src/systems/*/crafting*.py`/`harvest*.py`. `mountain_pass.yaml` (already composed into
`hero_guild_routing`, confirmed via `world.yaml:28`) is the only world_module in this composition
whose own `resources:` block declares `frost_shard_cluster` -- an entity can only ever obtain that
material by harvesting a node from this specific module's own placed content. A compiled node's
`kind` is the resource kind `frost_shard_cluster` and its `yields_item` is the catalog item
`frost_shard` (resource definition `frost_shard_cluster`, material/resource_type `frost_shard`).
This file originally asserted `yields_item == "frost_shard_cluster"` and claimed there was no
separate `frost_shard` item name; that pinned the kind/item field collision fixed by
TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND, so the assertion now checks the
real catalog item.
"""
from __future__ import annotations

import yaml

from src.core.items import ItemRegistry
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLD_MODULES_DIR = "data/content/world_modules"


def test_frost_shard_cluster_resource_only_declared_by_mountain_pass_module():
    world_yaml = yaml.safe_load(open("data/worlds/hero_guild_routing/world.yaml"))
    module_ids = [m["module_id"] for m in world_yaml["module_refs"]]
    assert "mountain_pass" in module_ids

    declaring_modules = []
    for module_id in module_ids:
        module = yaml.safe_load(open(f"{WORLD_MODULES_DIR}/{module_id}.yaml"))
        if "frost_shard_cluster" in (module.get("resources") or {}):
            declaring_modules.append(module_id)

    assert declaring_modules == ["mountain_pass"], (
        f"expected only mountain_pass to declare frost_shard_cluster, got {declaring_modules}"
    )


def test_frost_shard_cluster_compiles_into_a_real_resource_node():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("hero_guild_routing")
    state, _ = WorldCompiler.compile(spec, seed=42)

    nodes = [n for n in state.resource_nodes.values() if n.kind == "frost_shard_cluster"]
    assert nodes, "hero_guild_routing must compile at least one real frost_shard_cluster resource node"
    assert all(n.yields_item == "frost_shard" for n in nodes)
    assert all(ItemRegistry.get(n.yields_item) is not None for n in nodes), "yielded item must be registered"
