"""Every body of the sample worlds presents a species and a size (R3/D74: a compiled living body names a declared diet, so a species)."""
from __future__ import annotations

import pytest

from src.api.presenters.state_presenter import StatePresenter
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

SAMPLE_WORLDS = ["frontier_living_world", "urban_political", "crowded_frontier"]


@pytest.mark.parametrize("world", SAMPLE_WORLDS)
def test_the_sample_worlds_present_no_null_species(world):
    spec, context = WorldRepository("data/worlds").load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, 42, context=context)
    assert state.entities
    for entity in state.entities.values():
        for shape in (StatePresenter.present_entity, StatePresenter.present_entity_slim):
            out = shape(entity)
            assert out["species"] is not None and out["size"] in ("small", "medium", "large"), (world, entity.id, entity.kind, out["species"])
