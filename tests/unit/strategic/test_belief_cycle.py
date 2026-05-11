"""
Contract tests for Belief Cycle.

Covers:
- LEG-RPG-150: Belief cycle (Rumors)
- LEG-RPG-125: Contradiction degrades certainty
"""
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import EntityState
from src.core.strategic import (
    StrategicComponent, LeadState, LeadCertainty, HypothesisState, ConcernState
)
from src.systems.strategic_systems.belief import BeliefCycleSystem


def _make_entity_with_leads(leads=None, hypotheses=None, concerns=None):
    return (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(leads=leads or {},      
                        hypotheses=hypotheses or {},
                        concerns=concerns or {}
        )
        .build())


class TestBeliefDecay:
    """LEG-RPG-150: Beliefs decay over time."""

    def test_fresh_leads_not_decayed(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.APPROXIMATE, discovered_tick=90)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.decay_stale_beliefs(entity, current_tick=100)
        assert len(result.leads_add_or_update) == 0

    def test_stale_approximate_decays_to_vague(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.APPROXIMATE, discovered_tick=10)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.decay_stale_beliefs(entity, current_tick=100)
        assert len(result.leads_add_or_update) == 1
        assert result.leads_add_or_update[0].certainty == LeadCertainty.VAGUE

    def test_stale_vague_decays_to_exhausted(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.VAGUE, discovered_tick=10)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.decay_stale_beliefs(entity, current_tick=100)
        assert len(result.leads_add_or_update) == 1
        assert result.leads_add_or_update[0].certainty == LeadCertainty.EXHAUSTED

    def test_precise_observations_do_not_decay(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.PRECISE, discovered_tick=10)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.decay_stale_beliefs(entity, current_tick=100)
        assert len(result.leads_add_or_update) == 0


class TestRumors:
    """LEG-RPG-150: Rumors have lower certainty than observation."""

    def test_rumor_creates_vague_lead(self):
        entity = _make_entity_with_leads()
        result = BeliefCycleSystem.process_rumor(
            entity, rumor_subject="treasure", rumor_detail="cave to the north",
            source_entity_id=42, current_tick=50
        )
        assert len(result.leads_add_or_update) == 1
        lead = result.leads_add_or_update[0]
        assert lead.certainty == LeadCertainty.VAGUE
        assert lead.source_entity_id == 42

    def test_observation_creates_precise_lead(self):
        entity = _make_entity_with_leads()
        result = BeliefCycleSystem.process_observation(
            entity, subject="enemy_camp", detail="visible at (10,10)", current_tick=50
        )
        assert len(result.leads_add_or_update) == 1
        assert result.leads_add_or_update[0].certainty == LeadCertainty.PRECISE


class TestContradiction:
    """LEG-RPG-125: Contradiction degrades certainty."""

    def test_contradiction_demotes_precise_to_approximate(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.PRECISE)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.apply_contradiction(entity, "l1", "no gold found")
        assert len(result.leads_add_or_update) == 1
        assert result.leads_add_or_update[0].certainty == LeadCertainty.APPROXIMATE

    def test_contradiction_demotes_vague_to_exhausted(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.VAGUE)}
        entity = _make_entity_with_leads(leads=leads)
        result = BeliefCycleSystem.apply_contradiction(entity, "l1", "no gold found")
        assert result.leads_add_or_update[0].certainty == LeadCertainty.EXHAUSTED

    def test_contradiction_degrades_supporting_hypotheses(self):
        leads = {"l1": LeadState(id="l1", kind="location", subject="gold",
                                  certainty=LeadCertainty.APPROXIMATE)}
        hyps = {"h1": HypothesisState(
            id="h1", subject="gold_mine", claim="gold mine exists north",
            confidence=0.7, supporting_lead_ids=["l1"]
        )}
        entity = _make_entity_with_leads(leads=leads, hypotheses=hyps)
        result = BeliefCycleSystem.apply_contradiction(entity, "l1", "area empty")
        assert len(result.hypotheses_add_or_update) == 1
        assert result.hypotheses_add_or_update[0].confidence < 0.7

    def test_nonexistent_lead_returns_empty(self):
        entity = _make_entity_with_leads()
        result = BeliefCycleSystem.apply_contradiction(entity, "nonexistent", "evidence")
        assert len(result.leads_add_or_update) == 0


class TestThreatEstimation:
    """LEG-RPG-150: Threat estimation from belief state."""

    def test_danger_concern_raises_threat(self):
        concerns = {"c1": ConcernState(id="c1", kind="danger", source="swamp", urgency=0.8)}
        entity = _make_entity_with_leads(concerns=concerns)
        threat = BeliefCycleSystem.estimate_threat(entity, "swamp")
        assert threat > 0.5

    def test_no_beliefs_zero_threat(self):
        entity = _make_entity_with_leads()
        threat = BeliefCycleSystem.estimate_threat(entity, "plains")
        assert threat == 0.0
