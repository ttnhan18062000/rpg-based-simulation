"""
tests/unit/domains/information/test_phase5_belief_route_impact.py

Phase 5 — BeliefRouteImpactService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.domains.information.schema import InformationAssimilationResult
from src.domains.information.route_impact import BeliefRouteImpactService


def test_known_fact_boosts_gather_route():
    eb = V2EntityBuilder(1)
    entity_before = eb.build()
    entity_after = eb.build()
    
    res = InformationAssimilationResult(
        knowledge_update=None,
        strategic_update=None,
        source_trust_update=None,
        trace={"answer_kind": "KNOWN_FACT"},
    )
    
    hint = BeliefRouteImpactService.evaluate_impact(entity_before, entity_after, res)
    
    assert "gather_resource" in hint.boosted_route_families
    assert "unknown_material_source" in hint.resolved_blockers


def test_partial_lead_boosts_scout_route():
    eb = V2EntityBuilder(1)
    entity_before = eb.build()
    entity_after = eb.build()
    
    res = InformationAssimilationResult(
        knowledge_update=None,
        strategic_update=None,
        source_trust_update=None,
        trace={"answer_kind": "PARTIAL_LEAD"},
    )
    
    hint = BeliefRouteImpactService.evaluate_impact(entity_before, entity_after, res)
    
    assert "scout_location" in hint.boosted_route_families
    assert len(hint.new_blockers) == 1
