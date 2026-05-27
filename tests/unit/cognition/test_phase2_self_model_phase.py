"""
tests/unit/cognition/test_phase2_self_model_phase.py

Phase 2 — SelfModelUpdatePhase unit tests.
Verifies dirty-check, service orchestration, and trace event generation.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact, CapabilityEstimateComponent
from src.cognition.self_model_phase import SelfModelUpdatePhase
from src.cognition.capability_estimate import CapabilityContext
from src.world.providers.information import InformationResponse, KnowledgeFact as ProviderFact
from src.cognition.trace_events import (
    SelfAwarenessUpdatedEvent,
    NeedInterpretedEvent,
    CapabilityEstimateUpdatedEvent,
    KnowledgeFactLearnedEvent,
    KnowledgeUnknownRecordedEvent,
)


def _entity(hp=100, max_hp=100, stamina=100, max_stamina=100, hunger=0.0, sleep_debt=0.0, atk=10, level=1):
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=atk, def_stat=2))
    b.replace_stamina(StaminaComponent(current=stamina, max_stamina=max_stamina))
    b.replace_biological(BiologicalComponent(hunger=hunger, sleep_debt=sleep_debt))
    b.identity(evolution_level=level)
    return b.build()


def test_phase2_update_phase_first_run_is_always_run():
    entity = _entity()
    assert entity.self_model.self_awareness.last_self_check_tick == 0

    trace_collector = []
    new_bundle = SelfModelUpdatePhase.run(entity, tick=1, trace_events_collector=trace_collector)

    assert new_bundle.self_awareness.last_self_check_tick == 1
    assert new_bundle.needs.last_interpreted_tick == 1
    assert len(trace_collector) >= 2
    assert any(isinstance(ev, SelfAwarenessUpdatedEvent) for ev in trace_collector)
    assert any(isinstance(ev, NeedInterpretedEvent) for ev in trace_collector)


def test_phase2_update_phase_clean_entity_skips_run():
    # Run once to establish base bundle at tick 1
    entity1 = _entity()
    bundle1 = SelfModelUpdatePhase.run(entity1, tick=1)
    entity2 = V2EntityBuilder(1).replace_self_model(bundle1).replace_combat(entity1.combat).replace_stamina(entity1.stamina).replace_biological(entity1.biological).identity(evolution_level=entity1.identity.evolution_level).build()

    trace_collector = []
    # Running again on tick 2 with no changes and no events should trigger dirty-check skip
    new_bundle = SelfModelUpdatePhase.run(entity2, tick=2, trace_events_collector=trace_collector)

    # Both bundle identity and collector empty check
    assert new_bundle == bundle1
    assert len(trace_collector) == 0


def test_phase2_update_phase_dirty_hp_triggers_run():
    entity1 = _entity()
    bundle1 = SelfModelUpdatePhase.run(entity1, tick=1)
    
    # Modify HP to 30 (wounded)
    entity2 = V2EntityBuilder(1).replace_self_model(bundle1).replace_combat(CombatComponent(hp=30, max_hp=100, atk=10, def_stat=2)).replace_stamina(entity1.stamina).replace_biological(entity1.biological).identity(evolution_level=entity1.identity.evolution_level).build()

    trace_collector = []
    new_bundle = SelfModelUpdatePhase.run(entity2, tick=2, trace_events_collector=trace_collector)

    assert new_bundle.self_awareness.last_self_check_tick == 2
    assert new_bundle.needs.last_interpreted_tick == 2
    assert "low_health" in new_bundle.self_awareness.perceived_weaknesses
    assert new_bundle.needs.dominant_need == "healing"
    assert len(trace_collector) >= 2


def test_phase2_update_phase_assimilates_info_event():
    entity1 = _entity()
    bundle1 = SelfModelUpdatePhase.run(entity1, tick=1)
    entity2 = V2EntityBuilder(1).replace_self_model(bundle1).replace_combat(entity1.combat).replace_stamina(entity1.stamina).replace_biological(entity1.biological).identity(evolution_level=entity1.identity.evolution_level).inventory(gold=100).build()

    # Create dummy information response event
    provider_fact = ProviderFact(subject="iron_sword", fact_type="recipe_definition", details={"requires": "iron_ore"})
    event = InformationResponse(
        answer_kind="known",
        facts=(provider_fact,),
        unknowns=(),
        suggested_leads=(),
        certainty=1.0,
        source_id="blacksmith_hometown"
    )

    trace_collector = []
    new_bundle = SelfModelUpdatePhase.run(entity2, events=[event], tick=2, trace_events_collector=trace_collector)

    # Verify fact learned
    assert "iron_sword" in new_bundle.knowledge.facts
    assert new_bundle.knowledge.last_updated_tick == 2
    assert any(isinstance(ev, KnowledgeFactLearnedEvent) for ev in trace_collector)


def test_phase2_update_phase_capability_estimates_scoped():
    entity = _entity(atk=30, level=1)
    context = CapabilityContext.for_combat(["rat", "wolf"])

    trace_collector = []
    new_bundle = SelfModelUpdatePhase.run(entity, tick=1, capability_context=context, trace_events_collector=trace_collector)

    assert "combat.enemy_type.rat" in new_bundle.capabilities.estimates
    assert "combat.enemy_type.wolf" in new_bundle.capabilities.estimates
    assert any(isinstance(ev, CapabilityEstimateUpdatedEvent) for ev in trace_collector)
