"""
tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py

Phase 3 — AdventureDecisionPhase integration tests.
Verifies entity lifecycle filtering, strategic lock compliance, and transition.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.adventure.phase import AdventureDecisionPhase
from src.core.strategic import ProjectState, ProjectKind, ProjectStatus, ObjectiveState, ObjectiveKind, ObjectiveStatus, StrategicComponent
from src.domains.adventure.schema import RouteFamily


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=5,
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


def test_filters_out_locked_projects():
    # Build entity with a locked strategic project
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    
    # Add active locked project until tick 10 (current is 5)
    obj = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_SERVICE, target=None, target_position=None, status=ObjectiveStatus.UNRESOLVED, blocker_ids=[])
    proj = ProjectState(
        id="proj1",
        kind=ProjectKind.RECOVERY,
        status=ProjectStatus.ACTIVE,
        score=1.0,
        lock_until_tick=10,
        objectives=[obj],
        active_objective_id="o1",
        created_tick=1,
    )
    b.replace_self_model(None) # simple default self model
    
    # Set strategic projects
    entity = b.build()
    # Force projects mapping manually
    from src.engine.apply import replace
    new_strat = replace(entity.strategic, projects={"proj1": proj}, current_project_id="proj1", current_objective_id="o1")
    entity = replace(entity, strategic=new_strat)
    
    state = _state([entity])
    
    # Run integration phase
    update = AdventureDecisionPhase.apply(state)
    
    # Should skip hero because project is locked
    assert not update.entity_updates
