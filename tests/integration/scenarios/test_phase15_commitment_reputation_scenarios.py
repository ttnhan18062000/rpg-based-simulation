import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, CommitmentModel, CommitmentEntry, PublicReputationProfile, RelationshipModel, ValuePreferenceProfile, MotivationModel
from src.domains.commitment.pressure import CommitmentPressureService
from src.domains.commitment.abandonment import AbandonmentEvaluator
from src.domains.commitment.reputation import ReputationUpdateService
from src.domains.commitment.impact import CommitmentReputationRouteImpact

def test_accepted_escort_prevents_minor_loot_switch():
    # Setup entity with active escort commitment
    entry = CommitmentEntry(
        id="escort_1",
        kind="escort",
        target_id="villager_1",
        strength=0.8,
        deadline_tick=100,
        created_tick=10
    )
    commitment = CommitmentModel(active_commitments={"escort_1": entry})
    cognition = CognitionModel(commitment=commitment)
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)

    # Base score of route options
    base_escort_score = 1.0
    base_loot_score = 1.2 # loot option is slightly higher initially

    # Apply route bias
    escort_score = CommitmentReputationRouteImpact.apply_route_bias(entity, ["escort"], base_escort_score)
    loot_score = CommitmentReputationRouteImpact.apply_route_bias(entity, ["loot"], base_loot_score)

    # Commitment should boost escort route higher than the slight loot advantage
    assert escort_score > loot_score

def test_abandoning_party_changes_future_partner_selection():
    # Evaluate a bad abandonment
    eval_res = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=True, is_greed_driven=True
    )
    assert eval_res["is_betrayal"] is True
    
    # Process betrayal event to update public reputation
    profile = PublicReputationProfile(labels={"reliable": 0.6})
    updated_profile = ReputationUpdateService.process_witnessed_event(profile, "betrayal")
    assert updated_profile.labels.get("betrayer", 0.0) == 0.4
    assert updated_profile.labels.get("reliable", 0.0) == 0.3

    # Fit score calculation for a third party
    fit_score = CommitmentReputationRouteImpact.apply_partner_fit_bias(
        entity=EntityState(id=2, kind="HERO"),
        candidate_reputation=updated_profile.labels,
        base_fit=1.0
    )
    # Fit score is significantly penalized due to the candidate's betrayer label
    assert fit_score < 0.5
