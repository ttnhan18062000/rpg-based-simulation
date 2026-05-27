"""
tests/unit/entity/test_phase2_self_model_components.py

Phase 2 — Self Model Component Schema tests.
Covers: default construction, canonical serialisation stability,
equality determinism, and builder integration.
"""

import pytest
from src.core.self_model import (
    InterpretedNeed,
    CapabilityEstimate,
    KnowledgeFact,
    UnknownFact,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    CapabilityEstimateComponent,
    KnowledgeModelComponent,
    SelfModelBundle,
)
from src.core.builder import V2EntityBuilder


# ─────────────────────────────────────────────────────────────────────────────
# SelfAwarenessComponent
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfAwarenessComponent:
    def test_phase2_self_model_default_construction(self):
        sa = SelfAwarenessComponent()
        assert sa.perceived_condition == {}
        assert sa.perceived_weaknesses == ()
        assert sa.perceived_strengths == ()
        assert sa.confidence_level == 0.5
        assert sa.stress_level == 0.0
        assert sa.uncertainty_level == 0.0
        assert sa.last_self_check_tick == 0

    def test_phase2_self_model_canonical_serialisation_stability(self):
        sa = SelfAwarenessComponent(
            perceived_condition={"health": 0.2, "stamina": 0.9},
            perceived_weaknesses=("low_health",),
            perceived_strengths=("high_stamina",),
            confidence_level=0.3,
            stress_level=0.7,
            uncertainty_level=0.1,
            last_self_check_tick=42,
        )
        d1 = sa.to_canonical_dict()
        d2 = sa.to_canonical_dict()
        assert d1 == d2

    def test_phase2_self_model_canonical_keys(self):
        sa = SelfAwarenessComponent()
        d = sa.to_canonical_dict()
        assert set(d.keys()) == {
            "perceived_condition",
            "perceived_weaknesses",
            "perceived_strengths",
            "confidence_level",
            "stress_level",
            "uncertainty_level",
            "last_self_check_tick",
        }

    def test_phase2_self_model_equality_deterministic(self):
        sa1 = SelfAwarenessComponent(confidence_level=0.7, stress_level=0.3)
        sa2 = SelfAwarenessComponent(confidence_level=0.7, stress_level=0.3)
        assert sa1 == sa2

    def test_phase2_self_model_condition_sorted_in_canonical(self):
        sa = SelfAwarenessComponent(
            perceived_condition={"z_key": 1.0, "a_key": 0.5}
        )
        d = sa.to_canonical_dict()
        keys = list(d["perceived_condition"].keys())
        assert keys == sorted(keys)


# ─────────────────────────────────────────────────────────────────────────────
# NeedInterpretationComponent
# ─────────────────────────────────────────────────────────────────────────────

class TestNeedInterpretationComponent:
    def test_phase2_need_default_construction(self):
        n = NeedInterpretationComponent()
        assert n.active_needs == {}
        assert n.dominant_need is None
        assert n.last_interpreted_tick == 0

    def test_phase2_need_canonical_serialisation_stability(self):
        need = InterpretedNeed(key="healing", urgency=0.9, confidence=0.8, reason="low_health")
        n = NeedInterpretationComponent(
            active_needs={"healing": need},
            dominant_need="healing",
            last_interpreted_tick=10,
        )
        d1 = n.to_canonical_dict()
        d2 = n.to_canonical_dict()
        assert d1 == d2

    def test_phase2_need_canonical_keys(self):
        n = NeedInterpretationComponent()
        d = n.to_canonical_dict()
        assert set(d.keys()) == {"active_needs", "dominant_need", "last_interpreted_tick"}

    def test_phase2_need_equality_deterministic(self):
        need = InterpretedNeed(key="food", urgency=0.5, confidence=0.9, reason="hunger")
        n1 = NeedInterpretationComponent(active_needs={"food": need}, dominant_need="food")
        n2 = NeedInterpretationComponent(active_needs={"food": need}, dominant_need="food")
        assert n1 == n2


# ─────────────────────────────────────────────────────────────────────────────
# CapabilityEstimateComponent
# ─────────────────────────────────────────────────────────────────────────────

class TestCapabilityEstimateComponent:
    def test_phase2_capability_default_construction(self):
        c = CapabilityEstimateComponent()
        assert c.estimates == {}
        assert c.last_updated_tick == 0

    def test_phase2_capability_canonical_serialisation_stability(self):
        est = CapabilityEstimate(
            capability_key="combat.enemy_type.rat",
            estimate=0.6,
            confidence=0.8,
            source="stat_comparison",
            last_updated_tick=5,
        )
        c = CapabilityEstimateComponent(estimates={"combat.enemy_type.rat": est}, last_updated_tick=5)
        d1 = c.to_canonical_dict()
        d2 = c.to_canonical_dict()
        assert d1 == d2

    def test_phase2_capability_canonical_keys(self):
        c = CapabilityEstimateComponent()
        d = c.to_canonical_dict()
        assert set(d.keys()) == {"estimates", "last_updated_tick"}

    def test_phase2_capability_estimate_key_sorted(self):
        est_rat = CapabilityEstimate("combat.enemy_type.rat", 0.7, 0.8, "src", 1)
        est_wolf = CapabilityEstimate("combat.enemy_type.wolf", 0.3, 0.7, "src", 1)
        c = CapabilityEstimateComponent(estimates={
            "combat.enemy_type.wolf": est_wolf,
            "combat.enemy_type.rat": est_rat,
        })
        keys = list(c.to_canonical_dict()["estimates"].keys())
        assert keys == sorted(keys)


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeModelComponent
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeModelComponent:
    def test_phase2_knowledge_default_construction(self):
        k = KnowledgeModelComponent()
        assert k.facts == {}
        assert k.unknowns == {}
        assert k.last_updated_tick == 0

    def test_phase2_knowledge_canonical_serialisation_stability(self):
        fact = KnowledgeFact(
            subject="iron_ore",
            fact_type="resource_source",
            details={"source_regions": ["forest"]},
            certainty=1.0,
            source_id="guide_hometown",
            recorded_tick=3,
        )
        unknown = UnknownFact(
            subject="material.moon_resin.source",
            reason="provider_partial",
            recorded_tick=5,
        )
        k = KnowledgeModelComponent(
            facts={"iron_ore": fact},
            unknowns={"material.moon_resin.source": unknown},
            last_updated_tick=5,
        )
        d1 = k.to_canonical_dict()
        d2 = k.to_canonical_dict()
        assert d1 == d2

    def test_phase2_knowledge_canonical_keys(self):
        k = KnowledgeModelComponent()
        d = k.to_canonical_dict()
        assert set(d.keys()) == {"facts", "unknowns", "last_updated_tick"}

    def test_phase2_knowledge_fact_keys_sorted(self):
        f1 = KnowledgeFact("z_subject", "type_a")
        f2 = KnowledgeFact("a_subject", "type_b")
        k = KnowledgeModelComponent(facts={"z_subject": f1, "a_subject": f2})
        keys = list(k.to_canonical_dict()["facts"].keys())
        assert keys == sorted(keys)


# ─────────────────────────────────────────────────────────────────────────────
# SelfModelBundle
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfModelBundle:
    def test_phase2_bundle_default_construction(self):
        b = SelfModelBundle()
        assert isinstance(b.self_awareness, SelfAwarenessComponent)
        assert isinstance(b.needs, NeedInterpretationComponent)
        assert isinstance(b.capabilities, CapabilityEstimateComponent)
        assert isinstance(b.knowledge, KnowledgeModelComponent)

    def test_phase2_bundle_empty_classmethod(self):
        b = SelfModelBundle.empty()
        assert b == SelfModelBundle()

    def test_phase2_bundle_canonical_keys(self):
        b = SelfModelBundle()
        d = b.to_canonical_dict()
        assert set(d.keys()) == {"self_awareness", "needs", "capabilities", "knowledge"}

    def test_phase2_bundle_canonical_stability(self):
        b = SelfModelBundle()
        d1 = b.to_canonical_dict()
        d2 = b.to_canonical_dict()
        assert d1 == d2

    def test_phase2_bundle_equality_deterministic(self):
        b1 = SelfModelBundle()
        b2 = SelfModelBundle()
        assert b1 == b2


# ─────────────────────────────────────────────────────────────────────────────
# Builder integration
# ─────────────────────────────────────────────────────────────────────────────

class TestBuilderIntegration:
    def test_phase2_builder_has_default_self_model(self):
        entity = V2EntityBuilder(1).build()
        assert hasattr(entity, "self_model")
        assert isinstance(entity.self_model, SelfModelBundle)

    def test_phase2_builder_replace_self_model(self):
        awareness = SelfAwarenessComponent(
            perceived_weaknesses=("low_health",),
            stress_level=0.8,
        )
        bundle = SelfModelBundle(self_awareness=awareness)
        entity = V2EntityBuilder(2).replace_self_model(bundle).build()
        assert entity.self_model.self_awareness.stress_level == 0.8
        assert "low_health" in entity.self_model.self_awareness.perceived_weaknesses

    def test_phase2_entity_canonical_includes_self_model(self):
        entity = V2EntityBuilder(3).build()
        cd = entity.to_canonical_dict()
        assert "self_model" in cd
        assert "self_awareness" in cd["self_model"]
        assert "needs" in cd["self_model"]
        assert "capabilities" in cd["self_model"]
        assert "knowledge" in cd["self_model"]
