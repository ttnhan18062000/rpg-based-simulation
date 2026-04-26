import pytest
from src_legacy.core.state import EntityState, IdentityComponent, AttributeComponent
from src_legacy.core.strategic import StrategicComponent, CognitionProfile, LeadCertainty, SourceTrustEntry
from src_legacy.strategy.leads import LeadService

def create_mock_entity_with_trust(trust_scores: dict[int, float]):
    strat = StrategicComponent(
        profile=CognitionProfile(max_leads=5),
        source_trust={eid: SourceTrustEntry(entity_id=eid, trust=score) for eid, score in trust_scores.items()}
    )
    return EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        attributes=AttributeComponent(),
        identity=IdentityComponent(),
        strategic=strat
    )

def test_lead_creation_with_trust():
    entity = create_mock_entity_with_trust({10: 0.9, 11: 0.1})
    
    # Trusted source -> PRECISE
    lead1 = LeadService.create_lead(entity, "location", "secret_cave", source_id=10, tick=100)
    assert lead1.certainty == LeadCertainty.PRECISE
    assert lead1.source_entity_id == 10
    
    # Untrusted source -> VAGUE
    lead2 = LeadService.create_lead(entity, "location", "rumored_inn", source_id=11, tick=101)
    assert lead2.certainty == LeadCertainty.VAGUE

def test_lead_capacity_limit():
    entity = create_mock_entity_with_trust({})
    # Max leads is 5 in mock
    for i in range(5):
        entity.strategic.leads[f"L{i}"] = LeadService.create_lead(entity, "test", str(i))
        
    # 6th lead should be None
    lead6 = LeadService.create_lead(entity, "test", "6")
    assert lead6 is None

def test_lead_outcome_evaluation():
    lead = LeadService.create_lead(create_mock_entity_with_trust({}), "location", "target", tick=100)
    
    # Success
    updated_success = LeadService.evaluate_lead_outcome(lead, success=True)
    assert updated_success.tested is True
    assert updated_success.test_outcome == "SUCCESS"
    
    # Failure
    updated_fail = LeadService.evaluate_lead_outcome(lead, success=False)
    assert updated_fail.certainty == LeadCertainty.EXHAUSTED
    assert updated_fail.test_outcome == "FAILURE"
