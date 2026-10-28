"""TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED.

The strategic winner lookup used to take the FIRST stored project of the kind in dict order, any status: a COMPLETED or ABANDONED first match blocked the resume of a live
sibling, skipped the capacity gate (a duplicate over the cap) and the capacity trim then evicted the entity's own suspended project. The record a goal continues, resumes
or supersedes is now the live one (the current project, else the newest live record), matched on its typed target (rpg-designer's ruling, 2026-10-28, rules 1-5):
a matching target continues (current) or resumes; a different target is superseded by a winning candidate, cap-neutral; no live record goes through the gate.
"""
from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import (
    GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectEnd, ProjectState, ProjectStatus,
    is_live_project, live_projects, project_target_matches, same_kind_record, supersede_record,
)
from src.engine.checkpoint import CanonicalStateHasher
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

FATIGUE = GoalKind.FATIGUE
INN = "7"          # the id of the only inn: the fatigue candidate's target_id in these states
ELSEWHERE = "99"


def _project(pid, status, target=INN, entity=None, created=0, kind=FATIGUE, score=10.0, lock=0):
    objective = ObjectiveState(id=f"o_{pid}", kind=ObjectiveKind.REACH_LOCATION, target=target, target_entity_id=entity, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind=kind, status=status, objectives=[objective], active_objective_id=objective.id, score=score, created_tick=created, lock_until_tick=lock)


def _entity(projects, current=None, max_projects=3, sleep_debt=90.0):
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).cognition(max_active_projects=max_projects).build()
    entity = replace(entity, biological=replace(entity.biological, sleep_debt=sleep_debt))
    strategic = replace(entity.strategic, projects={p.id: p for p in projects}, current_project_id=current,
                        current_objective_id=(projects[0].active_objective_id if current and projects else None))
    return replace(entity, strategic=strategic)


def _state(entity):
    return AuthoritativeState(tick=500, seed=1, entities={entity.id: entity}, buildings={7: BuildingState(id=7, kind="inn", position=(5.0, 5.0), functional=True)})


def _evaluate(entity):
    return StrategicIntelligenceSystem.evaluate_strategic_intent(_state(entity), entity, force=True)


def _apply(entity, update):
    """The projects after the update's add-or-update, in the order the update lists them (a later entry for an id wins)."""
    projects = dict(entity.strategic.projects)
    for p in update.projects_add_or_update or []:
        projects[p.id] = p
    return projects


# --- the lookup -----------------------------------------------------------------------------------------------------------

def test_the_current_project_of_the_kind_is_the_record():
    projects = {p.id: p for p in (_project("a", ProjectStatus.SUSPENDED, created=5), _project("b", ProjectStatus.ACTIVE, created=1))}
    assert same_kind_record(projects, FATIGUE, "b").id == "b"


def test_the_newest_live_record_wins_independent_of_dict_order():
    older, newer = _project("a", ProjectStatus.SUSPENDED, created=3), _project("b", ProjectStatus.SUSPENDED, created=9)
    assert same_kind_record({"a": older, "b": newer}, FATIGUE).id == "b"
    assert same_kind_record({"b": newer, "a": older}, FATIGUE).id == "b"


def test_a_tie_on_created_tick_goes_to_the_larger_id_and_an_active_record_beats_a_suspended_one():
    tie = {p.id: p for p in (_project("a", ProjectStatus.SUSPENDED, created=4), _project("b", ProjectStatus.SUSPENDED, created=4))}
    assert same_kind_record(tie, FATIGUE).id == "b"
    mixed = {p.id: p for p in (_project("a", ProjectStatus.ACTIVE, created=1), _project("b", ProjectStatus.SUSPENDED, created=9))}
    assert same_kind_record(mixed, FATIGUE).id == "a"


@pytest.mark.parametrize("dead", (ProjectStatus.COMPLETED, ProjectStatus.ABANDONED))
def test_a_dead_record_takes_no_part_in_the_lookup(dead):
    projects = {p.id: p for p in (_project("dead", dead, created=99), _project("live", ProjectStatus.SUSPENDED, created=1))}
    assert same_kind_record(projects, FATIGUE).id == "live"
    assert same_kind_record({"dead": projects["dead"]}, FATIGUE) is None


def test_target_match_reads_the_entity_key_when_either_side_has_one_else_the_id_and_none_matches_none():
    assert project_target_matches(_project("p", ProjectStatus.ACTIVE, target="1", entity=14), "2", 14)
    assert not project_target_matches(_project("p", ProjectStatus.ACTIVE, target="1", entity=14), "1", 15)
    assert not project_target_matches(_project("p", ProjectStatus.ACTIVE, target="1", entity=None), "1", 15)
    assert project_target_matches(_project("p", ProjectStatus.ACTIVE, target="7"), 7, None)
    assert not project_target_matches(_project("p", ProjectStatus.ACTIVE, target="7"), "8", None)
    assert project_target_matches(_project("p", ProjectStatus.ACTIVE, target=None), None, None)


# --- the winner: continue / resume / supersede / gate --------------------------------------------------------------------

def test_a_dead_record_first_in_dict_order_no_longer_blocks_the_resume_of_the_live_sibling():
    """Acceptance 1: dead first, a SUSPENDED sibling later at the candidate's target -> it is resumed; no project is created; nothing is evicted."""
    dead = _project("dead", ProjectStatus.ABANDONED, created=1)
    live = _project("live", ProjectStatus.SUSPENDED, created=2)
    entity = _entity([dead, live])
    update = _evaluate(entity)
    assert [(p.id, p.status) for p in update.projects_add_or_update] == [("live", ProjectStatus.ACTIVE)]
    assert update.current_project_id_set == "live"
    assert len(_apply(entity, update)) == 2


def test_the_current_project_at_the_same_target_continues_with_no_update():
    current = _project("cur", ProjectStatus.ACTIVE, created=1)
    entity = _entity([current], current="cur")
    update = _evaluate(entity)
    assert not update.projects_add_or_update
    assert update.current_project_id_set is None


def test_no_live_record_goes_through_the_cap_gate_and_a_full_cap_below_the_onset_refuses():
    """Rule 4 (decision 2): dead records are no reason to pass; at a full cap only an escalated need is admitted."""
    full = [_project(f"l{i}", ProjectStatus.SUSPENDED, kind=f"other{i}") for i in range(3)]
    dead = _project("dead", ProjectStatus.COMPLETED)
    assert _evaluate(_entity(full + [dead], sleep_debt=50.0)).projects_add_or_update == []
    admitted = _evaluate(_entity(full + [dead], sleep_debt=90.0)).projects_add_or_update
    assert [getattr(p.kind, "value", p.kind) for p in admitted] == ["fatigue"]


def _winning_entity():
    """A live SUSPENDED fatigue record at another target, an unrelated current project that the fatigue candidate beats, and an older same-kind duplicate."""
    stale = _project("stale", ProjectStatus.SUSPENDED, target=ELSEWHERE, created=1)
    record = _project("record", ProjectStatus.SUSPENDED, target=ELSEWHERE, created=5)
    current = _project("cur", ProjectStatus.ACTIVE, target="x", kind="travel", score=0.5, created=2)
    return _entity([current, stale, record], current="cur")


def test_a_different_target_candidate_that_wins_the_switch_ends_exactly_one_record_and_creates_one():
    entity = _winning_entity()
    update = _evaluate(entity)
    ended = [p for p in update.projects_add_or_update if p.ended_by is not None]
    assert [(p.id, p.status, p.ended_by) for p in ended] == [("record", ProjectStatus.ABANDONED, ProjectEnd.SUPERSEDED_BY_TARGET)]
    created = [p for p in update.projects_add_or_update if p.id not in entity.strategic.projects]
    assert len(created) == 1 and getattr(created[0].kind, "value", created[0].kind) == "fatigue"
    assert update.current_project_id_set == created[0].id
    after = _apply(entity, update)
    # the older duplicate is left alone and the live count of the kind is unchanged (one ended, one created)
    assert after["stale"].status == ProjectStatus.SUSPENDED and after["stale"].ended_by is None
    live_fatigue = [p for p in live_projects(after).values() if p.kind == FATIGUE]
    assert len(live_fatigue) == 2 and "record" not in {p.id for p in live_fatigue}


def test_a_different_target_candidate_that_loses_the_switch_changes_nothing_and_creates_nothing():
    """The current project is locked and strong: the switch returns None, so no record is ended and no project is created (rule 5 as amended)."""
    stale = _project("stale", ProjectStatus.SUSPENDED, target=ELSEWHERE, created=1)
    current = _project("cur", ProjectStatus.ACTIVE, target="x", kind="travel", score=500.0, created=2, lock=10_000)
    entity = _entity([current, stale], current="cur")
    update = _evaluate(entity)
    assert not update.projects_add_or_update
    assert all(p.ended_by is None for p in _apply(entity, update).values())


def test_the_current_project_of_the_kind_at_another_target_is_kept_when_the_candidate_does_not_beat_its_live_score():
    """The live score of a current project of the candidate's own kind equals the candidate's, so the switch returns None: nothing is ended or created (rule 5 as amended)."""
    current = _project("cur", ProjectStatus.ACTIVE, target=ELSEWHERE, score=0.0, created=1)
    entity = _entity([current], current="cur")
    update = _evaluate(entity)
    assert not update.projects_add_or_update and update.current_project_id_set is None


# --- ended_by: typed, hash-neutral, one writer -------------------------------------------------------------------------------

def test_supersede_record_is_abandoned_with_the_typed_reason():
    ended = supersede_record(_project("r", ProjectStatus.SUSPENDED))
    assert (ended.status, ended.ended_by) == (ProjectStatus.ABANDONED, ProjectEnd.SUPERSEDED_BY_TARGET)
    assert not is_live_project(ended)


def test_ended_by_is_none_by_default_and_absent_from_the_canonical_dict_until_set():
    plain = _entity([_project("r", ProjectStatus.SUSPENDED)])
    assert plain.strategic.projects["r"].ended_by is None
    assert "ended_by" not in plain.to_canonical_dict()["strategic"]["projects"]["r"]
    ended = replace(plain, strategic=replace(plain.strategic, projects={"r": supersede_record(plain.strategic.projects["r"])}))
    assert ended.to_canonical_dict()["strategic"]["projects"]["r"]["ended_by"] == "SUPERSEDED_BY_TARGET"
    assert ended.to_canonical_dict()["strategic"]["projects"]["r"]["status"] != plain.to_canonical_dict()["strategic"]["projects"]["r"]["status"]


def test_a_state_with_no_superseded_project_hashes_exactly_as_it_did_before_the_field_existed():
    """Hash neutrality: the canonical form of a project with ended_by None is the pre-field form (status, kind, objectives, no extra key)."""
    entity = _entity([_project("r", ProjectStatus.SUSPENDED)])
    assert set(entity.to_canonical_dict()["strategic"]["projects"]["r"]) == {"kind", "status", "active_objective_id", "objectives"}
    state = _state(entity)
    assert CanonicalStateHasher.get_hash(state) == CanonicalStateHasher.get_hash(_state(entity))


@pytest.mark.parametrize("ended_by", (None, ProjectEnd.SUPERSEDED_BY_TARGET))
def test_ended_by_round_trips_through_the_state_checkpoint_and_the_canonical_hash(ended_by):
    project = replace(_project("r", ProjectStatus.ABANDONED if ended_by else ProjectStatus.SUSPENDED), ended_by=ended_by)
    state = _state(_entity([project]))
    restored = pickle.loads(pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))   # ScenarioCheckpointer's blob format
    assert restored.entities[1].strategic.projects["r"].ended_by == ended_by
    assert CanonicalStateHasher.get_hash(restored) == CanonicalStateHasher.get_hash(state)
    if ended_by:
        assert CanonicalStateHasher.get_hash(state) != CanonicalStateHasher.get_hash(_state(_entity([replace(project, ended_by=None)])))


def test_a_project_built_without_the_field_loads_with_none():
    """A record or snapshot from before the field: the constructor default is None."""
    legacy = {k: v for k, v in _project("r", ProjectStatus.SUSPENDED).__dict__.items() if k != "ended_by"} if hasattr(_project("r", ProjectStatus.SUSPENDED), "__dict__") else None
    if legacy is None:  # slots dataclass
        import dataclasses
        legacy = {f.name: getattr(_project("r", ProjectStatus.SUSPENDED), f.name) for f in dataclasses.fields(ProjectState) if f.name != "ended_by"}
    assert ProjectState(**legacy).ended_by is None


def test_ended_by_is_set_only_with_abandoned_and_supersede_record_is_its_only_writer():
    """Invariant: ended_by set implies ABANDONED; nothing under src/ writes ended_by except supersede_record."""
    import pathlib
    import re
    assert supersede_record(_project("r", ProjectStatus.ACTIVE)).status == ProjectStatus.ABANDONED
    writers = []
    for path in pathlib.Path("src").rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            if re.search(r"\bended_by\s*=(?!=)", code) and "ended_by: Optional" not in code:
                writers.append(f"{path}:{number}")
    assert writers == [f"src/core/strategic.py:{writers[0].rsplit(':', 1)[1]}"] and len(writers) == 1, writers
    assert "supersede_record" in pathlib.Path(writers[0].rsplit(":", 1)[0]).read_text(encoding="utf-8")


def test_the_cognition_graph_shows_ended_by_beside_the_status_only_when_set():
    from src.systems.strategic_systems.cognition_export import CognitionGraphExporter
    live = _project("r", ProjectStatus.SUSPENDED)
    entity = _entity([live])
    node = next(n for n in CognitionGraphExporter.export(entity).nodes if n.id == "r")
    assert node.attributes["status"] == "SUSPENDED" and "ended_by" not in node.attributes
    ended = replace(entity, strategic=replace(entity.strategic, projects={"r": supersede_record(live)}))
    node = next(n for n in CognitionGraphExporter.export(ended).nodes if n.id == "r")
    assert node.attributes["status"] == "ABANDONED" and node.attributes["ended_by"] == "SUPERSEDED_BY_TARGET"


# --- a matching live record is never left beside a same-target duplicate (designer edges a and b) --------------------------
def test_an_active_record_that_lost_current_project_id_is_made_current_not_duplicated():
    """Several writers clear current_project_id without ending the project (e.g. building arrival), so an ACTIVE non-current record is a reachable state."""
    orphan = _project("orphan", ProjectStatus.ACTIVE, created=3)
    entity = _entity([orphan], current=None)
    update = _evaluate(entity)
    assert update.current_project_id_set == "orphan"
    assert update.current_objective_id_set == orphan.active_objective_id
    assert not update.projects_add_or_update


def test_a_resume_that_returns_none_ends_the_tick_with_no_project_created(monkeypatch):
    suspended = _project("sus", ProjectStatus.SUSPENDED, created=3)
    entity = _entity([suspended])
    monkeypatch.setattr(StrategicIntelligenceSystem, "resume_project", staticmethod(lambda entity, project_id: None))
    update = _evaluate(entity)
    assert not update.projects_add_or_update
    assert update.current_project_id_set is None


@pytest.mark.parametrize("status, current", [(ProjectStatus.ACTIVE, True), (ProjectStatus.ACTIVE, False), (ProjectStatus.SUSPENDED, False)])
def test_a_matching_live_record_never_coexists_with_a_new_project_of_the_same_kind_and_target(status, current):
    record = _project("rec", status, created=3)
    entity = _entity([record], current="rec" if current else None)
    created = [p for p in (_evaluate(entity).projects_add_or_update or []) if p.id != "rec"]
    assert created == []


def test_an_orphan_that_loses_the_margin_leaves_the_current_project_unchanged():
    """An ACTIVE matching record that is not current, beside another live current project, goes through the switch check: a loss changes nothing."""
    other = _project("other", ProjectStatus.ACTIVE, target="x", kind="travel", score=100000.0, created=1)
    orphan = _project("orphan", ProjectStatus.ACTIVE, created=3)
    entity = _entity([other, orphan], current="other")
    update = _evaluate(entity)
    assert update.current_project_id_set is None
    assert not update.projects_add_or_update


def test_an_orphan_that_wins_the_switch_becomes_current_with_nothing_created_and_the_live_count_unchanged():
    other = _project("other", ProjectStatus.ACTIVE, target="x", kind="travel", score=0.5, created=1)
    orphan = _project("orphan", ProjectStatus.ACTIVE, created=3)
    entity = _entity([other, orphan], current="other")
    update = _evaluate(entity)
    assert update.current_project_id_set == "orphan"
    assert update.current_objective_id_set == orphan.active_objective_id
    after = _apply(entity, update)
    assert set(after) == {"other", "orphan"}
    assert after["other"].status == ProjectStatus.SUSPENDED and after["orphan"].status == ProjectStatus.ACTIVE
    # A fresh commitment: stored at the goal's utility now and locked like a freshly switched-in project (t+10), not left at the orphan's old score and lock.
    assert after["orphan"].lock_until_tick == 510 and after["orphan"].score != orphan.score
    assert len([p for p in after.values() if p.status in (ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED)]) == 2


def test_an_active_matching_record_is_made_current_when_the_current_project_is_dead_or_absent():
    done = _project("done", ProjectStatus.COMPLETED, target="x", kind="travel", created=1)
    orphan = _project("orphan", ProjectStatus.ACTIVE, created=3)
    update = _evaluate(_entity([done, orphan], current="done"))
    assert update.current_project_id_set == "orphan"
