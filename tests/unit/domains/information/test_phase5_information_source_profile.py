"""
tests/unit/domains/information/test_phase5_information_source_profile.py

Phase 5 — InformationSourceProfile unit tests.
Verifies semantic constraints of blacksmith, guide, and scope matching.
"""

import pytest
from src.domains.information.schema import InformationSourceProfile


def test_blacksmith_scope_definition():
    prof = InformationSourceProfile(
        source_id="smithy_1",
        source_kind="blacksmith",
        knowledge_scopes=("recipe_requirements",),
        accuracy=0.95,
        freshness=1.0,
        cost_gold=5,
    )
    
    assert prof.source_id == "smithy_1"
    assert prof.source_kind == "blacksmith"
    assert "recipe_requirements" in prof.knowledge_scopes
    assert "rare_resource_hints" not in prof.knowledge_scopes
    assert prof.accuracy == 0.95
    assert prof.cost_gold == 5


def test_guide_scope_definition():
    prof = InformationSourceProfile(
        source_id="guide_1",
        source_kind="guide",
        knowledge_scopes=("common_resource_sources", "service_locations"),
        accuracy=0.85,
        freshness=0.9,
    )
    
    assert "common_resource_sources" in prof.knowledge_scopes
    assert "recipe_requirements" not in prof.knowledge_scopes
