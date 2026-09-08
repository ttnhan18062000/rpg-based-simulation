"""
tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py

Phase 4 — CombatEngagementPhase integration tests.
Verifies sensory range triggers, target limits, and performance skips.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.combat_engagement.phase import CombatEngagementPhase


def _entity(e_id, x=0.0, y=0.0, faction: Faction = None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p, faction=faction)
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


def test_phase_writes_no_threat_belief_without_skipping_posture_for_entity_without_relevant_target():
    """
    TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): no hostile in range
    still writes a real LOW combat_risk belief (restoring the "current assessment, replaced every
    tick" invariant), even though there is correctly no posture/target to set.
    """
    actor = _entity(1, x=0.0, y=0.0)
    target_far = _entity(2, x=50.0, y=50.0) # way out of sensory range (dist > 10)
    state = _state([actor, target_far])

    update = CombatEngagementPhase.apply(state)

    assert actor.id in update.entity_updates
    eu = update.entity_updates[actor.id]
    assert eu.property_updates == {}
    assert eu.strategic is not None
    assert eu.strategic.beliefs_add_or_update[0].claim == "LOW"


def test_phase_runs_when_hostile_enters_range():
    actor = _entity(1, x=0.0, y=0.0, faction=Faction.HERO_GUILD)
    target_near = _entity(2, x=3.0, y=4.0, faction=Faction.MONSTER_HORDE) # within sensory range (dist = 5)
    state = _state([actor, target_near])
    
    update = CombatEngagementPhase.apply(state)
    
    assert actor.id in update.entity_updates
    prop_ups = update.entity_updates[actor.id].property_updates
    assert prop_ups.get("last_combat_posture") is not None
    assert prop_ups.get("last_combat_posture_target") == 2
