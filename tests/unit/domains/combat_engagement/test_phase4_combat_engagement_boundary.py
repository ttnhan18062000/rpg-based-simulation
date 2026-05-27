"""
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py

Phase 4 — CombatEngagement boundary and coordinate checks.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.schema import CombatPosture


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
        tick=1,
        seed=1,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        building_tiles=(),
        terrain=(),
        home_storage={},
        town_center=(0, 0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def test_engagement_service_does_not_execute_attack():
    actor = _entity(1)
    target = _entity(2)
    state = _state([actor, target])

    # Run pre-combat engagement service
    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    # Pre-combat should not mutate HP or register attacks
    assert result.actor_id == 1
    assert result.target_id == 2
    assert result.posture in (CombatPosture.ENGAGE, CombatPosture.PROBE, CombatPosture.WATCH)
    assert actor.combat.hp == 100
    assert target.combat.hp == 100


def test_engagement_service_does_not_mutate_state():
    actor = _entity(1)
    target = _entity(2)
    state = _state([actor, target])
    
    initial_dict = actor.to_canonical_dict()
    
    # Run evaluation
    CombatEngagementDecisionService.evaluate(actor, target, state)
    
    assert actor.to_canonical_dict() == initial_dict
