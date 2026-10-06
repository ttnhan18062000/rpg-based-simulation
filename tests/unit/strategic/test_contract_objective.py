"""A project that serves a social contract: who it targets, and when it ends.

TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT. Measured on the corpus: every contract the
cooperation domain creates is held by its own source, so the objective sent the entity to its own position (both projects the four
corpus worlds produced), and a project outlived its contract (16 of 40 project-ticks). Each test builds the situation directly.
"""
from dataclasses import replace

import pytest

from src.ai.goals.social_contract_scorer import SocialContractGoalScorer
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.strategic import (
    ContractKind,
    ContractState,
    ContractStatus,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
    ProjectKind,
    ProjectState,
    ProjectStatus,
)
from src.systems.strategic_systems.entity_target_objective import (
    contract_id_of_project,
    contract_objective_outcome,
    contract_project_id,
    objective_outcome,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.strategic_systems.work_queue import StrategicWorkQueue

CONTRACT_ID = "cnt_recruit_2_1_9"


def _entity(eid, pos, faction=Faction.HERO_GUILD):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .identity(role=EntityRole.HERO, faction=faction)
        .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True)
        .lifecycle(active=True)
        .build()
    )


def _contract(source_id, target_id, status=ContractStatus.ACTIVE, contract_id=CONTRACT_ID):
    return ContractState(
        id=contract_id, kind=ContractKind.RECRUITMENT, source_id=source_id, target_id=target_id, status=status, created_tick=9
    )


def _holding(hero, *contracts):
    strat = replace(hero.strategic, contracts={c.id: c for c in contracts})
    return replace(hero, strategic=strat)


def _contract_project(hero, contract_id=CONTRACT_ID, *, tick=48):
    """``hero`` holding an ACTIVE project that serves ``contract_id`` (built the way the evaluator builds it)."""
    obj = ObjectiveState(
        id=f"obj_recruit_{contract_id}_t{tick}",
        kind=ObjectiveKind.REACH_LOCATION,
        target="2",
        target_position=(10.0, 12.0),
        status=ObjectiveStatus.ACTIVE,
    )
    proj = ProjectState(
        id=contract_project_id(contract_id, tick),
        kind=ProjectKind.COMBAT,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        created_tick=tick,
    )
    strat = replace(hero.strategic, projects={proj.id: proj}, current_project_id=proj.id, current_objective_id=obj.id)
    return replace(hero, strategic=strat), proj, obj


def _state(*entities, tick=50):
    return AuthoritativeState(tick=tick, seed=42, world_time=tick, entities={e.id: e for e in entities})


class TestScorerWithholdsTheObjectiveFromTheContractsOwnSource:
    def test_a_contract_the_holder_sourced_scores_zero(self):
        # entity 2 sourced it AND holds it: the objective would target entity 2's own position
        holder = _holding(_entity(2, (10.0, 10.0)), _contract(source_id=2, target_id=1))
        score = SocialContractGoalScorer().score(holder, _state(holder, _entity(1, (10.0, 14.0))))
        assert score.utility == 0.0 and score.target_id is None

    def test_the_other_party_still_scores_and_targets_the_source(self):
        # control that the guard does not silence the whole scorer: entity 1 holds a contract entity 2 sourced
        source = _entity(2, (10.0, 14.0))
        holder = _holding(_entity(1, (10.0, 10.0)), _contract(source_id=2, target_id=1))
        score = SocialContractGoalScorer().score(holder, _state(holder, source))
        assert score.utility > 0
        assert score.target_id == "2" and score.target_pos == (10.0, 14.0)

    def test_an_own_sourced_contract_does_not_hide_a_contract_from_someone_else(self):
        source = _entity(3, (10.0, 14.0))
        holder = _holding(
            _entity(2, (10.0, 10.0)),
            _contract(source_id=2, target_id=1, contract_id="cnt_recruit_2_1_9"),
            _contract(source_id=3, target_id=2, contract_id="cnt_recruit_3_2_9"),
        )
        score = SocialContractGoalScorer().score(holder, _state(holder, source))
        assert score.metadata["contract_id"] == "cnt_recruit_3_2_9"


class TestEvaluatorMaterializesOnlyTheCounterpartyContract:
    @staticmethod
    def _contract_projects(holder, *others):
        up = StrategicIntelligenceSystem.evaluate_strategic_intent(_state(holder, *others), holder, force=True)
        return [p for p in up.projects_add_or_update if contract_id_of_project(p.id) is not None]

    def test_an_own_sourced_contract_creates_no_project(self):
        holder = _holding(_entity(2, (10.0, 10.0)), _contract(source_id=2, target_id=1))
        assert self._contract_projects(holder, _entity(1, (10.0, 14.0))) == []

    def test_a_contract_sourced_by_someone_else_creates_the_project_with_the_builder_id(self):
        holder = _holding(_entity(1, (10.0, 10.0)), _contract(source_id=2, target_id=1))
        projects = self._contract_projects(holder, _entity(2, (10.0, 14.0)))
        assert [p.id for p in projects] == [contract_project_id(CONTRACT_ID, 50)]  # non-vacuous: one was made


class TestProjectIdRoundTrip:
    @pytest.mark.parametrize("contract_id", ["cnt_recruit_12_33_9", "contract_recruit_1_2_5", "cnt_t7_t9", "c"])
    def test_the_contract_id_is_read_back(self, contract_id):
        assert contract_id_of_project(contract_project_id(contract_id, 48)) == contract_id

    @pytest.mark.parametrize("project_id", ["proj_combat_engage_1", "proj_contract_", "proj_contract_x", "harvest_3"])
    def test_a_project_that_serves_no_contract_has_no_contract_id(self, project_id):
        assert contract_id_of_project(project_id) is None


class TestContractObjectiveOutcome:
    def _outcome(self, status=ContractStatus.ACTIVE, *, contract_present=True):
        hero = _entity(1, (10.0, 10.0))
        if contract_present:
            hero = _holding(hero, _contract(2, 1, status))
        hero, proj, _ = _contract_project(hero)
        return contract_objective_outcome(hero, proj)

    def test_none_while_the_contract_is_active(self):
        assert self._outcome(ContractStatus.ACTIVE) is None

    def test_a_fulfilled_contract_resolves_and_completes(self):
        assert self._outcome(ContractStatus.FULFILLED) == (ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED)

    @pytest.mark.parametrize(
        "status",
        [ContractStatus.FAILED, ContractStatus.BETRAYED, ContractStatus.EXPIRED, ContractStatus.CANCELLED,
         ContractStatus.OFFERED, ContractStatus.ACCEPTED, ContractStatus.COUNTERED],
    )
    def test_any_other_status_fails_and_abandons(self, status):
        assert self._outcome(status) == (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED)

    def test_a_contract_gone_from_the_entity_fails_and_abandons(self):
        assert self._outcome(contract_present=False) == (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED)

    def test_a_project_that_serves_no_contract_is_never_touched(self):
        hero = _entity(1, (10.0, 10.0))
        proj = ProjectState(id="proj_combat_engage_1", kind=ProjectKind.COMBAT, status=ProjectStatus.ACTIVE)
        assert contract_objective_outcome(hero, proj) is None


class TestObjectiveOutcomeDispatch:
    def test_an_entity_targeted_objective_still_ends_by_its_target(self):
        hero = _entity(1, (10.0, 10.0))
        foe = replace(_entity(2, (10.0, 11.0), Faction.MONSTER_HORDE), combat=replace(_entity(2, (0.0, 0.0)).combat, alive=False, hp=0))
        obj = ObjectiveState(id="combat_engage_2", kind=ObjectiveKind.DEFEAT_ENEMY, target="2", status=ObjectiveStatus.ACTIVE,
                             target_entity_id=2)
        proj = ProjectState(id="proj_combat_engage_1", kind=ProjectKind.COMBAT, status=ProjectStatus.ACTIVE, objectives=[obj],
                            active_objective_id=obj.id)
        assert objective_outcome(hero, _state(hero, foe), proj, obj) == (ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED)

    def test_a_contract_project_ends_by_its_contract(self):
        hero, proj, obj = _contract_project(_holding(_entity(1, (10.0, 10.0)), _contract(2, 1, ContractStatus.CANCELLED)))
        assert objective_outcome(hero, _state(hero), proj, obj) == (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED)


class TestLifecycleThroughStrategicIntent:
    """The termination is applied by the real evaluate_strategic_intent, not just the predicate."""

    @staticmethod
    def _update(status):
        hero, proj, _ = _contract_project(_holding(_entity(1, (10.0, 10.0)), _contract(2, 1, status)))
        return proj, StrategicIntelligenceSystem.evaluate_strategic_intent(_state(hero, _entity(2, (10.0, 12.0))), hero, force=True)

    def test_a_fulfilled_contract_completes_the_project_and_frees_the_slot(self):
        proj, up = self._update(ContractStatus.FULFILLED)
        closed = next(p for p in up.projects_add_or_update if p.id == proj.id)
        assert closed.status == ProjectStatus.COMPLETED and closed.objectives[0].status == ObjectiveStatus.RESOLVED
        assert up.current_project_id_set == "" and up.current_objective_id_set == ""

    def test_a_cancelled_contract_abandons_the_project(self):
        proj, up = self._update(ContractStatus.CANCELLED)
        closed = next(p for p in up.projects_add_or_update if p.id == proj.id)
        assert closed.status == ProjectStatus.ABANDONED and closed.objectives[0].status == ObjectiveStatus.FAILED

    def test_an_active_contract_does_not_end_the_project(self):
        proj, up = self._update(ContractStatus.ACTIVE)
        assert not any(
            p.id == proj.id and p.status in (ProjectStatus.COMPLETED, ProjectStatus.ABANDONED) for p in up.projects_add_or_update
        )


class TestWorkQueueSchedulesTheTermination:
    """An entity holding an ACTIVE project is otherwise only evaluated when dirty or on the sweep, so a finished contract would
    be noticed late. The queue must treat it as a transition (tier 3), the same as an entity-targeted objective."""

    @staticmethod
    def _selected(hero):
        from src.core.dirty import DirtySet
        from src.core.updates import StateUpdate

        # sweep_interval=10 and (tick + id) % 10 != 0 for entity 1 at tick 50: only an urgent tier selects it.
        return StrategicWorkQueue.build(_state(hero), StateUpdate(), DirtySet(), budget=10, sweep_interval=10)

    def test_a_fulfilled_contract_schedules_the_holder(self):
        hero, _, _ = _contract_project(_holding(_entity(1, (10.0, 10.0)), _contract(2, 1, ContractStatus.FULFILLED)))
        assert 1 in self._selected(hero)

    def test_an_active_contract_is_not_scheduled(self):
        hero, _, _ = _contract_project(_holding(_entity(1, (10.0, 10.0)), _contract(2, 1, ContractStatus.ACTIVE)))
        assert 1 not in self._selected(hero)
