"""
tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py

Phase 4 — EngagementRiskEvaluator unit tests.
Verifies subjective risk evaluations, uncertainty penalty, and personality tolerance.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent
from src.domains.combat_engagement.schema import PerceivedOpponentEstimate, SelfCombatEstimate
from src.domains.combat_engagement.risk_evaluator import EngagementRiskEvaluator


def _entity(bravery=0.5, greed=0.5, grudges=None):
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    
    p = PersonalityComponent(greed=greed, bravery=bravery, sociability=0.5, industry=0.5)
    props = {}
    if grudges:
        props["grudges"] = grudges
        
    b.identity(evolution_level=1, personality=p, properties=props)
    return b.build()


def test_equal_power_high_uncertainty_prefers_probe_or_watch():
    actor = _entity(bravery=0.5)
    
    opp_est = PerceivedOpponentEstimate(target_id=2, estimated_power=30.0, uncertainty=0.6, confidence=0.4)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    eval_res = EngagementRiskEvaluator.evaluate(actor, opp_est, self_est)
    
    # Acceptability is likely false or low due to uncertainty penalty
    assert "high_uncertainty_penalty" in eval_res.reasons


def test_low_hp_increases_death_risk():
    actor = _entity(bravery=0.5)
    
    opp_est = PerceivedOpponentEstimate(target_id=2, estimated_power=30.0, uncertainty=0.1, confidence=0.9)
    # Actor is near_death
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=10.0, confidence=0.2, constraints=("near_death",))
    
    eval_res = EngagementRiskEvaluator.evaluate(actor, opp_est, self_est)
    
    assert eval_res.death_risk >= 0.8
    assert "near_death_alert" in eval_res.reasons
    assert not eval_res.acceptable


def test_brave_trait_increases_risk_tolerance():
    actor_brave = _entity(bravery=0.9)
    actor_cautious = _entity(bravery=0.1) # derived caution = 0.9
    
    opp_est = PerceivedOpponentEstimate(target_id=2, estimated_power=40.0, uncertainty=0.2, confidence=0.8)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    eval_brave = EngagementRiskEvaluator.evaluate(actor_brave, opp_est, self_est)
    eval_cautious = EngagementRiskEvaluator.evaluate(actor_cautious, opp_est, self_est)
    
    # Brave has higher value score / lower risk score ratio
    assert eval_brave.value_score > eval_cautious.value_score
    assert eval_brave.risk_score < eval_cautious.risk_score


def test_grudge_can_override_caution_with_trace():
    # Cautious actor with a heavy grudge against target 2
    actor = _entity(bravery=0.1, grudges={"2": 80.0})
    
    opp_est = PerceivedOpponentEstimate(target_id=2, estimated_power=45.0, uncertainty=0.1, confidence=0.9)
    self_est = SelfCombatEstimate(actor_id=1, estimated_power=30.0, confidence=0.8)
    
    eval_res = EngagementRiskEvaluator.evaluate(actor, opp_est, self_est)
    
    assert "grudge_vengeance" in eval_res.reasons
    assert eval_res.emotional_bias > 0.3
