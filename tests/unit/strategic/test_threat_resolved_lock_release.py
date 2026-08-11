"""
tests/unit/strategic/test_threat_resolved_lock_release.py

AC3 (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION): a COMBAT_RETREAT/RECOVER-kind
project locked via a non-adventure ("System B") caller, with the triggering threat
resolved (HP > 80%, no hostile within radius 10.0), is now also early-released by
StrategicIntelligenceSystem.evaluate_project_switch()'s own internal lock-expiry check --
closing the STRAT-236 documented-but-never-wired gap. This file is dedicated,
generalized-scope coverage, distinct from tests/unit/systems/test_spawn_lock_condition.py's
adventure-domain-specific coverage (which remains untouched and is exercised via
AdventureDecisionPhase.apply() instead of calling evaluate_project_switch() directly).
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, CombatComponent
from src.core.strategic import (
    GoalKind,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectState,
    ProjectStatus,
)
from src.engine.apply import replace as fast_replace
from src.systems.strategic import StrategicIntelligenceSystem


def _make_state(entities: list, tick: int = 5) -> AuthoritativeState:
    """Minimal AuthoritativeState fixture, mirroring
    tests/unit/systems/test_spawn_lock_condition.py's own _make_state() shape."""
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=tick,
        seed=42,
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
        town_center=(0.0, 0.0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def _make_hero_with_combat_retreat_lock(hp: int, max_hp: int = 100, entity_id: int = 1):
    """Build a hero whose current project is a GoalKind.COMBAT_RETREAT project locked via
    a direct assignment onto entity.strategic -- never routed through
    AdventureDecisionPhase -- to prove the generalized (non-adventure) caller path."""
    b = V2EntityBuilder(entity_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.location(5.0, 5.0)

    obj = ObjectiveState(
        id=f"obj_retreat_{entity_id}",
        kind=ObjectiveKind.REACH_SERVICE,
        target=None,
        target_position=None,
        status=ObjectiveStatus.UNRESOLVED,
        blocker_ids=[],
    )
    proj = ProjectState(
        id=f"proj_retreat_{entity_id}",
        kind=GoalKind.COMBAT_RETREAT,
        status=ProjectStatus.ACTIVE,
        score=10.0,
        lock_until_tick=100,
        objectives=[obj],
        active_objective_id=obj.id,
        created_tick=1,
    )

    entity = b.build()
    new_strat = fast_replace(
        entity.strategic,
        projects={proj.id: proj},
        current_project_id=proj.id,
    )
    return fast_replace(entity, strategic=new_strat)


def _make_hostile(entity_id: int = 99, position=(5.0, 5.0), hp: int = 100):
    b = V2EntityBuilder(entity_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2, alive=True))
    b.location(*position)
    b.identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
    return b.build()


def test_combat_retreat_project_locked_via_system_b_early_released_when_threat_resolved():
    """HP > 80%, no hostile in range, lock still active by tick -- the GoalKind.COMBAT_RETREAT
    project locked directly (not through AdventureDecisionPhase) is early-released via
    evaluate_project_switch()'s own internal check, and the raw comparison alone decides."""
    hero = _make_hero_with_combat_retreat_lock(hp=100, max_hp=100)
    state = _make_state([hero], tick=50)

    # Scored to clearly win the raw comparison (score=10, no retention margin since profile
    # defaults to interruption_resistance=0.0 -> effective_current_score=10).
    candidate = ProjectState(
        id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=999.0
    )

    result = StrategicIntelligenceSystem.evaluate_project_switch(
        hero, candidate, current_tick=50, state=state
    )
    assert result is not None
    assert result.current_project_id_set == "rival"


def test_combat_retreat_project_locked_via_system_b_retained_when_threat_still_active():
    """Same setup, but a hostile is present within radius 10.0 -- the threat has not
    resolved, so the lock is still enforced and the pre-existing percentage/urgency-floor
    gate still runs. A candidate scored to fail that gate is blocked (result is None),
    proving the new check is genuinely conditional, not an unconditional bypass."""
    hero = _make_hero_with_combat_retreat_lock(hp=100, max_hp=100)
    hostile = _make_hostile(entity_id=99, position=(6.0, 6.0))
    state = _make_state([hero, hostile], tick=50)

    # candidate_pct = 40/100 = 0.4, below the 0.8 urgency floor -> blocked by the
    # pre-existing gate, which still runs since threat_resolved is False here.
    candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=40.0)

    result = StrategicIntelligenceSystem.evaluate_project_switch(
        hero, candidate, current_tick=50, state=state
    )
    assert result is None
