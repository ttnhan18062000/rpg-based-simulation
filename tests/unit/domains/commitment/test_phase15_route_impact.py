import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, CommitmentModel, CommitmentEntry, PublicReputationProfile, RelationshipModel
from src.domains.commitment.impact import CommitmentReputationRouteImpact

def test_commitment_route_impact():
    # Active quest commitment
    entry = CommitmentEntry(
        id="quest_1",
        kind="escort",
        target_id="npc_2",
        strength=0.8,
        deadline_tick=100,
        created_tick=10
    )
    commitment = CommitmentModel(active_commitments={"quest_1": entry})
    cognition = CognitionModel(commitment=commitment)
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)

    # Scored related route tags
    assert CommitmentReputationRouteImpact.apply_route_bias(entity, ["escort"], 1.0) > 1.0
    # Scored unrelated route tags
    assert CommitmentReputationRouteImpact.apply_route_bias(entity, ["loot"], 1.0) == 1.0
