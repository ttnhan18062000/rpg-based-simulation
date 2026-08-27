"""
tests/unit/domains/information/test_phase5_observation_belief_bridge.py

Phase 5 — ObservationBeliefBridge unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.strategic import LeadState, LeadCertainty, StrategicComponent
from src.domains.information.bridge import ObservationBeliefBridge


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def test_observed_resource_creates_precise_fact():
    actor = _entity(1)
    state = _state([actor])
    
    event = {
        "kind": "resource_seen",
        "subject": "iron_ore",
        "details": {"location": "old_mine", "charges": 10},
    }
    
    result = ObservationBeliefBridge.process_observation(actor, event, state)

    assert result.knowledge_update is not None
    assert "iron_ore" in result.knowledge_update.facts
    fact = result.knowledge_update.facts["iron_ore"]
    assert fact.certainty == 1.0
    assert fact.details.get("location") == "old_mine"


def _entity_with_lead(e_id, lead):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.replace_strategic(StrategicComponent(leads={lead.id: lead}))
    return b.build()


def test_claim_failed_search_routes_through_belief_contradiction_service():
    """Step 5 fix: claim_failed_search now calls BeliefContradictionService.detect()
    and applies the result as a typed StrategicUpdate, not a direct mutation."""
    lead = LeadState(
        id="lead_1", kind="location", subject="moon_resin", detail="north_ruin",
        certainty=LeadCertainty.APPROXIMATE,
    )
    actor = _entity_with_lead(1, lead)
    state = _state([actor])

    event = {
        "kind": "claim_failed_search",
        "subject": "moon_resin",
        "location_searched": "north_ruin",
        "lead_id": "lead_1",
    }
    result = ObservationBeliefBridge.process_observation(actor, event, state)

    assert result.strategic_update is not None
    assert len(result.strategic_update.leads_add_or_update) == 1
    failed_lead = result.strategic_update.leads_add_or_update[0]
    assert failed_lead.id == "lead_1"
    assert failed_lead.certainty == LeadCertainty.EXHAUSTED
    assert failed_lead.test_outcome == "FAILURE"
    assert failed_lead.tested is True
    assert failed_lead.failure_count == 1


def test_region_danger_seen_routes_through_belief_contradiction_service():
    """Step 5 fix: region_danger_seen now calls BeliefContradictionService.detect()."""
    lead = LeadState(
        id="lead_2", kind="location", subject="safe_road", detail="bandit_road",
        certainty=LeadCertainty.VAGUE,
    )
    actor = _entity_with_lead(1, lead)
    state = _state([actor])

    event = {
        "kind": "region_danger_seen",
        "subject": "safe_road",
        "region_id": "bandit_road",
    }
    result = ObservationBeliefBridge.process_observation(actor, event, state)

    assert result.strategic_update is not None
    failed_lead = result.strategic_update.leads_add_or_update[0]
    assert failed_lead.id == "lead_2"
    assert failed_lead.certainty == LeadCertainty.EXHAUSTED
    assert failed_lead.test_outcome == "FAILURE"


def test_claim_failed_search_no_op_when_no_contradiction():
    """No matching lead → no strategic_update, no mutation (mirrors LeadContradictionSystem's
    own skip-when-not-contradicted behavior)."""
    actor = _entity(1)
    state = _state([actor])

    event = {
        "kind": "claim_failed_search",
        "subject": "unrelated_subject",
        "location_searched": "nowhere",
    }
    result = ObservationBeliefBridge.process_observation(actor, event, state)

    assert result.strategic_update is None
