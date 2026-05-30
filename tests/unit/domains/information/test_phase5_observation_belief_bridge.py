"""
tests/unit/domains/information/test_phase5_observation_belief_bridge.py

Phase 5 — ObservationBeliefBridge unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.information.bridge import ObservationBeliefBridge


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
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


def test_observed_resource_creates_precise_fact():
    actor = _entity(1)
    state = _state([actor])
    
    event = {
        "kind": "resource_seen",
        "subject": "iron_ore",
        "details": {"location": "old_mine", "charges": 10},
    }
    
    result = ObservationBeliefBridge.process_observation(actor, event, state)
    
    assert result.knowledge_update is not None
    assert "iron_ore" in result.knowledge_update.facts
    fact = result.knowledge_update.facts["iron_ore"]
    assert fact.certainty == 1.0
    assert fact.details.get("location") == "old_mine"
