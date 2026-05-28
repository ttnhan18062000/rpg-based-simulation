"""
tests/integration/domains/information/test_phase5_information_belief_phase.py

Phase 5 — InformationBeliefPhase integration tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.domains.information.schema import InformationSourceProfile
from src.domains.information.phase import InformationBeliefPhase


def _entity(e_id, x=0.0, y=0.0, unknowns=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(x, y)
    
    if unknowns:
        km = KnowledgeModelComponent(unknowns=unknowns)
        sm = SelfModelBundle(knowledge=km)
        b.replace_self_model(sm)
        
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


def test_phase_routes_query_for_active_unknowns():
    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=1)
    actor = _entity(1, x=0.0, y=0.0, unknowns={"iron_ore": unk})
    guide = _entity(2, x=1.0, y=1.0)  # close source
    state = _state([actor, guide])

    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.8,
            freshness=0.9,
        )
    ]

    update = InformationBeliefPhase.apply(state, profiles)

    assert actor.id in update.entity_updates
    prop_ups = update.entity_updates[actor.id].property_updates
    assert prop_ups.get("last_routed_query_subject") == "iron_ore"
    assert len(update.entity_updates[actor.id].intent_results) == 1
    assert update.entity_updates[actor.id].intent_results[0].kind == "ASK_INFORMATION"
