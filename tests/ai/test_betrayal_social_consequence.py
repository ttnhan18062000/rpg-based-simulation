import pytest
from unittest.mock import MagicMock
from src.ai.states.base import AIContext
from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService
from src.core.models.strategy import RecruitmentOfferRecord, ProjectRecord
from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind, OfferStatus, ContractKind
from src.core.models.vectors import Vector2

@pytest.fixture
def base_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 300
    
    # Recruiter (Founder)
    recruiter = MagicMock()
    recruiter.id = 1
    recruiter.identity.reputation.trustworthiness = 5.0 # Neutral
    recruiter.identity.reputation.heroism_score = 0.0
    recruiter.combat.alive = True
    
    # Candidate
    candidate = MagicMock()
    candidate.id = 2
    candidate.mind.social.known_bonds = {}
    candidate.mind.decision.personality.greed = 0.5
    candidate.mind.decision.motives = []
    candidate.combat.hp_ratio = 1.0
    candidate.mind.strategic.concerns = []
    candidate.mind.strategic.directives = []
    candidate.mind.narrative.turning_points = []
    
    ctx.actor = candidate
    ctx.snapshot.entities = {1: recruiter, 2: candidate}
    return ctx

def test_betrayal_social_consequence(base_ctx):
    """Verify that private betrayal trauma prevents recruitment even for reputable founders."""
    candidate = base_ctx.actor
    recruiter = base_ctx.snapshot.entities[1]
    
    from src.core.models.enums import ProjectKind
    project = ProjectRecord(project_id="prj_1", label="Testing Project", priority=3.0, kind=ProjectKind.QUEST)
    
    # 1. Base Case: Neutral acceptance
    # (High payout to ensure acceptance in normal conditions)
    offer = RecruitmentOfferRecord(
        offer_id="off_1",
        recruiter_id=recruiter.id,
        candidate_id=candidate.id,
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING,
        proposed_terms=[{"term_type": "payout", "label": "Payout", "params": {"value": 0.6}}] # 60% share
    )
    
    appraisal = RecruitmentNegotiationService.evaluate_offer(base_ctx, offer)
    assert appraisal.status == OfferStatus.ACCEPTED
    
    # 2. General Betrayal Trauma (Someone else betrayed us)
    tp_general = TurningPointRecord(
        event_id="evt_beta_1",
        kind=TurningPointKind.BETRAYAL,
        tick=100,
        involved_entity_ids=[999], # Stranger
        summary_tag="Betrayed by a stranger"
    )
    candidate.mind.narrative.turning_points = [tp_general]
    
    appraisal_trauma = RecruitmentNegotiationService.evaluate_offer(base_ctx, offer)
    assert appraisal_trauma.status == OfferStatus.DECLINED
    
    # 3. Direct Betrayal (THIS recruiter betrayed us)
    tp_direct = TurningPointRecord(
        event_id="evt_beta_2",
        kind=TurningPointKind.BETRAYAL,
        tick=200,
        involved_entity_ids=[recruiter.id],
        summary_tag="Betrayed by THIS recruiter"
    )
    candidate.mind.narrative.turning_points = [tp_direct]
    
    appraisal_direct = RecruitmentNegotiationService.evaluate_offer(base_ctx, offer)
    assert appraisal_direct.status == OfferStatus.DECLINED
    assert "past betrayal" in appraisal_direct.reason.lower()
    
    print("Social Social Consequence Test Passed: Betrayal trauma correctly biases recruitment.")
