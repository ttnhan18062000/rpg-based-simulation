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


def test_urban_political_guide_profile_selected_for_danger_rating_query():
    """TCK-20260702-SIMQ-UPLIFT2-INFORMATION: proves the corrected `town_notice_board`
    knowledge_scopes (data/worlds/urban_political/world.yaml) actually match
    InformationQueryRouter.matches_scope()'s hard-coded vocabulary — a compile-only test
    would miss a silent-non-match bug."""
    actor = _entity(1, x=0.0, y=0.0)
    state = _state([actor])

    town_notice_board = InformationSourceProfile(
        source_id="town_notice_board",
        source_kind="guide",
        knowledge_scopes=("regional_danger", "common_resource_sources"),
        accuracy=0.4,
        freshness=0.6,
        bias=0.1,
        cost_gold=0,
        max_answers_per_query=2,
    )

    q = InformationQuery(subject="bandit_road", kind="danger_rating")
    candidates = InformationQueryRouter.route(actor, q, state, [town_notice_board])

    assert len(candidates) == 1
    assert candidates[0].source_id == "town_notice_board"


def test_urban_political_traveling_merchant_profile_always_candidate_with_zero_distance_cost():
    """TCK-20260702-SIMQ-UPLIFT2-INFORMATION: `traveling_merchant_rumors` has
    source_kind="traveler", which bypasses matches_scope() entirely (router.py:57), so it is
    always a candidate regardless of query kind. Its source_id is a literal string (per
    plan.md's UQ-4 resolution), not a compiled entity id, so state.entities.get(...) always
    misses and distance_cost stays 0.0 — documented here as an explicit, asserted behavior."""
    actor = _entity(1, x=10.0, y=10.0)
    state = _state([actor])

    traveling_merchant_rumors = InformationSourceProfile(
        source_id="traveling_merchant_rumors",
        source_kind="traveler",
        knowledge_scopes=("common_resource_sources", "recipe_requirements"),
        accuracy=0.65,
        freshness=0.8,
        bias=0.2,
        cost_gold=5,
        max_answers_per_query=3,
    )

    q = InformationQuery(subject="anything", kind="danger_rating")
    candidates = InformationQueryRouter.route(actor, q, state, [traveling_merchant_rumors])

    assert len(candidates) == 1
    assert candidates[0].source_id == "traveling_merchant_rumors"
    assert candidates[0].distance_cost == 0.0
