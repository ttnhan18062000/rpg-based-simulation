"""
tests/unit/domains/information/test_phase5_information_intent_resolver.py

Phase 5 — InformationIntentResolver unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.information.schema import InformationSourceCandidate, InformationQuery
from src.domains.information.resolver import InformationIntentResolver


def _entity(e_id, x=0.0, y=0.0, gold=100):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(x, y)
    b.gold = gold # Set gold directly or use builder inventory helper
    b.inventory(gold=gold)
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


def test_far_source_resolves_to_move_to():
    actor = _entity(1, x=0.0, y=0.0)
    source = _entity(2, x=10.0, y=10.0)  # far
    state = _state([actor, source])
    
    cand = InformationSourceCandidate(
        source_id=2,
        source_kind="guide",
        expected_relevance=0.8,
        expected_certainty=0.7,
        cost_gold=5,
        distance_cost=14.14,
        trust_score=0.5,
        reason="Matched guide scope.",
    )
    
    q = InformationQuery(subject="iron_ore", kind="material_source")
    
    intent = InformationIntentResolver.resolve(actor, cand, q, state)
    
    assert intent is not None
    assert intent.kind == "MOVE_TO"
    assert intent.target_id == 2
    assert intent.payload.get("position") == (10.0, 10.0)


def test_near_source_resolves_to_ask_information():
    actor = _entity(1, x=0.0, y=0.0, gold=10)
    source = _entity(2, x=1.0, y=1.0)  # near (dist = 1.41)
    state = _state([actor, source])
    
    cand = InformationSourceCandidate(
        source_id=2,
        source_kind="guide",
        expected_relevance=0.8,
        expected_certainty=0.7,
        cost_gold=5,
        distance_cost=1.41,
        trust_score=0.5,
        reason="Matched guide scope.",
    )
    
    q = InformationQuery(subject="iron_ore", kind="material_source")
    
    intent = InformationIntentResolver.resolve(actor, cand, q, state)
    
    assert intent is not None
    assert intent.kind == "ASK_INFORMATION"
    assert intent.target_id == 2
    assert intent.payload.get("cost_paid") == 5
    assert intent.payload.get("subject") == "iron_ore"
