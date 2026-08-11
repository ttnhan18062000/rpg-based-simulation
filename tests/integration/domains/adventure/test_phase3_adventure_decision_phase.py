"""
tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py

Phase 3 — AdventureDecisionPhase integration tests.
Verifies entity lifecycle filtering, strategic lock compliance, and transition.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.adventure.phase import AdventureDecisionPhase
from src.core.strategic import ProjectState, ProjectKind, GoalKind, ProjectStatus, ObjectiveState, ObjectiveKind, ObjectiveStatus, StrategicComponent
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.generator import AdventureRouteGenerator


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=5,
        seed=1,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        building_tiles=(),
        terrain=(),
        home_storage={},
        town_center=(0, 0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def test_filters_out_locked_projects():
    # Build entity with a locked strategic project.
    # HP is set low (40/100 = 0.4) so the threat-resolution early-release condition does
    # NOT trigger — the lock must be respected while the entity is still in danger.
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=40, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    
    # Add active locked project until tick 10 (current is 5)
    obj = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_SERVICE, target=None, target_position=None, status=ObjectiveStatus.UNRESOLVED, blocker_ids=[])
    proj = ProjectState(
        id="proj1",
        kind=ProjectKind.RECOVERY,
        status=ProjectStatus.ACTIVE,
        score=1.0,
        lock_until_tick=10,
        objectives=[obj],
        active_objective_id="o1",
        created_tick=1,
    )
    b.replace_self_model(None) # simple default self model
    
    # Set strategic projects
    entity = b.build()
    # Force projects mapping manually
    from src.engine.apply import replace
    new_strat = replace(entity.strategic, projects={"proj1": proj}, current_project_id="proj1", current_objective_id="o1")
    entity = replace(entity, strategic=new_strat)
    
    state = _state([entity])
    
    # Run integration phase
    update = AdventureDecisionPhase.apply(state)
    
    # Should skip hero because project is locked
    assert not update.entity_updates


def _build_hero_with_active_system_b_lock(current_score: float, current_resistance: float) -> AuthoritativeState:
    """Build a hero (HP > 80%, no hostile nearby -> _threat_resolved() True, so the per-hero
    own-lock gate at phase.py:150 does NOT skip the entity) with current_project_id pointing
    at an ACTIVE System-B (GoalKind-typed) ProjectState whose lock has not yet expired at
    state.tick=5."""
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=90, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)

    obj = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=None, target_position=None, status=ObjectiveStatus.UNRESOLVED, blocker_ids=[])
    proj = ProjectState(
        id="proj_system_b",
        kind=GoalKind.COMBAT_ENGAGE,
        status=ProjectStatus.ACTIVE,
        score=current_score,
        lock_until_tick=100,
        objectives=[obj],
        active_objective_id="o1",
        created_tick=1,
    )
    entity = b.build()
    from src.engine.apply import replace
    new_strat = replace(
        entity.strategic,
        projects={"proj_system_b": proj},
        current_project_id="proj_system_b",
        current_objective_id="o1",
    )
    if current_resistance is not None:
        from dataclasses import replace as dc_replace
        new_strat = dc_replace(new_strat, profile=dc_replace(new_strat.profile, interruption_resistance=current_resistance))
    entity = replace(entity, strategic=new_strat)

    return _state([entity])


def test_apply_respects_active_system_b_lock(monkeypatch):
    """AC3: a hero with current_project_id pointing at an ACTIVE System-B project with an
    unexpired lock, where AdventureDecisionPhase independently proposes a new route the same
    tick whose real (post-Step-2) score does not clear the generalized bypass gate -- apply()
    must NOT overwrite current_project_id while the System-B lock is active."""
    state = _build_hero_with_active_system_b_lock(current_score=50.0, current_resistance=0.3)

    weak_route = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=0.5,
        expected_benefit=0.3,
        expected_risk=0.5,
    )
    monkeypatch.setattr(
        AdventureRouteGenerator, "generate",
        staticmethod(lambda entity, state=None, opportunities=(): (weak_route,)),
    )

    update = AdventureDecisionPhase.apply(state)

    # The System-B project's current_project_id must be preserved: either no entity_update
    # entry for this hero at all, or one whose strategic update does not overwrite
    # current_project_id_set to the new route's project id.
    if 1 in update.entity_updates:
        strat = update.entity_updates[1].strategic
        assert strat is None or not strat.current_project_id_set or strat.current_project_id_set == "proj_system_b"


def test_apply_switches_when_candidate_clears_bar(monkeypatch):
    """Inverse of test_apply_respects_active_system_b_lock: the new route's real (post-Step-2)
    score clears both the current project's normalized effective score and the urgency floor
    (and the unchanged raw effective_current_score check) after normalization -- apply() must
    still commit the switch, proving Step 7's rewiring doesn't over-correct into 'never switch
    while any lock exists'.

    current.score/resistance are kept low (rather than a realistic mid/high System-B score) so
    the function's unchanged final raw `candidate.score > effective_current_score` check also
    clears -- that raw check is independent of the lock-bypass gate and applies to every path,
    so a System-A-scale candidate (~0-2.9) can only ever clear it against a current whose raw
    score+margin is comparably small (see test_score_normalization.py's own note on this same
    structural point)."""
    state = _build_hero_with_active_system_b_lock(current_score=1.0, current_resistance=0.0)

    strong_route = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=1.0,
        expected_benefit=15.0,
        expected_risk=0.0,
    )
    monkeypatch.setattr(
        AdventureRouteGenerator, "generate",
        staticmethod(lambda entity, state=None, opportunities=(): (strong_route,)),
    )

    update = AdventureDecisionPhase.apply(state)

    assert 1 in update.entity_updates
    strat = update.entity_updates[1].strategic
    assert strat is not None
    assert strat.current_project_id_set not in (None, "", "proj_system_b")


def test_zero_regression_human_practical_humanoid_hero_archetype_native():
    """TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY Step 6: an archetype-native hero
    (identity.role=HERO, properties carrying explicit archetype_id/role_id/cognition_profile_id
    per ArchetypeEntityFactory.build_entity's real output shape, src/entities/archetype_factory.py
    :48-57) is included under the new cognition-profile eligibility check exactly as it was
    under the old role-only check -- both checks agree this entity is eligible, since
    practical_humanoid.supports_adventure_routing=True and identity.role==HERO also holds."""
    b = V2EntityBuilder(1)
    b.identity(
        role=0,  # EntityRole.HERO
        properties={
            "archetype_id": "adventurer_hero",
            "race_id": "human",
            "faction_id": "hero_guild",
            "role_id": "hero",
            "cognition_profile_id": "practical_humanoid",
        },
    )
    entity = b.build()
    state = _state([entity])

    update = AdventureDecisionPhase.apply(state)

    # No opportunities are wired in this minimal state, so the service defers with a reason
    # rather than picking a route -- that deferral is itself the observable proof the entity
    # was evaluated at all (excluded entities never reach the decision service and produce no
    # entity_update whatsoever).
    assert 1 in update.entity_updates
    assert update.entity_updates[1].property_updates.get("last_defer_reason")


def test_zero_regression_human_practical_humanoid_hero_legacy_guard_shape():
    """TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY Step 7: a hero spawned via the
    hero_adventurers world module's real shape (WorldEntitySpawner._spawn_legacy_guard,
    src/worldassembly/entity_spawner.py:118-127) has NO cognition_profile_id key and an
    explicitly-None role_id in identity.properties -- the confirmed real-corpus gap
    (investigation.md Risk 1). This is the single highest-value zero-regression test: it fails
    loudly if the Tier-3 EntityRole.HERO -> 'hero' role default fallback is missing or wrong,
    since both of the only two real corpus worlds with ENABLE_ADVENTURE_ROUTING on today spawn
    heroes through exactly this shape."""
    b = V2EntityBuilder(1)
    b.identity(
        role=0,  # EntityRole.HERO
        properties={
            "archetype_id": None,
            "race_id": None,
            "role_id": None,
            "faction_id": None,
        },
    )
    entity = b.build()
    state = _state([entity])

    update = AdventureDecisionPhase.apply(state)

    assert 1 in update.entity_updates
    assert update.entity_updates[1].property_updates.get("last_defer_reason")


def test_adventure_decision_does_not_discard_earlier_phase_updates():
    """TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING: the adventure_decision phase's
    own run_phase call site in pipeline.py previously returned AdventureDecisionPhase.apply()'s
    fresh StateUpdate directly instead of merging it into the accumulated update -- silently
    discarding every phase's output that ran earlier in the same tick (diplomatic_transitions,
    information_belief, cooperation, contracts/blacksmith) whenever ENABLE_ADVENTURE_ROUTING=ON.
    Real, controlled proof this was NOT an RNG-consumption-order bug (the ticket's own original
    hypothesis): compute_transitions() is a pure function of state.factions and produced the
    identical FactionUpdate list regardless of the flag -- the discard happened strictly inside
    refine(), after diplomatic_transitions merged its updates, before refine() returned."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.state import FactionState, DiplomaticState
    from src.systems.world_systems.generator import EntityGenerator
    from src.domains.optimization.feature_flags import FeatureMode

    # Two factions with tension high enough that diplomatic_state_machine.compute_transitions()
    # produces a real NEUTRAL -> TENSE FactionUpdate for this pair (threshold: pair_tension > 0.4).
    factions = {
        "alpha": FactionState(faction_id="alpha", tension_level=0.5),
        "beta": FactionState(faction_id="beta", tension_level=0.5),
    }
    hero = EntityGenerator(seed=1).spawn_hero((10.0, 10.0))

    state = _state([hero])
    from dataclasses import replace as dc_replace
    state = dc_replace(
        state, factions=factions, building_tiles={},
        feature_flags={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON},
    )

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())

    assert refined.faction_updates, (
        "diplomatic_transitions' own real FactionUpdate output was discarded by the "
        "adventure_decision phase -- it must survive refine() when routing is ON"
    )
    assert any(
        fu.faction_id in ("alpha", "beta") and fu.diplomatic_relations_set
        for fu in refined.faction_updates
    )
