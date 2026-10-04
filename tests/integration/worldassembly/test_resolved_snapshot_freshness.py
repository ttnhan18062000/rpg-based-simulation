"""
A composition world runs its committed `resolved/world.resolved.yaml`, never its `world.yaml`
(WorldRepository.load_world redirects). That snapshot is a function of `world.yaml` plus the module and
catalog content read at resolve time, so it can go stale from any of those. These tests assert the
snapshot equals a FRESH resolve of its source, and pin the dungeon_crawl balance remedy at the location
production actually loads.
"""
from pathlib import Path

import pytest
import yaml

from src.content.repository import CatalogRepository
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec
from src.worldbuilding.cli import render_resolved_world_yaml
from src.worldbuilding.repository import WorldRepository
from src.worldmodules.repository import WorldModuleRepository

pytestmark = pytest.mark.worldassembly

WORLDS_DIR = Path("data/worlds")


def _composition_world_ids() -> list[str]:
    ids = []
    for world_yaml in sorted(WORLDS_DIR.glob("*/world.yaml")):
        raw = yaml.safe_load(world_yaml.read_text(encoding="utf-8"))
        if "worldcomposition" in (raw or {}).get("schema_version", ""):
            ids.append(world_yaml.parent.name)
    return ids


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def _fresh_resolve(world_id: str, repos) -> str:
    cat, mod = repos
    raw = yaml.safe_load((WORLDS_DIR / world_id / "world.yaml").read_text(encoding="utf-8"))
    bundle = WorldAssemblyResolver(cat, mod).assemble(WorldCompositionSpec.model_validate(raw))
    return render_resolved_world_yaml(bundle)


def test_composition_worlds_discovered():
    assert len(_composition_world_ids()) > 10, "discovery found too few worlds; the freshness check would be vacuous"


@pytest.mark.parametrize("world_id", _composition_world_ids())
def test_committed_snapshot_equals_fresh_resolve(world_id, repos):
    """The world the engine loads is the one its authored definition resolves to."""
    snapshot = WORLDS_DIR / world_id / "resolved" / "world.resolved.yaml"
    assert snapshot.is_file(), f"{world_id} has no committed resolved snapshot"
    assert snapshot.read_text(encoding="utf-8") == _fresh_resolve(world_id, repos), (
        f"{world_id}: committed resolved/ snapshot is stale; run `make world-resolve WORLD={world_id}`"
    )


def test_fresh_resolve_is_byte_deterministic(repos):
    assert _fresh_resolve("dungeon_crawl", repos) == _fresh_resolve("dungeon_crawl", repos)


def test_dungeon_crawl_runs_the_accepted_balance_remedy():
    """The 94-97% extinction fix (32 -> 12 entities) must be in what production actually loads."""
    source = yaml.safe_load((WORLDS_DIR / "dungeon_crawl" / "world.yaml").read_text(encoding="utf-8"))
    module_ids = [ref["module_id"] for ref in source["module_refs"]]
    assert module_ids == ["ruins_mystery_quest", "scalable_bandit_camp"]
    bandit = next(r for r in source["module_refs"] if r["module_id"] == "scalable_bandit_camp")
    assert bandit["parameters"]["danger_scale"] == 2

    snapshot_text = (WORLDS_DIR / "dungeon_crawl" / "resolved" / "world.resolved.yaml").read_text(encoding="utf-8")
    assert "goblin_camp_conflict" not in snapshot_text
    assert "old_mine_resource_loop" not in snapshot_text

    world = WorldRepository("data/worlds").load_world("dungeon_crawl")
    assert world.entities, "no populations loaded; the count assertion would be vacuous"
    assert sum(pop.count for pop in world.entities) == 12
