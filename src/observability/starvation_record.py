"""
src/observability/starvation_record.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6

The M0 gate's hard check H6 is "no starvation with an untried way in reach". This module writes the typed record it is judged from: one
`StarvationDeathRecord` per starvation death, keyed off the typed cause the writer stamped (`PassiveDeathCause.STARVATION` on the fatal tick),
never off "no attacker" or a hunger threshold.

Observational only (no state field, no behaviour change). The per-subject trail below is a bounded, non-authoritative cache rebuilt from the
state and update streams each run, cleared by `reset_run_state()`, like the extractor's own `_emitted_*` sets.

* column (a): the UNION of the ways the subject's pull judged open and in reach, sampled on its strategic re-decision ticks while it is
  hungry enough to escalate, since its last meal. Until M1's honest-perception child lands the pull sees the true map, so a sample's judged set
  equals the true-map set (`_judged_ways` is that one seam; a test pins the equality).
* `ways_in_reach_at_death`: the true-map set on the state before the fatal tick (column b).
* `ways_attempted`: the ways the subject tried since its last meal, from the resolver's accepted and rejected transfers.

Records, the header and the tally carry severity WARNING so the recorder's DEGRADED and PRESSURE modes (which drop or sample INFO) cannot lose them;
SURVIVAL drops everything, and the tally then exceeds the records, which is the no-data signal.

NO-DATA, never zero: a `starvation_channel_live` header opens the run and a `starvation_channel_tally` closes it with the count of starvation
deaths seen. A run without the header, or with fewer records than deaths seen, did not measure H6 (the metric reads that as `harness_error`).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.ai.goals.ways import WayKind, ways_in_reach
from src.core.enums import PassiveDeathCause
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState, EntityState
from src.observability.events import SimulationEvent

CHANNEL_LIVE_EVENT = "starvation_channel_live"
CHANNEL_TALLY_EVENT = "starvation_channel_tally"
RECORD_EVENT = "starvation_death_record"
_SOURCE = "starvation_record"


def _always(tick: int, entity_id: Optional[int], cadence: int) -> bool:
    """The unconfigured gate: every tick counts (the kernel replaces it with the cadence's stagger)."""
    return True


@dataclass(frozen=True)
class StarvationDeathRecord:
    """One starvation death: who, when, the ways judged open (a), the ways truly open at the end (b), and the ways tried."""
    entity_id: int
    kind: str
    tick: int
    cause_tick: int
    ways_open_in_reach_union: Tuple[WayKind, ...]
    ways_in_reach_at_death: Tuple[WayKind, ...]
    ways_attempted: Tuple[WayKind, ...]
    last_meal_tick: Optional[int]

    def untried_in_reach(self) -> Tuple[WayKind, ...]:
        """H6: the ways the pull judged open and in reach that the subject never attempted."""
        return tuple(w for w in self.ways_open_in_reach_union if w not in self.ways_attempted)

    def to_payload(self) -> Dict[str, Any]:
        """The record as plain JSON-able fields (way kinds by value)."""
        return {
            "entity_id": self.entity_id, "kind": self.kind, "tick": self.tick, "cause_tick": self.cause_tick,
            "ways_open_in_reach_union": [w.value for w in self.ways_open_in_reach_union],
            "ways_in_reach_at_death": [w.value for w in self.ways_in_reach_at_death],
            "ways_attempted": [w.value for w in self.ways_attempted],
            "last_meal_tick": self.last_meal_tick,
        }


def _judged_ways(entity: EntityState, state: AuthoritativeState) -> Tuple[WayKind, ...]:
    """What the subject's pull judges open. The true map until M1's honest-perception child gives the subject its own picture."""
    return ways_in_reach(entity, state)


def _ordered(ways: Set[WayKind]) -> Tuple[WayKind, ...]:
    return tuple(w for w in WayKind if w in ways)


def _attempted_way(source_kind: str, source_id: Any, state: AuthoritativeState) -> Optional[WayKind]:
    """The food way a resolver transfer stands for, or None when it is not a food way."""
    if source_kind == "CARRIED_FOOD":
        return WayKind.CARRIED_FOOD
    if source_kind == "TOWN_SERVICE":
        return WayKind.INN_MEAL
    if source_kind == "SHOP_SELL":
        return WayKind.BUY
    if source_kind == "WAGE":
        return WayKind.WORK_SHIFT
    if source_kind == "NODE":
        try:
            node = state.resource_nodes.get(int(source_id))
        except (TypeError, ValueError):
            return None
        return WayKind.FORAGE if node is not None and food_hunger_recovery(node.yields_item) > 0.0 else None
    return None


class StarvationRecorder:
    """Per-run trail of the ways each hungry subject had open and tried; emits the death record, the live header and the tally."""

    _live: bool = False  # set by the kernel (configure): False under a profile with no observability budget, where the channel writes nothing (not even its header)
    _period: int = 1
    _escalated_hunger: float = float("inf")  # set by the kernel (configure): the hunger the pull begins to escalate at
    _gate: Callable[[int, Optional[int], int], bool] = staticmethod(_always)  # set by the kernel: the cadence's per-subject stagger
    _union: Dict[int, Set[WayKind]] = {}
    _attempted: Dict[int, Set[WayKind]] = {}
    _last_meal: Dict[int, int] = {}
    _deaths_seen: int = 0
    _records_emitted: int = 0
    _header_sent: bool = False
    _recorded: Set[int] = set()
    _last_tick: int = 0

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear the trail, the counts and the header flag at run start (and in test teardown)."""
        cls._live = False
        cls._period = 1
        cls._escalated_hunger = float("inf")
        cls._gate = _always
        cls._union.clear()
        cls._attempted.clear()
        cls._last_meal.clear()
        cls._recorded.clear()
        cls._deaths_seen = 0
        cls._records_emitted = 0
        cls._header_sent = False
        cls._last_tick = 0

    @classmethod
    def configure(cls, strategic_cadence: int, escalated_hunger: float, gate: Callable[[int, Optional[int], int], bool], live: bool = True) -> None:
        """What the kernel (the engine side, which observability may not import) tells the recorder: the profile's strategic re-decision cadence
        (the ticks on which a subject's pull is re-judged), the hunger at which the pull begins to escalate, and the cadence's per-subject stagger; ``live`` is whether the profile has an observability budget at all (a zero-budget profile, e.g. the scale test, accumulates no telemetry, so the channel stays silent and reads as not live)."""
        cls._live = live
        cls._period = max(1, int(strategic_cadence))
        cls._escalated_hunger = float(escalated_hunger)
        cls._gate = gate

    @classmethod
    def observe(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> List[SimulationEvent]:
        """Advance the trail by one tick and return the events it owes (the live header once, a record per starvation death)."""
        if not cls._live:
            return []
        tick = current.tick
        cls._last_tick = tick
        events: List[SimulationEvent] = []
        if not cls._header_sent:
            cls._header_sent = True
            events.append(cls._event(CHANNEL_LIVE_EVENT, tick, None, {"strategic_cadence": cls._period}))
        cls._sample(prior, tick)
        updates = getattr(update, "entity_updates", None) or {}
        for eid in (updates.keys() or current.entities.keys()):
            entity = current.entities.get(eid)
            prior_ent = prior.entities.get(eid)
            if entity is None or prior_ent is None:
                continue
            cls._note_attempts(prior, prior_ent, entity, updates.get(eid), tick)
            record = cls._death(prior, prior_ent, entity, tick)
            if record is not None:
                events.append(cls._event(RECORD_EVENT, tick, record.entity_id, record.to_payload()))
        return events

    @classmethod
    def closing_event(cls, event_counts: Dict[str, int]) -> Optional[SimulationEvent]:
        """The tally for a recorder that recorded this run's live header, else nothing: a channel that never opened must not look live."""
        return cls.tally_event() if event_counts.get(CHANNEL_LIVE_EVENT, 0) > 0 else None

    @classmethod
    def tally_event(cls, tick: Optional[int] = None) -> SimulationEvent:
        """The closing marker: the starvation deaths this run saw against the records it wrote."""
        return cls._event(CHANNEL_TALLY_EVENT, cls._last_tick if tick is None else tick, None,
                          {"starvation_deaths_seen": cls._deaths_seen, "records_emitted": cls._records_emitted})

    @classmethod
    def _sample(cls, prior: AuthoritativeState, tick: int) -> None:
        for eid, entity in prior.entities.items():
            if (entity.biological.hunger >= cls._escalated_hunger and entity.combat.alive
                    and cls._gate(tick, eid, cls._period)):
                cls._union.setdefault(eid, set()).update(_judged_ways(entity, prior))

    @classmethod
    def _note_attempts(cls, prior: AuthoritativeState, prior_ent: EntityState, entity: EntityState, upd: Any, tick: int) -> None:
        if prior_ent.biological.hunger < cls._escalated_hunger:
            return
        ate = entity.biological.hunger < prior_ent.biological.hunger
        for result in (getattr(upd, "intent_results", None) or []):
            way = _attempted_way(getattr(result, "source_kind", ""), getattr(result, "source_id", ""), prior)
            if way is None:
                continue
            cls._attempted.setdefault(entity.id, set()).add(way)
            if ate and getattr(result, "accepted", False) and way in (WayKind.CARRIED_FOOD, WayKind.INN_MEAL):
                cls._union.pop(entity.id, None)
                cls._attempted.pop(entity.id, None)
                cls._last_meal[entity.id] = tick

    @classmethod
    def _death(cls, prior: AuthoritativeState, prior_ent: EntityState, entity: EntityState, tick: int) -> Optional[StarvationDeathRecord]:
        life = entity.lifecycle
        if (life.passive_death_cause is not PassiveDeathCause.STARVATION or life.passive_death_cause_tick != tick
                or entity.id in cls._recorded):
            return None
        cls._recorded.add(entity.id)
        cls._deaths_seen += 1
        cls._records_emitted += 1
        at_death = ways_in_reach(prior_ent, prior)
        union = set(cls._union.pop(entity.id, set())) | set(_judged_ways(prior_ent, prior))
        attempted = cls._attempted.pop(entity.id, set())
        return StarvationDeathRecord(
            entity_id=entity.id, kind=entity.kind, tick=tick, cause_tick=tick,
            ways_open_in_reach_union=_ordered(union), ways_in_reach_at_death=at_death,
            ways_attempted=_ordered(attempted), last_meal_tick=cls._last_meal.get(entity.id))

    @staticmethod
    def _event(event_type: str, tick: int, entity_id: Optional[int], payload: Dict[str, Any]) -> SimulationEvent:
        return SimulationEvent(event_type=event_type, event_category="lifecycle", tick=tick, entity_id=entity_id, severity="WARNING",
                               source_system=_SOURCE, message="", payload=payload, timestamp=time.time())
