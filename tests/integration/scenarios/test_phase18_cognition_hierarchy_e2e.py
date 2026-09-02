import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent
from src.core.cognition import (
    CognitionModel, SubjectiveModel, PerceptionModel, PerceivedEntity,
    TemporalModel, DeadlineEntry, MemoryModel, CausalMemory, CausalMemoryEntry,
    MotivationModel, IdentityDoctrine, ValuePreferenceProfile,
    CommitmentModel, CommitmentEntry, RelationshipModel, PublicReputationProfile,
    RoleModelBundle
)
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.domains.optimization.feature_flags import FeatureMode
from src.domains.motivation.service import MotivationBiasService
from src.domains.commitment.impact import CommitmentReputationRouteImpact
from src.observability.trace import DecisionTrace, DecisionOptionTrace, RejectedOptionTrace
from src.observability.validator import DecisionTraceValidator

def test_cognition_hierarchy_e2e_smoke():
    # 1. Setup nested whitelisted CognitionModel hierarchy
    doctrine = IdentityDoctrine(class_id="warrior", preferred_route_tags={"melee": 0.5})
    values = ValuePreferenceProfile(survival=0.8)
    motivation = MotivationModel(doctrine=doctrine, values=values)
    
    entry = CommitmentEntry(id="quest_1", kind="escort", strength=0.8, created_tick=1)
    commitment = CommitmentModel(active_commitments={"quest_1": entry})
    
    cognition = CognitionModel(motivation=motivation, commitment=commitment)
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)

    # 2. Evaluate motivational biases and commitment boosts together
    route_tags = ["melee", "escort"]
    scored = 1.0
    scored = MotivationBiasService.compute_bias_multiplier(entity, route_tags) * scored
    scored = CommitmentReputationRouteImpact.apply_route_bias(entity, route_tags, scored)

    # Scored value is boosted correctly
    assert scored > 1.0

    # 3. Decision Trace validates STRICTLY
    trace = DecisionTrace(
        decision_id="dec_e2e_1",
        entity_id=1,
        decision_kind="strategic_route",
        noticed=("quest_target",),
        known=(),
        needs=("quest_fulfillment",),
        capability_refs=(),
        considered_options=(DecisionOptionTrace(name="escort_route", score=scored),),
        selected_option="escort_route",
        rejected_options=(),
        reason="high_commitment_pressure",
        expected_effects=("victory",)
    )
    
    assert DecisionTraceValidator.validate(trace, mode="STRICT") is True


def test_cognition_bundle_set_apply_round_trip_includes_role_model():
    """TCK-20260831-ROLE-MODEL-IMITATION: RoleModelBundle rides through the existing wholesale
    `cognition` passthrough in ApplyPath._fast_replace_entity (src/engine/apply.py:611) with zero
    apply.py/patches.py changes -- this is the concrete proof, not an assumption."""
    entity = EntityState(id=1, kind="HERO", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    state = AuthoritativeState(tick=1, seed=1, world_time=100, entities={1: entity})

    staged_cognition = CognitionModel(role_model=RoleModelBundle(
        admired_entity_id=99, admired_since_tick=1, last_reconsidered_tick=1, imitation_fidelity=1.0
    ))
    e_upd = EntityUpdate(entity_id=1, cognition_bundle_set=staged_cognition)
    update = StateUpdate(entity_updates={1: e_upd}, force_full_scan=True)

    new_state = ApplyPath.apply_generation(state, update, next_tick=2, cadence=SystemCadence())
    result_entity = new_state.entities[1]

    assert result_entity.cognition == staged_cognition
    assert result_entity.cognition.role_model.admired_entity_id == 99
    assert result_entity.cognition.role_model.admired_since_tick == 1
    assert result_entity.cognition.role_model.last_reconsidered_tick == 1
    assert result_entity.cognition.role_model.imitation_fidelity == 1.0


def test_role_model_imitation_flag_defaults_off_and_phase_does_not_run():
    """DEV-002 sentinel: ENABLE_ROLE_MODEL_IMITATION defaults OFF, so RoleModelSelectionPhase
    must not run (and must not stage a role_model change) through the real pipeline unless the
    flag is explicitly turned ON -- mirrors
    test_habit_bias_pipeline_wiring.py::test_habit_bias_action_style_flag_gates_pipeline_phase."""
    from src.engine.pipeline import AuthoritativeApplyPipeline

    watcher = EntityState(id=1, kind="HERO", identity=replace(EntityState(id=1, kind="HERO").identity, evolution_level=1))
    admired = EntityState(id=2, kind="HERO", identity=replace(EntityState(id=2, kind="HERO").identity, evolution_level=5))

    state_off = AuthoritativeState(tick=9, seed=1, entities={1: watcher, 2: admired})
    refined_off = AuthoritativeApplyPipeline.refine(state_off, StateUpdate())
    entity_update_off = refined_off.entity_updates.get(1)
    assert (
        entity_update_off is None
        or entity_update_off.cognition_bundle_set is None
        or entity_update_off.cognition_bundle_set.role_model.admired_entity_id is None
    )

    state_on = AuthoritativeState(
        tick=9, seed=1, entities={1: watcher, 2: admired},
        feature_flags={"ENABLE_ROLE_MODEL_IMITATION": "ON"},
    )
    refined_on = AuthoritativeApplyPipeline.refine(state_on, StateUpdate())
    cognition_on = refined_on.entity_updates[1].cognition_bundle_set
    assert cognition_on is not None
    assert cognition_on.role_model.admired_entity_id == 2
