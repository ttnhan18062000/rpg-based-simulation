"""
src/observability/run_ledger.py
───────────────────────────────────────────────────────────────────────────────
The run ledger (M0 regression gate, TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS).

A run leaves only the curated event file and the FINAL state: the resolver's transfers (what was eaten, from which source, who was paid), the coin
the world held at the start, where entities were added from, and the population over time are in neither. This bounded, non-authoritative,
run-scoped observer counts them, by kind group (``kind_group``: what the kind's diet declares, never a role), and writes ONE closing tally so the
gate's metric module reads typed records and never touches live state.

Like the starvation-death record: a live header opens the run (``rpg_gate_ledger_live``), the tally closes it (``rpg_gate_ledger_tally``), both
WARNING severity so the DEGRADED/PRESSURE recorder modes keep them; a recorder that never saw the header writes no tally, and a silent ledger reads as
no-data (harness_error), never as zero violations. A profile with no observability budget leaves it silent. It reads the staged update and the two
states; it writes nothing back.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from src.ai.goals.kind_group import kind_group
from src.core.region_resolution import is_inside_world
from src.core.spawn_source import SpawnKind
from src.core.state import AuthoritativeState
from src.core.treasury import total_coin
from src.observability.events import SimulationEvent

LEDGER_LIVE_EVENT = "rpg_gate_ledger_live"
LEDGER_TALLY_EVENT = "rpg_gate_ledger_tally"
UNSOURCED = "unsourced"
POPULATION_SAMPLE_EVERY = 500  # ticks between population samples (the first observed tick is always sampled): ten samples over a 5000-tick run
_SOURCE = "run_ledger"
_WORLD_EVENT_KEYS = ("FEEDING_KILL", "MEAT_DECAYED")
_RAW_MEAT = "raw_meat"  # engine.carcass.RAW_MEAT_ITEM (observability may not import the engine; a test pins the two equal)
MAX_EXAMPLES = 5


def _key(*parts: Any) -> str:
    return "|".join(str(p) for p in parts)


class RunLedger:
    """Per-run counters the gate's validity and outcome rows read; every key is ``group|...`` with the group from ``kind_group``."""

    _live: bool = False
    _header_sent: bool = False
    _first_tick: Optional[int] = None
    _last_tick: int = 0
    _coin_first: float = 0.0
    _coin_last: float = 0.0
    _declared_coin: float = 0.0  # gold the world creates by declaration: an added entity's starting purse
    _population: Dict[int, Dict[str, int]] = {}
    _transfers: Dict[str, int] = {}  # group|source_kind|accepted
    _hunger_drops: Dict[str, int] = {}  # group|with_accepted_transfer / group|without_transfer
    _deaths: Dict[str, int] = {}  # group|cause
    _adds: Dict[str, int] = {}  # group|SpawnKind or unsourced
    _world_events: Dict[str, float] = {}  # FEEDING_KILL / MEAT_DECAYED counts, and meat_decayed_quantity
    _meat: Dict[str, float] = {}  # made (new bodies), taken (off persisting bodies: eaten or looted), vanished (on bodies that left the world)
    _attacks: Dict[str, int] = {}  # attacker_group|victim_group|hit or kill: genuine entity-vs-entity combat resolutions
    _out_of_world: Dict[str, int] = {}  # group -> entity-ticks of a moved, alive entity outside the world extent
    _out_of_world_examples: List[Dict[str, Any]] = []

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear every counter and the header flag at run start (and in test teardown)."""
        cls._live = False
        cls._header_sent = False
        cls._first_tick = None
        cls._last_tick = 0
        cls._coin_first = cls._coin_last = cls._declared_coin = 0.0
        cls._population = {}
        cls._transfers = {}
        cls._hunger_drops = {}
        cls._deaths = {}
        cls._adds = {}
        cls._world_events = {}
        cls._meat = {}
        cls._attacks = {}
        cls._out_of_world = {}
        cls._out_of_world_examples = []

    @classmethod
    def configure(cls, live: bool) -> None:
        """Whether the profile has an observability budget at all (False: the ledger stays silent and reads as not live)."""
        cls._live = live

    @classmethod
    def observe(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> List[SimulationEvent]:
        """Count one tick: the live header once, then transfers, hunger drops, deaths, adds and world events; sample coin and population."""
        if not cls._live:
            return []
        tick = current.tick
        cls._last_tick = tick
        events: List[SimulationEvent] = []
        if not cls._header_sent:
            cls._header_sent = True
            cls._first_tick = tick
            cls._coin_first = total_coin(prior)
            events.append(cls._event(LEDGER_LIVE_EVENT, tick, {"population_sample_every": POPULATION_SAMPLE_EVERY}))
        cls._coin_last = total_coin(current)
        if cls._first_tick == tick or tick % POPULATION_SAMPLE_EVERY == 0:
            cls._population[tick] = cls._alive_by_group(current)
        cls._count_transfers(prior, current, update)
        cls._count_deaths(prior, current)
        cls._count_adds(update)
        cls._count_world_events(update)
        cls._count_meat(prior, current)
        cls._count_positions(current, update)
        cls._count_attacks(prior, current, update)
        return events

    @staticmethod
    def _alive_by_group(state: AuthoritativeState) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for entity in state.entities.values():
            if entity.combat.alive:
                group = kind_group(entity)
                counts[group] = counts.get(group, 0) + 1
        return counts

    @classmethod
    def _count_transfers(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> None:
        for eid, upd in (getattr(update, "entity_updates", None) or {}).items():
            entity = current.entities.get(eid)
            prior_ent = prior.entities.get(eid)
            if entity is None or prior_ent is None:
                continue
            group = kind_group(entity)
            results = getattr(upd, "intent_results", None) or []
            cls._count_results(group, results)
            if entity.biological.hunger < prior_ent.biological.hunger:
                cls._count_hunger_drop(group, results)

    @classmethod
    def _count_results(cls, group: str, results: List[Any]) -> None:
        for result in results:
            outcome = "accepted" if getattr(result, "accepted", False) else "rejected"
            key = _key(group, getattr(result, "source_kind", ""), outcome)
            cls._transfers[key] = cls._transfers.get(key, 0) + 1

    @classmethod
    def _count_hunger_drop(cls, group: str, results: List[Any]) -> None:
        backed = any(getattr(r, "accepted", False) for r in results)
        key = _key(group, "with_accepted_transfer" if backed else "without_transfer")
        cls._hunger_drops[key] = cls._hunger_drops.get(key, 0) + 1

    @classmethod
    def _count_deaths(cls, prior: AuthoritativeState, current: AuthoritativeState) -> None:
        for eid, entity in current.entities.items():
            prior_ent = prior.entities.get(eid)
            if prior_ent is not None and prior_ent.combat.alive and not entity.combat.alive:
                life = entity.lifecycle
                cause = getattr(life.passive_death_cause, "value", None) or life.death_reason or "unknown"
                key = _key(kind_group(entity), cause)
                cls._deaths[key] = cls._deaths.get(key, 0) + 1

    @classmethod
    def _count_adds(cls, update: Any) -> None:
        sources = getattr(update, "entity_spawn_sources", None) or {}
        for entity in (getattr(update, "entities_add", None) or []):
            source = sources.get(entity.id)
            kind = source.kind.value if source is not None and isinstance(source.kind, SpawnKind) else UNSOURCED
            key = _key(kind_group(entity), kind)
            cls._adds[key] = cls._adds.get(key, 0) + 1
            cls._declared_coin += float(entity.inventory.gold)

    @classmethod
    def _count_world_events(cls, update: Any) -> None:
        for event in (getattr(update, "world_events_add", None) or []):
            name = str(getattr(getattr(event, "category", None), "name", getattr(event, "category", "")))
            if name in _WORLD_EVENT_KEYS:
                cls._world_events[name] = cls._world_events.get(name, 0) + 1
                if name == "MEAT_DECAYED":
                    qty = (getattr(event, "payload", None) or {}).get("quantity", 0.0)
                    cls._world_events["meat_decayed_quantity"] = cls._world_events.get("meat_decayed_quantity", 0.0) + float(qty)

    @staticmethod
    def _meat_on(corpse: Any) -> float:
        return float(sum(st.quantity for st in getattr(corpse, "items", ()) if st.item_id == _RAW_MEAT))

    @classmethod
    def _count_meat(cls, prior: AuthoritativeState, current: AuthoritativeState) -> None:
        before, after = prior.corpses or {}, current.corpses or {}
        for cid, corpse in after.items():
            now = cls._meat_on(corpse)
            if cid not in before:
                cls._meat["made"] = cls._meat.get("made", 0.0) + now
            else:
                cls._meat["taken"] = cls._meat.get("taken", 0.0) + max(0.0, cls._meat_on(before[cid]) - now)
        for cid, corpse in before.items():
            if cid not in after:
                cls._meat["vanished"] = cls._meat.get("vanished", 0.0) + cls._meat_on(corpse)

    @classmethod
    def _count_attacks(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> None:
        for eid, upd in (getattr(update, "entity_updates", None) or {}).items():
            combat = getattr(upd, "combat", None)
            attacker_id = getattr(combat, "attacker_id", None)
            if attacker_id is None or getattr(combat, "hp_delta", 0) >= 0:
                continue
            victim, attacker = current.entities.get(eid), prior.entities.get(attacker_id)
            if victim is None or attacker is None:
                continue
            outcome = "kill" if getattr(combat, "outcome_kind", None) == "KILL" else "hit"
            key = _key(kind_group(attacker), kind_group(victim), outcome)
            cls._attacks[key] = cls._attacks.get(key, 0) + 1

    @classmethod
    def _count_positions(cls, current: AuthoritativeState, update: Any) -> None:
        for eid in (getattr(update, "entity_updates", None) or {}):
            entity = current.entities.get(eid)
            if entity is None or not entity.combat.alive:
                continue
            pos = entity.navigation.position
            if not is_inside_world(current, pos):
                group = kind_group(entity)
                cls._out_of_world[group] = cls._out_of_world.get(group, 0) + 1
                if len(cls._out_of_world_examples) < MAX_EXAMPLES:
                    cls._out_of_world_examples.append({"entity_id": eid, "tick": current.tick, "position": [pos[0], pos[1]]})

    @classmethod
    def closing_event(cls, event_counts: Dict[str, int]) -> Optional[SimulationEvent]:
        """The tally for a recorder that recorded this run's live header, else nothing: a ledger that never opened must not look live."""
        return cls.tally_event() if event_counts.get(LEDGER_LIVE_EVENT, 0) > 0 else None

    @classmethod
    def tally_event(cls) -> SimulationEvent:
        """The closing marker: every counter, with sorted keys so two runs of the same seed write the same bytes."""
        payload = {
            "first_tick": cls._first_tick, "last_tick": cls._last_tick,
            "coin_first": cls._coin_first, "coin_last": cls._coin_last, "declared_coin": cls._declared_coin,
            "population": {str(t): dict(sorted(g.items())) for t, g in sorted(cls._population.items())},
            "transfers": dict(sorted(cls._transfers.items())), "hunger_drops": dict(sorted(cls._hunger_drops.items())),
            "deaths": dict(sorted(cls._deaths.items())), "adds": dict(sorted(cls._adds.items())),
            "world_events": dict(sorted(cls._world_events.items())), "meat": dict(sorted(cls._meat.items())),
            "attacks": dict(sorted(cls._attacks.items())), "out_of_world": dict(sorted(cls._out_of_world.items())), "out_of_world_examples": list(cls._out_of_world_examples),
        }
        return cls._event(LEDGER_TALLY_EVENT, cls._last_tick, payload)

    @staticmethod
    def _event(event_type: str, tick: int, payload: Dict[str, Any]) -> SimulationEvent:
        return SimulationEvent(event_type=event_type, event_category="lifecycle", tick=tick, entity_id=None, severity="WARNING",
                               source_system=_SOURCE, message="", payload=payload, timestamp=time.time())
