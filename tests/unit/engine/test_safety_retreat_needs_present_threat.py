"""TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07.

World Rule AGENCY-07: a cautious disposition lowers the bar at which a threat makes a subject run and never
makes it run by itself. Before this ticket the SAFETY_PRESSURE_RETREAT branch fired on `hostiles and
safety_pressure > 0.75`, so every `high`-safety entity fled the moment any hostile was perceived, at full
health, with the hostile far away and not targeting it. These tests pin the present-threat gate.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.content.repository import CatalogRepository
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_threat import (
    CAUTIOUS_SAFETY_PRESSURE,
    ThreatTerm,
    present_threat_terms,
    safety_retreat_warranted,
)


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _entity(eid, faction, pos, *, hp=100, max_hp=100, atk=None, **props):
    e = (
        V2EntityBuilder(eid).kind("hero" if faction == Faction.HERO_GUILD else "monster")
        .location(float(pos[0]), float(pos[1])).identity(faction=faction)
        .combat(hp=hp, max_hp=max_hp, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True).build()
    )
    if atk is not None:
        e = replace(e, combat=replace(e.combat, atk=atk))
    if props:
        e = replace(e, identity=replace(e.identity, properties={**(e.identity.properties or {}), **props}))
    return e


def _cautious(pos=(0.0, 0.0), **kw):
    # cautious_commoner: a `high` safety drive, so safety_pressure 0.9 (data/content/living/drive_profiles.yaml)
    return _entity(1, Faction.HERO_GUILD, pos, drive_profile_id="cautious_commoner", **kw)


def _hostile(pos, *, targeting=None, last_position=None, **kw):
    m = _entity(2, Faction.MONSTER_HORDE, pos, **kw)
    if targeting is not None:
        m = replace(m, task=replace(m.task, payload={"target_id": targeting}))
    if last_position is not None:
        m = replace(m, navigation=replace(m.navigation, last_position=last_position))
    return m


def _reason(subject, hostile):
    state = AuthoritativeState(tick=1, seed=1, entities={subject.id: subject, hostile.id: hostile})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, subject)
    payload = (update.task.payload_set or {}) if update is not None and update.task is not None else {}
    return payload.get("reason")


# --- the defect: a trait must not decide flight on sight ------------------------------------------------------

def test_a_cautious_subject_at_full_health_does_not_flee_a_distant_untargeting_hostile():
    reason = _reason(_cautious(), _hostile((8.0, 0.0)))
    assert reason != "SAFETY_PRESSURE_RETREAT"


def test_the_same_subject_does_flee_once_that_distant_hostile_targets_it():
    """Positive control: the hostile is perceived and the branch is reachable at this distance."""
    assert _reason(_cautious(), _hostile((8.0, 0.0), targeting=1)) == "SAFETY_PRESSURE_RETREAT"


@pytest.mark.parametrize("name,subject,hostile", [
    ("wounded", _cautious(hp=60), _hostile((8.0, 0.0))),
    ("adjacent", _cautious(), _hostile((1.0, 0.0))),
    ("targeted", _cautious(), _hostile((8.0, 0.0), targeting=1)),
    ("closing", _cautious(), _hostile((4.0, 0.0), last_position=(6.0, 0.0))),
    ("outmatched", _cautious(), _hostile((3.0, 0.0), atk=80, max_hp=400, hp=400)),
])
def test_each_present_threat_makes_a_cautious_subject_flee(name, subject, hostile):
    assert _reason(subject, hostile) == "SAFETY_PRESSURE_RETREAT", name


# --- the terms -------------------------------------------------------------------------------------------------

def test_no_term_holds_for_a_healthy_subject_and_a_distant_untargeting_hostile():
    assert present_threat_terms(_cautious(), [_hostile((8.0, 0.0))]) == []


def test_each_term_is_reported_by_name():
    assert present_threat_terms(_cautious(hp=60), [_hostile((8.0, 0.0))]) == [ThreatTerm.WOUNDED]
    assert present_threat_terms(_cautious(), [_hostile((1.0, 0.0))])[0] == ThreatTerm.ADJACENT
    assert present_threat_terms(_cautious(), [_hostile((8.0, 0.0), targeting=1)]) == [ThreatTerm.TARGETED]
    assert present_threat_terms(_cautious(), [_hostile((4.0, 0.0), last_position=(6.0, 0.0))]) == [ThreatTerm.CLOSING]
    assert ThreatTerm.OUTMATCHED in present_threat_terms(_cautious(), [_hostile((3.0, 0.0), atk=80, max_hp=400, hp=400)])


def test_a_hostile_stepping_away_or_beyond_range_is_not_closing():
    assert present_threat_terms(_cautious(), [_hostile((4.0, 0.0), last_position=(3.0, 0.0))]) == []
    assert present_threat_terms(_cautious(), [_hostile((6.0, 0.0), last_position=(8.0, 0.0))]) == []


def test_a_strong_hostile_beyond_threat_range_does_not_outmatch_the_subject():
    assert present_threat_terms(_cautious(), [_hostile((9.0, 0.0), atk=80, max_hp=400, hp=400)]) == []


def test_a_bystander_targeted_by_the_hostile_is_not_a_threat_to_the_subject():
    assert present_threat_terms(_cautious(), [_hostile((8.0, 0.0), targeting=99)]) == []


# --- the gate ----------------------------------------------------------------------------------------------------

def test_the_gate_needs_both_the_disposition_and_a_present_threat():
    adjacent = [_hostile((1.0, 0.0))]
    assert safety_retreat_warranted(_cautious(), adjacent, 0.9)
    assert not safety_retreat_warranted(_cautious(), adjacent, CAUTIOUS_SAFETY_PRESSURE)  # not cautious: 0.75 is the bar
    assert not safety_retreat_warranted(_cautious(), [_hostile((8.0, 0.0))], 0.9)  # cautious, nothing present
    assert not safety_retreat_warranted(_cautious(), [], 0.9)
