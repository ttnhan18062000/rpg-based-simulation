"""Economy events of one entity: gold transactions and the intent-result events."""

from __future__ import annotations

from typing import Any

from src.observability.config import ObservabilityMode
from src.observability.events import GoldTransactionEvent, SimulationEvent
from src.observability.extraction.context import ExtractContext

# Economy + Information events from intent_results (resource_transfers cleared
# by PP-27). Flag-gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live
# behind EconomyShaper when ENABLE_PUSH_EVENT_SHAPERS is "ON" (default); this loop
# is the rollback path when it isn't. Every branch inside is a migrated ECONOMY
# event — no partial-condition case here, unlike the Kill-events branch above.
_GOLD_SINK_KINDS = frozenset(("REPAIR_FEE", "SERVICE_FEE", "TAX"))


def gold_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """gold_transaction on a non-zero gold change."""
    tick = ctx.tick
    now = ctx.now
    mode = ctx.mode
    events: list[SimulationEvent] = []
    # Economy/Gold events (exclusively meaningful changes)
    gold_diff = entity.inventory.gold - prior_ent.inventory.gold
    if gold_diff != 0:
        # Volumization rule: ignore micro-trades (< 5.0 gold) in LIGHT mode
        if abs(gold_diff) >= 5.0 or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
            kind = "gain" if gold_diff > 0 else "loss"
            events.append(GoldTransactionEvent(
                tick=tick, timestamp=now, entity_id=eid,
                amount=float(abs(gold_diff)), transaction_kind=kind
            ))
    return events


def _information_purchase_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any, ir: Any) -> list[SimulationEvent]:
    """The events of an accepted INFORMATION_PURCHASE intent result."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    _info_src = str(getattr(ir, "source_id", ""))
    events.append(SimulationEvent(
        event_type="paid_information_transaction", event_category="economy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="event_extractor", message="",
        payload={"source_id": _info_src},
    ))
    # Economy pillar: distinct from paid_information_transaction (INFORMATION scorer)
    events.append(SimulationEvent(
        event_type="paid_info_transaction", event_category="economy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="event_extractor", message="",
        payload={"source_id": _info_src},
    ))
    # paid_info_changed_goal: fires when info purchase correlates with project switch
    if (prior_ent is not None
            and hasattr(entity, "strategic") and hasattr(prior_ent, "strategic")
            and entity.strategic.current_project_id != prior_ent.strategic.current_project_id):
        events.append(SimulationEvent(
            event_type="paid_info_changed_goal", event_category="strategy",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"source_id": _info_src},
        ))
    return events


def intent_result_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any, e_upd_ext: Any) -> list[SimulationEvent]:
    """One event set per accepted intent result (rollback path only)."""
    tick = ctx.tick
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    for ir in ([] if _push_shapers_active else (getattr(e_upd_ext, "intent_results", None) or [])):
        if not getattr(ir, "accepted", False):
            continue
        src_kind = getattr(ir, "source_kind", None)
        if src_kind == "NODE":
            events.append(SimulationEvent(
                event_type="resource_harvested", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"node_id": str(getattr(ir, "source_id", ""))},
            ))
        elif src_kind == "CRAFTING":
            events.append(SimulationEvent(
                event_type="item_crafted", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"source_id": str(getattr(ir, "source_id", ""))},
            ))
        elif src_kind in ("SHOP_BUY", "SHOP_SELL"):
            events.append(SimulationEvent(
                event_type="shop_transaction", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"kind": src_kind},
            ))
            events.append(SimulationEvent(
                event_type="trade_executed", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"kind": src_kind},
            ))
        elif src_kind == "QUEST":
            events.append(SimulationEvent(
                event_type="quest_reward_dispensed", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"source_id": str(getattr(ir, "source_id", ""))},
            ))
        elif src_kind in _GOLD_SINK_KINDS:
            events.append(SimulationEvent(
                event_type="gold_sink_fired", event_category="economy",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"mechanism": src_kind},
            ))
        elif src_kind == "INFORMATION_PURCHASE":
            events.extend(_information_purchase_events(ctx, eid, entity, prior_ent, ir))
    return events
