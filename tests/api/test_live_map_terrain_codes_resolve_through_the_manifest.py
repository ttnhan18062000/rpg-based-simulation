"""The Live Map's terrain path end to end (issue #519, TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE).

/api/v1/map numbers terrain per world (codes 0..n-1 over the terrain actually present), so a code means nothing without the manifest. For each world
the test drives the real API app, decodes the RLE grid, and checks that every tile's code resolves through /api/v1/manifest `terrain_types` to the
terrain meaning the compiled engine state holds for that tile. A client that colours by the manifest name is then right for any world.
"""
from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from src.api.presenters.state_presenter import StatePresenter
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL
from src.content.repository import CatalogRepository
from src.core.state import AuthoritativeState
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

KEY = "live-map-terrain-probe"
WORLDS = ["sandbox_world", "dungeon_crawl"]  # both mix upper- and lower-case raw terrain or several terrains: the codes differ per world
SEED = 42


def _decode(grid, width, height):
    flat = []
    for value, count in zip(grid[0::2], grid[1::2]):
        flat.extend([value] * count)
    assert len(flat) == width * height
    return {(i % width, i // width): flat[i] for i in range(len(flat))}


def _meaning(raw: str, catalog: CatalogRepository) -> str:
    definition = catalog.terrain.get(raw.lower())
    return (definition.display_name or definition.id) if definition is not None else raw.title()


@pytest.mark.parametrize("world_id", WORLDS)
def test_every_tile_code_resolves_through_the_manifest_to_the_terrain_the_engine_holds(world_id):
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    app = create_v2_app(profile, seed=SEED, world_id=world_id)
    state, _ = WorldCompiler.compile(WorldRepository("data/worlds").load_world(world_id), seed=SEED)
    catalog = CatalogRepository()
    catalog.load_all()
    with TestClient(app, headers={"X-API-Key": KEY}) as client:
        manifest = client.get("/api/v1/manifest").json()
        grid = client.get("/api/v1/map").json()
    codes = _decode(grid["grid"], grid["width"], grid["height"])
    names = manifest["terrain_types"]
    assert len(codes) == len(state.terrain) > 0
    for tile, raw in state.terrain.items():
        assert names[str(codes[tile])] == _meaning(raw, catalog), f"{world_id} tile {tile}: raw {raw!r}, code {codes[tile]}"


def test_one_terrain_has_one_code_whatever_the_case_of_its_raw_string():
    """The engine carries both 'PLAIN' (the compiler's fill) and 'plain' (content): the presenter gives them one code, so the manifest names it once."""
    state = AuthoritativeState(tick=0, seed=1, terrain={(0, 0): "PLAIN", (1, 0): "plain", (2, 0): "forest", (3, 0): "FOREST"})
    code_map = StatePresenter.terrain_code_map(state)
    assert code_map["PLAIN"] == code_map["plain"] and code_map["forest"] == code_map["FOREST"]
    assert code_map["plain"] != code_map["forest"]
    assert sorted(set(code_map.values())) == [0, 1]


@pytest.mark.parametrize("world_id", WORLDS)
def test_the_live_world_is_the_compiled_authored_world_with_no_demo_spawn(world_id):
    """D69 (owner ruling 2026-10-14): the API runs the same compiled world the simulation and the gate run. Before the first tick its entity set IS
    the compiled world's, so no body lacks an authored source and there is no hero-and-goblin demo diagonal. (Mid-run additions are not asserted here:
    the camp spawn is being removed under D70, whose ticket adds the no-parentless-add test.)"""
    from src.api.engine_manager import V2EngineManager
    from tests.helpers.scenario import compile_world

    compiled = compile_world(world_id, SEED)
    manager = V2EngineManager(PROD_SMALL, seed=SEED, world_id=world_id)  # builds the world, does not start the loop
    try:
        first = manager.kernel.state
        assert first.tick == 0
        assert {i: (e.kind, tuple(e.navigation.position)) for i, e in first.entities.items()} == {
            i: (e.kind, tuple(e.navigation.position)) for i, e in compiled.entities.items()}
    finally:
        manager.kernel.shutdown()


def test_the_engine_manager_has_no_demo_spawn_switch():
    import inspect

    from src.api.engine_manager import V2EngineManager

    assert "entities_count" not in inspect.signature(V2EngineManager.__init__).parameters
    assert "entities_count" not in inspect.signature(create_v2_app).parameters


def test_the_authored_world_presents_every_entity_including_those_carrying_items():
    """Found by D69: the demo spawn carried no items, so the entity presenter's read of an item's `metadata` (an ItemStack has `properties`) never ran
    live. The authored world's merchants and workers carry items, and the entity DTO raised AttributeError for them."""
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    app = create_v2_app(profile, seed=SEED, world_id="sandbox_world")
    with TestClient(app, headers={"X-API-Key": KEY}) as client:
        response = client.get("/api/v1/entities", params={"limit": 50})
    assert response.status_code == 200
    entities = response.json()["entities"]
    carrying = [e for e in entities if e["inventory"]["items"]]
    assert carrying, "sandbox_world authors entities that carry items; none was presented"
    assert all("metadata" in item for e in carrying for item in e["inventory"]["items"])
