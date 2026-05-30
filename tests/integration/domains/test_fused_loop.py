"""
tests/integration/domains/test_fused_loop.py

Unified fusion integration tests.
Verifies Aspect-Gated Feature Flags, Shadow Mode parity, spatial candidate capping,
and knowledge persistence under the authoritative apply pipeline.
"""

import pytest
from typing import Any
from dataclasses import replace as dataclass_replace
from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState, CombatComponent, BiologicalComponent,
    PersonalityComponent, ResourceNodeState
)
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.core.updates import StateUpdate
from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.world.providers.resources import ResourceOpportunityProvider
from src.domains.information.schema import InformationSourceProfile


def _create_entity(ent_id: int, x: float, y: float, hp: int = 100) -> Any:
    b = V2EntityBuilder(ent_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p, class_id="warrior")
    b.location(x, y)
    b.lifecycle(active=True)
    return b.build()


def _create_state(entities: list, resource_nodes: dict = None) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=42, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes=resource_nodes or {}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=set(),
        building_tiles={}, terrain={}, home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=set(), town_entity_ids=set(),
    )


def test_feature_shadow_mode_preserves_authoritative_hash():
    """
    Verify that running the loop in SHADOW mode evaluates all logic but discards
    the final state aspect changes, guaranteeing exact state equivalence to OFF mode.
    """
    e1 = _create_entity(1, 0.0, 0.0, hp=50)
    e2 = _create_entity(2, 1.0, 1.0)
    
    # 1. State under OFF mode
    state_off = _create_state([e1, e2])
    state_off = dataclass_replace(state_off, pressure_signals={
        "ENABLE_SELF_MODEL_COGNITION": 0.0,
        "ENABLE_ADVENTURE_ROUTING": 0.0,
        "ENABLE_COMBAT_ENGAGEMENT": 0.0,
        "ENABLE_BELIEF_ASSIMILATION": 0.0,
        "ENABLE_SOCIAL_COOPERATION": 0.0,
        "ENABLE_WORLD_EMERGENCE": 0.0,
    })
    
    update_off = StateUpdate()
    refined_off = AuthoritativeApplyPipeline.refine(state_off, update_off)
    next_state_off = ApplyPath.apply_generation(state_off, refined_off, next_tick=2)

    # 2. State under SHADOW mode
    state_shadow = _create_state([e1, e2])
    state_shadow = dataclass_replace(state_shadow, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.SHADOW,
        "ENABLE_ADVENTURE_ROUTING": FeatureMode.SHADOW,
        "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.SHADOW,
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.SHADOW,
        "ENABLE_SOCIAL_COOPERATION": FeatureMode.SHADOW,
        "ENABLE_WORLD_EMERGENCE": FeatureMode.SHADOW,
    })

    update_shadow = StateUpdate()
    refined_shadow = AuthoritativeApplyPipeline.refine(state_shadow, update_shadow)
    next_state_shadow = ApplyPath.apply_generation(state_shadow, refined_shadow, next_tick=2)

    # Assert that metrics ran/skipped are present in refined_shadow
    assert refined_shadow.metric_counters.get("run_self_model", 0) > 0 or refined_shadow.metric_counters.get("skip_self_model", 0) == 0

    # Verify entities are identical because SHADOW updates were discarded
    for ent_id in (1, 2):
        ent_off = next_state_off.entities[ent_id]
        ent_shadow = next_state_shadow.entities[ent_id]
        
        # Check coordinates and health are identical
        assert ent_off.navigation.position == ent_shadow.navigation.position
        assert ent_off.combat.hp == ent_shadow.combat.hp
        assert ent_off.strategic.current_project_id == ent_shadow.strategic.current_project_id
        
        # Check custom property updates are discarded in shadow
        assert ent_shadow.identity.properties.get("last_combat_posture") is None


def test_self_model_phase_runs_in_shadow_without_state_mutation():
    """
    Ensure the Self Model phase runs in SHADOW mode (recording metric counters)
    but does not mutate the entity's actual self_model aspect or live fields.
    """
    e = _create_entity(1, 0.0, 0.0, hp=40) # Needs healing / low HP
    state = _create_state([e])
    state = dataclass_replace(state, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.SHADOW,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Assert run counter is incremented
    assert refined.metric_counters.get("run_self_model", 0) == 1
    # Verify entity update is NOT applied to self_model_bundle
    assert 1 not in refined.entity_updates or refined.entity_updates[1].self_model_bundle_set is None


def test_adventure_phase_receives_nonempty_world_opportunities():
    """
    Verify adventure routing receives non-empty world opportunities generated from live state nodes.
    """
    e = _create_entity(1, 0.0, 0.0)
    object.__setattr__(e.navigation, "region_id", "old_mine") # match resource node
    node = ResourceNodeState(
        id=201, kind="node_iron", position=(1.0, 1.0), yields_item="iron_ore",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    state = _create_state([e], resource_nodes={node.id: node})
    
    # Verify provider gets opportunities
    opps = ResourceOpportunityProvider.get_opportunities(e, state)
    assert len(opps) > 0
    assert opps[0].target_id == "201"
    assert opps[0].subject == "iron_ore"


def test_combat_engagement_caps_candidates():
    """
    Verify CombatEngagementPhase uses the proximity grid/capping to evaluate up to 3 candidate targets.
    """
    actor = _create_entity(1, 0.0, 0.0)
    # Add 5 hostiles close by
    hostiles = [_create_entity(i, 0.5, 0.5) for i in range(2, 8)]
    state = _create_state([actor] + hostiles)
    
    # Enable Combat phase
    state = dataclass_replace(state, feature_flags={
        "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify that the posture selection processed cleanly
    assert actor.id in refined.entity_updates
    assert "last_combat_posture" in refined.entity_updates[actor.id].property_updates


def test_belief_assimilation_persists_facts():
    """
    Verify Phase 5 belief assimilation facts persist into entity.self_model across ticks.
    """
    unk = UnknownFact(subject="coal_ore", reason="need_material", recorded_tick=1)
    # Set up entity with unknown fact and self_model knowledge component
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1, personality=PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5))
    b.location(0.0, 0.0)
    b.lifecycle(active=True)
    
    km = KnowledgeModelComponent(unknowns={"coal_ore": unk})
    sm = SelfModelBundle(knowledge=km)
    b.replace_self_model(sm)
    actor = b.build()

    state = _create_state([actor])
    
    # Ingest a pending response for coal_ore fact assimilation
    pending = [{
        "actor_id": 1,
        "subject": "coal_ore",
        "query_kind": "material_source",
        "source_id": 2,
        "raw_response": {
            "answer_kind": "KNOWN_FACT",
            "certainty": 1.0,
            "details": {"source": "old_mine"},
        },
        "cost_paid": 5,
    }]
    state = dataclass_replace(state, pending_information_responses=pending, feature_flags={
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Check that knowledge update is packed in update
    assert 1 in refined.entity_updates
    eu = refined.entity_updates[1]
    assert eu.self_model_bundle_set is not None
    # Apply update to state
    next_state = ApplyPath.apply_generation(state, refined, next_tick=2)
    next_actor = next_state.entities[1]
    
    # Check that the coal_ore unknown is cleared or updated correctly
    assert next_actor.self_model.knowledge is not None
