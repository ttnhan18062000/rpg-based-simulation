import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent
from src.core.cognition import (
    CognitionModel, SubjectiveModel, PerceptionModel, PerceivedEntity,
    TemporalModel, DeadlineEntry, MemoryModel, CausalMemory, CausalMemoryEntry,
    RoleModelBundle
)
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.domains.optimization.feature_flags import FeatureMode

# TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT (2026-09-08): removed
# test_cognition_hierarchy_e2e_smoke, which exercised the now-deleted MotivationBiasService/
# IdentityDoctrine/ValuePreferenceProfile chain (confirmed dead in production, see
# docs/guidelines/intentional_divergences.md §2.53). No replacement needed -- the real live
# path (AdventureRouteScorer.score()'s personality_bias) has its own coverage in
# tests/unit/domains/adventure/.


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
