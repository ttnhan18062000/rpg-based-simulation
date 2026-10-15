"""
src/observability/death_ledger.py
───────────────────────────────────────────────────────────────────────────────
The death ledger (TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH): a typed source for every hp loss, and the deaths by cause.

The durable record of a death (cause, tick, last attacker, hazard kind) is `LifecycleComponent.death_record`, written by the lifecycle resolver. What no
state can hold is where each hp went: the starving drain is taken inside the apply path's passive branch and no update carries it. This bounded,
non-authoritative, run-scoped observer reads the staged update and the two states and writes nothing back. Each tick it splits every hp loss into hit,
hazard and starving drain (a loss none explains is UNATTRIBUTED, a count that must stay at zero), keeps the hp each body lost by source, and on the
tick a death record first appears tallies the death by cause and writes one row with that body's hp lost by source (so the dominant source is read,
not rebuilt).

Like the run ledger: a live header opens the run, ONE tally closes it, both WARNING so the DEGRADED/PRESSURE recorder modes keep them; a recorder
that never saw the header writes no tally, and a silent ledger reads as no-data, never as zero.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set

from src.ai.goals.kind_group import is_person, kind_group
from src.core.death_cause import DeathCause, HpLossSource
from src.core.state import AuthoritativeState, EntityState
from src.observability.events import SimulationEvent

LEDGER_LIVE_EVENT = "death_ledger_live"
LEDGER_TALLY_EVENT = "death_ledger_tally"
_SOURCE = "death_ledger"
MAX_RECORDS = 5000  # a run's deaths: far above any measured world; past it the count still grows and the records stop


def _key(*parts: Any) -> str:
    return "|".join(str(p) for p in parts)


class DeathLedger:
    """Per-run death records and hp-loss totals; every key is ``group|...`` with the group from ``kind_group``."""

    _live: bool = False
    _header_sent: bool = False
    _last_tick: int = 0
    _starving_line: float = float("inf")  # set by the kernel (configure): the hunger at which the passive drain takes hp
    _deaths: Dict[str, int] = {}  # group|cause|person
    _hp_lost: Dict[str, int] = {}  # group|source
    _records: List[Dict[str, Any]] = []
    _by_entity: Dict[int, Dict[str, int]] = {}  # entity id -> hp lost by source so far
    _unrecorded: Set[int] = set()  # bodies seen dying with no death reason yet; any still here at the close are UNKNOWN

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear every counter and the header flag at run start (and in test teardown)."""
        cls._live = False
        cls._header_sent = False
        cls._last_tick = 0
        cls._starving_line = float("inf")
        cls._deaths = {}
        cls._hp_lost = {}
        cls._records = []
        cls._by_entity = {}
        cls._unrecorded = set()

    @classmethod
    def configure(cls, starving_line: float, live: bool = True) -> None:
        """What the kernel gives the ledger: the engine's starving line (observability may not import it) and whether the profile has a budget."""
        cls._starving_line = float(starving_line)
        cls._live = live

    @classmethod
    def observe(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> List[SimulationEvent]:
        """Count one tick: the live header once, then every hp loss by source and every death record that first appears; silent when not live."""
        if not cls._live:
            return []
        tick = current.tick
        cls._last_tick = tick
        events: List[SimulationEvent] = []
        if not cls._header_sent:
            cls._header_sent = True
            events.append(cls._event(LEDGER_LIVE_EVENT, tick, {"starving_line": cls._starving_line}))
        updates = getattr(update, "entity_updates", None) or {}
        for eid, entity in current.entities.items():
            before = prior.entities.get(eid)
            if before is None:
                continue
            cls._count_hp_loss(eid, before, entity, updates.get(eid))
            cls._record_death(tick, eid, before, entity)
        return events

    @classmethod
    def _count_hp_loss(cls, eid: int, before: EntityState, entity: EntityState, upd: Any) -> None:
        loss = before.combat.hp - entity.combat.hp
        if loss <= 0:
            return
        combat = getattr(upd, "combat", None)
        hazard = min(loss, int(getattr(combat, "hazard_damage", 0) or 0))
        hit = min(loss - hazard, max(0, -int(getattr(combat, "hp_delta", 0) or 0) - hazard))
        rest = loss - hazard - hit
        # The passive branch takes hp exactly when the hunger it reads (the post-update hunger) is at the starving line; no update carries it.
        passive = HpLossSource.STARVATION if rest > 0 and entity.biological.hunger >= cls._starving_line else HpLossSource.UNATTRIBUTED
        group = kind_group(entity)
        for source, amount in ((HpLossSource.HIT, hit), (HpLossSource.HAZARD, hazard), (passive, rest)):
            if amount > 0:
                cls._hp_lost[_key(group, source.value)] = cls._hp_lost.get(_key(group, source.value), 0) + amount
                mine = cls._by_entity.setdefault(eid, {})
                mine[source.value] = mine.get(source.value, 0) + amount

    @classmethod
    def _record_death(cls, tick: int, eid: int, before: EntityState, entity: EntityState) -> None:
        if before.combat.alive and not entity.combat.alive and entity.lifecycle.death_record is None:
            cls._unrecorded.add(eid)
        if before.lifecycle.death_record is not None or entity.lifecycle.death_record is None:
            return
        cls._unrecorded.discard(eid)
        record = entity.lifecycle.death_record
        group = kind_group(entity)
        person = int(bool(is_person(entity)))
        cls._deaths[_key(group, record.cause.value, person)] = cls._deaths.get(_key(group, record.cause.value, person), 0) + 1
        if len(cls._records) < MAX_RECORDS:
            cls._records.append({"entity_id": eid, "group": group, "person": bool(person), "tick": tick, "cause": record.cause.value,
                                 "hp_lost": dict(sorted(cls._by_entity.get(eid, {}).items()))})
        cls._by_entity.pop(eid, None)

    @classmethod
    def closing_event(cls, event_counts: Dict[str, int]) -> Optional[SimulationEvent]:
        """The tally for a recorder that recorded this run's live header, else nothing: a ledger that never opened must not look live."""
        return cls.tally_event() if event_counts.get(LEDGER_LIVE_EVENT, 0) > 0 else None

    @classmethod
    def tally_event(cls) -> SimulationEvent:
        """The closing marker: deaths by cause, hp lost by source, the unattributed hp (must be 0) and one row per death, sorted so two runs of a seed write the same bytes."""
        deaths = dict(sorted(cls._deaths.items()))
        unknown = len(cls._unrecorded)
        payload = {
            "last_tick": cls._last_tick, "deaths": deaths, "unknown_deaths": unknown + sum(v for k, v in deaths.items() if k.split("|")[1] == DeathCause.UNKNOWN.value),
            "hp_lost": dict(sorted(cls._hp_lost.items())),
            "unattributed_hp": sum(v for k, v in cls._hp_lost.items() if k.endswith("|" + HpLossSource.UNATTRIBUTED.value)),
            "records": list(cls._records),
        }
        return cls._event(LEDGER_TALLY_EVENT, cls._last_tick, payload)

    @staticmethod
    def _event(event_type: str, tick: int, payload: Dict[str, Any]) -> SimulationEvent:
        return SimulationEvent(event_type=event_type, event_category="lifecycle", tick=tick, entity_id=None, severity="WARNING",
                               source_system=_SOURCE, message="", payload=payload, timestamp=time.time())
