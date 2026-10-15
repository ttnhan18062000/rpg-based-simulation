"""
src/observability/death_ledger.py
───────────────────────────────────────────────────────────────────────────────
The death ledger (TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH): one typed record per death and a typed source for every hp loss.

`death_reason` is durable but a string, the hazard kind lives only on the region, and the last attacker only on the transient combat update. This
bounded, non-authoritative, run-scoped observer reads the staged update and the two states and writes nothing back: it adds nothing to the state
fingerprint. Each tick it (1) splits every hp loss into hit, hazard and starving drain (a loss none explains is UNATTRIBUTED), (2) remembers the
last attacker per body, and (3) on the tick a death reason is first recorded writes a `DeathRecord`: the typed cause, the last attacker, the
region's hazard kind when the cause is a hazard, and the hp the body lost by source over its life (so the dominant source is read, not rebuilt).

Like the run ledger: a live header opens the run, ONE tally closes it, both WARNING so the DEGRADED/PRESSURE recorder modes keep them; a recorder
that never saw the header writes no tally, and a silent ledger reads as no-data, never as zero.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set

from src.ai.goals.kind_group import is_person, kind_group
from src.core.death_cause import DeathCause, HpLossSource, death_cause_of
from src.core.region_resolution import resolve_region_among
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
    _last_attacker: Dict[int, Dict[str, int]] = {}  # entity id -> {"id", "tick"} of the last damaging attacker
    _unrecorded: Set[int] = set()  # bodies seen dying with no death reason yet; any still here at the close are UNKNOWN

    @classmethod
    def reset_run_state(cls) -> None:
        cls._live = False
        cls._header_sent = False
        cls._last_tick = 0
        cls._starving_line = float("inf")
        cls._deaths = {}
        cls._hp_lost = {}
        cls._records = []
        cls._by_entity = {}
        cls._last_attacker = {}
        cls._unrecorded = set()

    @classmethod
    def configure(cls, starving_line: float, live: bool = True) -> None:
        """What the kernel gives the ledger: the engine's starving line (observability may not import it) and whether the profile has a budget."""
        cls._starving_line = float(starving_line)
        cls._live = live

    @classmethod
    def observe(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> List[SimulationEvent]:
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
            cls._count_hp_loss(tick, eid, before, entity, updates.get(eid))
            cls._record_death(tick, eid, before, entity, current)
        return events

    @classmethod
    def _count_hp_loss(cls, tick: int, eid: int, before: EntityState, entity: EntityState, upd: Any) -> None:
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
        attacker = getattr(combat, "attacker_id", None)
        if attacker is not None and hit > 0:
            cls._last_attacker[eid] = {"id": int(attacker), "tick": tick}

    @classmethod
    def _record_death(cls, tick: int, eid: int, before: EntityState, entity: EntityState, current: AuthoritativeState) -> None:
        if before.combat.alive and not entity.combat.alive and entity.lifecycle.death_reason is None:
            cls._unrecorded.add(eid)
        if before.lifecycle.death_reason is not None or entity.lifecycle.death_reason is None:
            return
        cls._unrecorded.discard(eid)
        cause = death_cause_of(entity.lifecycle.death_reason)
        group = kind_group(entity)
        person = bool(is_person(entity))
        cls._deaths[_key(group, cause.value, int(person))] = cls._deaths.get(_key(group, cause.value, int(person)), 0) + 1
        if len(cls._records) < MAX_RECORDS:
            hazard_kind: Optional[str] = None
            if cause is DeathCause.HAZARD:
                x, y = entity.navigation.position
                region = resolve_region_among(current.regions.values(), x, y)
                hazard_kind = getattr(region, "hazard_kind", None)
            attacker = cls._last_attacker.get(eid)
            cls._records.append({
                "entity_id": eid, "group": group, "person": person, "tick": tick, "cause": cause.value,
                "last_attacker_id": attacker["id"] if attacker else None, "hazard_kind": hazard_kind,
                "hp_lost": dict(sorted(cls._by_entity.get(eid, {}).items())),
            })
        cls._by_entity.pop(eid, None)
        cls._last_attacker.pop(eid, None)

    @classmethod
    def closing_event(cls, event_counts: Dict[str, int]) -> Optional[SimulationEvent]:
        return cls.tally_event() if event_counts.get(LEDGER_LIVE_EVENT, 0) > 0 else None

    @classmethod
    def tally_event(cls) -> SimulationEvent:
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
