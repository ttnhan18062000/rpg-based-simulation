"""Combat events of one entity: damage, kill, initiated, near-death and hazard drain, plus the real-combat guard."""

from __future__ import annotations

from typing import Any

from src.core.combat_constants import NEAR_DEATH_HP_RATIO
from src.observability.config import ObservabilityMode
from src.observability.events import CombatDamageEvent, CombatKillEvent, SimulationEvent
from src.observability.extraction.context import ExtractContext

# TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: moved to src/core/combat_constants.py so
# src/domains/combat_engagement/power.py (Sec 13.5a) can share the same cutoff without pointing
# gameplay logic at this observability module (the reverse of this repo's own domains->
# observability import boundary, enforced by tests/architecture/test_phase18_import_boundaries.py).
NEAR_DEATH_THRESHOLD = NEAR_DEATH_HP_RATIO

# outcome_kind values that never represent a real entity-vs-entity combat resolution, even when
# a CombatUpdate carries an attacker_id (defense-in-depth alongside the attacker_id check below).
_NON_COMBAT_OUTCOME_KINDS = ("HAZARD", "REJECTED")


def real_combat_update(e_upd: Any) -> Any | None:
    """Return e_upd.combat only if it represents a genuine entity-vs-entity combat resolution.

    attacker_id is the primary discriminant: every real damage-dealing CombatUpdate constructed
    by src/engine/combat.py sets it, while non-combat HP-reducing sources (hazard drain in
    world_dynamics.py, starvation/exhaustion in biological.py) never do — both leave attacker_id
    at its None default. outcome_kind is checked too, defense-in-depth, since CombatUpdate's own
    dataclass default for outcome_kind ("SURVIVE") coincides with a real combat value and is not
    itself a safe discriminant on its own.
    """
    combat_upd = getattr(e_upd, "combat", None) if e_upd is not None else None
    if combat_upd is None:
        return None
    if getattr(combat_upd, "attacker_id", None) is None:
        return None
    if getattr(combat_upd, "outcome_kind", None) in _NON_COMBAT_OUTCOME_KINDS:
        return None
    return combat_upd


def damage_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """combat_damage (rollback path only)."""
    tick = ctx.tick
    now = ctx.now
    mode = ctx.mode
    update = ctx.update
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # Combat damage event — only classified as combat when a genuine entity-vs-entity
    # combat resolution caused the HP loss (see real_combat_update: hazard drain and
    # biological/starvation damage both reduce HP without ever setting attacker_id).
    # Flag-gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live behind
    # src/observability/event_shapers.py's CombatShaper when ENABLE_PUSH_EVENT_SHAPERS is
    # "ON" (default); this branch is the rollback path when it isn't.
    hp_diff = entity.combat.hp - prior_ent.combat.hp
    if not _push_shapers_active and hp_diff < 0:
        e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
        real_combat_upd = real_combat_update(e_upd)
        if real_combat_upd is not None:
            is_lethal = (entity.combat.hp <= 0 or not entity.lifecycle.active)
            # Volumization rule: skip routine damage inside LIGHT or LONG_RUN mode unless lethal
            if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                events.append(CombatDamageEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    attacker_id=real_combat_upd.attacker_id, damage=int(-hp_diff),
                    is_lethal=is_lethal
                ))
    return events


def _hero_death_events(ctx: ExtractContext, eid: int, entity: Any) -> list[SimulationEvent]:
    """hero_death_unrecorded for a hero that was deactivated."""
    tick = ctx.tick
    events: list[SimulationEvent] = []
    # NARRATIVE: hero_death_unrecorded — hero-kind entity deactivated this tick
    # (D4). Deliberately NOT gated on is_genuine_combat_death: this is a broader
    # "a hero died and nothing else recorded it" narrative-gap signal, not a
    # combat-specific one — a hero dying of old age with no other tracking is just
    # as real an "unrecorded" gap as a hero dying in unattributed combat.
    if getattr(entity, "kind", None) == "hero":
        events.append(SimulationEvent(
            event_type="hero_death_unrecorded",
            event_category="lifecycle",
            tick=tick,
            entity_id=eid,
            severity="WARNING",
            source_system="event_extractor",
            message="",
            payload={"entity_id": eid},
        ))
    return events


def kill_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """combat_kill and hero_death_unrecorded on an active to inactive transition."""
    tick = ctx.tick
    now = ctx.now
    update = ctx.update
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # Kill events — fires on a lifecycle.active→False transition, EXCEPT the same-tick
    # outcome_kind=="KILL" case, which CombatShaper now owns live when
    # ENABLE_PUSH_EVENT_SHAPERS is "ON" (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-
    # FACTION), and EXCEPT any death whose own authoritative
    # `LifecycleComponent.death_reason` isn't "COMBAT" (TCK-20260809-COMBAT-KILL-
    # LIFECYCLE-CREDIT-GAP-INVESTIGATION). `LifecycleSystem.resolve_lifecycle()` is the
    # sole runtime writer of both `lifecycle.active` and `death_reason` (set together, same
    # EntityUpdate) and only ever assigns "OLD_AGE" or "COMBAT" — this branch used to fire
    # unconditionally on ANY active->False transition regardless of cause, which meant
    # HAZARD-caused deaths (a world_dynamics-owned mechanic, already excluded from
    # `real_combat_update` via `_NON_COMBAT_OUTCOME_KINDS`) and OLD_AGE deaths were both
    # being counted as `combat_kill`/`entity_killed` and penalized under the COMBAT
    # pillar's attrition scoring, even though neither is combat. Confirmed via direct
    # pipeline instrumentation on `dungeon_crawl_seed42_2000t`: of the run's 25
    # calibrate_simq-scored `combat_kill` events, every one traced back to a `death_reason`
    # of "HAZARD-preceded" (killer_id always None, prior combat_upd outcome_kind="HAZARD")
    # or unset (no combat_upd at all, matching a mass despawn/old-age cluster) — none
    # traced to "COMBAT" — while genuine `combat_engagement_ended` activity that same run
    # produced zero credit because it never resolved as KILL/ESCAPED. This was the real,
    # structural reason the COMBAT pillar sat at the B/C grade boundary: it was absorbing
    # negative credit from non-combat mortality while its own positive-scoring surface
    # stayed unreachable. Genuine combat deaths (`death_reason=="COMBAT"`) were separately
    # confirmed still to fire correctly under this fix.
    # Old-age/despawn deaths keep their own real credit path: `demographic_mortality`
    # (WORLD pillar) fires separately when the corpse is later removed via
    # `entities_remove`, unaffected by this change.
    if prior_ent.lifecycle.active and not entity.lifecycle.active:
        e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
        real_combat_upd = real_combat_update(e_upd)
        is_shaper_owned_kill = (
            _push_shapers_active and real_combat_upd is not None
            and getattr(real_combat_upd, "outcome_kind", None) == "KILL"
        )
        is_genuine_combat_death = getattr(entity.lifecycle, "death_reason", None) == "COMBAT"
        if not is_shaper_owned_kill:
            if is_genuine_combat_death:
                killer_id = real_combat_upd.attacker_id if real_combat_upd is not None else None

                events.append(CombatKillEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    killer_id=killer_id
                ))
            events.extend(_hero_death_events(ctx, eid, entity))
    return events


def initiated_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """combat_initiated (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # Combat initiated — entity was at full HP prior tick, now taking damage from a
    # genuine combat resolution (same real_combat_update guard as combat_damage above).
    # Flag-gated, same rollback pattern as combat_damage above.
    if (not _push_shapers_active
            and entity.lifecycle.active
            and prior_ent.combat.hp == prior_ent.combat.max_hp
            and entity.combat.hp < entity.combat.max_hp):
        e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
        real_combat_upd = real_combat_update(e_upd)
        if real_combat_upd is not None:
            events.append(SimulationEvent(
                event_type="combat_initiated", event_category="combat",
                tick=tick, entity_id=eid, severity="INFO",
                source_system="event_extractor", message="",
                payload={"attacker_id": real_combat_upd.attacker_id},
            ))
    return events


def near_death_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """near_death_survival (rollback path only)."""
    tick = ctx.tick
    update = ctx.update
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # Near-death survival — HP crosses below 20% threshold while entity survives a
    # genuine combat resolution (previously fired on any HP-threshold crossing at all,
    # including hazard/biological causes — same real_combat_update guard as above).
    # Flag-gated, same rollback pattern as combat_damage above.
    near_death_hp = prior_ent.combat.max_hp * NEAR_DEATH_THRESHOLD
    if (not _push_shapers_active
            and entity.lifecycle.active
            and entity.combat.hp < near_death_hp
            and prior_ent.combat.hp >= near_death_hp):
        e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
        if real_combat_update(e_upd) is not None:
            events.append(SimulationEvent(
                event_type="near_death_survival", event_category="combat",
                tick=tick, entity_id=eid, severity="WARNING",
                source_system="event_extractor", message="",
                payload={"hp": entity.combat.hp, "max_hp": entity.combat.max_hp},
            ))
    return events


def hazard_drain_events(ctx: ExtractContext, eid: int, e_upd_ext: Any) -> list[SimulationEvent]:
    """hazard_drain_applied (rollback path only)."""
    tick = ctx.tick
    _push_shapers_active = ctx.push_shapers_active
    events: list[SimulationEvent] = []
    # World: hazard_drain_applied (WorldDynamicsSystem records `hazard_damage`,
    # independently of outcome_kind, so it also fires for an entity combat already
    # resolved this tick).
    # Flag-gated, same rollback pattern as the economy loop above — migrated alongside
    # COMBAT per TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT's Decision 1.
    combat_upd = getattr(e_upd_ext, "combat", None)
    _hazard_damage = getattr(combat_upd, "hazard_damage", 0) if combat_upd else 0
    if not _push_shapers_active and isinstance(_hazard_damage, int) and _hazard_damage > 0:
        events.append(SimulationEvent(
            event_type="hazard_drain_applied", event_category="combat",
            tick=tick, entity_id=eid, severity="WARNING",
            source_system="event_extractor", message="",
            payload={"damage": _hazard_damage},
        ))
    return events
