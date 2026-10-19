"""TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE: a missing diet is a content error, never a default.

The diet slice of SURV-05. A body with no species, an unknown species or a body model with no diet used to read as "eats anything" (a silent free meal);
a declared EMPTY diet (a guardian, a spirit, undead) is valid. The corpus test compiles every data world and finds no body the appraisal fallbacks could reach.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from src.worldbuilding.diet_declaration import require_declared_diet
from src.worldbuilding.schema import InvalidWorldSpecError

POP = SimpleNamespace(role="merchant", faction="merchant_league")


def test_a_body_with_no_species_is_a_content_error_that_names_the_world_and_population():
    with pytest.raises(InvalidWorldSpecError) as err:
        require_declared_diet("w1", "trading_pop_0", POP, None)
    text = str(err.value)
    assert "w1" in text and "trading_pop_0" in text and "merchant" in text and "no species" in text


def test_an_unknown_species_is_a_content_error():
    with pytest.raises(InvalidWorldSpecError, match="does not declare"):
        require_declared_diet("w1", "p", POP, "no_such_species_xyz")


def test_a_declared_diet_passes_and_so_does_a_declared_empty_diet():
    require_declared_diet("w1", "p", POP, "human")  # a list of food classes
    require_declared_diet("w1", "p", POP, "spirit")  # an empty list: it eats nothing, and that is declared


def test_a_species_whose_body_declares_no_diet_is_a_content_error(monkeypatch):
    from src.worldbuilding import diet_declaration
    catalog = SimpleNamespace(get_species=lambda species_id: SimpleNamespace(body_model="b"), get_body_model=lambda body_id: SimpleNamespace(diet=None))
    monkeypatch.setattr(diet_declaration, "warmed_catalog", lambda: catalog)
    with pytest.raises(InvalidWorldSpecError, match="no declared diet"):
        require_declared_diet("w1", "p", POP, "human")


def test_a_recipe_may_name_its_species_and_an_unknown_one_is_refused_at_resolve():
    from src.worldbuilding.recipe import PopulationRecipeSpec
    recipe = PopulationRecipeSpec(role="merchant", count=1, faction="merchant_league", species_id="human")
    assert recipe.species_id == "human"
    assert PopulationRecipeSpec(role="merchant", count=1, faction="merchant_league").species_id is None
    with pytest.raises(ValueError):
        PopulationRecipeSpec(role="merchant", count=1, faction="merchant_league", species_id="")


@pytest.mark.slow
def test_no_compiled_data_world_has_a_body_the_appraisal_fallbacks_could_reach():
    """Every data world compiles (the check runs inside compile), and every living body resolves to a declared diet."""
    from src.content_semantics.faction import get_species_id_str
    from src.engine.behavior_consumers import get_kind_properties
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    root = os.path.join("data", "worlds")
    worlds = sorted(d for d in os.listdir(root) if os.path.isfile(os.path.join(root, d, "world.yaml")))
    assert worlds
    gaps = []
    for world in worlds:
        spec, context = WorldRepository(root).load_world_with_context(world)
        state, _ = WorldCompiler.compile(spec, 42, context=context)
        for entity in state.entities.values():
            _, body = get_kind_properties(get_species_id_str(entity))
            if body is None or body.diet is None:
                gaps.append((world, entity.id, entity.kind))
    assert gaps == []
