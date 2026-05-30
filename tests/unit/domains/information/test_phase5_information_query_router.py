"""
tests/unit/domains/information/test_phase5_information_query_router.py

Phase 5 — InformationQueryRouter unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent
from src.domains.information.schema import InformationQuery, InformationSourceProfile
from src.domains.information.router import InformationQueryRouter


def _entity(e_id, x=0.0, y=0.0):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(x, y)
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def test_router_selects_and_sorts_correctly():
    actor = _entity(1, x=0.0, y=0.0)
    guide_entity = _entity(2, x=3.0, y=4.0)  # distance = 5
    state = _state([actor, guide_entity])

    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.8,
            freshness=0.9,
        ),
        InformationSourceProfile(
            source_id=3,
            source_kind="blacksmith",
            knowledge_scopes=("recipe_requirements",),
            accuracy=0.9,
            freshness=1.0,
            cost_gold=50,
        ),
    ]

    q = InformationQuery(subject="iron_ore", kind="material_source")
    candidates = InformationQueryRouter.route(actor, q, state, profiles)

    assert len(candidates) == 1
    c = candidates[0]
    assert c.source_id == 2
    assert c.source_kind == "guide"
    assert c.distance_cost == 5.0
