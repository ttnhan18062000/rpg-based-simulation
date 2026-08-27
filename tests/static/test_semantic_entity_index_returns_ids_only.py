# Compliance IDs: PERF-010, PERF-011
"""
AC #2 architecture guard: every SemanticEntityQuery method must return only entity IDs
(int / Tuple[int, ...]) -- never EntityState, IdentityComponent, or other component/domain
objects. Mirrors the runtime-assertion style of tests/static/test_no_direct_dirtyset_candidate_selection.py.
"""
from src.core.enums import EntityRole, Faction
from src.core.state import EntityState
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.engine.semantic_entity_index import SemanticEntityQuery
from tests.helpers.entities import make_entity, make_state, with_biological, with_navigation


def _fixture_state():
    hero = with_navigation(
        make_entity(1, role=EntityRole.HERO, faction=Faction.HERO_GUILD, class_id="WARRIOR"),
        region_id="north_woods",
    )
    starving = with_biological(make_entity(5, role=EntityRole.CITIZEN), hunger=99.0)
    provider = InformationProviderState(
        entity_id=9,
        archetype=InformationProviderArchetype.MERCHANT,
        knowledge_domains=("material_source",),
    )
    return make_state(entities=[hero, starving], tick=1, information_providers={9: provider})


def test_query_methods_return_only_entity_ids_not_objects():
    state = _fixture_state()
    results = [
        SemanticEntityQuery.by_role_class(state, None, EntityRole.HERO, "WARRIOR"),
        SemanticEntityQuery.by_region(state, None, "north_woods"),
        SemanticEntityQuery.by_faction(state, None, Faction.HERO_GUILD),
        SemanticEntityQuery.by_need(state, None, "hunger"),
        SemanticEntityQuery.by_knowledge_domain(state, None, "material_source"),
    ]
    for result in results:
        assert isinstance(result, tuple)
        assert len(result) > 0
        for item in result:
            assert isinstance(item, int)
            assert not isinstance(item, EntityState)
