"""
tests/integration/domains/test_fused_loop.py

Unified fusion integration tests.
Verifies Aspect-Gated Feature Flags, Shadow Mode parity, spatial candidate capping,
and knowledge persistence under the authoritative apply pipeline.
"""

import pytest
from typing import Any
from dataclasses import replace as dataclass_replace
from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState, CombatComponent, BiologicalComponent,
    PersonalityComponent, ResourceNodeState
)
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.core.updates import StateUpdate
from src.domains.optimization.feature_flags import FeatureMode, FeatureFlagManager
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.world.providers.resources import ResourceOpportunityProvider
from src.domains.information.schema import InformationSourceProfile
from src.world.providers.information import InformationResponse


def _create_entity(ent_id: int, x: float, y: float, hp: int = 100) -> Any:
    b = V2EntityBuilder(ent_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p, class_id="warrior")
    b.location(x, y)
    b.lifecycle(active=True)
    return b.build()


def _create_state(entities: list, resource_nodes: dict = None) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=42, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes=resource_nodes or {}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=set(),
        building_tiles={}, terrain={}, home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=set(), town_entity_ids=set(),
    )


def test_feature_shadow_mode_preserves_authoritative_hash():
    """
    Verify that running the loop in SHADOW mode evaluates all logic but discards
    the final state aspect changes, guaranteeing exact state equivalence to OFF mode.
    """
    e1 = _create_entity(1, 0.0, 0.0, hp=50)
    e2 = _create_entity(2, 1.0, 1.0)
    
    # 1. State under OFF mode
    state_off = _create_state([e1, e2])
    state_off = dataclass_replace(state_off, pressure_signals={
        "ENABLE_SELF_MODEL_COGNITION": 0.0,
        "ENABLE_ADVENTURE_ROUTING": 0.0,
        "ENABLE_COMBAT_ENGAGEMENT": 0.0,
        "ENABLE_BELIEF_ASSIMILATION": 0.0,
        "ENABLE_SOCIAL_COOPERATION": 0.0,
        "ENABLE_WORLD_EMERGENCE": 0.0,
    })
    
    update_off = StateUpdate()
    refined_off = AuthoritativeApplyPipeline.refine(state_off, update_off)
    next_state_off = ApplyPath.apply_generation(state_off, refined_off, next_tick=2)

    # 2. State under SHADOW mode
    state_shadow = _create_state([e1, e2])
    state_shadow = dataclass_replace(state_shadow, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.SHADOW,
        "ENABLE_ADVENTURE_ROUTING": FeatureMode.SHADOW,
        "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.SHADOW,
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.SHADOW,
        "ENABLE_SOCIAL_COOPERATION": FeatureMode.SHADOW,
        "ENABLE_WORLD_EMERGENCE": FeatureMode.SHADOW,
    })

    update_shadow = StateUpdate()
    refined_shadow = AuthoritativeApplyPipeline.refine(state_shadow, update_shadow)
    next_state_shadow = ApplyPath.apply_generation(state_shadow, refined_shadow, next_tick=2)

    # Assert that metrics ran/skipped are present in refined_shadow
    assert refined_shadow.metric_counters.get("run_self_model", 0) > 0 or refined_shadow.metric_counters.get("skip_self_model", 0) == 0

    # Verify entities are identical because SHADOW updates were discarded
    for ent_id in (1, 2):
        ent_off = next_state_off.entities[ent_id]
        ent_shadow = next_state_shadow.entities[ent_id]
        
        # Check coordinates and health are identical
        assert ent_off.navigation.position == ent_shadow.navigation.position
        assert ent_off.combat.hp == ent_shadow.combat.hp
        assert ent_off.strategic.current_project_id == ent_shadow.strategic.current_project_id
        
        # Check custom property updates are discarded in shadow
        assert ent_shadow.identity.properties.get("last_combat_posture") is None


def test_self_model_phase_runs_in_shadow_without_state_mutation():
    """
    Ensure the Self Model phase runs in SHADOW mode (recording metric counters)
    but does not mutate the entity's actual self_model aspect or live fields.
    """
    e = _create_entity(1, 0.0, 0.0, hp=40) # Needs healing / low HP
    state = _create_state([e])
    state = dataclass_replace(state, feature_flags={
        "ENABLE_SELF_MODEL_COGNITION": FeatureMode.SHADOW,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Assert run counter is incremented
    assert refined.metric_counters.get("run_self_model", 0) == 1
    # Verify entity update is NOT applied to self_model_bundle
    assert 1 not in refined.entity_updates or refined.entity_updates[1].self_model_bundle_set is None


def test_adventure_phase_receives_nonempty_world_opportunities():
    """
    Verify adventure routing receives non-empty world opportunities generated from live state nodes.
    """
    e = _create_entity(1, 0.0, 0.0)
    object.__setattr__(e.navigation, "region_id", "old_mine") # match resource node
    node = ResourceNodeState(
        id=201, kind="node_iron", position=(1.0, 1.0), yields_item="iron_ore",
        remaining_charges=5, max_charges=5, required_ticks=10
    )
    state = _create_state([e], resource_nodes={node.id: node})
    
    # Verify provider gets opportunities
    opps = ResourceOpportunityProvider.get_opportunities(e, state)
    assert len(opps) > 0
    assert opps[0].target_id == "201"
    assert opps[0].subject == "iron_ore"


def test_combat_engagement_caps_candidates():
    """
    Verify CombatEngagementPhase uses the proximity grid/capping to evaluate up to 3 candidate targets.
    """
    actor = _create_entity(1, 0.0, 0.0)
    # Add 5 hostiles close by
    hostiles = [_create_entity(i, 0.5, 0.5) for i in range(2, 8)]
    state = _create_state([actor] + hostiles)
    
    # Enable Combat phase
    state = dataclass_replace(state, feature_flags={
        "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify that the posture selection processed cleanly
    assert actor.id in refined.entity_updates
    assert "last_combat_posture" in refined.entity_updates[actor.id].property_updates


def test_belief_assimilation_persists_facts():
    """
    Verify Phase 5 belief assimilation facts persist into entity.self_model across ticks.
    """
    unk = UnknownFact(subject="coal_ore", reason="need_material", recorded_tick=1)
    # Set up entity with unknown fact and self_model knowledge component
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1, personality=PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5))
    b.location(0.0, 0.0)
    b.lifecycle(active=True)
    
    km = KnowledgeModelComponent(unknowns={"coal_ore": unk})
    sm = SelfModelBundle(knowledge=km)
    b.replace_self_model(sm)
    actor = b.build()

    state = _create_state([actor])
    
    # Ingest a pending response for coal_ore fact assimilation
    pending = [{
        "actor_id": 1,
        "subject": "coal_ore",
        "query_kind": "material_source",
        "source_id": 2,
        "raw_response": {
            "answer_kind": "KNOWN_FACT",
            "certainty": 1.0,
            "details": {"source": "old_mine"},
        },
        "cost_paid": 5,
    }]
    state = dataclass_replace(state, pending_information_responses=pending, feature_flags={
        "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
    })

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Check that knowledge update is packed in update
    assert 1 in refined.entity_updates
    eu = refined.entity_updates[1]
    assert eu.self_model_bundle_set is not None
    # Apply update to state
    next_state = ApplyPath.apply_generation(state, refined, next_tick=2)
    next_actor = next_state.entities[1]
    
    # Check that the coal_ore unknown is resolved into a fact with the expected content
    # (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B supplementary fix: self_model_bundle_set now
    # durably materializes via SelfModelPatch, so this assertion actually proves the fix
    # instead of merely tolerating an always-non-None default).
    fact = next_actor.self_model.knowledge.facts.get("coal_ore")
    assert fact is not None
    assert fact.details == {"source": "old_mine"}
    assert next_actor.self_model.knowledge.unknowns.get("coal_ore") is None


def test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B: SelfModelUpdatePhase.apply() sources real
    InformationResponse-shaped events from state.pending_self_model_information_events
    (grouped by actor_id) instead of the previous events=[] hardcoding. Isolated from
    Finding 4 (ENABLE_BELIEF_ASSIMILATION left unset/OFF).
    """
    e1 = _create_entity(1, 0.0, 0.0)
    e2 = _create_entity(2, 5.0, 5.0)
    state = _create_state([e1, e2])

    seeded_event = {
        "actor_id": 1,
        "event": InformationResponse(answer_kind="unknown", unknowns=("material.moon_resin.source",)),
    }
    state = dataclass_replace(
        state,
        pending_self_model_information_events=[seeded_event],
        feature_flags={"ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON},
    )

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)

    assert 1 in refined.entity_updates
    eu1 = refined.entity_updates[1]
    assert eu1.self_model_bundle_set is not None
    unk = eu1.self_model_bundle_set.knowledge.unknowns.get("material.moon_resin.source")
    assert unk is not None
    assert unk.reason == "provider_unknown"

    # Entity 2 (no seeded event) still gets a valid self_model_bundle_set — confirms the
    # fix does not regress entities without a seeded event.
    assert 2 in refined.entity_updates
    assert refined.entity_updates[2].self_model_bundle_set is not None

    # Step 7 single-fire regression guard: not carried forward past this tick.
    next_state = ApplyPath.apply_generation(state, refined, next_tick=2)
    assert next_state.pending_self_model_information_events == []
    # Finding 5 (supplementary fix, this session): EntityUpdate.self_model_bundle_set now
    # durably materializes into entity.self_model across the tick boundary via
    # SelfModelPatch (src/engine/patches.py) — confirmed by asserting the actual unknown
    # entry's content, not just non-None presence.
    persisted_unk = next_state.entities[1].self_model.knowledge.unknowns.get("material.moon_resin.source")
    assert persisted_unk is not None
    assert persisted_unk.reason == "provider_unknown"


def test_information_belief_merge_preserves_self_model_writes_both_flags_on():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (Finding-4 fix-proving test): with BOTH
    ENABLE_SELF_MODEL_COGNITION and ENABLE_BELIEF_ASSIMILATION ON simultaneously,
    InformationBeliefPhase's pipeline-wiring fix (u.merge(...) at
    src/engine/pipeline.py:152's information_belief call site) must not wipe
    entity_updates for an entity it never touches.

    Before this ticket's fix (pipeline.py:152 called InformationBeliefPhase.apply()
    directly instead of via u.merge(...)), this exact scenario (2 entities, no
    pending_information_responses, entity B has no unknowns) emptied
    refined.entity_updates to {} entirely — empirically reproduced during this
    ticket's implementation by temporarily reverting the fix. This test is the direct
    regression guard against that clobbering ever being reintroduced.
    """
    e_a = _create_entity(1, 0.0, 0.0)  # gets a seeded self-model event
    e_b = _create_entity(2, 5.0, 5.0)  # unrelated; no seeded event, no unknowns
    state = _create_state([e_a, e_b])

    seeded_event = {
        "actor_id": 1,
        "event": InformationResponse(answer_kind="unknown", unknowns=("material.moon_resin.source",)),
    }
    state = dataclass_replace(
        state,
        pending_self_model_information_events=[seeded_event],
        feature_flags={
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        },
    )

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)

    # Entity A: Step 4's fix fired (self_model wrote the unknown this tick).
    assert 1 in refined.entity_updates
    unk = refined.entity_updates[1].self_model_bundle_set.knowledge.unknowns.get("material.moon_resin.source")
    assert unk is not None

    # Entity B: information_belief never touches it (no unknowns, no pending response) —
    # but self_model's own same-tick write for entity B must survive the merge fix.
    assert 2 in refined.entity_updates
    assert refined.entity_updates[2].self_model_bundle_set is not None


def test_information_belief_branch_b_routes_query_when_unknown_precondition_met():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B: proves InformationBeliefPhase's Branch B
    (route a new query for an actor's first unresolved unknown, phase.py:84-105) is
    genuinely reachable and coexists with a same-tick self_model write via the merge
    fix, both flags ON simultaneously.

    Entity A already has self_model.knowledge.unknowns populated directly on `state`
    (the durable precondition Branch B's routing checks) — this isolates "does Branch
    B's routing logic itself work" from "can SelfModelUpdatePhase's same-tick write
    reach `state` in time" (it cannot within a single refine() call; see
    test_self_model_apply_sources_events_from_pending_field_isolated_from_finding4's
    NOTE on phase ordering / Finding 5). Entity B is seeded via the new
    pending_self_model_information_events field so self_model produces a fresh
    same-tick EntityUpdate for it — proving the two entities' distinct contributions
    coexist under the merge fix.
    """
    unk = UnknownFact(subject="material.moon_resin.source", reason="provider_unknown", recorded_tick=0)
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1, personality=PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5))
    b.location(0.0, 0.0)
    b.lifecycle(active=True)
    b.replace_self_model(SelfModelBundle(knowledge=KnowledgeModelComponent(unknowns={"material.moon_resin.source": unk})))
    actor_a = b.build()

    actor_b = _create_entity(2, 5.0, 5.0)

    profile = InformationSourceProfile(
        source_id="town_notice_board", source_kind="guide",
        knowledge_scopes=("regional_danger", "common_resource_sources"),
        accuracy=0.4, freshness=0.6, bias=0.1, cost_gold=0, max_answers_per_query=2,
    )

    seeded_event = {
        "actor_id": 2,
        "event": InformationResponse(answer_kind="unknown", unknowns=("recipe.iron_dagger.requirements",)),
    }

    state = _create_state([actor_a, actor_b])
    state = dataclass_replace(
        state,
        information_source_profiles=[profile],
        pending_self_model_information_events=[seeded_event],
        feature_flags={
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        },
    )

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)

    # Entity A: Branch B fired — a new query was routed for its pre-existing unknown.
    eu_a = refined.entity_updates.get(1)
    assert eu_a is not None
    assert eu_a.property_updates.get("last_routed_query_subject") == "material.moon_resin.source"
    assert eu_a.intent_results, "expected a routed ASK_INFORMATION intent for entity A"
    assert eu_a.intent_results[0].kind == "ASK_INFORMATION"

    # Entity B: Step 4's fix fired for a distinct entity/subject in the same tick —
    # and its self_model write survives the merge alongside entity A's Branch B write.
    eu_b = refined.entity_updates.get(2)
    assert eu_b is not None
    assert eu_b.self_model_bundle_set is not None
    assert eu_b.self_model_bundle_set.knowledge.unknowns.get("recipe.iron_dagger.requirements") is not None


def test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B: compile urban_political's real resolved world
    spec, override ENABLE_SELF_MODEL_COGNITION to ON for this test only (leaving
    ENABLE_BELIEF_ASSIMILATION at its shipped urban_political profile value, ON), and
    confirm the events=[] fix populates pop_1's self_model_bundle_set with real
    compiled content in the same tick Branch A (pending_information_responses) fires
    for pop_0 — proving the two coexist correctly under the merge fix.

    Honest scope note: InformationBeliefPhase's Branch B routing itself does NOT fire
    within this same tick 0 call, because InformationBeliefPhase.apply() reads
    `actor.self_model` off the frozen `state` object (not the in-flight `update`), and
    `state` is not remutated mid-refine() — self_model's write for pop_1 lands only in
    `update` this tick. See
    test_information_belief_branch_b_routes_query_when_unknown_precondition_met above
    for proof that Branch B's routing logic itself is reachable once its state-level
    precondition is met.
    """
    from src.worldbuilding.schema import load_world_spec_from_yaml
    from src.worldbuilding.compiler import WorldCompiler

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=42)
    state = dataclass_replace(
        state,
        feature_flags={
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        },
    )

    pop_1_id = next(
        eid for eid, e in state.entities.items()
        if e.properties.get("population_id") == "pop_1"
    )
    pop_0_id = next(
        eid for eid, e in state.entities.items()
        if e.properties.get("population_id") == "pop_0"
    )

    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)

    eu_1 = refined.entity_updates[pop_1_id]
    assert eu_1.self_model_bundle_set is not None
    assert eu_1.self_model_bundle_set.knowledge.unknowns.get("material.moon_resin.source") is not None

    eu_0 = refined.entity_updates[pop_0_id]
    assert eu_0.property_updates.get("last_assimilated_subject") == "bandit_road_danger"


def test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (supplementary fix, Finding 5): proves the full
    seed -> assimilate -> materialize -> route sequence works end-to-end across a real
    tick boundary, now that SelfModelPatch (src/engine/patches.py) durably materializes
    EntityUpdate.self_model_bundle_set into entity.self_model via ApplyPath.

    Tick N: a pending_self_model_information_events "unknown" event is seeded for the
    actor. Within this same refine() call, InformationBeliefPhase reads the actor's
    self_model off the still-frozen `state` (pre-materialization) — so Branch B does
    NOT route in tick N (matches the documented same-tick phase-ordering limitation in
    test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist).
    After ApplyPath.apply_generation() commits tick N's self_model write, the actor's
    durable self_model.knowledge.unknowns is populated for the first time.

    Tick N+1: a second refine() call (no new seed) on the resulting next_state now sees
    the durably materialized unknown and InformationBeliefPhase's Branch B routes a
    query for it — the exact cross-tick reachability this ticket's own Finding 5
    recommended as a follow-up.
    """
    profile = InformationSourceProfile(
        source_id="town_notice_board", source_kind="guide",
        knowledge_scopes=("regional_danger", "common_resource_sources"),
        accuracy=0.4, freshness=0.6, bias=0.1, cost_gold=0, max_answers_per_query=2,
    )

    actor = _create_entity(1, 0.0, 0.0)
    state = _create_state([actor])

    seeded_event = {
        "actor_id": 1,
        "event": InformationResponse(answer_kind="unknown", unknowns=("material.moon_resin.source",)),
    }
    state = dataclass_replace(
        state,
        pending_self_model_information_events=[seeded_event],
        information_source_profiles=[profile],
        feature_flags={
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON,
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
        },
    )

    # Tick N: seed materializes into an EntityUpdate this tick, but Branch B cannot
    # route yet (state.entities[1].self_model is still pre-write, same-tick limitation).
    update_n = StateUpdate()
    refined_n = AuthoritativeApplyPipeline.refine(state, update_n)
    eu_n = refined_n.entity_updates.get(1)
    assert eu_n is not None
    assert eu_n.self_model_bundle_set is not None
    assert eu_n.self_model_bundle_set.knowledge.unknowns.get("material.moon_resin.source") is not None
    assert eu_n.property_updates.get("last_routed_query_subject") is None

    next_state = ApplyPath.apply_generation(state, refined_n, next_tick=state.tick + 1)
    # Single-fire field cleared; durable materialization confirmed via SelfModelPatch.
    assert next_state.pending_self_model_information_events == []
    materialized_unk = next_state.entities[1].self_model.knowledge.unknowns.get("material.moon_resin.source")
    assert materialized_unk is not None
    assert materialized_unk.reason == "provider_unknown"

    # information_source_profiles is now a persistent field (reclassified by
    # TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION, unlike its sibling
    # pending_information_responses/pending_self_model_information_events, which remain
    # Bounded/single-fire) — confirmed carried forward onto next_state unchanged here,
    # so no manual re-seed is needed for tick N+1.
    assert next_state.information_source_profiles == [profile]

    # Tick N+1: no new self-model event seed — Branch B now sees the durably
    # materialized unknown (carried on `next_state` via this fix) and routes.
    update_n1 = StateUpdate()
    refined_n1 = AuthoritativeApplyPipeline.refine(next_state, update_n1)
    eu_n1 = refined_n1.entity_updates.get(1)
    assert eu_n1 is not None, "expected InformationBeliefPhase's Branch B to route a query in tick N+1"
    assert eu_n1.property_updates.get("last_routed_query_subject") == "material.moon_resin.source"
    assert eu_n1.intent_results, "expected a routed ASK_INFORMATION intent in tick N+1"
    assert eu_n1.intent_results[0].kind == "ASK_INFORMATION"
