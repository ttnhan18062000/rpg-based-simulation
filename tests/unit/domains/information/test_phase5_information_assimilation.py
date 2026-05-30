"""
tests/unit/domains/information/test_phase5_information_assimilation.py

Phase 5 — InformationAssimilationService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent
from src.core.self_model import SelfModelBundle
from src.domains.information.schema import InformationQuery
from src.domains.information.normalizer import InformationResponseNormalizer
from src.domains.information.assimilation import InformationAssimilationService


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def test_assimilate_known_fact_updates_knowledge_model():
    actor = _entity(1)
    
    q = InformationQuery(subject="iron_ore", kind="material_source")
    raw = {
        "answer_kind": "KNOWN_FACT",
        "certainty": 0.95,
        "details": {"location": "old_mine"},
    }
    
    response = InformationResponseNormalizer.normalize(q, "guide_1", raw)
    result = InformationAssimilationService.assimilate(actor, response, current_tick=10)
    
    assert result.knowledge_update is not None
    assert "iron_ore" in result.knowledge_update.facts
    assert result.knowledge_update.facts["iron_ore"].details.get("location") == "old_mine"
    assert result.knowledge_update.last_updated_tick == 10
