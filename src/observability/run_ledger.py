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

from src.ai.goals.kind_group import eats_outside_its_diet, is_person, kind_group
from src.ai.goals.scorers_support import perceived_hostiles
from src.core.movement_modes import MovementMode
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
PERCEPTION_SAMPLE_EVERY = 10  # ticks between perception samples (perceived_hostiles scans neighbours per entity); the sample count is in the tally
FLEE_MODES = frozenset({MovementMode.RETREAT})
PURSUIT_MODES = frozenset({MovementMode.PURSUE, MovementMode.INTERCEPT})
MAX_EXAMPLES = 5


def _tile(position: Any) -> tuple:
    return (int(position[0]), int(position[1]))


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
    _diet_breaches: Dict[str, int] = {}  # group|source_kind|item_id: an accepted EAT of food whose class is outside the eater's diet (a consumption, never a pickup)
    _hunger_drops: Dict[str, int] = {}  # group|with_accepted_transfer / group|without_transfer
    _deaths: Dict[str, int] = {}  # group|cause
    _adds: Dict[str, int] = {}  # group|SpawnKind or unsourced
    _world_events: Dict[str, float] = {}  # FEEDING_KILL / MEAT_DECAYED counts, and meat_decayed_quantity
    _meat: Dict[str, float] = {}  # made (new bodies), taken (off persisting bodies: eaten or looted a part), looted (a body taken whole by a CORPSE transfer), vanished (left with no transfer: the decay sink)
    _attacks: Dict[str, int] = {}  # attacker_group|attacker_person|victim_person|hit or kill (person = 1 when the species keeps coin and trades, D43): genuine entity-vs-entity combat resolutions
    _behaviour: Dict[str, int] = {}  # measure|group|person: flee/pursuit entity-ticks and episodes (typed MovementMode), steps|terrain (tile entered), perceiving entity-ticks and perceived-hostile counts (sampled)
    _perception_samples: int = 0  # ticks on which perception was sampled
    _out_of_world: Dict[str, int] = {}  # group -> entity-ticks of a moved, alive entity outside the world extent
    _out_of_world_examples: List[Dict[str, Any]] = []
    _unsourced_examples: List[Dict[str, Any]] = []

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
        cls._diet_breaches = {}
        cls._deaths = {}
        cls._adds = {}
        cls._world_events = {}
        cls._meat = {}
        cls._attacks = {}
        cls._behaviour = {}
        cls._perception_samples = 0
        cls._out_of_world = {}
        cls._out_of_world_examples = []
        cls._unsourced_examples = []

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
        cls._count_adds(update, tick)
        cls._count_world_events(update)
        cls._count_meat(prior, current, update)
        cls._count_positions(current, update)
        cls._count_attacks(prior, current, update)
        cls._count_behaviour(prior, current)
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
            cls._count_diet_breaches(prior, current, entity, group, results)
            if entity.biological.hunger < prior_ent.biological.hunger:
                cls._count_hunger_drop(group, results, cls._inventory_moved(prior_ent, entity) or cls._corpse_moved(prior, current, results))

    @classmethod
    def _count_results(cls, group: str, results: List[Any]) -> None:
        for result in results:
            outcome = "accepted" if getattr(result, "accepted", False) else "rejected"
            key = _key(group, getattr(result, "source_kind", ""), outcome)
            cls._transfers[key] = cls._transfers.get(key, 0) + 1

    @staticmethod
    def _inventory_moved(prior_ent: Any, entity: Any) -> bool:
        """Whether the eater's inventory actually changed this tick: the gold or any item stack differs between the two states. This is the quantity APPLIED after
        the clamp (an inn charge of 5 on a subject holding 0 moves nothing), never the requested delta, which the intent and the transaction record carry."""
        before, after = prior_ent.inventory, entity.inventory
        if before.gold != after.gold:
            return True
        def stacks(inv: Any) -> Dict[str, int]:
            held: Dict[str, int] = {}
            for st in inv.items:
                held[st.item_id] = held.get(st.item_id, 0) + st.quantity
            return held
        return stacks(before) != stacks(after)

    @staticmethod
    def _corpse_moved(prior: AuthoritativeState, current: AuthoritativeState, results: List[Any]) -> bool:
        """Whether a body an accepted CORPSE / CORPSE_FOOD transfer named lost food this tick: a meal eaten where the body lies moves the corpse's stack, not the
        eater's inventory."""
        def held(state: AuthoritativeState, cid: Any) -> int:
            corpse = (getattr(state, "corpses", None) or {}).get(cid)
            return 0 if corpse is None else sum(st.quantity for st in getattr(corpse, "items", ()))
        return any(held(prior, r.source_id) != held(current, r.source_id) for r in results
                   if getattr(r, "accepted", False) and getattr(r, "source_kind", "") in ("CORPSE", "CORPSE_FOOD"))

    @classmethod
    def _count_diet_breaches(cls, prior: AuthoritativeState, current: AuthoritativeState, entity: Any, group: str, results: List[Any]) -> None:
        """V4 reads CONSUMPTION: an accepted carried-food or corpse-food EAT after which a food item whose class the eater's diet lacks has left the
        carried stack or the body. The ledger sees the resolved results (the intents are consumed before observation), so the eaten item is read from
        what left the inventory or the corpse between the two states."""
        for result in results:
            source = getattr(result, "source_kind", None)
            if not getattr(result, "accepted", False) or source not in ("CARRIED_FOOD", "CORPSE_FOOD"):
                continue
            for item_id in cls._items_that_left(prior, current, entity, source, getattr(result, "source_id", None)):
                if eats_outside_its_diet(entity, item_id):
                    key = _key(group, source, item_id)
                    cls._diet_breaches[key] = cls._diet_breaches.get(key, 0) + 1

    @staticmethod
    def _items_that_left(prior: AuthoritativeState, current: AuthoritativeState, entity: Any, source: str, source_id: Any) -> List[str]:
        """The item ids whose quantity fell on the carried stack (CARRIED_FOOD) or on the named body (CORPSE_FOOD) across the tick."""
        if source == "CARRIED_FOOD":
            before, after = prior.entities[entity.id].inventory.items, entity.inventory.items
        else:
            body_before, body_after = (prior.corpses or {}).get(source_id), (current.corpses or {}).get(source_id)
            before, after = (body_before.items if body_before else []), (body_after.items if body_after else [])
        remaining: Dict[str, float] = {}
        for stack in after:
            remaining[stack.item_id] = remaining.get(stack.item_id, 0.0) + stack.quantity
        left: List[str] = []
        for stack in before:
            if stack.quantity > remaining.get(stack.item_id, 0.0):
                left.append(stack.item_id)
        return left

    @classmethod
    def _count_hunger_drop(cls, group: str, results: List[Any], moved: bool = True) -> None:
        """A drop is backed only when an accepted transfer exists AND the eater's inventory actually moved: an accepted inn charge at 0 gold is not a source."""
        backed = moved and any(getattr(r, "accepted", False) for r in results)
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
    def _count_adds(cls, update: Any, tick: int) -> None:
        sources = getattr(update, "entity_spawn_sources", None) or {}
        for entity in (getattr(update, "entities_add", None) or []):
            source = sources.get(entity.id)
            kind = source.kind.value if source is not None and isinstance(source.kind, SpawnKind) else UNSOURCED
            key = _key(kind_group(entity), kind)
            cls._adds[key] = cls._adds.get(key, 0) + 1
            if kind == UNSOURCED and len(cls._unsourced_examples) < MAX_EXAMPLES:
                cls._unsourced_examples.append({"entity_id": entity.id, "tick": tick, "kind_group": kind_group(entity), "check": UNSOURCED})
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

    @staticmethod
    def _corpses_looted_whole(update: Any) -> set:
        """The ids of bodies an accepted CORPSE transfer took whole this tick (the looter receives their items, meat included)."""
        results = (r for u in (getattr(update, "entity_updates", None) or {}).values() for r in (getattr(u, "intent_results", None) or []))
        return {r.source_id for r in results if getattr(r, "source_kind", "") == "CORPSE" and getattr(r, "accepted", False)}

    @classmethod
    def _count_meat(cls, prior: AuthoritativeState, current: AuthoritativeState, update: Any) -> None:
        before, after = prior.corpses or {}, current.corpses or {}
        looted_whole = cls._corpses_looted_whole(update)
        for cid, corpse in after.items():
            now = cls._meat_on(corpse)
            if cid not in before:
                cls._meat["made"] = cls._meat.get("made", 0.0) + now
            else:
                cls._meat["taken"] = cls._meat.get("taken", 0.0) + max(0.0, cls._meat_on(before[cid]) - now)
        for cid, corpse in before.items():
            if cid not in after:
                kind = "looted" if cid in looted_whole else "vanished"
                cls._meat[kind] = cls._meat.get(kind, 0.0) + cls._meat_on(corpse)

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
            key = _key(kind_group(attacker), int(is_person(attacker)), int(is_person(victim)), outcome)
            cls._attacks[key] = cls._attacks.get(key, 0) + 1

    @classmethod
    def _count_behaviour(cls, prior: AuthoritativeState, current: AuthoritativeState) -> None:
        """Flee and pursuit from the typed movement mode (entity-ticks, and episodes = ticks that enter the mode), steps by the terrain entered, and
        perception from ``perceived_hostiles`` on every ``PERCEPTION_SAMPLE_EVERY``-th tick. Reads only; nothing here reaches the state."""
        sample = current.tick % PERCEPTION_SAMPLE_EVERY == 0
        cls._perception_samples += 1 if sample else 0
        for eid, entity in current.entities.items():
            if not entity.combat.alive:
                continue
            who = _key(kind_group(entity), int(is_person(entity)))
            before = prior.entities.get(eid)
            before = before if before is not None and before.combat.alive else None
            cls._count_modes(who, entity, before)
            cls._count_step(current, entity, before)
            if sample:
                cls._count_perception(who, entity, current)

    @classmethod
    def _count_modes(cls, who: str, entity: Any, before: Any) -> None:
        mode = entity.navigation.movement_mode
        was = before.navigation.movement_mode if before is not None else None
        for name, modes in (("flee", FLEE_MODES), ("pursuit", PURSUIT_MODES)):
            if mode in modes:
                cls._bump(_key(name + "_ticks", who))
                if was not in modes:
                    cls._bump(_key(name + "_episodes", who))

    @classmethod
    def _count_step(cls, current: AuthoritativeState, entity: Any, before: Any) -> None:
        if before is not None:
            tile = _tile(entity.navigation.position)
            if tile != _tile(before.navigation.position):
                cls._bump(_key("steps", current.terrain.get(tile, "unknown")))

    @classmethod
    def _count_perception(cls, who: str, entity: Any, current: AuthoritativeState) -> None:
        seen = len(perceived_hostiles(entity, current))
        if seen:
            cls._bump(_key("perceiving_ticks", who))
            cls._bump(_key("perceived_hostiles", who), seen)

    @classmethod
    def _bump(cls, key: str, n: int = 1) -> None:
        cls._behaviour[key] = cls._behaviour.get(key, 0) + n

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
            "transfers": dict(sorted(cls._transfers.items())), "hunger_drops": dict(sorted(cls._hunger_drops.items())), "diet_breaches": dict(sorted(cls._diet_breaches.items())),
            "deaths": dict(sorted(cls._deaths.items())), "adds": dict(sorted(cls._adds.items())),
            "world_events": dict(sorted(cls._world_events.items())), "meat": dict(sorted(cls._meat.items())),
            "attacks": dict(sorted(cls._attacks.items())), "behaviour": dict(sorted(cls._behaviour.items())), "perception_samples": cls._perception_samples, "out_of_world": dict(sorted(cls._out_of_world.items())), "out_of_world_examples": list(cls._out_of_world_examples), "unsourced_examples": list(cls._unsourced_examples),
        }
        return cls._event(LEDGER_TALLY_EVENT, cls._last_tick, payload)

    @staticmethod
    def _event(event_type: str, tick: int, payload: Dict[str, Any]) -> SimulationEvent:
        return SimulationEvent(event_type=event_type, event_category="lifecycle", tick=tick, entity_id=None, severity="WARNING",
                               source_system=_SOURCE, message="", payload=payload, timestamp=time.time())
