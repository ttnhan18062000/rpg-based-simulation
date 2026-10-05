"""Entity-targeted objectives: typed target, live position, and a real lifecycle.

TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES.
"""
from dataclasses import replace

import pytest

from src.ai.goals.scorers import CombatEngageScorer
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, ResourceNodeState
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.tactical import TacticalDecisionSystem
from src.systems.strategic_systems.entity_target_objective import (
    ENTITY_TARGET_PERCEPTION_RADIUS,
    entity_target_outcome as _entity_target_outcome,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue


def _entity(eid, faction, pos, hp=100):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=hp > 0)
        .lifecycle(active=True)
        .build()
    )


def _node(nid, pos):
    return ResourceNodeState(
        id=nid, kind="WOOD", position=pos, yields_item="wood", remaining_charges=5, max_charges=5, required_ticks=3
    )


def _with_combat_project(hero, target_entity_id, *, target="2", target_position=(10.0, 11.0)):
    obj = ObjectiveState(
        id=f"combat_engage_{target}",
        kind=ObjectiveKind.DEFEAT_ENEMY,
        target=target,
        target_position=target_position,
        status=ObjectiveStatus.ACTIVE,
        target_entity_id=target_entity_id,
    )
    proj = ProjectState(
        id="proj_combat_engage_1",
        kind="combat_engage",
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        created_tick=1,
    )
    strat = replace(
        hero.strategic,
        projects={proj.id: proj},
        current_project_id=proj.id,
        current_objective_id=obj.id,
    )
    return replace(hero, strategic=strat), proj, obj


def _state(*entities, tick=50):
    return AuthoritativeState(tick=tick, seed=42, world_time=tick, entities={e.id: e for e in entities})


class TestScorerAndObjectiveCreation:
    def test_combat_engage_scorer_names_the_entity_it_chose(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0))
        score = CombatEngageScorer().score(hero, _state(hero, foe))
        assert score.utility > 0  # non-vacuous: a hostile was found
        assert score.target_entity_id == 2
        assert score.target_id == "2"  # the string form other consumers read is unchanged

    def test_non_entity_scorers_leave_the_typed_field_unset(self):
        from src.ai.goals.scorers import TownScorer

        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        assert TownScorer().score(hero, _state(hero)).target_entity_id is None

    def test_created_objective_carries_the_typed_target(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0))
        up = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero, foe), hero, force=True)
        combat = [p for p in up.projects_add_or_update if p.objectives and p.objectives[0].kind == ObjectiveKind.DEFEAT_ENEMY]
        assert combat, "a hostile neighbour must produce a combat objective"
        assert combat[0].objectives[0].target_entity_id == 2


class TestEntityTargetOutcome:
    def test_none_while_target_alive_and_in_range(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0))
        hero, _, obj = _with_combat_project(hero, 2)
        assert _entity_target_outcome(hero, _state(hero, foe), obj) is None

    def test_dead_target_resolves_and_completes(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0), hp=0)
        hero, _, obj = _with_combat_project(hero, 2)
        assert _entity_target_outcome(hero, _state(hero, foe), obj) == (ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED)

    def test_missing_target_fails_and_abandons(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, _, obj = _with_combat_project(hero, 99, target="99")
        assert _entity_target_outcome(hero, _state(hero), obj) == (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED)

    def test_target_outside_perception_radius_fails_and_abandons(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        far = (10.0 + ENTITY_TARGET_PERCEPTION_RADIUS + 1.0, 10.0)
        foe = _entity(2, Faction.MONSTER_HORDE, far)
        hero, _, obj = _with_combat_project(hero, 2)
        assert _entity_target_outcome(hero, _state(hero, foe), obj) == (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED)

    def test_target_exactly_at_radius_still_holds(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0 + ENTITY_TARGET_PERCEPTION_RADIUS, 10.0))
        hero, _, obj = _with_combat_project(hero, 2)
        assert _entity_target_outcome(hero, _state(hero, foe), obj) is None

    def test_place_objective_is_never_touched(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, _, obj = _with_combat_project(hero, None, target="town_center")
        assert _entity_target_outcome(hero, _state(hero), obj) is None


class TestLifecycleThroughStrategicIntent:
    """The termination is applied by the real evaluate_strategic_intent, not just the helper."""

    def _update(self, foe_kwargs, *, foe_present=True):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, proj, _ = _with_combat_project(hero, 2)
        entities = [hero]
        if foe_present:
            entities.append(_entity(2, Faction.MONSTER_HORDE, **foe_kwargs))
        return proj, StrategicIntelligenceSystem.evaluate_strategic_intent(_state(*entities), hero, force=True)

    def test_dead_target_completes_the_project_and_frees_the_slot(self):
        proj, up = self._update(dict(pos=(10.0, 11.0), hp=0))
        closed = next(p for p in up.projects_add_or_update if p.id == proj.id)
        assert closed.status == ProjectStatus.COMPLETED
        assert closed.objectives[0].status == ObjectiveStatus.RESOLVED
        assert up.current_project_id_set == "" and up.current_objective_id_set == ""

    def test_vanished_target_abandons_the_project(self):
        proj, up = self._update({}, foe_present=False)
        closed = next(p for p in up.projects_add_or_update if p.id == proj.id)
        assert closed.status == ProjectStatus.ABANDONED
        assert closed.objectives[0].status == ObjectiveStatus.FAILED
        assert up.current_project_id_set == ""

    def test_out_of_perception_target_abandons_the_project(self):
        proj, up = self._update(dict(pos=(10.0, 10.0 + ENTITY_TARGET_PERCEPTION_RADIUS + 5.0)))
        closed = next(p for p in up.projects_add_or_update if p.id == proj.id)
        assert closed.status == ProjectStatus.ABANDONED

    def test_live_in_range_target_does_not_end_the_project(self):
        proj, up = self._update(dict(pos=(10.0, 11.0)))
        # force=True may still switch projects (SUSPENDED); what must not happen is a terminal close.
        assert not any(
            p.id == proj.id and p.status in (ProjectStatus.COMPLETED, ProjectStatus.ABANDONED)
            for p in up.projects_add_or_update
        )


class TestResolveTargetPosition:
    def test_typed_target_resolves_to_the_live_position_not_the_snapshot(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (25.0, 4.0))  # moved away from the (10, 11) snapshot
        hero, _, obj = _with_combat_project(hero, 2, target_position=(10.0, 11.0))
        pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(_state(hero, foe), obj)
        assert pos == (25.0, 4.0)
        assert node_id is None and building_id is None

    def test_entity_id_equal_to_a_resource_node_id_is_not_resolved_as_the_node(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (25.0, 4.0))
        node = _node(2, (40.0, 40.0))
        state = replace(_state(hero, foe), resource_nodes={2: node})
        hero, _, obj = _with_combat_project(hero, 2)
        pos, node_id, _ = TacticalDecisionSystem._resolve_target_position(state, obj)
        assert pos == (25.0, 4.0)
        assert node_id is None

    def test_dead_or_missing_entity_has_no_position_and_no_stale_fallback(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        dead = _entity(2, Faction.MONSTER_HORDE, (25.0, 4.0), hp=0)
        hero, _, obj = _with_combat_project(hero, 2, target_position=(10.0, 11.0))
        assert TacticalDecisionSystem._resolve_target_position(_state(hero, dead), obj) == (None, None, None)
        assert TacticalDecisionSystem._resolve_target_position(_state(hero), obj) == (None, None, None)


class TestLegacyPlaceTargetsUnchanged:
    """TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG's cases: the target_position fallback still works."""

    def _obj(self, target, target_position, status=ObjectiveStatus.ACTIVE):
        return ObjectiveState(
            id="o", kind=ObjectiveKind.REACH_LOCATION, target=target, target_position=target_position, status=status
        )

    def test_town_center_string_falls_back_to_target_position(self):
        pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(
            _state(), self._obj("town_center", (3.0, 4.0))
        )
        assert pos == (3.0, 4.0) and node_id is None and building_id is None

    def test_int_castable_resource_node_still_resolves_to_node(self):
        node = _node(7, (8.0, 9.0))
        state = replace(_state(), resource_nodes={7: node})
        pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(state, self._obj("7", (0.0, 0.0)))
        assert pos == (8.0, 9.0) and node_id == 7 and building_id is None

    def test_coordinate_string_still_parses(self):
        pos, _, _ = TacticalDecisionSystem._resolve_target_position(_state(), self._obj("(5.0, 6.0)", None))
        assert pos == (5.0, 6.0)


class TestCanonicalDict:
    def test_unset_target_entity_id_is_omitted_so_unrelated_hashes_do_not_move(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, proj, _ = _with_combat_project(hero, None, target="town_center")
        objectives = hero.to_canonical_dict()["strategic"]["projects"][proj.id]["objectives"]
        assert objectives and "target_entity_id" not in objectives[0]

    def test_set_target_entity_id_is_part_of_canonical_state(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, proj, _ = _with_combat_project(hero, 2)
        objectives = hero.to_canonical_dict()["strategic"]["projects"][proj.id]["objectives"]
        assert objectives[0]["target_entity_id"] == 2


class TestWorkQueueSchedulesTheTermination:
    """An entity holding an ACTIVE project is otherwise only evaluated when dirty or on the sweep, so a
    dead target would be noticed late. The queue must treat it as a transition (tier 3)."""

    @staticmethod
    def _selected(hero, *others):
        from src.core.dirty import DirtySet
        from src.core.updates import StateUpdate

        state = _state(hero, *others)
        # sweep_interval=10 and (tick + id) % 10 != 0 for entity 1 at tick 50: only an urgent tier selects it.
        return StrategicWorkQueue.build(state, StateUpdate(), DirtySet(), budget=10, sweep_interval=10)

    def test_dead_target_schedules_the_holder(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0), hp=0)
        hero, _, _ = _with_combat_project(hero, 2)
        assert 1 in self._selected(hero, foe)

    def test_live_in_range_target_is_not_scheduled(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        foe = _entity(2, Faction.MONSTER_HORDE, (10.0, 11.0))
        hero, _, _ = _with_combat_project(hero, 2)
        assert 1 not in self._selected(hero, foe)

    def test_place_objective_is_not_scheduled(self):
        hero = _entity(1, Faction.HERO_GUILD, (10.0, 10.0))
        hero, _, _ = _with_combat_project(hero, None, target="town_center")
        assert 1 not in self._selected(hero)
