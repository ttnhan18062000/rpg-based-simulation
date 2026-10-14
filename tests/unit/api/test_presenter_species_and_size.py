"""The entity presenter emits the species id and the species' declared power band as `size` (map markers key on them); never derived in code."""
from __future__ import annotations

import pytest

from src.api.presenters.state_presenter import StatePresenter
from src.content_semantics.faction import get_faction_semantics_service
from src.core.builder import V2EntityBuilder


def _entity(species_id):
    props = {"species_id": species_id} if species_id else {}
    return V2EntityBuilder(1).kind("worker").properties(props).location(5.0, 5.0).build()


@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_slim])
@pytest.mark.parametrize("species_id", ["human", "wolf", "small_plant_eater"])
def test_a_known_species_presents_its_id_and_declared_band(shape, species_id):
    declared = get_faction_semantics_service().repo.get_species(species_id).power
    assert declared in ("small", "medium", "large")
    out = shape(_entity(species_id))
    assert out["species"] == species_id
    assert out["size"] == declared


@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_slim])
def test_a_body_with_no_species_presents_null_for_both(shape):
    out = shape(_entity(None))
    assert out["species"] is None and out["size"] is None


@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_slim])
def test_an_unknown_species_keeps_its_id_and_has_no_size(shape):
    out = shape(_entity("no_such_species"))
    assert out["species"] == "no_such_species" and out["size"] is None
