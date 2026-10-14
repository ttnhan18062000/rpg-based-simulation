"""The static walk check reads the compiled blocked tiles (and building tiles), never a terrain name."""
from pathlib import Path
from types import SimpleNamespace

import yaml

from src.engine.candidate_selector import MovementCandidateSelector

TERRAIN_YAML = Path(__file__).resolve().parents[3] / "data/content/world/terrain.yaml"


def _state(terrain, blocked=(), buildings=()):
    return SimpleNamespace(
        terrain=terrain,
        blocked_tiles=set(blocked),
        buildings={i: SimpleNamespace(position=p) for i, p in enumerate(buildings)},
    )


def test_a_blocked_tile_is_refused():
    state = _state({(3, 3): "plain"}, blocked=[(3, 3)])
    assert MovementCandidateSelector.is_static_position_blocked(state, (3.4, 3.9))


def test_a_building_tile_is_refused():
    state = _state({(2, 2): "plain"}, buildings=[(2, 2)])
    assert MovementCandidateSelector.is_static_position_blocked(state, (2.0, 2.0))


def test_any_catalog_terrain_not_blocked_is_walkable():
    ids = [t["id"] for t in yaml.safe_load(TERRAIN_YAML.read_text()) if t]
    assert ids
    for terrain_id in ids:
        state = _state({(1, 1): terrain_id})
        assert not MovementCandidateSelector.is_static_position_blocked(state, (1.0, 1.0)), terrain_id
