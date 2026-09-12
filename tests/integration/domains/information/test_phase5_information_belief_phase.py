"""
tests/integration/domains/information/test_phase5_information_belief_phase.py

Phase 5 — InformationBeliefPhase integration tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.core.updates import StateUpdate
from src.domains.information.schema import InformationSourceProfile
from src.domains.information.phase import InformationBeliefPhase
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.pipeline import AuthoritativeApplyPipeline


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
    intent = update.entity_updates[actor.id].pending_action_intent
    assert intent is not None
    assert intent.kind == "ASK_INFORMATION"


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
    intent = eu.pending_action_intent
    assert intent is not None
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


def _full_pipeline_state(entities) -> AuthoritativeState:
    """Distinct from module-level _state(): building_tiles/town_tiles/blocked_tiles must
    be dict/set (not tuple) for later pipeline phases (e.g. BlacksmithSystem) that this
    file's other tests never reach via direct InformationBeliefPhase.apply() calls."""
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=set(),
        building_tiles={}, terrain={}, home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=set(), town_entity_ids=set(),
    )


def _selfmodel_execution_probe_state():
    unk = UnknownFact(subject="iron_ore", reason="test_unk", recorded_tick=1)
    actor = _entity(1, x=0.0, y=0.0, unknowns={"iron_ore": unk})
    guide = _entity(2, x=1.0, y=1.0)  # close source, matches existing routing tests
    state = _full_pipeline_state([actor, guide])

    profiles = [
        InformationSourceProfile(
            source_id=2,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.8,
            freshness=0.9,
            cost_gold=0,
        )
    ]
    from dataclasses import replace as dataclass_replace
    state = dataclass_replace(state, information_source_profiles=profiles)
    return state, actor


def test_action_intent_execution_phase_fires_in_real_tick_pipeline():
    """TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE: with ENABLE_SELF_MODEL_COGNITION,
    ENABLE_BELIEF_ASSIMILATION, and ENABLE_INFORMATION_INTENT_EXECUTION all ON, a real
    end-to-end AuthoritativeApplyPipeline.refine() call must route the actor's unresolved
    "iron_ore" unknown (Branch B) AND execute the resulting ActionIntent through
    ActionIntentAdapter.execute() (the new phase), closing the loop into
    self_model_bundle_set within a single tick — not just via direct
    ActionIntentAdapter.execute() invocation."""
    from dataclasses import replace as dataclass_replace
    from src.domains.optimization.feature_flags import FeatureMode

    state, actor = _selfmodel_execution_probe_state()
    state = dataclass_replace(state, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        "ENABLE_INFORMATION_INTENT_EXECUTION": FeatureMode.ON,
    })

    from src.core.updates import StateUpdate
    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())

    eu = refined.entity_updates.get(actor.id)
    assert eu is not None
    assert eu.self_model_bundle_set is not None
    assert "iron_ore" in eu.self_model_bundle_set.knowledge.facts, (
        "expected ActionIntentAdapter.execute() to fire through the real pipeline and "
        "assimilate the routed query's answer into self_model_bundle_set.facts"
    )
    assert "iron_ore" not in eu.self_model_bundle_set.knowledge.unknowns


def test_action_intent_execution_phase_off_by_default_is_a_noop():
    """Same setup as test_action_intent_execution_phase_fires_in_real_tick_pipeline, but
    ENABLE_INFORMATION_INTENT_EXECUTION is left unset (default OFF). Branch B still routes
    the ActionIntent into pending_action_intent (ENABLE_BELIEF_ASSIMILATION stays ON), but it
    must sit inert, unconsumed — the flag gate must actually block production reachability."""
    from dataclasses import replace as dataclass_replace
    from src.domains.optimization.feature_flags import FeatureMode

    state, actor = _selfmodel_execution_probe_state()
    state = dataclass_replace(state, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
    })

    from src.core.updates import StateUpdate
    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())

    eu = refined.entity_updates.get(actor.id)
    assert eu is not None
    assert eu.pending_action_intent is not None, (
        "expected Branch B to still route the ActionIntent into pending_action_intent"
    )
    assert eu.self_model_bundle_set is not None
    assert "iron_ore" not in eu.self_model_bundle_set.knowledge.facts, (
        "ActionIntentAdapter.execute() must not have fired while the flag is OFF"
    )
    assert "iron_ore" in eu.self_model_bundle_set.knowledge.unknowns


def test_routed_action_intent_never_reaches_durable_latest_intent_results_flag_off():
    """TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE
    end-to-end regression: with ENABLE_INFORMATION_INTENT_EXECUTION OFF (the shipped default --
    the exact real-world condition that crashed StrategicWorkQueue.build() on real corpus worlds
    at real population density), a routed self-model query must never reach
    entity.identity.latest_intent_results (typed for IntentResult only), and
    StrategicWorkQueue.build() must not crash on the resulting entity."""
    from dataclasses import replace as dataclass_replace
    from src.domains.optimization.feature_flags import FeatureMode
    from src.core.updates import StateUpdate
    from src.engine.patches import extract_patches, IdentityPatch
    from src.engine.intent.action_intent import ActionIntent
    from src.systems.strategic_systems.work_queue import StrategicWorkQueue
    from src.core.dirty import DirtySet

    state, actor = _selfmodel_execution_probe_state()
    state = dataclass_replace(state, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        # ENABLE_INFORMATION_INTENT_EXECUTION deliberately left unset (default OFF).
    })

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())
    eu = refined.entity_updates[actor.id]
    assert isinstance(eu.pending_action_intent, ActionIntent), (
        "test setup assumption: Branch B routed a real ActionIntent this tick"
    )

    # Materialize the durable IdentityComponent the way the real apply pipeline would --
    # extract_patches() -> IdentityPatch.apply() -- and confirm latest_intent_results never
    # picks up the routed ActionIntent regardless of the flag being off.
    patches = extract_patches(actor.id, eu)
    identity_patches = [p for p in patches if isinstance(p, IdentityPatch)]
    changes: dict = {}
    for p in identity_patches:
        p.apply(actor, changes)
    new_identity = changes.get("identity", actor.identity)
    assert not any(isinstance(r, ActionIntent) for r in new_identity.latest_intent_results), (
        "a routed ActionIntent must never reach latest_intent_results, with the flag off or on"
    )

    updated_actor = dataclass_replace(actor, identity=new_identity)
    updated_state = dataclass_replace(state, entities={**state.entities, actor.id: updated_actor})

    # Must not raise -- this is the exact call site that crashed with
    # AttributeError: 'ActionIntent' object has no attribute 'accepted'. A real (non-None) empty
    # DirtySet is required so build() reaches the tier1 .accepted check instead of taking its own
    # early-return path for force_full_scan/no-dirty-set.
    StrategicWorkQueue.build(updated_state, StateUpdate(), dirty=DirtySet())
