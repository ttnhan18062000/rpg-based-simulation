"""Pure tag-reachability predicate shared between the build-time WORLD-REACH-001
validator rule (src/worldbuilding/validator.py) and any future runtime/
AuthoritativeState reachability check. Deliberately decoupled from WorldSpec's
own types where possible so it stays reusable against a differently-shaped
tag pool.
"""
from __future__ import annotations

from typing import Optional

from src.content.repository import CatalogRepository
from src.worldbuilding.schema import PopulationSpec, WorldSpec


def is_reachable(required_tags: list[str], available_tags: Optional[set[str]]) -> bool:
    """True if every required tag is satisfiable. An empty requirement is always
    satisfied. `available_tags is None` signals "no catalog to verify against" and
    is treated as cannot-verify, not as a violation.
    """
    if not required_tags:
        return True
    if available_tags is None:
        return True
    return set(required_tags).issubset(available_tags)


def resolve_population_tags(population: PopulationSpec, catalog_repo: Optional[CatalogRepository]) -> set[str]:
    """Tags a single population contributes to the reachable pool, via its
    archetype_id -> role -> compatible_traits chain. Returns an empty set for any
    unresolvable link (no catalog, no archetype_id, unknown archetype, unknown role)
    rather than raising — an unresolvable population carries no verifiable evidence
    of what it can satisfy.
    """
    if catalog_repo is None or population.archetype_id is None:
        return set()
    archetype = catalog_repo.get_entity_archetype(population.archetype_id)
    if archetype is None:
        return set()
    role = catalog_repo.get_role(archetype.role)
    if role is None:
        return set()
    return set(role.compatible_traits)


def build_available_participant_tags(spec: WorldSpec, catalog_repo: Optional[CatalogRepository]) -> Optional[set[str]]:
    """The union of every population's reachable tags in `spec`. Returns None when
    no catalog is available at all (the explicit cannot-verify signal consumed by
    `is_reachable`) rather than an empty set, which instead means "catalog present,
    but nothing in this spec resolves any traits" — a real, checkable pool.
    """
    if catalog_repo is None:
        return None
    available: set[str] = set()
    for population in spec.entities:
        available |= resolve_population_tags(population, catalog_repo)
    return available
