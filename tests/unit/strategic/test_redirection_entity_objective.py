"""The redirection writers must not turn an entity-typed objective into a stale navigation point.

TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK: after a pursuit ended and the navigation
target was cleared, the strategic pass re-asserted `ObjectiveState.target_position` (the snapshot taken when the
objective was created) one pass later, dragging the entity to a stale point. Strategy names WHICH entity; tactics resolve
WHERE to step. A place-targeted objective must keep its point.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.inventory import ItemStack
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.core.updates import StateUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic_systems.redirection import StrategicRedirectionSystem


def _hero_with_objective(*, target_entity_id, target_position=(41.0, 45.0), carrying=False):
    hero = (
        V2EntityBuilder(1).kind("hero").location(42.0, 46.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True).lifecycle(active=True)
        .inventory(items=[ItemStack(item_id="herb", quantity=1)] if carrying else [])
        .build()
    )
    obj = ObjectiveState(
        id="obj", kind=ObjectiveKind.DEFEAT_ENEMY, target="2", target_position=target_position,
        status=ObjectiveStatus.ACTIVE, target_entity_id=target_entity_id,
    )
    proj = ProjectState(id="proj", kind="combat_engage", status=ProjectStatus.ACTIVE, objectives=[obj],
                        active_objective_id="obj", created_tick=1)
    strat = replace(hero.strategic, projects={"proj": proj}, current_project_id="proj", current_objective_id="obj")
    return replace(hero, strategic=strat)


def _enforce(hero):
    # (tick + entity id) % cadence == 0 so the entity is processed; force a full scan so it is relevant.
    state = AuthoritativeState(tick=9, seed=42, world_time=9, entities={hero.id: hero})
    update = replace(StateUpdate(), force_full_scan=True)
    out = StrategicRedirectionSystem.enforce(state, update, SystemCadence())
    return out.entity_updates.get(hero.id)


def _target_set(entity_update):
    nav = entity_update.navigation if entity_update is not None else None
    return None if nav is None else nav.target_set


def test_place_objective_still_gets_its_navigation_point():
    # Control: proves the entity is processed and the writer fires for an untyped objective.
    upd = _enforce(_hero_with_objective(target_entity_id=None))
    assert _target_set(upd) == (41.0, 45.0)


def test_entity_typed_objective_writes_no_navigation_point():
    upd = _enforce(_hero_with_objective(target_entity_id=2))
    assert _target_set(upd) is None


def test_entity_typed_objective_still_suppresses_the_return_to_town_fallback():
    # The objective still owns the direction: a carrying entity must not be sent home (REGROUP) instead.
    # Control: with an UNTYPED objective carrying an item the writer sets the objective point, not REGROUP, so the
    # carrying entity here would only be sent home if the typed branch failed to claim the navigation.
    upd = _enforce(_hero_with_objective(target_entity_id=2, carrying=True))
    nav = upd.navigation if upd is not None else None
    assert nav is None or (nav.target_set is None and nav.movement_mode_set is None)
