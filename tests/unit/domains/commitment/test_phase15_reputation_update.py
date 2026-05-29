import pytest
from src.core.cognition import PublicReputationProfile
from src.domains.commitment.reputation import ReputationUpdateService

def test_reputation_update_service():
    profile = PublicReputationProfile(labels={"reliable": 0.5})
    
    # Successful escort
    updated_1 = ReputationUpdateService.process_witnessed_event(profile, "successful_escort")
    assert updated_1.labels["reliable"] > 0.5
    
    # Betrayal
    updated_2 = ReputationUpdateService.process_witnessed_event(profile, "betrayal")
    assert updated_2.labels.get("betrayer", 0.0) > 0.0
