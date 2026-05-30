import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import (
    CognitionModel, SubjectiveModel, PerceptionModel, PerceivedEntity,
    TemporalModel, DeadlineEntry, MemoryModel, CausalMemory, CausalMemoryEntry,
    MotivationModel, IdentityDoctrine, ValuePreferenceProfile,
    CommitmentModel, CommitmentEntry, RelationshipModel, PublicReputationProfile
)
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
