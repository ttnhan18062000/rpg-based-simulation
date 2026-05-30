"""
tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py

Phase 4 — CombatReassessmentService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.combat_engagement.reassessment import CombatReassessmentService
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.schema import CombatPosture


def _entity(e_id, hp=100):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def _state(entities, tick=10) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=tick, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def test_high_damage_received_triggers_retreat_reassessment():
    actor = _entity(1, hp=15) # near_death HP
    target = _entity(2, hp=100)
    state = _state([actor, target])
    
    # Establish previous decision (e.g. earlier when healthy we had PROBE/ENGAGE)
    prev = CombatEngagementDecisionService.evaluate(_entity(1, hp=100), target, state)
    assert prev.posture == CombatPosture.PROBE
    
    # Simulate dynamic combat events: actor took heavy damage
    events = [
        {"attacker_id": 2, "defender_id": 1, "damage": 25, "skill_id": None}
    ]
    
    # Reassess
    new_decision = CombatReassessmentService.reassess(actor, target, events, prev, state)
    
    # Should retreat due to near_death condition check
    assert new_decision.posture == CombatPosture.RETREAT
