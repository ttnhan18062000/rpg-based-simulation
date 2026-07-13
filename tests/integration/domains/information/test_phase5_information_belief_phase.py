"""
tests/integration/domains/information/test_phase5_information_belief_phase.py

Phase 5 — InformationBeliefPhase integration tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.domains.information.schema import InformationSourceProfile
from src.domains.information.phase import InformationBeliefPhase
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter


def _entity(e_id, x=0.0, y=0.0, unknowns=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(x, y)
    
    if unknowns:
        km = KnowledgeModelComponent(unknowns=unknowns)
        sm = SelfModelBundle(knowledge=km)
        b.replace_self_model(sm)
        
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


def test_phase_routes_query_for_active_unknowns():
    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=1)
    actor = _entity(1, x=0.0, y=0.0, unknowns={"iron_ore": unk})
    guide = _entity(2, x=1.0, y=1.0)  # close source
    state = _state([actor, guide])

    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.8,
            freshness=0.9,
        )
    ]

    update = InformationBeliefPhase.apply(state, profiles)

    assert actor.id in update.entity_updates
    prop_ups = update.entity_updates[actor.id].property_updates
    assert prop_ups.get("last_routed_query_subject") == "iron_ore"
    assert len(update.entity_updates[actor.id].intent_results) == 1
    assert update.entity_updates[actor.id].intent_results[0].kind == "ASK_INFORMATION"


def test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure():
    """TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE fix 2: when the top-ranked candidate
    (higher expected_certainty, paid) fails to resolve because the actor cannot afford it,
    InformationBeliefPhase.apply()'s Branch B must fall back to the next candidate
    (free, lower-certainty) rather than silently producing no EntityUpdate for the tick."""
    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=1)
    actor = _entity(1, x=0.0, y=0.0, unknowns={"iron_ore": unk})
    paid_source = _entity(2, x=1.0, y=1.0)   # near, ranked first (higher certainty)
    free_source = _entity(3, x=1.0, y=1.0)   # near, ranked second (lower certainty, free)
    state = _state([actor, paid_source, free_source])

    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.9,
            freshness=0.9,
            cost_gold=5,
        ),
        InformationSourceProfile(
            source_id=3,
            source_kind="traveler",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.4,
            freshness=0.6,
            cost_gold=0,
        ),
    ]

    update = InformationBeliefPhase.apply(state, profiles)

    assert actor.id in update.entity_updates
    eu = update.entity_updates[actor.id]
    assert eu.property_updates.get("last_routed_query_subject") == "iron_ore"
    assert len(eu.intent_results) == 1
    intent = eu.intent_results[0]
    assert intent.kind == "ASK_INFORMATION"
    assert intent.target_id == 3, "expected fallback past the unaffordable candidate to the free one"
    assert intent.payload.get("cost_paid") == 0


def test_ask_information_intent_execution_closes_the_loop():
    """TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE fix 5: executing a real, information-
    domain-originated ASK_INFORMATION intent (as produced by InformationIntentResolver, i.e.
    carrying "query_kind" in its payload) must both deduct the real cost_gold (dead-key fix:
    "cost_paid", not "cost_gold") and durably assimilate the answer into the entity's own
    self_model via the canonical InformationResponseNormalizer/InformationAssimilationService
    chain — closing the loop that previously only deducted (a dead-keyed, always-zero) gold."""
    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=1)
    actor = _entity(1, x=0.0, y=0.0, unknowns={"iron_ore": unk})

    intent = ActionIntent(
        kind="ASK_INFORMATION",
        actor_id=actor.id,
        target_id=2,
        payload={
            "subject": "iron_ore",
            "query_kind": "material_source",
            "cost_paid": 5,
            "expected_certainty": 0.7,
            "source_kind": "guide",
        },
        reason="Querying 2 for information on iron_ore.",
    )

    updates = ActionIntentAdapter.execute(actor, intent, current_tick=10)

    assert actor.id in updates
    eu = updates[actor.id]
    assert eu.inventory.gold_delta == -5, "expected real cost_gold deduction via cost_paid, not the dead cost_gold key"
    assert eu.self_model_bundle_set is not None
    assert "iron_ore" in eu.self_model_bundle_set.knowledge.facts
    assert "iron_ore" not in eu.self_model_bundle_set.knowledge.unknowns
