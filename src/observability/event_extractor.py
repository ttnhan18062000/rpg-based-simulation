from __future__ import annotations
import time
import logging
from typing import Any, List, Optional
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectStatus
from src.core.quests import QuestState
from src.core.updates import StateUpdate
from src.domains.commitment.abandonment import AbandonmentEvaluator, AbandonmentCategory
from src.domains.world_emergence.schema import WorldEventCategory
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import (
    SimulationEvent, CombatDamageEvent, CombatKillEvent,
    GoldTransactionEvent, QuestEvent, MovementEvent, LifecycleEvent
)
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS

logger = logging.getLogger(__name__)

_NEAR_DEATH_THRESHOLD = 0.2

# outcome_kind values that never represent a real entity-vs-entity combat resolution, even when
# a CombatUpdate carries an attacker_id (defense-in-depth alongside the attacker_id check below).
_NON_COMBAT_OUTCOME_KINDS = ("HAZARD", "REJECTED")


def _real_combat_update(e_upd: Any) -> Any | None:
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

# LeadCertainty enum value → float for band-crossing delta computation (lead_certainty_updated)
_CERTAINTY_FLOAT: dict[str, float] = {
    "PRECISE": 1.0, "APPROXIMATE": 0.5, "VAGUE": 0.25, "EXHAUSTED": 0.0,
}

# Ticks without certainty change before a lead is considered stale (belief_stale)
_BELIEF_STALE_TICKS = 50

# How many ticks without XP before progression_plateau_detected fires (xp_rate_zero)
_XP_PLATEAU_TICKS = 50

# How many ticks with zero movement across level/skills/gear/gold before
# capability_growth_stalled fires (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE)
_CAPABILITY_STALL_TICKS = 300

# Minimum lifecycle.generation (a completed Hero's Journey rebirth already occurred) for
# life_arc_incoherent to be eligible
_LATE_GENERATION_THRESHOLD = 2

# Project kinds inconsistent with a high-urgency DANGER concern (decision_divergence_detected)
_NON_SURVIVAL_PROJECT_KINDS = frozenset(("harvesting", "exploration", "social", "crafting"))

# Spawn interval (must match SpawnService.SPAWN_INTERVAL)
_SPAWN_INTERVAL = 50


class EventExtractor:
    """Extracts curated low-volume SimulationEvents from state changes and committed updates."""

    # Per-run tracking for route novelty: entity_id → set of seen family strings.
    # NOT durable state — must be cleared at run start via reset_run_state().
    _seen_routing_families: dict[int, set[str]] = {}

    # Progression: entity_id → last tick XP was granted (for plateau detection)
    _last_xp_tick: dict[int, int] = {}
    # Entities already emitted progression_plateau this run
    _emitted_plateau: set[int] = set()
    # Leads already emitted as stale this run: entity_id → set of lead_ids
    _emitted_stale_leads: dict[int, set[str]] = {}
    # Social memory: (entity_id, other_entity_id) pairs already emitted this run
    _emitted_social_memory: set[tuple[int, int]] = set()
    # Contract milestones: "{contract_id}:{label}" keys already emitted this run
    _emitted_contract_milestones: set[str] = set()

    # Capability trend / life-arc coherence (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE):
    # entity_id → last tick any of level/skills/gear/gold moved. Initialized to first-observed
    # tick (not 0) so an entity first seen mid-run isn't immediately treated as stalled.
    _last_capability_growth_tick: dict[int, int] = {}
    _emitted_capability_stalled: set[int] = set()
    _emitted_life_arc_incoherent: set[int] = set()

    _SOCIAL_MEMORY_THRESHOLD = 0.3  # minimum trust_history delta to emit
    _CONTRACT_MILESTONE_THRESHOLDS = ((0.25, "25%"), (0.50, "50%"), (0.75, "75%"))

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start and in test teardown."""
        cls._seen_routing_families.clear()
        cls._last_xp_tick.clear()
        cls._emitted_plateau.clear()
        cls._emitted_stale_leads.clear()
        cls._emitted_social_memory.clear()
        cls._emitted_contract_milestones.clear()
        cls._last_capability_growth_tick.clear()
        cls._emitted_capability_stalled.clear()
        cls._emitted_life_arc_incoherent.clear()

    @staticmethod
    def extract(
        prior_state: AuthoritativeState,
        current_state: AuthoritativeState,
        update: Any,
        mode: ObservabilityMode = ObservabilityMode.LIGHT
    ) -> List[SimulationEvent]:
        """Compares state transitions to produce semantic events matching volume policies."""
        if mode == ObservabilityMode.OFF:
            return []

        # TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION: COMBAT/ECONOMY/FACTION event
        # emission moved to src/observability/event_shapers.py's apply-layer shaper registry,
        # delivered live by Kernel._phase_observability() when this flag is "ON" (the default —
        # see FeatureFlagManager). The branches below stay in this file, flag-gated, as a real
        # rollback path: set ENABLE_PUSH_EVENT_SHAPERS to anything other than "ON" to restore
        # exact pre-cutover diffing behavior for these 3 domains. Default "ON" (not falling back
        # to the old path) when feature_flags is absent/doesn't override — matches
        # FeatureFlagManager's own new default, so an unconfigured run gets the current default
        # behavior, not a silent revert to pre-cutover diffing.
        _push_shapers_active = (getattr(prior_state, "feature_flags", None) or {}).get(
            "ENABLE_PUSH_EVENT_SHAPERS", "ON") == "ON"

        # Phase 2 cutover (TCK-20260806-PUSH-CUTOVER-PHASE2): same rollback pattern as
        # _push_shapers_active above, but on the SEPARATE ENABLE_PUSH_EVENT_SHAPERS_PHASE2 flag —
        # NOT the same flag reused, contrary to this epic's own original premise. Phase 2's
        # shapers live in a separate PHASE2_SHAPER_REGISTRY specifically because
        # ENABLE_PUSH_EVENT_SHAPERS already defaulted "ON" by the time Phase 2 began (Phase 1's
        # own cutover), so registering into the same registry/flag would have delivered
        # immediately with no SHADOW window — a real bug found and fixed during
        # TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY's own build. Default "ON" for the same reason
        # _push_shapers_active defaults "ON": this cutover ticket is what flips the *default*
        # (feature_flags.py), so an unconfigured run gets the new default behavior, not a silent
        # revert.
        _push_shapers_phase2_active = (getattr(prior_state, "feature_flags", None) or {}).get(
            "ENABLE_PUSH_EVENT_SHAPERS_PHASE2", "ON") == "ON"

        # Quest cutover (TCK-20260807-QUEST-EVENT-PUSH-MIGRATION): same rollback pattern as
        # _push_shapers_active/_push_shapers_phase2_active above, on its OWN
        # ENABLE_PUSH_EVENT_SHAPERS_QUEST flag — NOT the Phase 2 flag (already ON, would give no
        # SHADOW window, the same reason Phase 2 needed its own flag distinct from Phase 1's).
        # Gates ONLY the quest_event construction below, NOT commitment_abandoned (a separate,
        # not-yet-migrated signal, tracked by TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP).
        _push_shapers_quest_active = (getattr(prior_state, "feature_flags", None) or {}).get(
            "ENABLE_PUSH_EVENT_SHAPERS_QUEST", "ON") == "ON"

        # Agency cutover (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP,
        # TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP): same rollback pattern as the
        # flags above, on its OWN ENABLE_PUSH_EVENT_SHAPERS_AGENCY flag — gates commitment_abandoned
        # and rejection_cascade_tick, the last 2 real push-migration gaps found in this file.
        _push_shapers_agency_active = (getattr(prior_state, "feature_flags", None) or {}).get(
            "ENABLE_PUSH_EVENT_SHAPERS_AGENCY", "ON") == "ON"

        tick = current_state.tick
        now = time.time()
        events: List[SimulationEvent] = []

        # Optimization: Scoped comparison using dirty entity IDs
        dirty_entity_ids = update.entity_updates.keys() if (update and hasattr(update, "entity_updates")) else []
        if not dirty_entity_ids:
            dirty_entity_ids = current_state.entities.keys()

        for eid in dirty_entity_ids:
            entity = current_state.entities.get(eid)
            prior_ent = prior_state.entities.get(eid)

            # Despawn lifecycle
            if entity is None:
                if prior_ent is not None:
                    events.append(LifecycleEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        action="despawn", details={"kind": prior_ent.kind, "position": prior_ent.navigation.position}
                    ))
                    # Demographic mortality — despawn without a combat attacker. Flag-gated
                    # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind DeferredInstrumentationShaper
                    # when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this branch is the
                    # rollback path when it isn't. LifecycleEvent (despawn) above stays
                    # unconditional — it is not a migrated event.
                    if not _push_shapers_phase2_active:
                        e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                        has_attacker = _real_combat_update(e_upd) is not None
                        if not has_attacker:
                            events.append(SimulationEvent(
                                event_type="demographic_mortality", event_category="lifecycle",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"kind": prior_ent.kind},
                            ))
                continue

            # Spawn lifecycle
            if prior_ent is None:
                events.append(LifecycleEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    action="spawn", details={"kind": entity.kind, "position": entity.navigation.position}
                ))
                # demographic_birth: flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same pattern —
                # LifecycleEvent (spawn) above stays unconditional.
                if not _push_shapers_phase2_active:
                    events.append(SimulationEvent(
                        event_type="demographic_birth", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"kind": entity.kind},
                    ))
                continue

            # Movement (exclusively low-volume for non-LIGHT/LONG_RUN modes)
            if prior_ent.navigation.position != entity.navigation.position:
                if mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    events.append(MovementEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        start_pos=prior_ent.navigation.position,
                        end_pos=entity.navigation.position
                    ))

            # Vitals — biological/stamina/wounds (TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP).
            # Full coverage by design (every real delta, not just threshold crossings), same
            # high-volume-but-real precedent as `movement` above — emitted unconditionally,
            # severity distinguishes major from minor, not scored to any SimQ pillar in this pass
            # (a separate decision; see the ticket's own Out of Scope).
            #
            # _is_real_number guards against test fixtures that build `entity`/`prior_ent` as a
            # bare MagicMock() with only some components explicitly wired (a well-established
            # pattern across tests/unit/observability/ — .biological/.stamina are commonly left
            # unset, which MagicMock auto-fills with further Mocks, not real floats). Real
            # EntityState objects always carry real floats here; this never affects real ticks.
            def _is_real_number(*values: Any) -> bool:
                return all(isinstance(v, (int, float)) for v in values)

            if mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                bio, prior_bio = entity.biological, prior_ent.biological
                if _is_real_number(
                    bio.hunger, bio.sleep_debt, bio.rest_pressure,
                    prior_bio.hunger, prior_bio.sleep_debt, prior_bio.rest_pressure,
                ) and (bio.hunger, bio.sleep_debt, bio.rest_pressure) != (
                    prior_bio.hunger, prior_bio.sleep_debt, prior_bio.rest_pressure
                ):
                    worst = max(bio.hunger, bio.sleep_debt, bio.rest_pressure)
                    severity = "CRITICAL" if worst >= 95 else "WARNING" if worst >= 80 else "INFO"
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

                stam, prior_stam = entity.stamina, prior_ent.stamina
                if _is_real_number(stam.current, prior_stam.current) and stam.current != prior_stam.current:
                    severity = "WARNING" if stam.current < stam.exhaustion_threshold else "INFO"
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

                entity_wounds = entity.combat.wounds if isinstance(entity.combat.wounds, (list, tuple)) else []
                prior_wounds = prior_ent.combat.wounds if isinstance(prior_ent.combat.wounds, (list, tuple)) else []
                prior_wound_ids = {w.id for w in prior_wounds}
                for wound in entity_wounds:
                    if wound.id not in prior_wound_ids:
                        severity = "CRITICAL" if wound.severity >= 0.7 else "WARNING" if wound.severity >= 0.4 else "INFO"
                        events.append(SimulationEvent(
                            event_type="wound_sustained", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity=severity,
                            source_system="event_extractor", message="",
                            payload={"wound_id": wound.id, "kind": wound.kind, "severity": wound.severity},
                        ))
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

                # Base attributes (TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP). Full
                # coverage by design, same rationale as the vitals events above. Severity is
                # direction-based (WARNING on any decline, INFO otherwise) rather than
                # magnitude-based -- no existing numeric "significant attribute change" threshold
                # exists anywhere in the repo to reuse, unlike exhaustion_threshold/WoundState.
                # severity above.
                attrs, prior_attrs = entity.attributes, prior_ent.attributes
                _ATTR_FIELDS = (
                    "strength", "agility", "vitality", "endurance",
                    "intelligence", "spirit", "wisdom", "perception", "charisma",
                )
                if _is_real_number(*(getattr(attrs, f) for f in _ATTR_FIELDS)) and _is_real_number(
                    *(getattr(prior_attrs, f) for f in _ATTR_FIELDS)
                ):
                    attr_deltas = {
                        f: getattr(attrs, f) - getattr(prior_attrs, f)
                        for f in _ATTR_FIELDS
                        if getattr(attrs, f) != getattr(prior_attrs, f)
                    }
                    if attr_deltas:
                        severity = "WARNING" if any(d < 0 for d in attr_deltas.values()) else "INFO"
                        events.append(SimulationEvent(
                            event_type="attribute_changed", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity=severity,
                            source_system="event_extractor", message="",
                            payload={"deltas": attr_deltas},
                        ))

                # Equipment (TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP). Full coverage by
                # design, same rationale as the events above -- durability only changes on
                # discrete combat-hit/repair actions (never an unconditional per-tick decay), so
                # per-real-delta coverage does not create movement/biological-class volume.
                eq, prior_eq = entity.equipment, prior_ent.equipment
                eq_slots = eq.slots if isinstance(eq.slots, dict) else {}
                prior_eq_slots = prior_eq.slots if isinstance(prior_eq.slots, dict) else {}
                for slot in set(eq_slots) | set(prior_eq_slots):
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

                # Durability severity bands (INFO >= 50, WARNING < 50 and > 0, CRITICAL <= 0) use
                # the field's real 0-100 scale (src/core/equipment.py/combat.py/core_actions.py
                # all agree on this scale) -- the same 50% "needs repair" intent already designed
                # into src/domains/progression/gaps.py and src/engine/gold_sink.py, just applied
                # correctly (both of those compare against a 0-1 scale by mistake, a disclosed,
                # unfixed bug -- see this ticket's own investigation.md).
                eq_dur = eq.durability if isinstance(eq.durability, dict) else {}
                prior_eq_dur = prior_eq.durability if isinstance(prior_eq.durability, dict) else {}
                for slot in set(eq_dur) | set(prior_eq_dur):
                    new_dur = eq_dur.get(slot)
                    old_dur = prior_eq_dur.get(slot)
                    if not _is_real_number(new_dur, old_dur) or new_dur == old_dur:
                        continue
                    if new_dur > old_dur:
                        severity = "INFO"
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
                new_recipes = ident.known_recipes if isinstance(ident.known_recipes, (set, frozenset)) else set()
                prior_recipes = prior_ident.known_recipes if isinstance(prior_ident.known_recipes, (set, frozenset)) else set()
                for recipe_id in new_recipes - prior_recipes:
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

            # Combat damage event — only classified as combat when a genuine entity-vs-entity
            # combat resolution caused the HP loss (see _real_combat_update: hazard drain and
            # biological/starvation damage both reduce HP without ever setting attacker_id).
            # Flag-gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live behind
            # src/observability/event_shapers.py's CombatShaper when ENABLE_PUSH_EVENT_SHAPERS is
            # "ON" (default); this branch is the rollback path when it isn't.
            hp_diff = entity.combat.hp - prior_ent.combat.hp
            if not _push_shapers_active and hp_diff < 0:
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                real_combat_upd = _real_combat_update(e_upd)
                if real_combat_upd is not None:
                    is_lethal = (entity.combat.hp <= 0 or not entity.lifecycle.active)
                    # Volumization rule: skip routine damage inside LIGHT or LONG_RUN mode unless lethal
                    if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                        events.append(CombatDamageEvent(
                            tick=tick, timestamp=now, entity_id=eid,
                            attacker_id=real_combat_upd.attacker_id, damage=int(-hp_diff),
                            is_lethal=is_lethal
                        ))

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
            # `_real_combat_update` via `_NON_COMBAT_OUTCOME_KINDS`) and OLD_AGE deaths were both
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
                real_combat_upd = _real_combat_update(e_upd)
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

            # Combat initiated — entity was at full HP prior tick, now taking damage from a
            # genuine combat resolution (same _real_combat_update guard as combat_damage above).
            # Flag-gated, same rollback pattern as combat_damage above.
            if (not _push_shapers_active
                    and entity.lifecycle.active
                    and prior_ent.combat.hp == prior_ent.combat.max_hp
                    and entity.combat.hp < entity.combat.max_hp):
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                real_combat_upd = _real_combat_update(e_upd)
                if real_combat_upd is not None:
                    events.append(SimulationEvent(
                        event_type="combat_initiated", event_category="combat",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"attacker_id": real_combat_upd.attacker_id},
                    ))

            # Near-death survival — HP crosses below 20% threshold while entity survives a
            # genuine combat resolution (previously fired on any HP-threshold crossing at all,
            # including hazard/biological causes — same _real_combat_update guard as above).
            # Flag-gated, same rollback pattern as combat_damage above.
            near_death_hp = prior_ent.combat.max_hp * _NEAR_DEATH_THRESHOLD
            if (not _push_shapers_active
                    and entity.lifecycle.active
                    and entity.combat.hp < near_death_hp
                    and prior_ent.combat.hp >= near_death_hp):
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                if _real_combat_update(e_upd) is not None:
                    events.append(SimulationEvent(
                        event_type="near_death_survival", event_category="combat",
                        tick=tick, entity_id=eid, severity="WARNING",
                        source_system="event_extractor", message="",
                        payload={"hp": entity.combat.hp, "max_hp": entity.combat.max_hp},
                    ))

            # XP granted and level-up (via IdentityComponent). Flag-gated
            # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind ProgressionShaper when
            # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
            if not _push_shapers_phase2_active and hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
                xp_delta = entity.identity.evolution_points - prior_ent.identity.evolution_points
                if xp_delta > 0:
                    events.append(SimulationEvent(
                        event_type="xp_granted", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"amount": xp_delta},
                    ))
                if entity.identity.evolution_level > prior_ent.identity.evolution_level:
                    events.append(SimulationEvent(
                        event_type="level_up", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"new_level": entity.identity.evolution_level},
                    ))

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

            # Agency and cognition events — derived from EntityUpdate fields
            e_upd_ext = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
            if e_upd_ext is not None:
                prop = getattr(e_upd_ext, "property_updates", None) or {}

                # route_selected through cooperation_event: flag-gated
                # (TCK-20260806-PUSH-CUTOVER-PHASE2) — live behind StrategyShaper when
                # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback
                # path when it isn't. The intent_results loop below is a SEPARATE, already-guarded
                # (Phase 1) block — not touched here.
                if not _push_shapers_phase2_active:
                    # Agency: route_selected / action_executed
                    routing_family = prop.get("last_routing_family")
                    if routing_family:
                        events.append(SimulationEvent(
                            event_type="route_selected", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"family": routing_family},
                        ))
                        events.append(SimulationEvent(
                            event_type="action_executed", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"family": routing_family},
                        ))
                        # Agency: route_family_first_use (once per novel family per entity per run)
                        seen = EventExtractor._seen_routing_families.setdefault(eid, set())
                        if routing_family not in seen:
                            seen.add(routing_family)
                            events.append(SimulationEvent(
                                event_type="route_family_first_use", event_category="strategy",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"entity_id": eid, "family": routing_family, "tick": tick},
                            ))

                    # Agency: defer_with_reason — property set by phase.py on DEFER_WITH_REASON
                    # path. Key "last_defer_reason" must match phase.py property_updates key
                    # exactly.
                    defer_reason = prop.get("last_defer_reason")
                    if defer_reason:
                        events.append(SimulationEvent(
                            event_type="defer_with_reason", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"entity_id": eid, "reason": defer_reason, "tick": tick},
                        ))

                    # Cognition: self_model_updated (PP-03)
                    if getattr(e_upd_ext, "self_model_bundle_set", None) is not None:
                        events.append(SimulationEvent(
                            event_type="self_model_updated", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={},
                        ))

                    # Information: belief_assimilated + belief_updated (PP-04)
                    if prop.get("last_assimilated_tick") == prior_state.tick:
                        subject = prop.get("last_assimilated_subject", "unknown")
                        events.append(SimulationEvent(
                            event_type="belief_assimilated", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"subject": subject},
                        ))
                        events.append(SimulationEvent(
                            event_type="belief_updated", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"subject": subject},
                        ))

                    # Information: route_new_query (fix 4,
                    # TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE)
                    if prop.get("last_routed_query_tick") == prior_state.tick:
                        subject = prop.get("last_routed_query_subject", "unknown")
                        events.append(SimulationEvent(
                            event_type="route_new_query", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"subject": subject},
                        ))

                    # Social: cooperation_event (PP-05)
                    if prop.get("last_cooperation_decision") is not None:
                        events.append(SimulationEvent(
                            event_type="cooperation_event", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"entity_id": eid,
                                     "decision": str(prop["last_cooperation_decision"])},
                        ))

                # Economy + Information events from intent_results (resource_transfers cleared
                # by PP-27). Flag-gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live
                # behind EconomyShaper when ENABLE_PUSH_EVENT_SHAPERS is "ON" (default); this loop
                # is the rollback path when it isn't. Every branch inside is a migrated ECONOMY
                # event — no partial-condition case here, unlike the Kill-events branch above.
                _GOLD_SINK_KINDS = frozenset(("REPAIR_FEE", "SERVICE_FEE", "TAX"))
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

                # World: hazard_drain_applied (WorldDynamicsSystem sets outcome_kind="HAZARD").
                # Flag-gated, same rollback pattern as the economy loop above — migrated alongside
                # COMBAT per TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT's Decision 1.
                combat_upd = getattr(e_upd_ext, "combat", None)
                if not _push_shapers_active and combat_upd and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
                    hp_delta = getattr(combat_upd, "hp_delta", 0)
                    if hp_delta < 0:
                        events.append(SimulationEvent(
                            event_type="hazard_drain_applied", event_category="combat",
                            tick=tick, entity_id=eid, severity="WARNING",
                            source_system="event_extractor", message="",
                            payload={"damage": int(-hp_delta)},
                        ))

            # Cognition: lead_certainty_changed (PP-30 side effect — state diff)
            # Information: lead_certainty_updated (band-crossing), belief_stale, decision signals
            # Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): the entire block below
            # (lead_certainty_changed through decision_divergence_detected) is migrated to
            # StrategyShaper — live when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this
            # block is the rollback path when it isn't.
            if not _push_shapers_phase2_active and hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
                curr_leads = getattr(entity.strategic, "leads", None) or {}
                prior_leads = getattr(prior_ent.strategic, "leads", None) or {}
                _stale_emitted = EventExtractor._emitted_stale_leads.setdefault(eid, set())
                for lid, lead in curr_leads.items():
                    prior_lead = prior_leads.get(lid)
                    if prior_lead is not None and lead.certainty != prior_lead.certainty:
                        events.append(SimulationEvent(
                            event_type="lead_certainty_changed", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={
                                "lead_id": lid,
                                "from_certainty": str(prior_lead.certainty),
                                "to_certainty": str(lead.certainty),
                            },
                        ))
                        # Information: lead_certainty_updated — distinct from lead_certainty_changed;
                        # carries float delta so InformationScorer can score direction and magnitude.
                        _prior_cv = _CERTAINTY_FLOAT.get(getattr(prior_lead.certainty, "value", str(prior_lead.certainty)), 0.0)
                        _curr_cv = _CERTAINTY_FLOAT.get(getattr(lead.certainty, "value", str(lead.certainty)), 0.0)
                        events.append(SimulationEvent(
                            event_type="lead_certainty_updated", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={
                                "lead_id": lid,
                                "certainty_delta": round(_curr_cv - _prior_cv, 4),
                                "lead_active": entity.strategic.current_project_id is not None,
                            },
                        ))
                    # belief_contradiction / lead_contradiction_resolved (this ticket): fires when
                    # LeadContradictionSystem.enforce() (run_phase "lead_contradiction") has just
                    # transitioned this lead to EXHAUSTED + test_outcome="FAILURE" this tick. Mirrors
                    # the exact payload shape LeadContradictionSystem.enforce() itself builds so a
                    # refine()-driven test observes identical events to a direct .enforce() call.
                    _prior_failed = (
                        prior_lead is not None
                        and getattr(prior_lead, "test_outcome", None) == "FAILURE"
                        and getattr(prior_lead.certainty, "value", str(prior_lead.certainty)) == "EXHAUSTED"
                    )
                    _curr_failed = (
                        getattr(lead, "test_outcome", None) == "FAILURE"
                        and getattr(lead.certainty, "value", str(lead.certainty)) == "EXHAUSTED"
                    )
                    if prior_lead is not None and _curr_failed and not _prior_failed:
                        events.append(SimulationEvent(
                            event_type="belief_contradiction", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="lead_contradiction_system", message="",
                            payload={
                                "lead_id": lid,
                                "provider_id": getattr(lead, "source_entity_id", None),
                                "subject": lead.subject,
                                "old_certainty": getattr(prior_lead.certainty, "value", str(prior_lead.certainty)),
                                "failure_count": lead.failure_count,
                            },
                        ))
                        events.append(SimulationEvent(
                            event_type="lead_contradiction_resolved", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="lead_contradiction_system", message="",
                            payload={
                                "lead_id": lid,
                                "subject": lead.subject,
                                "failure_count": lead.failure_count,
                            },
                        ))
                    # belief_stale: lead dormant for > threshold ticks without certainty update
                    # Uses discovered_tick as staleness proxy (last_updated_tick not tracked on LeadState)
                    _cert_str = getattr(lead.certainty, "value", str(lead.certainty))
                    _discovered = getattr(lead, "discovered_tick", tick)
                    try:
                        _age = tick - int(_discovered)
                    except (TypeError, ValueError):
                        _age = 0
                    if (lid not in _stale_emitted
                            and _cert_str in ("VAGUE", "EXHAUSTED")
                            and _age > _BELIEF_STALE_TICKS):
                        _stale_emitted.add(lid)
                        events.append(SimulationEvent(
                            event_type="belief_stale", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"lead_id": lid, "certainty": _cert_str},
                        ))

                # decision_diverged_by_belief: entity pursuing non-information project while
                # holding VAGUE/EXHAUSTED leads — indicates stale belief driving sub-optimal choice
                _curr_proj_id = entity.strategic.current_project_id
                _has_vague_lead = any(
                    getattr(l.certainty, "value", str(l.certainty)) in ("VAGUE", "EXHAUSTED")
                    for l in curr_leads.values()
                )
                if _curr_proj_id and _has_vague_lead:
                    _curr_proj = entity.strategic.projects.get(_curr_proj_id)
                    _proj_kind = getattr(getattr(_curr_proj, "kind", None), "value",
                                         str(getattr(_curr_proj, "kind", ""))) if _curr_proj else ""
                    if _proj_kind and _proj_kind not in ("information", "information_seeking"):
                        events.append(SimulationEvent(
                            event_type="decision_diverged_by_belief", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"project_kind": _proj_kind},
                        ))

                # decision_divergence_detected (COGNITION): active project kind inconsistent with
                # top-urgency concern — e.g., harvesting while DANGER concern is critical
                _concerns = getattr(entity.strategic, "concerns", None) or {}
                if _curr_proj_id and _concerns:
                    _top_concern = max(_concerns.values(), key=lambda c: getattr(c, "urgency", 0.0), default=None)
                    _top_urgency = getattr(_top_concern, "urgency", 0.0)
                    _top_kind = getattr(getattr(_top_concern, "kind", None), "value",
                                        str(getattr(_top_concern, "kind", ""))) if _top_concern else ""
                    if _top_urgency > 0.7 and _top_kind == "danger":
                        _curr_proj2 = entity.strategic.projects.get(_curr_proj_id)
                        _pk2 = getattr(getattr(_curr_proj2, "kind", None), "value",
                                       str(getattr(_curr_proj2, "kind", ""))) if _curr_proj2 else ""
                        if _pk2 in _NON_SURVIVAL_PROJECT_KINDS:
                            events.append(SimulationEvent(
                                event_type="decision_divergence_detected", event_category="strategy",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"project_kind": _pk2, "concern_kind": _top_kind,
                                         "concern_urgency": round(_top_urgency, 4)},
                            ))

            # Social: group_joined / group_expelled (PP-34 group membership state diff). Flag-gated
            # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind SocialShaper when
            # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
            curr_group = getattr(entity, "group_id", None)
            prior_group = getattr(prior_ent, "group_id", None)
            if not _push_shapers_phase2_active and curr_group != prior_group:
                if curr_group is not None:
                    events.append(SimulationEvent(
                        event_type="group_joined", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"group_id": str(curr_group)},
                    ))
                else:
                    events.append(SimulationEvent(
                        event_type="group_expelled", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"prior_group_id": str(prior_group)},
                    ))

            # Social: reputation_delta (PP-18, significant public reputation change) +
            # social_memory_created below. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same
            # rollback pattern.
            if not _push_shapers_phase2_active and hasattr(entity, "social") and hasattr(prior_ent, "social"):
                curr_rep = getattr(entity.social, "public_reputation", None)
                prior_rep = getattr(prior_ent.social, "public_reputation", None)
                if isinstance(curr_rep, (int, float)) and isinstance(prior_rep, (int, float)):
                    delta = curr_rep - prior_rep
                else:
                    delta = 0.0
                if isinstance(delta, (int, float)) and abs(delta) > 0.05:
                    events.append(SimulationEvent(
                        event_type="reputation_delta", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"entity_id": eid, "delta": round(delta, 6)},
                    ))

                # Social: social_memory_created — new or significantly shifted trust entry
                curr_trust = getattr(entity.social, "trust_history", None) or {}
                prior_trust = getattr(prior_ent.social, "trust_history", None) or {}
                for other_id, curr_score in curr_trust.items():
                    pair = (eid, other_id)
                    if pair in EventExtractor._emitted_social_memory:
                        continue
                    prior_score = prior_trust.get(other_id)
                    is_new = prior_score is None
                    is_significant = (
                        not is_new
                        and isinstance(curr_score, (int, float))
                        and isinstance(prior_score, (int, float))
                        and abs(curr_score - prior_score) >= EventExtractor._SOCIAL_MEMORY_THRESHOLD
                    )
                    if is_new or is_significant:
                        EventExtractor._emitted_social_memory.add(pair)
                        events.append(SimulationEvent(
                            event_type="social_memory_created", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"other_entity_id": other_id,
                                     "score": round(float(curr_score), 6)},
                        ))

            # Social: contract lifecycle events (PP-35 contracts state diff). Flag-gated
            # (TCK-20260806-PUSH-CUTOVER-PHASE2): the entire block below (through
            # contract_milestone_completed) is migrated to SocialShaper — live when
            # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
            # The Quest progress lifecycle block right after this one is a SEPARATE, unrelated,
            # NOT-migrated block (QuestEvent, out of this epic's scope) — not touched here.
            if not _push_shapers_phase2_active and hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
                curr_contracts = getattr(entity.strategic, "contracts", None) or {}
                prior_contracts = getattr(prior_ent.strategic, "contracts", None) or {}
                for cid, cs in curr_contracts.items():
                    prior_cs = prior_contracts.get(cid)
                    if prior_cs is None:
                        new_status = getattr(getattr(cs, "status", None), "name",
                                             str(getattr(cs, "status", "")))
                        if new_status == "OFFERED":
                            events.append(SimulationEvent(
                                event_type="contract_offer_created", event_category="social",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"contract_id": cid},
                            ))
                        continue
                    curr_status = getattr(getattr(cs, "status", None), "name", str(getattr(cs, "status", "")))
                    prior_status = getattr(getattr(prior_cs, "status", None), "name", str(getattr(prior_cs, "status", "")))
                    if curr_status == prior_status:
                        continue
                    if prior_status == "OFFERED" and curr_status == "ACTIVE":
                        events.append(SimulationEvent(
                            event_type="contract_offer_accepted", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))
                    elif curr_status == "FULFILLED":
                        events.append(SimulationEvent(
                            event_type="contract_completed", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))
                    elif curr_status == "EXPIRED":
                        if prior_status == "ACTIVE":
                            events.append(SimulationEvent(
                                event_type="contract_lapsed", event_category="social",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"contract_id": cid},
                            ))
                        elif prior_status == "OFFERED":
                            events.append(SimulationEvent(
                                event_type="contract_expired_offer", event_category="social",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"contract_id": cid},
                            ))
                # PP-36: contract_expired_offer from reap path (contract removed entirely)
                for cid, prior_cs in prior_contracts.items():
                    if cid in curr_contracts:
                        continue
                    prior_status = getattr(getattr(prior_cs, "status", None), "name",
                                           str(getattr(prior_cs, "status", "")))
                    if prior_status == "OFFERED":
                        events.append(SimulationEvent(
                            event_type="contract_expired_offer", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))

                # Contract milestones: time-gated progress signals for ACTIVE duration
                # contracts. Uses (contract_id, label) gate so each milestone fires
                # exactly once per run regardless of which entity processes the contract.
                for cid, cs in curr_contracts.items():
                    cs_status = getattr(getattr(cs, "status", None), "name",
                                        str(getattr(cs, "status", "")))
                    if cs_status != "ACTIVE":
                        continue
                    expiry = getattr(cs, "expiry_tick", -1)
                    created = getattr(cs, "created_tick", 0)
                    if not isinstance(expiry, int) or not isinstance(created, int):
                        continue
                    if expiry <= 0 or expiry <= created:
                        continue
                    elapsed = tick - created
                    if elapsed <= 0:
                        continue
                    progress = elapsed / (expiry - created)
                    source_id = getattr(cs, "source_id", eid)
                    for threshold, label in EventExtractor._CONTRACT_MILESTONE_THRESHOLDS:
                        gate_key = f"{cid}:{label}"
                        if gate_key in EventExtractor._emitted_contract_milestones:
                            continue
                        if progress >= threshold:
                            EventExtractor._emitted_contract_milestones.add(gate_key)
                            events.append(SimulationEvent(
                                event_type="contract_milestone_completed",
                                event_category="social",
                                tick=tick, entity_id=source_id, severity="INFO",
                                source_system="event_extractor", message="",
                                payload={"contract_id": cid, "milestone": label,
                                         "kind": str(getattr(cs, "kind", ""))},
                            ))

            # Quest progress lifecycle events (TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG: gated to
            # real QuestState instances only — this loop previously iterated ALL strategic
            # projects of any kind, mislabeling unrelated GoalKind-typed AI strategic goals
            # (town_return, combat_engage, harvesting, etc.) as quest_event. commitment_abandoned
            # (below) is deliberately NOT gated the same way — it is a generic project-abandonment
            # classification that applies to any project kind, not quest-specific, and must keep
            # reading the generic ProjectStatus field).
            #
            # QuestEvent construction itself is flag-gated (TCK-20260807-QUEST-EVENT-PUSH-
            # MIGRATION): live behind NarrativeShaper when ENABLE_PUSH_EVENT_SHAPERS_QUEST is "ON"
            # (default); the branch below is the rollback path. commitment_abandoned stays
            # unconditional — not yet migrated (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-
            # GAP).
            prior_projects = prior_ent.strategic.projects
            current_projects = entity.strategic.projects
            for qid, qstate in current_projects.items():
                prior_qstate = prior_projects.get(qid)

                if not _push_shapers_quest_active and isinstance(qstate, QuestState):
                    # quest_status (QuestStatus: ACTIVE/COMPLETED/REWARD_PENDING/REWARDED) is the
                    # field QuestService/QuestResolutionSystem actually mutate — NOT the generic
                    # .status (ProjectStatus) inherited from ProjectState, which quest logic never
                    # touches. .name.lower() (not str(enum)) so the status string matches what
                    # quality_hub.py's _translate_quest_event() checks for ("completed"/"failed").
                    # Explicit payload={"status": ...} — QuestEvent.status is a top-level Pydantic
                    # field, never copied into .payload by ObservabilityEventEnvelope.
                    # from_simulation_event() (which only carries .payload through), so without
                    # this, quality_hub.py's translator is structurally blind to the real status
                    # regardless of which field this branch reads — a second, deeper bug found
                    # alongside the ProjectStatus/QuestStatus field mismatch itself.
                    if prior_qstate is None or not isinstance(prior_qstate, QuestState):
                        events.append(QuestEvent(
                            tick=tick, timestamp=now, entity_id=eid,
                            quest_id=qid, status="started",
                            payload={"status": "started"},
                        ))
                    elif prior_qstate.quest_status != qstate.quest_status:
                        _status_str = qstate.quest_status.name.lower()
                        events.append(QuestEvent(
                            tick=tick, timestamp=now, entity_id=eid,
                            quest_id=qid, status=_status_str,
                            payload={"status": _status_str},
                        ))

                # Agency: commitment_abandoned (behavioral classification, not just status
                # change — coexists with the QuestEvent above which becomes project_abandoned via
                # _TRANSLATE_CONDITIONAL in quality_hub.py) — generic to ANY project kind, keyed
                # on the generic ProjectStatus field, deliberately independent of the
                # QuestState-only gate above. Flag-gated (TCK-20260807-COMMITMENT-ABANDONED-PUSH-
                # MIGRATION-GAP): live behind AgencyShaper when ENABLE_PUSH_EVENT_SHAPERS_AGENCY is
                # "ON" (default); the branch below is the rollback path.
                if not _push_shapers_agency_active and prior_qstate is not None and (
                        getattr(prior_qstate, "status", None) != ProjectStatus.ABANDONED
                        and getattr(qstate, "status", None) == ProjectStatus.ABANDONED):
                    _hp = getattr(getattr(entity, "combat", None), "hp", 100)
                    _max_hp = getattr(getattr(entity, "combat", None), "max_hp", 100)
                    _classification = AbandonmentEvaluator.evaluate_abandonment(
                        _hp, _max_hp,
                        is_party_in_combat=False,   # Q1: default; see plan decisions
                        is_greed_driven=False,       # Q1: default; see plan decisions
                    )
                    if _classification.category != AbandonmentCategory.SURVIVAL:
                        events.append(SimulationEvent(
                            event_type="commitment_abandoned", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={
                                "entity_id": eid,
                                "project_id": qid,
                                "category": _classification.category.value,
                                "penalty": _classification.penalty,
                                "tick": tick,
                            },
                        ))

            # Progression: skill_unlocked, trait_expressed, pillar_trait_unlocked,
            # progression_conversion_applied, progression_plateau_detected. Flag-gated
            # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind ProgressionShaper when
            # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
            if not _push_shapers_phase2_active and hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
                _curr_id = entity.identity
                _prior_id = prior_ent.identity
                _curr_skills = getattr(_curr_id, "learned_skills", None) or frozenset()
                _prior_skills = getattr(_prior_id, "learned_skills", None) or frozenset()
                for _sk in (set(_curr_skills) - set(_prior_skills)):
                    events.append(SimulationEvent(
                        event_type="skill_unlocked", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"skill_id": _sk, "tick": tick},
                    ))

                _curr_traits = getattr(_curr_id, "traits", None) or frozenset()
                _prior_traits = getattr(_prior_id, "traits", None) or frozenset()
                for _tr in (set(_curr_traits) - set(_prior_traits)):
                    events.append(SimulationEvent(
                        event_type="trait_expressed", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"trait_id": _tr, "tick": tick},
                    ))

                _curr_breaks = getattr(_curr_id, "active_breakthroughs", None) or frozenset()
                _prior_breaks = getattr(_prior_id, "active_breakthroughs", None) or frozenset()
                for _bt in (set(_curr_breaks) - set(_prior_breaks)):
                    events.append(SimulationEvent(
                        event_type="pillar_trait_unlocked", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"trait_id": _bt, "tick": tick},
                    ))

                # progression_conversion_applied: unspent_ap decreased = AP converted to permanent stat
                _curr_ap = getattr(_curr_id, "unspent_ap", 0)
                _prior_ap = getattr(_prior_id, "unspent_ap", 0)
                if isinstance(_curr_ap, int) and isinstance(_prior_ap, int) and _curr_ap < _prior_ap:
                    events.append(SimulationEvent(
                        event_type="progression_conversion_applied", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"ap_spent": _prior_ap - _curr_ap, "tick": tick},
                    ))

                # progression_plateau_detected: XP rate dropped to zero or skill silence
                _curr_xp = getattr(_curr_id, "evolution_points", 0)
                _prior_xp = getattr(_prior_id, "evolution_points", 0)
                if _curr_xp != _prior_xp:
                    EventExtractor._last_xp_tick[eid] = tick
                elif eid not in EventExtractor._emitted_plateau:
                    _since = tick - EventExtractor._last_xp_tick.get(eid, 0)
                    if _since > _XP_PLATEAU_TICKS:
                        EventExtractor._emitted_plateau.add(eid)
                        events.append(SimulationEvent(
                            event_type="progression_plateau_detected", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"type": "xp_rate_zero", "ticks_since_xp": _since},
                        ))
                    elif (getattr(_curr_id, "evolution_level", 1) >= 5
                            and not set(_curr_skills)):
                        EventExtractor._emitted_plateau.add(eid)
                        events.append(SimulationEvent(
                            event_type="progression_plateau_detected", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"type": "skill_silence",
                                     "level": getattr(_curr_id, "evolution_level", 1)},
                        ))

            # Capability trend / life-arc coherence (TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-
            # LIFECYCLE). NEW signal, not a Phase 1/2 migration — no ProgressionShaper equivalent
            # exists, so there is no double-fire risk and this block is deliberately NOT gated
            # behind _push_shapers_phase2_active; it always runs regardless of that flag's value
            # (see staging_artifacts/TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE/
            # investigation.md's architecture-decision section for the full reasoning).
            if (hasattr(entity, "identity") and hasattr(prior_ent, "identity")
                    and hasattr(entity, "lifecycle") and hasattr(entity, "equipment")
                    and hasattr(entity, "inventory")):
                _cap_curr_id = entity.identity
                _cap_curr_level = getattr(_cap_curr_id, "evolution_level", 1)
                _cap_prior_level = getattr(prior_ent.identity, "evolution_level", 1)
                _cap_curr_skills = getattr(_cap_curr_id, "learned_skills", None) or frozenset()
                _cap_prior_skills = getattr(prior_ent.identity, "learned_skills", None) or frozenset()
                _cap_curr_gold = getattr(entity.inventory, "gold", 0)
                _cap_prior_gold = getattr(prior_ent.inventory, "gold", 0)
                _cap_curr_slots = getattr(entity.equipment, "slots", None)
                _cap_prior_slots = getattr(prior_ent.equipment, "slots", None)
                _cap_curr_gear = (sum(1 for v in _cap_curr_slots.values() if v)
                                  if isinstance(_cap_curr_slots, dict) else 0)
                _cap_prior_gear = (sum(1 for v in _cap_prior_slots.values() if v)
                                   if isinstance(_cap_prior_slots, dict) else 0)
                _cap_levels_numeric = isinstance(_cap_curr_level, (int, float)) and isinstance(_cap_prior_level, (int, float))
                _cap_gold_numeric = isinstance(_cap_curr_gold, (int, float)) and isinstance(_cap_prior_gold, (int, float))

                _cap_grew = (
                    (_cap_levels_numeric and _cap_curr_level > _cap_prior_level)
                    or len(_cap_curr_skills) > len(_cap_prior_skills)
                    or _cap_curr_gear > _cap_prior_gear
                    or (_cap_gold_numeric and _cap_curr_gold > _cap_prior_gold)
                )
                if eid not in EventExtractor._last_capability_growth_tick:
                    EventExtractor._last_capability_growth_tick[eid] = tick
                if _cap_grew:
                    EventExtractor._last_capability_growth_tick[eid] = tick
                elif eid not in EventExtractor._emitted_capability_stalled:
                    _since_growth = tick - EventExtractor._last_capability_growth_tick[eid]
                    if _since_growth > _CAPABILITY_STALL_TICKS:
                        EventExtractor._emitted_capability_stalled.add(eid)
                        events.append(SimulationEvent(
                            event_type="capability_growth_stalled", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"ticks_since_growth": _since_growth, "level": _cap_curr_level},
                        ))

                _cap_generation = getattr(entity.lifecycle, "generation", 1)
                if (
                    eid not in EventExtractor._emitted_life_arc_incoherent
                    and isinstance(_cap_generation, int)
                    and _cap_generation >= _LATE_GENERATION_THRESHOLD
                    and _cap_levels_numeric and _cap_curr_level <= 1
                    and not set(_cap_curr_skills)
                ):
                    EventExtractor._emitted_life_arc_incoherent.add(eid)
                    events.append(SimulationEvent(
                        event_type="life_arc_incoherent", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"generation": _cap_generation, "level": _cap_curr_level},
                    ))

        # Agency: rejection_cascade_tick — post-entity-loop population aggregate. Flag-gated
        # (TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP): live behind AgencyShaper when
        # ENABLE_PUSH_EVENT_SHAPERS_AGENCY is "ON" (default); the block below is the rollback path.
        if not _push_shapers_agency_active:
            _total_rejections = 0
            _reason_counts: dict[str, int] = {}
            _all_upd = getattr(update, "entity_updates", {}) or {}
            for _e_upd in _all_upd.values():
                for _ir in (getattr(_e_upd, "intent_results", None) or []):
                    if not getattr(_ir, "accepted", True):
                        _total_rejections += 1
                        _r = getattr(_ir, "reason", None) or "unknown"
                        _reason_counts[_r] = _reason_counts.get(_r, 0) + 1
            if _total_rejections >= _MAX_CONSECUTIVE_REJECTIONS:
                _dominant = max(_reason_counts, key=_reason_counts.__getitem__) if _reason_counts else "unknown"
                events.append(SimulationEvent(
                    event_type="rejection_cascade_tick", event_category="strategy",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={
                        "count": _total_rejections,
                        "tick": tick,
                        "dominant_failure_reason": _dominant,
                    },
                ))

        # Resource node depletion and regeneration. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2):
        # live behind DeferredInstrumentationShaper when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON"
        # (default); this block is the rollback path.
        if not _push_shapers_phase2_active and hasattr(current_state, "resource_nodes") and hasattr(prior_state, "resource_nodes"):
            for node_id, node in current_state.resource_nodes.items():
                prior_node = prior_state.resource_nodes.get(node_id)
                if prior_node is None:
                    continue
                if prior_node.remaining_charges > 0 and node.remaining_charges == 0:
                    events.append(SimulationEvent(
                        event_type="resource_node_depleted", event_category="resource",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"node_id": node_id, "charges": 0, "max_charges": node.max_charges},
                    ))
                elif prior_node.remaining_charges == 0 and node.remaining_charges > 0:
                    events.append(SimulationEvent(
                        event_type="resource_node_regenerated", event_category="resource",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"node_id": node_id, "charges": node.remaining_charges, "max_charges": node.max_charges},
                    ))
                    # World: node_recharged — distinct from resource_node_regenerated (scored by WorldDynamicsScorer)
                    # Only on 0→>0 transition (node_recharged is the scored event; resource_node_regenerated is unscored_intentional)
                    events.append(SimulationEvent(
                        event_type="node_recharged", event_category="resource",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"node_id": node_id, "charges": node.remaining_charges},
                    ))

        # World: ecology_cycle_completed — fires once per region per ecology interval (every 200 ticks)
        # ResourceEcologyService.ECOLOGY_INTERVAL == 200. Flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind WorldDynamicsShaper when
        # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this block is the rollback path.
        if not _push_shapers_phase2_active and tick % 200 == 0 and hasattr(current_state, "regions"):
            for _r_id, _region in (current_state.regions or {}).items():
                events.append(SimulationEvent(
                    event_type="ecology_cycle_completed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": _r_id,
                             "cycle_type": getattr(_region, "kind", "unknown"),
                             "net_pressure_delta": 0.0},
                ))

        # World: spawn_cadence_fired — detects spawn batch committed on cadence tick. Flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
        if not _push_shapers_phase2_active and tick % _SPAWN_INTERVAL == 0:
            _spawned_monsters = [
                e for e in (getattr(update, "entities_add", None) or [])
                if getattr(e, "kind", None) not in (None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")
            ]
            if _spawned_monsters:
                events.append(SimulationEvent(
                    event_type="spawn_cadence_fired", event_category="lifecycle",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"spawned_count": len(_spawned_monsters), "tick": tick},
                ))

        # Economy: conservation_law_verified — throttled (1 per 50 ticks) to avoid noise
        # Fires when economy transactions occurred this tick, implying the conservation law was
        # checked. Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind
        # run_shadow_shapers()'s own cross-shaper aggregation when ENABLE_PUSH_EVENT_SHAPERS_PHASE2
        # is "ON" (default); this block is the rollback path.
        if not _push_shapers_phase2_active and tick % 50 == 0:
            _has_economy_tx = any(
                e.event_type in ("resource_harvested", "item_crafted", "shop_transaction",
                                 "paid_information_transaction", "gold_sink_fired")
                for e in events
            )
            if _has_economy_tx:
                events.append(SimulationEvent(
                    event_type="conservation_law_verified", event_category="economy",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"tick": tick},
                ))

        # World dynamics events — from StateUpdate world_updates and entities_add. Flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2): region_trauma_delta through region_transformed are
        # migrated to WorldDynamicsShaper — live when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON"
        # (default); this loop is the rollback path. building_sabotaged below is a SEPARATE loop,
        # guarded independently.
        for rid, w_upd in ([] if _push_shapers_phase2_active else (getattr(update, "world_updates", None) or {}).items()):
            if getattr(w_upd, "trauma_delta", 0.0) != 0.0:
                events.append(SimulationEvent(
                    event_type="region_trauma_delta", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "delta": w_upd.trauma_delta},
                ))
            # World: threat_evolved — trauma crossing major thresholds (25, 50, 75, 100) signals tier shift
            _prior_region = getattr(prior_state, "regions", {}).get(rid) if prior_state else None
            if _prior_region is not None:
                try:
                    _prior_trauma = float(getattr(_prior_region, "trauma_score", 0.0))
                    _trauma_delta = float(getattr(w_upd, "trauma_delta", 0.0))
                    _new_trauma = _prior_trauma + _trauma_delta
                    for _threshold in (25.0, 50.0, 75.0, 100.0):
                        if _prior_trauma < _threshold <= _new_trauma:
                            events.append(SimulationEvent(
                                event_type="threat_evolved", event_category="region",
                                tick=tick, entity_id=None, severity="WARNING",
                                source_system="event_extractor", message="",
                                payload={"region_id": rid, "threshold": _threshold,
                                         "prior_trauma": round(_prior_trauma, 2),
                                         "new_trauma": round(_new_trauma, 2)},
                            ))
                            break
                except (TypeError, ValueError):
                    pass
            if getattr(w_upd, "owner_faction_id_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_ownership_changed", event_category="region",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "new_owner": str(w_upd.owner_faction_id_set)},
                ))
            if getattr(w_upd, "kind_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_transformed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "new_kind": w_upd.kind_set},
                ))

        # World: building_sabotaged — building took sabotage damage (hp_delta < 0 discriminates
        # BuildingSabotageSystem.resolve() from town_resolution.py's insolvency writes, which only
        # ever set functional_set=False with no hp_delta). Flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
        for b_id, b_upd in ([] if _push_shapers_phase2_active else (getattr(update, "building_updates", None) or {}).items()):
            if getattr(b_upd, "hp_delta", 0.0) is not None and getattr(b_upd, "hp_delta", 0.0) < 0:
                from src.engine.kernel import Kernel
                _region = Kernel.get_building_region(current_state, b_id) if current_state else None
                events.append(SimulationEvent(
                    event_type="building_sabotaged", event_category="region",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"building_id": b_id, "hp_delta": b_upd.hp_delta,
                             "region_id": _region.id if _region else None},
                ))

        # calamity_spawned: flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
        if not _push_shapers_phase2_active and getattr(update, "last_calamity_tick_set", None) == prior_state.tick:
            events.append(SimulationEvent(
                event_type="calamity_spawned", event_category="lifecycle",
                tick=tick, entity_id=None, severity="CRITICAL",
                source_system="event_extractor", message="",
                payload={"tick": tick},
            ))

        # boss_spawned / narrative_milestone (boss variant) / raid_party_spawned: flag-gated
        # (TCK-20260806-PUSH-CUTOVER-PHASE2), same rollback pattern.
        _BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel", "dragonkin"))
        for new_ent in ([] if _push_shapers_phase2_active else (getattr(update, "entities_add", None) or [])):
            kind = getattr(new_ent, "kind", None)
            if kind in _BOSS_KINDS:
                events.append(SimulationEvent(
                    event_type="boss_spawned", event_category="lifecycle",
                    tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"kind": kind},
                ))
                # NARRATIVE: narrative_milestone — boss spawn (D2, D5 from plan/UQ-1)
                events.append(SimulationEvent(
                    event_type="narrative_milestone",
                    event_category="lifecycle",
                    tick=tick,
                    entity_id=getattr(new_ent, "id", None),
                    severity="WARNING",
                    source_system="event_extractor",
                    message="",
                    payload={"milestone": "first_boss_spawned", "kind": kind},
                ))
            elif kind == "goblin_raider":
                events.append(SimulationEvent(
                    event_type="raid_party_spawned", event_category="lifecycle",
                    tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"kind": kind},
                ))

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

            # FACTION: faction_tension_delta (PP-09) — any non-zero delta
            if getattr(upd, "tension_delta", 0.0) != 0.0:
                events.append(SimulationEvent(
                    event_type="faction_tension_delta", event_category="faction",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"faction_id": fid, "delta": upd.tension_delta},
                ))

        # Faction events from WorldEvent domain objects (PP-10/11)
        _MILITARY_RESOLVED = frozenset({
            WorldEventCategory.TERRITORY_TRANSFERRED,
            WorldEventCategory.WAR_ENDED_EXHAUSTION,
        })
        _world_evts = getattr(update, "world_events_add", None)
        if not isinstance(_world_evts, (list, tuple)):
            _world_evts = ()
        for we in _world_evts:
            cat = getattr(we, "category", None)
            # war_declared/military_conflict_resolved specifically are migrated (FACTION), flag-
            # gated (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION) — but this loop ALSO
            # produces world_emergence_event/narrative_milestone (NARRATIVE, out of migration
            # scope) below, which must stay fully unconditional. Only this if/elif is guarded, not
            # the whole loop.
            if _push_shapers_active:
                pass
            elif cat == WorldEventCategory.FACTION_WAR_DECLARED:
                events.append(SimulationEvent(
                    event_type="war_declared", event_category="faction",
                    tick=tick, entity_id=None, severity="CRITICAL",
                    source_system="event_extractor", message="",
                    payload={"faction_pair": str(getattr(we, "subject", ""))},
                ))
            elif cat in _MILITARY_RESOLVED:
                events.append(SimulationEvent(
                    event_type="military_conflict_resolved", event_category="faction",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={
                        "subject": str(getattr(we, "subject", "")),
                        "category": str(cat),
                    },
                ))

            # NARRATIVE: world_emergence_event — one per WorldEvent in world_events_add (D1).
            # narrative_milestone (war/sovereignty variant) below too. Both migrated to
            # WorldDynamicsShaper — flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2), live when
            # ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default); this pair is the rollback path.
            # Only these two constructs are guarded, not the whole loop — the war_declared/
            # military_conflict_resolved if/elif above (Phase 1, ENABLE_PUSH_EVENT_SHAPERS) stays
            # independently gated by its own, separate flag, untouched here.
            if not _push_shapers_phase2_active:
                events.append(SimulationEvent(
                    event_type="world_emergence_event",
                    event_category="lifecycle",
                    tick=tick,
                    entity_id=None,
                    severity="INFO",
                    source_system="event_extractor",
                    message="",
                    payload={
                        "category": str(cat) if cat else "",
                        "region_id": str(getattr(we, "region_id", "") or ""),
                        "subject": str(getattr(we, "subject", "") or ""),
                    },
                ))

                # NARRATIVE: narrative_milestone — war and sovereignty (D2)
                if cat == WorldEventCategory.FACTION_WAR_DECLARED:
                    events.append(SimulationEvent(
                        event_type="narrative_milestone",
                        event_category="lifecycle",
                        tick=tick,
                        entity_id=None,
                        severity="WARNING",
                        source_system="event_extractor",
                        message="",
                        payload={
                            "milestone": "first_war",
                            "subject": str(getattr(we, "subject", "") or ""),
                        },
                    ))
                elif cat == WorldEventCategory.SOVEREIGNTY_SHIFT:
                    events.append(SimulationEvent(
                        event_type="narrative_milestone",
                        event_category="lifecycle",
                        tick=tick,
                        entity_id=None,
                        severity="WARNING",
                        source_system="event_extractor",
                        message="",
                        payload={
                            "milestone": "first_sovereignty_transfer",
                            "region_id": str(getattr(we, "region_id", "") or ""),
                        },
                    ))

        # FACTION: faction_extinct (PP-08/PP-33) — only when faction state changed this tick.
        # Flag-gated (TCK-20260806-PUSH-CUTOVER-PHASE2): live behind
        # DeferredInstrumentationShaper when ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is "ON" (default);
        # this block is the rollback path.
        _faction_upd_list = getattr(update, "faction_updates", None)
        if not _push_shapers_phase2_active and isinstance(_faction_upd_list, list) and _faction_upd_list:
            _living_faction_ids: set = set()
            for _ent in (getattr(current_state, "entities", {}) or {}).values():
                _hp = getattr(_ent, "hp", None)
                _fac = getattr(getattr(_ent, "identity", None), "faction", None)
                _hp_alive = _hp is None or (isinstance(_hp, (int, float)) and _hp > 0)
                if _fac is not None and _hp_alive:
                    _living_faction_ids.add(str(_fac))

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

    @staticmethod
    def detect_grief_triggers(
        prior_state: AuthoritativeState,
        current_state: AuthoritativeState,
    ) -> List[Any]:
        """Detect mid-tick grief-urgency triggers from a live ally's death.

        Re-walks the same lifecycle.active True→False transition condition used above
        (line ~483's death-detection block) independently, as a second bounded pass over
        current_state.entities — EventExtractor.extract()'s own List[SimulationEvent]
        return type must not change (regression risk to its many callers/tests), so this
        lives as a sibling method rather than folded into extract() itself.

        Returns (griever_id, dead_ally_id, urgency) triples for every currently-alive
        entity whose entity.social.trust_history toward the newly-dead entity meets
        ALLY_TRUST_THRESHOLD. Urgency uses the exact same formula as
        CampaignOrchestrator._advance_grief_urgencies() (min(1.0, trust * 0.8)) so the
        mid-episode and episode-boundary trigger paths cannot drift apart.

        Called from Kernel._phase_observability, immediately after this class's own
        extract() call (TCK-20260824-GRIEF-NEMESIS-REACHABILITY) — the caller builds
        GriefUrgencyTriggeredEvent from each triple and queues the triple onto
        Kernel._pending_grief_triggers for a later tick's _phase_resolution to drain
        through StrategicPatch/ApplyPath.
        """
        from src.core.social_constants import ALLY_TRUST_THRESHOLD

        triggers: List[Any] = []
        for eid, entity in current_state.entities.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue
            if not (prior_ent.lifecycle.active and not entity.lifecycle.active):
                continue
            for other_id, other in current_state.entities.items():
                if other_id == eid or not other.lifecycle.active:
                    continue
                trust = getattr(other.social, "trust_history", {}).get(eid, 0.0)
                if trust >= ALLY_TRUST_THRESHOLD:
                    urgency = round(min(1.0, trust * 0.8), 6)
                    triggers.append((other_id, eid, urgency))
        return triggers
