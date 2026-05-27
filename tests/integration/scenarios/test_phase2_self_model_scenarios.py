"""
tests/integration/scenarios/test_phase2_self_model_scenarios.py

Phase 2 — Integrated scenario tests for bottom-up self-model.
Verifies standard gameplay scenarios 2.1 through 2.5.
"""

import pytest
import dataclasses
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent
from src.core.self_model import SelfModelBundle, KnowledgeFact, UnknownFact
from src.cognition.self_model_phase import SelfModelUpdatePhase
from src.cognition.capability_estimate import CapabilityContext
from src.world.providers.information import (
    BlacksmithInformationProvider,
    GuideInformationProvider,
    InformationQuery,
    InformationResponse,
    KnowledgeFact as ProviderFact,
)
from src.core.strategic import LeadState


# ── Scenario 2.1: Vulnerability Prioritisation ────────────────────────────────

def test_scenario_2_1_vulnerability_prioritisation():
    """
    Wounded entity (HP=10/100) with a weak weapon (ATK=2, level=3)
    must prioritise healing over equipment improvement.
    """
    # Build entity with low hp and weak weapon for level 3
    entity = (
        V2EntityBuilder(1)
        .replace_combat(CombatComponent(hp=10, max_hp=100, atk=2, def_stat=2))
        .identity(evolution_level=3)
        .build()
    )

    # Run SelfModelUpdatePhase
    bundle = SelfModelUpdatePhase.run(entity, tick=1)

    # 1. Perceived weaknesses must include low_health and weak_weapon
    assert "low_health" in bundle.self_awareness.perceived_weaknesses
    assert "weak_weapon" in bundle.self_awareness.perceived_weaknesses

    # 2. Dominant need must be healing, and its urgency >= 0.9
    assert bundle.needs.dominant_need == "healing"
    assert bundle.needs.active_needs["healing"].urgency >= 0.9

    # 3. Equipment improvement need is active but lower urgency than healing
    assert "equipment_improvement" in bundle.needs.active_needs
    assert bundle.needs.active_needs["healing"].urgency > bundle.needs.active_needs["equipment_improvement"].urgency


# ── Scenario 2.2: Recipe Gap and Information Need ────────────────────────────

def test_scenario_2_2_recipe_gap_and_information_need():
    """
    Learning a recipe (hunter_blade) requiring moon_resin
    should introduce a knowledge gap and trigger an information need.
    """
    # 1. Start with clean entity
    entity = V2EntityBuilder(1).inventory(gold=100).build()

    # 2. Forge response mimicking blacksmith giving hunter_blade recipe
    provider_fact = ProviderFact(
        subject="hunter_blade",
        fact_type="recipe_definition",
        details={"requires_items": {"moon_resin": 1}, "gold_cost": 25}
    )
    event = InformationResponse(
        answer_kind="known",
        facts=(provider_fact,),
        unknowns=("material.moon_resin.source",), # registers gap
        certainty=1.0,
        source_id="blacksmith_hometown"
    )

    # 3. Update self-model with the event
    bundle = SelfModelUpdatePhase.run(entity, events=[event], tick=5)

    # 4. Verify recipe learned and moon_resin.source is unknown
    assert "hunter_blade" in bundle.knowledge.facts
    assert "material.moon_resin.source" in bundle.knowledge.unknowns
    assert bundle.knowledge.unknowns["material.moon_resin.source"].reason == "provider_known"

    # 5. Information need is active
    assert "information" in bundle.needs.active_needs
    assert bundle.needs.dominant_need == "information"


# ── Scenario 2.3: Equipment-Aware Capability Estimates ────────────────────────

def test_scenario_2_3_equipment_aware_capability_estimates():
    """
    Better equipment (iron_sword vs bare hands) improves the entity's
    subjective capability estimate against a wolf.
    """
    # 1. Clean level 2 entity (low atk = 5)
    entity_weak = (
        V2EntityBuilder(1)
        .replace_combat(CombatComponent(hp=100, max_hp=100, atk=5, def_stat=2))
        .identity(evolution_level=2)
        .build()
    )

    context = CapabilityContext.for_combat(["wolf"])

    # Estimate capability for weak entity
    bundle_weak = SelfModelUpdatePhase.run(entity_weak, capability_context=context, tick=1)
    est_weak = bundle_weak.capabilities.estimates["combat.enemy_type.wolf"].estimate

    # 2. Strong level 2 entity with iron_sword (atk = 25)
    entity_strong = (
        V2EntityBuilder(1)
        .replace_combat(CombatComponent(hp=100, max_hp=100, atk=25, def_stat=2))
        .identity(evolution_level=2)
        .build()
    )

    bundle_strong = SelfModelUpdatePhase.run(entity_strong, capability_context=context, tick=1)
    est_strong = bundle_strong.capabilities.estimates["combat.enemy_type.wolf"].estimate

    # 3. Strong entity must have a significantly higher combat estimate
    assert est_strong > est_weak
    assert est_strong > 0.5


# ── Scenario 2.4: Condition-Driven Estimates and Needs ─────────────────────────

def test_scenario_2_4_condition_driven_estimates_and_needs():
    """
    Taking damage (100% -> 20% HP) vs a rat decreases the capability estimate
    and increases the healing need.
    """
    # 1. Entity at 100% HP
    entity_healthy = (
        V2EntityBuilder(1)
        .replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
        .build()
    )

    context = CapabilityContext.for_combat(["rat"])
    bundle_healthy = SelfModelUpdatePhase.run(entity_healthy, capability_context=context, tick=1)

    est_healthy = bundle_healthy.capabilities.estimates["combat.enemy_type.rat"].estimate
    assert "healing" not in bundle_healthy.needs.active_needs

    # 2. Entity wounded to 20% HP
    entity_wounded = (
        V2EntityBuilder(1)
        .replace_combat(CombatComponent(hp=20, max_hp=100, atk=10, def_stat=2))
        .build()
    )

    bundle_wounded = SelfModelUpdatePhase.run(entity_wounded, capability_context=context, tick=2)

    est_wounded = bundle_wounded.capabilities.estimates["combat.enemy_type.rat"].estimate
    
    # 3. Estimate drops and healing need appears
    assert est_wounded < est_healthy
    assert "healing" in bundle_wounded.needs.active_needs
    assert bundle_wounded.needs.active_needs["healing"].urgency >= 0.7


# ── Scenario 2.5: Information Opacity / No Hidden Leaks ────────────────────────

def test_scenario_2_5_information_opacity_no_hidden_leaks():
    """
    Assimilating a guide's partial answer (clue/lead only) must NOT
    leak the exact hidden source (moon_cave) into the entity's knowledge.
    """
    # 1. Entity with 50 gold to pay guide
    entity = V2EntityBuilder(1).inventory(gold=50).build()

    # 2. Query the guide provider for material_source of moon_resin
    query = InformationQuery(kind="material_source", subject="moon_resin", actor_id=1)
    response = GuideInformationProvider.query(entity, query)

    # 3. Run phase update to assimilate response
    bundle = SelfModelUpdatePhase.run(entity, events=[response], tick=10)

    # 4. Assert moon_resin.source remains unknown (gap)
    assert "material.moon_resin.source" in bundle.knowledge.unknowns

    # 5. A lead fact should be recorded (low-certainty hint)
    lead_keys = [k for k in bundle.knowledge.facts if k.startswith("lead.")]
    assert len(lead_keys) > 0
    for lk in lead_keys:
        assert bundle.knowledge.facts[lk].certainty < 1.0

    # 6. CRITICAL: The exact hidden source "moon_cave" must NOT exist in facts
    assert "resource.moon_resin.source" not in bundle.knowledge.facts
    assert "moon_cave" not in str(bundle.knowledge.facts)
