"""
tests/integration/scenarios/test_phase5_information_belief_scenarios.py

Phase 5 — Scenario-driven integration tests for Information, Belief, and Source-Trust loop.
Verifies Scenarios 5.1 to 5.6.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact, KnowledgeFact
from src.core.strategic import StrategicComponent, LeadState, LeadCertainty, SourceTrustEntry
from src.domains.information.schema import InformationQuery, InformationSourceProfile
from src.domains.information.router import InformationQueryRouter
from src.domains.information.normalizer import InformationResponseNormalizer
from src.domains.information.assimilation import InformationAssimilationService
from src.domains.information.contradiction import BeliefContradictionService
from src.domains.information.trust import SourceTrustUpdateService
from src.domains.information.bridge import ObservationBeliefBridge
from src.domains.information.route_impact import BeliefRouteImpactService


def _entity(e_id, x=0.0, y=0.0, unknowns=None, facts=None, source_trust=None, leads=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(x, y)
    
    km = KnowledgeModelComponent(unknowns=unknowns or {}, facts=facts or {})
    sm = SelfModelBundle(knowledge=km)
    b.replace_self_model(sm)
    
    sc = StrategicComponent(source_trust=source_trust or {}, leads=leads or {})
    b.replace_strategic(sc)
    
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


def test_scenario_5_1_common_material_source_learned_from_guide():
    actor = _entity(1)
    guide = _entity(2)
    state = _state([actor, guide])
    
    q = InformationQuery(subject="iron_ore", kind="material_source")
    raw = {
        "answer_kind": "KNOWN_FACT",
        "certainty": 0.9,
        "details": {"location": "old_mine"},
    }
    
    # Guide query response
    response = InformationResponseNormalizer.normalize(q, 2, raw, current_tick= state.tick)
    result = InformationAssimilationService.assimilate(actor, response, state.tick)
    
    assert result.knowledge_update is not None
    assert "iron_ore" in result.knowledge_update.facts
    assert result.knowledge_update.facts["iron_ore"].details.get("location") == "old_mine"


def test_scenario_5_2_rare_material_partial_lead():
    actor = _entity(1)
    guide = _entity(2)
    state = _state([actor, guide])
    
    q = InformationQuery(subject="moon_resin", kind="material_source")
    raw = {
        "answer_kind": "PARTIAL_LEAD",
        "certainty": 0.6,
        "details": {"clue_location": "north_ruin"},
    }
    
    response = InformationResponseNormalizer.normalize(q, 2, raw, current_tick=state.tick)
    result = InformationAssimilationService.assimilate(actor, response, state.tick)
    
    # Exact source remains unknown (not in facts), but registered in strategic leads
    assert "moon_resin" not in result.knowledge_update.facts
    assert len(result.strategic_update.leads_add_or_update) == 1
    assert result.strategic_update.leads_add_or_update[0].certainty == LeadCertainty.APPROXIMATE


def test_scenario_5_3_contradicted_rumor_changes_route():
    # Traveler gives rumor
    lead = LeadState(
        id="lead_moon_resin",
        kind="location",
        subject="moon_resin",
        detail="north_ruin",
        certainty=LeadCertainty.APPROXIMATE,
    )
    actor = _entity(1, leads={"lead_moon_resin": lead})
    state = _state([actor])
    
    obs = {
        "kind": "claim_failed_search",
        "subject": "moon_resin",
        "location_searched": "north_ruin",
    }
    
    res = BeliefContradictionService.detect(actor, obs, state)
    
    assert res.contradiction_detected is True
    assert res.new_certainty == LeadCertainty.EXHAUSTED


def test_scenario_5_4_direct_observation_overrides_rumor():
    actor = _entity(1)
    state = _state([actor])
    
    event = {
        "kind": "resource_seen",
        "subject": "iron_ore",
        "details": {"location": "old_mine"},
    }
    
    result = ObservationBeliefBridge.process_observation(actor, event, state)
    assert result.knowledge_update.facts["iron_ore"].certainty == 1.0


def test_scenario_5_5_two_sources_disagree():
    # Setup guide safety and traveler danger claims
    q = InformationQuery(subject="north_road", kind="danger_rating")
    
    raw_guide = {"answer_kind": "KNOWN_FACT", "certainty": 0.8, "details": {"status": "safe"}}
    raw_traveler = {"answer_kind": "KNOWN_FACT", "certainty": 0.4, "details": {"status": "dangerous"}}
    
    res_guide = InformationResponseNormalizer.normalize(q, 2, raw_guide)
    res_traveler = InformationResponseNormalizer.normalize(q, 3, raw_traveler)
    
    # Conflict checks: guide certainty > traveler certainty
    assert res_guide.certainty > res_traveler.certainty


def test_scenario_5_6_source_trust_affects_query_choice():
    # Trusting guide (trust = 0.8) vs traveler (trust = 0.3)
    trust_guide = SourceTrustEntry(entity_id=2, trust=0.8)
    trust_traveler = SourceTrustEntry(entity_id=3, trust=0.3)
    
    actor = _entity(1, source_trust={2: trust_guide, 3: trust_traveler})
    state = _state([actor])
    
    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.9,
            freshness=0.9,
        ),
        InformationSourceProfile(
            source_id=3,
            source_kind="traveler",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.9,
            freshness=0.9,
        ),
    ]
    
    q = InformationQuery(subject="iron_ore", kind="material_source")
    candidates = InformationQueryRouter.route(actor, q, state, profiles)
    
    # High-trust guide must be sorted first
    assert candidates[0].source_id == 2
