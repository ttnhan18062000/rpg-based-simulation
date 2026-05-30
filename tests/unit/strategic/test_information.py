import pytest
from src.core.builder import V2EntityBuilder
from src.world.providers.information import (
    InformationQuery, GuideInformationProvider, BlacksmithInformationProvider
)


def test_guide_query_normal_resource():
    """Verify Guide queries return exact facts for common resources without charging gold."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=5)
        .build())
        
    query = InformationQuery(kind="material_source", subject="wood", actor_id=1)
    res = GuideInformationProvider.query(ent, query)
    
    assert res.answer_kind == "known"
    assert res.cost_gold == 0
    assert len(res.facts) == 1
    assert res.facts[0].fact_type == "resource_source"
    assert "near_forest" in res.facts[0].details["source_regions"]


def test_guide_query_secret_resource_gold_gates():
    """Verify Guide queries for secret moon_resin require gold and return partial suggested leads."""
    # 1. Test insufficient gold
    ent_poor = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=5)
        .build())
    query = InformationQuery(kind="material_source", subject="moon_resin", actor_id=1)
    res_poor = GuideInformationProvider.query(ent_poor, query)
    assert res_poor.answer_kind == "insufficient_gold"
    assert res_poor.cost_gold == 10

    # 2. Test sufficient gold & partial redirect
    ent_rich = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=20)
        .build())
    res_rich = GuideInformationProvider.query(ent_rich, query)
    assert res_rich.answer_kind == "partial"
    assert res_rich.cost_gold == 10
    assert len(res_rich.suggested_leads) == 1
    assert res_rich.suggested_leads[0].detail == "north_ruin"


def test_blacksmith_recipe_query():
    """Verify Blacksmith recipe requirements query returns the seeded item materials."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
        
    query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
    res = BlacksmithInformationProvider.query(ent, query)
    
    assert res.answer_kind == "known"
    assert len(res.facts) == 1
    assert res.facts[0].details["requires_items"]["iron_ore"] == 2
