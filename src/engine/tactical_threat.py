"""
src/engine/tactical_threat.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07

World Rule AGENCY-07 (docs/world_rules/knowledge-agency/agency-decision.md): a cautious disposition
lowers the bar at which a threat makes a subject run, and never makes it run by itself. Flight needs a
present threat to the subject: its own wounds, a hostile adjacent or closing on it, being targeted, or
being clearly outmatched. Merely seeing a hostile somewhere is not such a threat.

`safety_retreat_warranted` is the gate of the tactical SAFETY_PRESSURE_RETREAT branch. The disposition is
`safety_pressure` (a static trait from the entity's need and drive profiles); the present threat is
`present_threat_terms`. Pure reads of already-perceived entities: no state is written here.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Sequence, Tuple

from src.core.movement_modes import MovementMode
from src.core.state import EntityState
from src.domains.combat_engagement.power import apparent_power
from src.engine.need_wake import NEED_WAKE_CADENCE

# A subject whose safety disposition is above this is "cautious" for the SAFETY_PRESSURE_RETREAT branch (the
# value that gate has always used; content has levels 0.9 and 0.75 and below, so it separates high from the rest).
CAUTIOUS_SAFETY_PRESSURE = 0.75

# A cautious subject counts itself wounded below this fraction of max HP. It matches the apparent-power
# "wounded" boundary (power.py), and it is deliberately looser than the panic gate's 0.4 first term: the
# disposition is what lowers the bar.
WOUNDED_HP_RATIO = 0.7
# A hostile this close (Manhattan) is adjacent: it can strike the subject now (melee reach is orthogonal, MOV-07).
ADJACENT_DISTANCE = 1.0
# A hostile counts as near enough to close on, or to outmatch, the subject within this Manhattan distance.
THREAT_RANGE = 4.0
# Near hostiles outmatch the subject when their summed apparent power reaches this multiple of its own.
OUTMATCH_RATIO = 1.5


class ThreatTerm(str, Enum):
    """The AGENCY-07 present-threat terms, named so a retreat can be explained."""

    WOUNDED = "WOUNDED"
    ADJACENT = "ADJACENT"
    TARGETED = "TARGETED"
    CLOSING = "CLOSING"
    OUTMATCHED = "OUTMATCHED"


def _distance(a: EntityState, position: Tuple[float, float]) -> float:
    ax, ay = a.navigation.position
    return abs(ax - position[0]) + abs(ay - position[1])


def _is_closing(entity: EntityState, hostile: EntityState, distance_now: float) -> bool:
    """The hostile is within threat range and nearer than it was at its previous position."""
    previous = hostile.navigation.last_position
    return distance_now <= THREAT_RANGE and previous is not None and distance_now < _distance(entity, previous)


def present_threat_terms(entity: EntityState, hostiles: Sequence[EntityState]) -> List[ThreatTerm]:
    """
    The AGENCY-07 threat terms that hold for `entity` given the hostiles it perceives, in a fixed order; empty when
    nothing present threatens it (seeing a distant, untargeting hostile at full health is not a threat).
    """
    terms: List[ThreatTerm] = []
    if entity.combat.hp / max(1, entity.combat.max_hp) < WOUNDED_HP_RATIO:
        terms.append(ThreatTerm.WOUNDED)
    distances = [_distance(entity, h.navigation.position) for h in hostiles]
    if any(d <= ADJACENT_DISTANCE for d in distances):
        terms.append(ThreatTerm.ADJACENT)
    if any(h.task.payload.get("target_id") == entity.id for h in hostiles):
        terms.append(ThreatTerm.TARGETED)
    if any(_is_closing(entity, h, d) for h, d in zip(hostiles, distances)):
        terms.append(ThreatTerm.CLOSING)
    near_power = sum(apparent_power(h) for h, d in zip(hostiles, distances) if d <= THREAT_RANGE)
    if near_power > 0.0 and near_power >= OUTMATCH_RATIO * apparent_power(entity):
        terms.append(ThreatTerm.OUTMATCHED)
    return terms


def safety_retreat_warranted(entity: EntityState, hostiles: Sequence[EntityState], safety_pressure: float) -> bool:
    """A cautious subject retreats only from a present threat; it never retreats from a hostile merely seen."""
    return bool(hostiles) and safety_pressure > CAUTIOUS_SAFETY_PRESSURE and bool(present_threat_terms(entity, hostiles))


# (a) The typed work that is an attack or a pursuit with the subject as its target (memo row 88 item 5). A task kept current until the hostile's
# next decision still counts, with no reach test: a committed act, at most one decision stale.
ATTACK_ACTIONS = frozenset({"ATTACK", "SKILL"})  # ENTITY_ACT: a basic attack, a skill, and the queued swing HOLD_BETWEEN_BLOWS (action ATTACK)
PURSUIT_MODES = frozenset({MovementMode.PURSUE, MovementMode.INTERCEPT})  # ENTITY_MOVE: closing on, or cutting off, the target
BRACKETING_REASON = "BRACKETING"  # ENTITY_MOVE in REPOSITION mode (tactical.py): the one move whose only typed mark is its reason, because REPOSITION also carries SEEK_COVER


def _task_acts_on(hostile: EntityState, subject_id: int) -> bool:
    """(a) The hostile's current task is an attack or a pursuit whose typed target is the subject. A bare `target_id` on any other task does not count
    (watching, guarding, kiting, taking cover, a chokepoint hold)."""
    task = hostile.task
    if task is None or task.payload.get("target_id") != subject_id:
        return False
    if task.work_kind == "ENTITY_ACT":
        return task.payload.get("action") in ATTACK_ACTIONS
    if task.work_kind == "ENTITY_MOVE":
        return hostile.navigation.movement_mode in PURSUIT_MODES or task.payload.get("reason") == BRACKETING_REASON
    return False


def _hit_acts_on(hostile: EntityState, subject: EntityState, tick: int) -> bool:
    """(b) The hostile is the body that last took hp from the subject, and that hit is within one brain cadence (opportunity hits included: they are hits)."""
    hit_tick = subject.combat.last_hit_tick
    return hit_tick is not None and subject.combat.last_attacker_id == hostile.id and tick - hit_tick <= NEED_WAKE_CADENCE


def hostile_acts_on(hostile: EntityState, subject: EntityState, tick: int) -> bool:
    """True when `hostile` acts on `subject` by an act: its current task attacks or pursues the subject, or it hit the subject within the window."""
    return _task_acts_on(hostile, subject.id) or _hit_acts_on(hostile, subject, tick)
