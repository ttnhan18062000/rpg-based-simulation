"""A panic flight needs a perceived threat (divergence 2.114, Bible 04 tier 1: only a PRESENT threat to life outranks a pressing need).

TCK-20261011-A-PANIC-RETREAT-TO-ITS-OWN-TILE-IS-HELD-WITH-NO-THREAT-IN-SIGHT: the HP, regional-dread and grudge terms of the panic need no
hostile, so a wounded subject with nothing in sight fled "from nothing" to its own tile and stood in a held PANIC_RETREAT (measured 500+
ticks), above hunger in the order of precedence.
"""
from src.core.enums import Faction
from src.engine.cognition import AppraisalSystem, HAZARD_GROWTH_TRAUMA_THRESHOLD
from src.engine.tactical import TacticalDecisionSystem
from tests.unit.combat.test_tactical_destinations import _entity, _state


def _reason(update):
    return update.task.payload_set.get("reason") if update.task is not None and update.task.payload_set else None


def test_a_wounded_subject_with_nothing_in_sight_does_not_flee():
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    assert AppraisalSystem.evaluate_emotional_state(me, []).is_fleeing  # the panic itself is unchanged: it is high
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(_state(me), me)) != "PANIC_RETREAT"


def test_the_same_subject_with_a_hostile_in_sight_still_flees():
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(_state(me, foe), me)) == "PANIC_RETREAT"


def test_regional_dread_alone_gives_no_flight_even_when_it_trips_the_panic_line():
    me = _entity(1, Faction.HERO_GUILD, hp=20, pos=(20.0, 20.0))  # 20% hp: +0.2 panic, below the line on its own
    trauma = HAZARD_GROWTH_TRAUMA_THRESHOLD * 10
    assert AppraisalSystem.evaluate_emotional_state(me, [], trauma).is_fleeing  # dread (+0.3) and the hp term (+0.2) trip the line
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(me), me, [], trauma)
    assert _reason(update) != "PANIC_RETREAT"


def test_a_hostile_beyond_perception_is_not_a_threat():
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    far = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 29.0))
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(_state(me, far), me, [])) != "PANIC_RETREAT"  # not among the neighbours handed in


def test_a_cornered_subject_with_a_threat_still_holds_its_tile():
    """MOV-03 is unchanged: with a threat and no valid destination the flight is a hold on the current tile."""
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
    state = _state(me, foe, regions=())  # no region: no destination
    update = TacticalDecisionSystem.evaluate_entity_intent(state, me)
    assert _reason(update) == "PANIC_RETREAT" and update.task.payload_set["target_position"] == me.navigation.position
