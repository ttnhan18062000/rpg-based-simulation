"""Idea 49 (Place-Tied Crafting Materials) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

REFINEMENT, found during Investigate: the real "place-tied" constraint is resource-node placement,
not a live crafting-time proximity check -- confirmed via grep, no such gate exists anywhere in
`src/systems/*/crafting*.py`/`harvest*.py`. `mountain_pass.yaml` (already composed into
`hero_guild_routing`, confirmed via `world.yaml:28`) is the only world_module in this composition
whose own `resources:` block declares `frost_shard_cluster` -- an entity can only ever obtain that
material by harvesting a node from this specific module's own placed content, since a compiled
resource node's real `kind`/`yields_item` field is literally `frost_shard_cluster` (there is no
separate `frost_shard` item name -- another citation the ticket's own text got wrong).
"""
from __future__ import annotations

import yaml

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
    assert all(n.yields_item == "frost_shard_cluster" for n in nodes)
