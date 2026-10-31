"""Faction events: diplomacy, territory, tension, world-event wars and extinction."""

from __future__ import annotations

from typing import Any

from src.observability.events import SimulationEvent
from src.observability.extraction.context import ExtractContext


def _alliance_events(ctx: ExtractContext, fid: Any, other_fid: Any) -> list[SimulationEvent]:
    """alliance_proposed and alliance_accepted for a new ALLIED state."""
    tick = ctx.tick
    prior_state = ctx.prior_state
    events: list[SimulationEvent] = []
    # alliance_proposed: fires when prior state was NEUTRAL/HOSTILE (proposal preceded acceptance)
    _prior_factions = getattr(prior_state, "factions", {}) or {}
    _prior_faction_st = _prior_factions.get(fid)
    _prior_diplo = (getattr(_prior_faction_st, "diplomatic_relations", {}) or {}) if _prior_faction_st else {}
    _prior_rel = getattr(_prior_diplo.get(other_fid), "name",
                         str(_prior_diplo.get(other_fid, "NEUTRAL")))
    if _prior_rel in ("NEUTRAL", "HOSTILE"):
        events.append(SimulationEvent(
            event_type="alliance_proposed", event_category="faction",
            tick=tick, entity_id=None, severity="INFO",
            source_system="event_extractor", message="",
            payload={"proposing_faction": fid, "target_faction": other_fid,
                     "prior_state": _prior_rel, "tick": tick},
        ))
    events.append(SimulationEvent(
        event_type="alliance_accepted", event_category="faction",
        tick=tick, entity_id=None, severity="INFO",
        source_system="event_extractor", message="",
        payload={"faction_id": fid, "partner_id": other_fid},
    ))
    return events


def _diplomatic_events(ctx: ExtractContext, upd: Any, fid: Any, _seen_diplo_pairs: set[Any]) -> list[SimulationEvent]:
    """diplomatic_transition, and the alliance events when the new state is ALLIED."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # FACTION: diplomatic_transition (PP-10) — one event per ordered pair
    for other_fid, new_state in (upd.diplomatic_relations_set or {}).items():
        pair = frozenset({fid, other_fid})
        if pair not in _seen_diplo_pairs:
            _seen_diplo_pairs.add(pair)
            state_name = getattr(new_state, "name", str(new_state))
            events.append(SimulationEvent(
                event_type="diplomatic_transition", event_category="faction",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={
                    "faction_id": fid,
                    "target_faction_id": other_fid,
                    "new_state": state_name,
                },
            ))
            # FACTION: alliance_accepted (PP-08/10) — when new state is ALLIED
            if state_name == "ALLIED":
                events.extend(_alliance_events(ctx, fid, other_fid))
    return events


def _territory_events(ctx: ExtractContext, upd: Any, fid: Any) -> list[SimulationEvent]:
    """territory_ownership_changed and resource_seized."""
    tick = ctx.tick
    current_state = ctx.current_state
    events: list[SimulationEvent] = []
    # FACTION: territory_ownership_changed (PP-11). faction_territory_pct
    # (TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP): this faction's post-update
    # territory count over total world regions — FactionScorer's faction_monopoly/
    # faction_conquest_degenerate branches depend on this key, previously never set.
    _total_regions = len(getattr(current_state, "regions", None) or {})
    _curr_faction_st = (getattr(current_state, "factions", None) or {}).get(fid)
    _curr_territory = getattr(_curr_faction_st, "territory", None) or ()
    _territory_pct = (len(_curr_territory) / _total_regions) if _total_regions > 0 else 0.0
    for region_id in (upd.territory_add or ()):
        events.append(SimulationEvent(
            event_type="territory_ownership_changed", event_category="faction",
            tick=tick, entity_id=None, severity="WARNING",
            source_system="event_extractor", message="",
            payload={"faction_id": fid, "region_id": region_id,
                     "faction_territory_pct": _territory_pct},
        ))
        # FACTION: resource_seized — territory transfer driven by faction conflict
        if getattr(upd, "tension_delta", 0.0) > 0:
            events.append(SimulationEvent(
                event_type="resource_seized", event_category="faction",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={"faction_id": fid, "region_id": region_id, "tick": tick},
            ))
    return events


def _tension_events(ctx: ExtractContext, upd: Any, fid: Any) -> list[SimulationEvent]:
    """faction_tension_delta."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # FACTION: faction_tension_delta (PP-09) — any non-zero delta
    if getattr(upd, "tension_delta", 0.0) != 0.0:
        events.append(SimulationEvent(
            event_type="faction_tension_delta", event_category="faction",
            tick=tick, entity_id=None, severity="INFO",
            source_system="event_extractor", message="",
            payload={"faction_id": fid, "delta": upd.tension_delta},
        ))
    return events


def faction_update_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """One event set per FactionUpdate record (rollback path only)."""
    update = ctx.update
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # Faction events from FactionUpdate records (PP-08/09/10/11). Flag-gated
    # (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live behind FactionShaper when
    # ENABLE_PUSH_EVENT_SHAPERS is "ON" (default); this loop is the rollback path when it
    # isn't. Every event this loop produces (diplomatic_transition, alliance_proposed,
    # alliance_accepted, territory_ownership_changed, resource_seized, faction_tension_delta)
    # is migrated — no partial-condition case here. faction_extinct (a separate block, below)
    # is explicitly DEFERRED, not migrated, and stays fully unconditional.
    _seen_diplo_pairs: set = set()
    _faction_upds = getattr(update, "faction_updates", None)
    if not isinstance(_faction_upds, (list, tuple)) or _push_shapers_active:
        _faction_upds = ()
    for upd in _faction_upds:
        fid = upd.faction_id
        events.extend(_diplomatic_events(ctx, upd, fid, _seen_diplo_pairs))
        events.extend(_territory_events(ctx, upd, fid))
        events.extend(_tension_events(ctx, upd, fid))
    return events


def _living_faction_id_set(ctx: ExtractContext) -> set[Any]:
    """Ids of the factions that have a living member in the current state."""
    current_state = ctx.current_state
    _living_faction_ids: set = set()
    for _ent in (getattr(current_state, "entities", {}) or {}).values():
        _hp = getattr(_ent, "hp", None)
        _fac = getattr(getattr(_ent, "identity", None), "faction", None)
        _hp_alive = _hp is None or (isinstance(_hp, (int, float)) and _hp > 0)
        if _fac is not None and _hp_alive:
            _living_faction_ids.add(str(_fac))
    return _living_faction_ids


def _extinct_events(ctx: ExtractContext, _living_faction_ids: set[Any]) -> list[SimulationEvent]:
    """faction_extinct for each faction that lost its last living member."""
    tick = ctx.tick
    prior_state = ctx.prior_state
    current_state = ctx.current_state
    events: list[SimulationEvent] = []
    for _fid, _fstate in (getattr(current_state, "factions", {}) or {}).items():
        if str(_fid) in _living_faction_ids:
            continue
        _prior_living = any(
            getattr(getattr(_pe, "identity", None), "faction", None) is not None
            and str(getattr(getattr(_pe, "identity", None), "faction", "")) == str(_fid)
            and (
                (lambda _h: _h is None or (isinstance(_h, (int, float)) and _h > 0))(
                    getattr(_pe, "hp", None)
                )
            )
            for _pe in (getattr(prior_state, "entities", {}) or {}).values()
        )
        if _prior_living:
            events.append(SimulationEvent(
                event_type="faction_extinct", event_category="faction",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={"faction_id": str(_fid)},
            ))
    return events


def faction_extinct_events(ctx: ExtractContext) -> list[SimulationEvent]:
    """faction_extinct, only when faction state changed this tick (rollback path only)."""
    update = ctx.update
    _push_shapers_phase2_active = ctx.push_shapers_phase2_active
    events: list[SimulationEvent] = []
    # FACTION: faction_extinct (PP-08/PP-33) — only when faction state changed this tick.
    # Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind
    # DeferredInstrumentationShaper when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default);
    # this block is the rollback path.
    _faction_upd_list = getattr(update, "faction_updates", None)
    if not _push_shapers_phase2_active and isinstance(_faction_upd_list, list) and _faction_upd_list:
        events.extend(_extinct_events(ctx, _living_faction_id_set(ctx)))
    return events
