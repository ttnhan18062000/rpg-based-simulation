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
    # Build entity with a locked strategic project.
    # HP is set low (40/100 = 0.4) so the threat-resolution early-release condition does
    # NOT trigger — the lock must be respected while the entity is still in danger.
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=40, max_hp=100, atk=10, def_stat=2))
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


def test_adventure_decision_does_not_discard_earlier_phase_updates():
    """TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING: the adventure_decision phase's
    own run_phase call site in pipeline.py previously returned AdventureDecisionPhase.apply()'s
    fresh StateUpdate directly instead of merging it into the accumulated update -- silently
    discarding every phase's output that ran earlier in the same tick (diplomatic_transitions,
    information_belief, cooperation, contracts/blacksmith) whenever ENABLE_ADVENTURE_ROUTING=ON.
    Real, controlled proof this was NOT an RNG-consumption-order bug (the ticket's own original
    hypothesis): compute_transitions() is a pure function of state.factions and produced the
    identical FactionUpdate list regardless of the flag -- the discard happened strictly inside
    refine(), after diplomatic_transitions merged its updates, before refine() returned."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.state import FactionState, DiplomaticState
    from src.systems.world_systems.generator import EntityGenerator
    from src.domains.optimization.feature_flags import FeatureMode

    # Two factions with tension high enough that diplomatic_state_machine.compute_transitions()
    # produces a real NEUTRAL -> TENSE FactionUpdate for this pair (threshold: pair_tension > 0.4).
    factions = {
        "alpha": FactionState(faction_id="alpha", tension_level=0.5),
        "beta": FactionState(faction_id="beta", tension_level=0.5),
    }
    hero = EntityGenerator(seed=1).spawn_hero((10.0, 10.0))

    state = _state([hero])
    from dataclasses import replace as dc_replace
    state = dc_replace(
        state, factions=factions, building_tiles={},
        feature_flags={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON},
    )

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())

    assert refined.faction_updates, (
        "diplomatic_transitions' own real FactionUpdate output was discarded by the "
        "adventure_decision phase -- it must survive refine() when routing is ON"
    )
    assert any(
        fu.faction_id in ("alpha", "beta") and fu.diplomatic_relations_set
        for fu in refined.faction_updates
    )
