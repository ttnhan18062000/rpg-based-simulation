"""Vitals, wounds, attributes, equipment and identity-change events of one entity (outside LIGHT and LONG_RUN mode)."""

from __future__ import annotations

from typing import Any

from src.observability.config import ObservabilityMode
from src.observability.events import EventSeverity, SimulationEvent
from src.observability.extraction.context import ExtractContext


def _is_real_number(*values: Any) -> bool:
    return all(isinstance(v, (int, float)) for v in values)


_ATTR_FIELDS = (
    "strength", "agility", "vitality", "endurance",
    "intelligence", "spirit", "wisdom", "perception", "charisma",
)


def vitals_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """All vitals-class events, in the order the old extract() emitted them; none in LIGHT or LONG_RUN mode."""
    events: list[SimulationEvent] = []
    if ctx.mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
        return events
    events.extend(_biological_events(ctx, eid, entity, prior_ent))
    events.extend(_stamina_events(ctx, eid, entity, prior_ent))
    events.extend(_wound_sustained_events(ctx, eid, entity, prior_ent))
    events.extend(_wound_healed_events(ctx, eid, entity, prior_ent))
    events.extend(_scar_events(ctx, eid, entity, prior_ent))
    events.extend(_attribute_events(ctx, eid, entity, prior_ent))
    events.extend(_equipment_events(ctx, eid, entity, prior_ent))
    events.extend(_durability_events(ctx, eid, entity, prior_ent))
    events.extend(_identity_change_events(ctx, eid, entity, prior_ent))
    events.extend(_identity_learning_events(ctx, eid, entity, prior_ent))
    return events


def _biological_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """biological_state_changed."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    bio, prior_bio = entity.biological, prior_ent.biological
    if _is_real_number(
        bio.hunger, bio.sleep_debt, bio.rest_pressure,
        prior_bio.hunger, prior_bio.sleep_debt, prior_bio.rest_pressure,
    ) and (bio.hunger, bio.sleep_debt, bio.rest_pressure) != (
        prior_bio.hunger, prior_bio.sleep_debt, prior_bio.rest_pressure
    ):
        worst = max(bio.hunger, bio.sleep_debt, bio.rest_pressure)
        severity: EventSeverity = "CRITICAL" if worst >= 95 else "WARNING" if worst >= 80 else "INFO"
        events.append(SimulationEvent(
            event_type="biological_state_changed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity=severity,
            source_system="event_extractor", message="",
            payload={
                "hunger": bio.hunger, "sleep_debt": bio.sleep_debt,
                "rest_pressure": bio.rest_pressure,
                "hunger_delta": bio.hunger - prior_bio.hunger,
                "sleep_debt_delta": bio.sleep_debt - prior_bio.sleep_debt,
                "rest_pressure_delta": bio.rest_pressure - prior_bio.rest_pressure,
            },
        ))
    return events


def _stamina_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """stamina_changed."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    stam, prior_stam = entity.stamina, prior_ent.stamina
    if _is_real_number(stam.current, prior_stam.current) and stam.current != prior_stam.current:
        severity: EventSeverity = "WARNING" if stam.current < stam.exhaustion_threshold else "INFO"
        events.append(SimulationEvent(
            event_type="stamina_changed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity=severity,
            source_system="event_extractor", message="",
            payload={
                "current": stam.current, "max_stamina": stam.max_stamina,
                "delta": stam.current - prior_stam.current,
                "exhausted": stam.current < stam.exhaustion_threshold,
            },
        ))
    return events


def _wound_sustained_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """wound_sustained."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    entity_wounds = entity.combat.wounds if isinstance(entity.combat.wounds, (list, tuple)) else []
    prior_wounds = prior_ent.combat.wounds if isinstance(prior_ent.combat.wounds, (list, tuple)) else []
    prior_wound_ids = {w.id for w in prior_wounds}
    for wound in entity_wounds:
        if wound.id not in prior_wound_ids:
            severity: EventSeverity = "CRITICAL" if wound.severity >= 0.7 else "WARNING" if wound.severity >= 0.4 else "INFO"
            events.append(SimulationEvent(
                event_type="wound_sustained", event_category="lifecycle",
                tick=tick, entity_id=eid, severity=severity,
                source_system="event_extractor", message="",
                payload={"wound_id": wound.id, "kind": wound.kind, "severity": wound.severity},
            ))
    return events


def _wound_healed_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """wound_healed."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    entity_wounds = entity.combat.wounds if isinstance(entity.combat.wounds, (list, tuple)) else []
    prior_wounds = prior_ent.combat.wounds if isinstance(prior_ent.combat.wounds, (list, tuple)) else []
    prior_wounds_by_id = {w.id: w for w in prior_wounds}
    for wound in entity_wounds:
        prior_wound = prior_wounds_by_id.get(wound.id)
        if prior_wound is not None and wound.healed and not prior_wound.healed:
            events.append(SimulationEvent(
                event_type="wound_healed", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"wound_id": wound.id, "kind": wound.kind},
            ))
    return events


def _scar_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """scar_gained."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    entity_scars = entity.combat.scars if isinstance(entity.combat.scars, (list, tuple)) else []
    prior_scars = prior_ent.combat.scars if isinstance(prior_ent.combat.scars, (list, tuple)) else []
    prior_scar_ids = {s.id for s in prior_scars}
    for scar in entity_scars:
        if scar.id not in prior_scar_ids:
            events.append(SimulationEvent(
                event_type="scar_gained", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"scar_id": scar.id, "wound_kind": scar.wound_kind},
            ))
    return events


def _attribute_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """attribute_changed."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Base attributes (TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP). Full
    # coverage by design, same rationale as the vitals events above. Severity is
    # direction-based (WARNING on any decline, INFO otherwise) rather than
    # magnitude-based -- no existing numeric "significant attribute change" threshold
    # exists anywhere in the repo to reuse, unlike exhaustion_threshold/WoundState.
    # severity above.
    attrs, prior_attrs = entity.attributes, prior_ent.attributes
    if _is_real_number(*(getattr(attrs, f) for f in _ATTR_FIELDS)) and _is_real_number(
        *(getattr(prior_attrs, f) for f in _ATTR_FIELDS)
    ):
        attr_deltas = {
            f: getattr(attrs, f) - getattr(prior_attrs, f)
            for f in _ATTR_FIELDS
            if getattr(attrs, f) != getattr(prior_attrs, f)
        }
        if attr_deltas:
            severity: EventSeverity = "WARNING" if any(d < 0 for d in attr_deltas.values()) else "INFO"
            events.append(SimulationEvent(
                event_type="attribute_changed", event_category="lifecycle",
                tick=tick, entity_id=eid, severity=severity,
                source_system="event_extractor", message="",
                payload={"deltas": attr_deltas},
            ))
    return events


def _equipment_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """item_equipped and item_unequipped, one per changed slot in slot order."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Equipment (TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP). Full coverage by
    # design, same rationale as the events above -- durability only changes on
    # discrete combat-hit/repair actions (never an unconditional per-tick decay), so
    # per-real-delta coverage does not create movement/biological-class volume.
    eq, prior_eq = entity.equipment, prior_ent.equipment
    eq_slots = eq.slots if isinstance(eq.slots, dict) else {}
    prior_eq_slots = prior_eq.slots if isinstance(prior_eq.slots, dict) else {}
    for slot in sorted(set(eq_slots) | set(prior_eq_slots), key=lambda s: getattr(s, "value", s)):
        new_item = eq_slots.get(slot)
        old_item = prior_eq_slots.get(slot)
        if new_item == old_item:
            continue
        if new_item is not None:
            events.append(SimulationEvent(
                event_type="item_equipped", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"slot": slot.value, "item_id": new_item, "previous_item_id": old_item},
            ))
        elif old_item is not None:
            events.append(SimulationEvent(
                event_type="item_unequipped", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"slot": slot.value, "previous_item_id": old_item},
            ))
    return events


def _durability_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """equipment_durability_changed, one per changed slot in slot order."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    eq, prior_eq = entity.equipment, prior_ent.equipment
    # Durability severity bands (INFO >= 50, WARNING < 50 and > 0, CRITICAL <= 0) use
    # the field's real 0-100 scale (src/core/equipment.py/combat.py/core_actions.py
    # all agree on this scale) -- the same 50% "needs repair" intent already designed
    # into src/domains/progression/gaps.py and src/engine/gold_sink.py, just applied
    # correctly (both of those compare against a 0-1 scale by mistake, a disclosed,
    # unfixed bug -- see this ticket's own investigation.md).
    eq_dur = eq.durability if isinstance(eq.durability, dict) else {}
    prior_eq_dur = prior_eq.durability if isinstance(prior_eq.durability, dict) else {}
    for slot in sorted(set(eq_dur) | set(prior_eq_dur), key=lambda s: getattr(s, "value", s)):
        new_dur: Any = eq_dur.get(slot)
        old_dur: Any = prior_eq_dur.get(slot)
        if not _is_real_number(new_dur, old_dur) or new_dur == old_dur:
            continue
        if new_dur > old_dur:
            severity: EventSeverity = "INFO"
        elif new_dur <= 0.0:
            severity = "CRITICAL"
        elif new_dur < 50.0:
            severity = "WARNING"
        else:
            severity = "INFO"
        events.append(SimulationEvent(
            event_type="equipment_durability_changed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity=severity,
            source_system="event_extractor", message="",
            payload={"slot": slot.value, "durability": new_dur, "delta": new_dur - old_dur},
        ))
    return events


def _identity_change_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """entity_role_changed and entity_faction_changed."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # Identity: role/faction/recipes/cooldowns (TCK-20260808-ENTITY-IDENTITY-ROLE-
    # FACTION-OBSERVABILITY-GAP). Full coverage by design, same rationale as the
    # events above. No TaskUpdate.work_kind_set event -- deliberate verdict, documented
    # in this ticket's own investigation.md: it is per-tick scheduling plumbing (every
    # acting entity, nearly every tick), not persistent narrative state.
    ident, prior_ident = entity.identity, prior_ent.identity
    if _is_real_number(ident.role, prior_ident.role) and ident.role != prior_ident.role:
        events.append(SimulationEvent(
            event_type="entity_role_changed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"role": ident.role, "previous_role": prior_ident.role},
        ))
    if _is_real_number(ident.faction, prior_ident.faction) and ident.faction != prior_ident.faction:
        events.append(SimulationEvent(
            event_type="entity_faction_changed", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"faction": ident.faction, "previous_faction": prior_ident.faction},
        ))
    return events


def _identity_learning_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """recipe_learned and skill_cooldown_started."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    ident, prior_ident = entity.identity, prior_ent.identity
    new_recipes = ident.known_recipes if isinstance(ident.known_recipes, (set, frozenset)) else set()
    prior_recipes = prior_ident.known_recipes if isinstance(prior_ident.known_recipes, (set, frozenset)) else set()
    for recipe_id in sorted(new_recipes - prior_recipes, key=lambda _id: _id):
        events.append(SimulationEvent(
            event_type="recipe_learned", event_category="lifecycle",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"recipe_id": recipe_id},
        ))
    new_cooldowns = ident.cooldowns if isinstance(ident.cooldowns, dict) else {}
    prior_cooldowns = prior_ident.cooldowns if isinstance(prior_ident.cooldowns, dict) else {}
    for skill_id, tick_ready in new_cooldowns.items():
        if prior_cooldowns.get(skill_id) != tick_ready:
            events.append(SimulationEvent(
                event_type="skill_cooldown_started", event_category="lifecycle",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"skill_id": skill_id, "tick_ready": tick_ready},
            ))
    return events
