"""A compiled body must resolve to a declared diet (the diet slice of SURV-05; TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET...).

A body with no species, an unknown species, or a body model that declares no diet used to be read by the appraisal as "eats anything", so it
took the inn's free meal and every food: a missing property was a silent default. It is now a content error at compile, naming the world, the
population and the role. A declared EMPTY diet (a guardian, a spirit, undead) is valid: it declares that the body eats nothing.
"""
from __future__ import annotations

from typing import Any, Optional

from src.content.common_knowledge_seed import warmed_catalog
from src.content.resolver import ResolverError
from src.worldbuilding.schema import InvalidWorldSpecError


def require_declared_diet(world_id: str, population_id: str, pop_spec: Any, species_id: Optional[str]) -> None:
    """Raise ``InvalidWorldSpecError`` unless ``species_id`` names a species whose body model declares a diet (an empty list counts)."""
    where = f"world '{world_id}', population '{population_id}' (role '{getattr(pop_spec, 'role', '?')}', faction '{getattr(pop_spec, 'faction', '?')}')"
    if not species_id:
        raise InvalidWorldSpecError(f"{where} spawns bodies with no species, so they have no declared diet: name a species (an archetype_id or the recipe's species_id)")
    catalog = warmed_catalog()
    species = catalog.get_species(species_id)
    body = catalog.get_body_model(species.body_model) if species is not None else None
    if species is None:
        raise InvalidWorldSpecError(f"{where} names species '{species_id}', which the content does not declare")
    if body is None or body.diet is None:
        raise InvalidWorldSpecError(f"{where}: species '{species_id}' has no declared diet (its body model declares none; an empty list declares that it eats nothing)")


def require_known_recipe_species(catalog_repo: Any, recipe: Any) -> None:
    """A recipe that names a species names one the catalog declares (its diet and other properties come from it)."""
    if recipe.species_id and not catalog_repo.get_species(recipe.species_id):
        raise ResolverError("species", recipe.species_id)
