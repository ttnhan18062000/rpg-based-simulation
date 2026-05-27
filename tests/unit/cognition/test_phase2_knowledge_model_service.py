"""
tests/unit/cognition/test_phase2_knowledge_model_service.py

Phase 2 — KnowledgeModelService unit tests.

Critical invariant tested: hidden world truth must NOT be leaked.
Only what the provider returned is assimilated.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.world.providers.information import (
    InformationResponse,
    InformationQuery,
    KnowledgeFact as ProviderFact,
    GuideInformationProvider,
    BlacksmithInformationProvider,
    GuildInformationProvider,
)
from src.core.strategic import LeadState, LeadCertainty
from src.cognition.knowledge_model import KnowledgeModelService


def _entity(unknowns=None, facts=None):
    from src.core.self_model import KnowledgeFact as EntityFact
    b = V2EntityBuilder(1)
    km = KnowledgeModelComponent(
        facts=facts or {},
        unknowns=unknowns or {},
    )
    bundle = SelfModelBundle(knowledge=km)
    b.replace_self_model(bundle)
    return b.build()


# ── Blacksmith recipe response ────────────────────────────────────────────────

class TestKnowledgeModelBlacksmith:
    def test_phase2_knowledge_blacksmith_recipe_creates_entity_fact(self):
        entity = _entity()
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)

        result = KnowledgeModelService.assimilate(entity, response, tick=5)
        assert "iron_sword" in result.facts
        assert result.facts["iron_sword"].fact_type == "recipe_definition"

    def test_phase2_knowledge_blacksmith_recipe_certainty_is_preserved(self):
        entity = _entity()
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)

        result = KnowledgeModelService.assimilate(entity, response, tick=5)
        assert result.facts["iron_sword"].certainty == 1.0

    def test_phase2_knowledge_blacksmith_source_id_recorded(self):
        entity = _entity()
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)

        result = KnowledgeModelService.assimilate(entity, response, tick=5)
        assert result.facts["iron_sword"].source_id == "blacksmith_hometown"

    def test_phase2_knowledge_blacksmith_tick_recorded(self):
        entity = _entity()
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)

        result = KnowledgeModelService.assimilate(entity, response, tick=42)
        assert result.facts["iron_sword"].recorded_tick == 42


# ── Guide partial answer (moon_resin) ─────────────────────────────────────────

class TestKnowledgeModelGuidePartial:
    def _query_moon_resin(self, entity):
        from src.core.builder import V2EntityBuilder
        from src.core.models.inventory import InventoryComponent
        # Need gold >=10 to pay for moon_resin query
        rich_entity = V2EntityBuilder(entity.id).replace_self_model(entity.self_model).inventory(gold=50).build()
        query = InformationQuery(kind="material_source", subject="moon_resin", actor_id=1)
        return GuideInformationProvider.query(rich_entity, query), rich_entity

    def test_phase2_knowledge_guide_partial_keeps_moon_resin_unknown(self):
        entity = _entity()
        response, rich_entity = self._query_moon_resin(entity)
        result = KnowledgeModelService.assimilate(rich_entity, response, tick=10)
        # moon_resin.source should remain as unknown
        assert "material.moon_resin.source" in result.unknowns

    def test_phase2_knowledge_guide_partial_records_lead_as_low_certainty_fact(self):
        entity = _entity()
        response, rich_entity = self._query_moon_resin(entity)
        result = KnowledgeModelService.assimilate(rich_entity, response, tick=10)
        # A lead fact should be recorded
        lead_keys = [k for k in result.facts if k.startswith("lead.")]
        assert len(lead_keys) > 0

    def test_phase2_knowledge_guide_partial_lead_certainty_below_full(self):
        entity = _entity()
        response, rich_entity = self._query_moon_resin(entity)
        result = KnowledgeModelService.assimilate(rich_entity, response, tick=10)
        lead_keys = [k for k in result.facts if k.startswith("lead.")]
        for k in lead_keys:
            assert result.facts[k].certainty < 1.0

    def test_phase2_knowledge_hidden_exact_source_not_leaked(self):
        """The guide only returns a lead, not the exact moon_cave location."""
        entity = _entity()
        response, rich_entity = self._query_moon_resin(entity)
        result = KnowledgeModelService.assimilate(rich_entity, response, tick=10)
        # moon_cave must NOT appear in facts as a confirmed, high-certainty fact
        moon_cave_fact = result.facts.get("resource.moon_resin.source")
        if moon_cave_fact:
            assert moon_cave_fact.certainty < 0.8  # not confirmed
        # Also must not have moon_cave in fact details at full confidence
        all_details_str = str(result.facts)
        assert "moon_cave" not in all_details_str  # exact hidden source never injected


# ── Guild danger hint ─────────────────────────────────────────────────────────

class TestKnowledgeModelGuildDanger:
    def test_phase2_knowledge_guild_danger_hint_creates_fact(self):
        entity = _entity()
        query = InformationQuery(kind="regional_danger", subject="near_forest", actor_id=1)
        response = GuildInformationProvider.query(entity, query)
        result = KnowledgeModelService.assimilate(entity, response, tick=7)
        assert "near_forest" in result.facts
        assert result.facts["near_forest"].fact_type == "danger_rating"

    def test_phase2_knowledge_guild_danger_certainty_below_full(self):
        entity = _entity()
        query = InformationQuery(kind="regional_danger", subject="near_forest", actor_id=1)
        response = GuildInformationProvider.query(entity, query)
        result = KnowledgeModelService.assimilate(entity, response, tick=7)
        # Guild info has 0.8 certainty
        assert result.facts["near_forest"].certainty < 1.0


# ── Unknown response ──────────────────────────────────────────────────────────

class TestKnowledgeModelUnknown:
    def test_phase2_knowledge_unknown_response_creates_unknown_fact(self):
        entity = _entity()
        query = InformationQuery(kind="material_source", subject="goblin_tears", actor_id=1)
        response = GuideInformationProvider.query(entity, query)
        result = KnowledgeModelService.assimilate(entity, response, tick=3)
        assert "goblin_tears" in result.unknowns

    def test_phase2_knowledge_unknown_response_no_fake_fact_created(self):
        entity = _entity()
        query = InformationQuery(kind="material_source", subject="goblin_tears", actor_id=1)
        response = GuideInformationProvider.query(entity, query)
        result = KnowledgeModelService.assimilate(entity, response, tick=3)
        assert "goblin_tears" not in result.facts


# ── Insufficient gold ─────────────────────────────────────────────────────────

class TestKnowledgeModelInsufficientGold:
    def test_phase2_knowledge_insufficient_gold_nothing_learned(self):
        entity = _entity()  # gold=0 by default
        query = InformationQuery(kind="material_source", subject="moon_resin", actor_id=1)
        # No gold — guide rejects
        poor_entity = V2EntityBuilder(1).build()  # 0 gold default
        response = GuideInformationProvider.query(poor_entity, query)
        result = KnowledgeModelService.assimilate(poor_entity, response, tick=1)
        # Should be empty (nothing new)
        assert result.facts == {}
        assert result.unknowns == {}


# ── Existing knowledge preserved ──────────────────────────────────────────────

class TestKnowledgeModelPreservation:
    def test_phase2_knowledge_existing_facts_preserved_on_new_assimilation(self):
        from src.core.self_model import KnowledgeFact as EntityFact
        existing_fact = EntityFact(
            subject="iron_ore", fact_type="resource_source",
            details={"source": "old_mine"}, certainty=1.0,
            source_id="guide", recorded_tick=1
        )
        entity = _entity(facts={"iron_ore": existing_fact})
        # Now assimilate a blacksmith response for iron_sword
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)
        result = KnowledgeModelService.assimilate(entity, response, tick=10)
        # Both old and new facts must be present
        assert "iron_ore" in result.facts
        assert "iron_sword" in result.facts

    def test_phase2_knowledge_output_is_deterministic(self):
        entity = _entity()
        query = InformationQuery(kind="recipe_requirements", subject="iron_sword", actor_id=1)
        response = BlacksmithInformationProvider.query(entity, query)
        r1 = KnowledgeModelService.assimilate(entity, response, tick=5)
        r2 = KnowledgeModelService.assimilate(entity, response, tick=5)
        assert r1 == r2
