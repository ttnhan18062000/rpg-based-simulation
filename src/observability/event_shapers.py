"""Apply-layer (push-based) event shapers — TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT,
TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION.

Alternative to EventExtractor's post-tick snapshot-diff model: shapers here derive events
directly from `prior_state` + `update` (the typed, already-causally-tagged records domain systems
produce), the same two objects already available before ApplyPath.apply_generation() ever runs.
No post-mutation `current_state` is read. See
stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md's "Design
refinement" section for the full reasoning.

SHADOW mode only in this ticket: shapers construct events, but nothing here delivers them to the
live BoundedObservabilityQueue. That is TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION's job,
gated on TCK-20260806-PUSH-SHADOW-VALIDATION-PERF's go verdict.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Protocol

from src.core.enums import EntityRole
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.observability.config import ObservabilityMode
from src.domains.world_emergence.schema import WorldEventCategory
from src.observability.event_extractor import (
    _real_combat_update, _NEAR_DEATH_THRESHOLD,
    _CERTAINTY_FLOAT, _BELIEF_STALE_TICKS, _NON_SURVIVAL_PROJECT_KINDS,
    _XP_PLATEAU_TICKS,
)
from src.observability.events import SimulationEvent, QuestEvent
from src.core.quests import QuestState
from src.core.strategic import ProjectStatus
from src.domains.commitment.abandonment import AbandonmentEvaluator, AbandonmentCategory
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS

logger = logging.getLogger(__name__)


class EventShaper(Protocol):
    """A shaper derives events for one domain from prior_state + update alone."""

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]: ...


# Real mechanics-bible modifier order (docs/mechanics/02_combat_laws.md §2), used as the
# deterministic tie-break when multiple tactical modifiers are simultaneously active on the
# same attack -- TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX. Deliberately excludes
# FINAL_ATK_MULT/FINAL_DEF_MULT (aggregate multipliers, not a discrete condition),
# REWARD_SOURCE/REWARD_CATEGORY (reward classification), and WOUND_INFLICTED (wound tracking) --
# all real CombatUpdate.trace keys, none a "tactical modifier" in the mechanics-bible sense.
_TACTICAL_MODIFIER_ORDER = (
    "HIGH_GROUND", "FLANKING", "SURROUNDED", "COVER_REDUCTION",
    "SHATTER", "EXHAUSTION", "STAMINA_EXHAUSTION", "BOND_SYNERGY",
)


def _select_tactical_modifier(trace: Optional[Dict[str, Any]]) -> Optional[str]:
    """First real tactical-modifier key present in a real CombatUpdate.trace, checked in
    mechanics-bible table order -- CombatScorer's own tactical_variety signal (+1 per unique
    modifier ever seen) expects a single string per combat_damage event, not the full trace."""
    if not trace:
        return None
    for key in _TACTICAL_MODIFIER_ORDER:
        if key in trace:
            return key
    return None


def _combat_entity_snapshot(ent: Optional[Any]) -> Optional[Dict[str, Any]]:
    """Real, honest snapshot of one combat participant's own state at the moment of a
    combat_engagement_started/ended event -- level, hp/max_hp, atk/def, role/faction/species,
    bravery, action_style -- sufficient to later judge whether a given combat scenario was
    reasonable (TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY). Reads prior_state only, matching
    this shaper's own prior_state+update-only design. Returns None if ent is None (e.g. an
    attacker_id that no longer resolves in prior_state)."""
    if ent is None:
        return None
    identity = getattr(ent, "identity", None)
    combat = getattr(ent, "combat", None)
    role_val = getattr(identity, "role", None)
    try:
        role_name = EntityRole(role_val).name
    except Exception:
        role_name = str(role_val) if role_val is not None else None
    properties = getattr(identity, "properties", None) or {}
    personality = getattr(identity, "personality", None)
    return {
        "level": getattr(identity, "evolution_level", None),
        "hp": getattr(combat, "hp", None),
        "max_hp": getattr(combat, "max_hp", None),
        "atk": getattr(combat, "atk", None),
        "def_stat": getattr(combat, "def_stat", None),
        "role": role_name,
        "faction_id": properties.get("faction_id"),
        "species_id": properties.get("species_id"),
        "bravery": getattr(personality, "bravery", None),
        "action_style": getattr(combat, "action_style", None),
    }


class CombatShaper:
    """COMBAT domain shaper — combat_initiated, combat_damage, near_death_survival,
    entity_killed, plus the colocated hazard_drain_applied/hero_death_unrecorded (see
    investigation.md Decision 1 for why these two ride along).

    Reuses event_extractor._real_combat_update() as the single source of truth for the
    attacker_id-primary / outcome_kind-defense-in-depth combat-classification discriminant —
    see TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX (INFRA-323) for why a
    plain outcome_kind allow-list is unsafe (collides with biological.py's SURVIVE default).

    Deliberately excluded (see investigation.md Decisions 2-3, not silently dropped):
    - demographic_mortality (despawn branch) — broader than combat, deferred to a later phase.
    - combat_resolved / attrition_threshold_crossed — dead code, never emitted by any path in
      this repo; nothing exists to migrate.
    """

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        events: List[SimulationEvent] = []
        now = time.time()
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue

            combat_upd = getattr(e_upd, "combat", None)

            # combat_engagement_ended(PURSUIT_ABANDONED) / (ESCAPED) -- real, but neither one
            # sets e_upd.combat (giving up a chase and a clean disengagement both involve no
            # CombatUpdate at all), so both must be checked BEFORE the combat_upd-is-None guard
            # below -- otherwise they would be silently skipped, exactly the kind of gap this
            # ticket exists to close (TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY).
            task_upd = getattr(e_upd, "task", None)
            task_reason = None
            if task_upd is not None:
                payload_set = getattr(task_upd, "payload_set", None) or {}
                task_reason = payload_set.get("reason")
            if task_reason in ("LEASH_RETURN", "STALEMATE_BREAK"):
                prior_task = getattr(prior_ent, "task", None)
                prior_target_id = None
                if prior_task is not None:
                    prior_target_id = getattr(prior_task, "payload", None) or {}
                    prior_target_id = prior_target_id.get("target_id")
                events.append(SimulationEvent(
                    event_type="combat_engagement_ended", event_category="combat",
                    tick=tick, entity_id=eid, target_id=prior_target_id, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={
                        "outcome": "PURSUIT_ABANDONED",
                        "reason": task_reason,
                        "actor_snapshot": _combat_entity_snapshot(prior_ent),
                    },
                ))

            property_updates = getattr(e_upd, "property_updates", None) or {}
            if property_updates.get("combat_escape") == "EVASIVE_SUCCESS":
                evaded_ids = list(property_updates.get("combat_escape_evaded_ids") or [])
                events.append(SimulationEvent(
                    event_type="combat_engagement_ended", event_category="combat",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={
                        "outcome": "ESCAPED",
                        "evaded_ids": evaded_ids,
                        "actor_snapshot": _combat_entity_snapshot(prior_ent),
                    },
                ))
                # combat_resolved -- real, ready COMBAT-pillar scorer signal (+3, the largest
                # positive weight in the pillar) that has never had a real producer anywhere in
                # this repo (TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX). ESCAPED is a literal
                # match for the pillar contract's own wording ("clear winner, loser retreats or
                # dies") -- the loser cleanly disengaged. CombatScorer requires no specific
                # payload fields, only a matching event_type.
                events.append(SimulationEvent(
                    event_type="combat_resolved", event_category="combat",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"outcome": "ESCAPED"},
                ))

            if combat_upd is None:
                continue

            hp_delta = getattr(combat_upd, "hp_delta", 0)
            prior_hp = prior_ent.combat.hp
            prior_max_hp = prior_ent.combat.max_hp
            new_hp = prior_hp + hp_delta

            # is_lethal / near_death survival must track CombatComponent.alive (what alive_set
            # actually sets — src/engine/patches.py:301), NOT LifecycleComponent.active. The two
            # are governed by different rules: LifecycleSystem.resolve_lifecycle() only flips
            # lifecycle.active on outcome_kind=="KILL" or old-age, never on alive_set alone — a
            # hazard hit (outcome_kind="HAZARD") can set alive_set=False (combat.alive=False)
            # while lifecycle.active stays True. Found by TCK-20260806-PUSH-SHADOW-VALIDATION-PERF's
            # shadow comparison (a real divergence against the old extractor), fixed here rather
            # than patched around downstream.
            alive_set = getattr(combat_upd, "alive_set", None)
            new_combat_alive = alive_set if alive_set is not None else prior_ent.combat.alive

            real_combat = _real_combat_update(e_upd)

            # combat_damage / combat_initiated — genuine combat resolution only
            if hp_delta < 0 and real_combat is not None:
                is_lethal = bool(new_hp <= 0 or not new_combat_alive)
                # Volumization rule (matches event_extractor.py exactly): skip routine,
                # non-lethal damage in LIGHT/LONG_RUN mode. Missing this in the initial
                # implementation caused a real, frequent divergence found by this ticket's own
                # shadow comparison (urban_political/crowded_frontier showed combat_damage firing
                # far more often than the old extractor during sustained combat sequences).
                if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    dmg_payload = {"attacker_id": real_combat.attacker_id, "damage": int(-hp_delta),
                                    "is_lethal": is_lethal}
                    tactical_modifier = _select_tactical_modifier(getattr(real_combat, "trace", None))
                    if tactical_modifier is not None:
                        dmg_payload["tactical_modifier"] = tactical_modifier
                    events.append(SimulationEvent(
                        event_type="combat_damage", event_category="combat",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload=dmg_payload,
                    ))
                if prior_hp == prior_max_hp and new_hp < prior_max_hp:
                    events.append(SimulationEvent(
                        event_type="combat_initiated", event_category="combat",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"attacker_id": real_combat.attacker_id},
                    ))
                    # combat_engagement_started -- fires alongside the gate above, same tick,
                    # same entity pair. trigger_reason is directly derivable from
                    # CombatUpdate.is_opportunity_attack: a legal attack that isn't an OA can
                    # only originate from tactical.py's own deliberate ATTACK/SKILL emission
                    # branch (structurally distinct from every retreat/reposition/hold branch).
                    attacker_ent = prior_state.entities.get(real_combat.attacker_id)
                    events.append(SimulationEvent(
                        event_type="combat_engagement_started", event_category="combat",
                        tick=tick, entity_id=eid, target_id=real_combat.attacker_id,
                        severity="INFO", source_system="event_shapers", message="",
                        payload={
                            "trigger_reason": "OPPORTUNITY_ATTACK" if real_combat.is_opportunity_attack else "GOAL_ENGAGE",
                            "defender_snapshot": _combat_entity_snapshot(prior_ent),
                            "attacker_snapshot": _combat_entity_snapshot(attacker_ent),
                        },
                    ))
                # combat_engagement_ended(CAUGHT_FLEEING) -- a real opportunity attack, by
                # construction, only ever fires on a hostile's own disengagement movement
                # (movement.py's engaged_hostiles-and-not-skip_oa gate) -- this IS "caught
                # while fleeing". Excludes a kill this tick (KILL fires its own outcome below).
                if real_combat.is_opportunity_attack and getattr(combat_upd, "outcome_kind", None) != "KILL":
                    attacker_ent = prior_state.entities.get(real_combat.attacker_id)
                    events.append(SimulationEvent(
                        event_type="combat_engagement_ended", event_category="combat",
                        tick=tick, entity_id=eid, target_id=real_combat.attacker_id,
                        severity="INFO", source_system="event_shapers", message="",
                        payload={
                            "outcome": "CAUGHT_FLEEING",
                            "defender_snapshot": _combat_entity_snapshot(prior_ent),
                            "attacker_snapshot": _combat_entity_snapshot(attacker_ent),
                        },
                    ))
                near_death_hp = prior_max_hp * _NEAR_DEATH_THRESHOLD
                if new_hp < near_death_hp <= prior_hp and new_combat_alive:
                    events.append(SimulationEvent(
                        event_type="near_death_survival", event_category="combat",
                        tick=tick, entity_id=eid, severity="WARNING",
                        source_system="event_shapers", message="",
                        payload={"hp": new_hp, "max_hp": prior_max_hp},
                    ))

            # entity_killed — gated on outcome_kind=="KILL" specifically (matches
            # LifecycleSystem.resolve_lifecycle()'s own real trigger for lifecycle.active's
            # combat-caused transition), NOT alive_set/HP arithmetic. Two disclosed, narrower-than-
            # old-extractor gaps, both confirmed by direct pipeline tracing during this ticket's
            # shadow-comparison investigation (see investigation.md's Reopen Notes):
            # (1) old-age deaths (LifecycleSystem's other trigger) never carry a combat_upd at all
            #     — genuinely outside this shaper's scope (COMBAT domain, not lifecycle/aging).
            # (2) hazard-caused "death" (combat.alive=False via alive_set) can transition
            #     lifecycle.active on a LATER tick than the causing CombatUpdate, with no
            #     combat_upd present at the tick the transition itself becomes visible — confirmed
            #     empirically (hero_guild_routing_seed42: combat.alive flips at tick 4, lifecycle
            #     .active flips at tick 5, zero entity_updates present at tick 5). The
            #     "prior_state+update alone" design cannot see a transition with no update record
            #     to read. Both gaps are the SAME underlying limitation — no update-record signal
            #     exists at the tick a non-KILL-tagged lifecycle transition becomes visible — not
            #     two separate bugs. The old extractor's kill-events branch fires on ANY
            #     lifecycle.active transition regardless of cause or timing; this shaper covers
            #     only same-tick, outcome_kind=="KILL" combat deaths. Real-corpus frequency of gap
            #     (2) specifically must be quantified by this ticket before cutover — see
            #     Recommendation.
            if getattr(combat_upd, "outcome_kind", None) == "KILL":
                killer_id = real_combat.attacker_id if real_combat is not None else None
                events.append(SimulationEvent(
                    event_type="entity_killed", event_category="combat",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"killer_id": killer_id},
                ))
                killer_ent = prior_state.entities.get(killer_id) if killer_id is not None else None
                events.append(SimulationEvent(
                    event_type="combat_engagement_ended", event_category="combat",
                    tick=tick, entity_id=eid, target_id=killer_id, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={
                        "outcome": "KILL",
                        "defender_snapshot": _combat_entity_snapshot(prior_ent),
                        "attacker_snapshot": _combat_entity_snapshot(killer_ent),
                    },
                ))
                # combat_resolved -- real, ready COMBAT-pillar scorer signal (+3, the largest
                # positive weight in the pillar) that has never had a real producer anywhere in
                # this repo (TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX). KILL is a literal
                # match for the pillar contract's own wording ("clear winner, loser retreats or
                # dies") -- the loser died. CombatScorer requires no specific payload fields,
                # only a matching event_type.
                events.append(SimulationEvent(
                    event_type="combat_resolved", event_category="combat",
                    tick=tick, entity_id=eid, target_id=killer_id, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"outcome": "KILL"},
                ))
                if getattr(prior_ent, "kind", None) == "hero":
                    events.append(SimulationEvent(
                        event_type="hero_death_unrecorded", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="WARNING",
                        source_system="event_shapers", message="",
                        payload={"entity_id": eid},
                    ))

            # hazard_drain_applied — colocated per Decision 1, not COMBAT-scored but same
            # typed-record read as everything above.
            if hp_delta < 0 and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
                events.append(SimulationEvent(
                    event_type="hazard_drain_applied", event_category="combat",
                    tick=tick, entity_id=eid, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"damage": int(-hp_delta)},
                ))

        return events


_GOLD_SINK_KINDS = frozenset(("REPAIR_FEE", "SERVICE_FEE", "TAX"))


class EconomyShaper:
    """ECONOMY domain shaper — resource_harvested, item_crafted, shop_transaction,
    trade_executed, quest_reward_dispensed, gold_sink_fired, paid_information_transaction,
    paid_info_transaction, paid_info_changed_goal.

    All 7 read `entity_updates[eid].intent_results[].source_kind` (typed record) — same mechanism
    `event_extractor.py` already uses, just from `prior_state`+`update` instead of post-hoc.

    Deliberately excluded (see epic investigation.md's event-coverage audit, not silently
    dropped):
    - gold_transaction/gold_transferred — pure `entity.inventory.gold` state diff, no typed
      record backs it.
    - resource_node_depleted / resource_node_regenerated / node_recharged — pure
      `state.resource_nodes` dict diff, not per-entity, no typed per-node record.
    - conservation_law_verified — derived from other events already emitted this tick + a
      tick-cadence gate; a meta/aggregate check, not a single update-record read.
    """

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to ECONOMY's migrated events (confirmed: the old
        # extractor's only 3 mode checks are movement, combat_damage, and gold_transaction — the
        # last of which is on this ticket's DEFERRED list, not migrated at all). `mode` accepted
        # for EventShaper protocol conformance only.
        events: List[SimulationEvent] = []
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)

            for ir in (getattr(e_upd, "intent_results", None) or []):
                if not getattr(ir, "accepted", False):
                    continue
                src_kind = getattr(ir, "source_kind", None)
                source_id = str(getattr(ir, "source_id", ""))

                if src_kind == "NODE":
                    events.append(SimulationEvent(
                        event_type="resource_harvested", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"node_id": source_id},
                    ))
                elif src_kind == "CRAFTING":
                    events.append(SimulationEvent(
                        event_type="item_crafted", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"source_id": source_id},
                    ))
                elif src_kind in ("SHOP_BUY", "SHOP_SELL"):
                    events.append(SimulationEvent(
                        event_type="shop_transaction", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"kind": src_kind},
                    ))
                    events.append(SimulationEvent(
                        event_type="trade_executed", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"kind": src_kind},
                    ))
                elif src_kind == "QUEST":
                    events.append(SimulationEvent(
                        event_type="quest_reward_dispensed", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"source_id": source_id},
                    ))
                elif src_kind in _GOLD_SINK_KINDS:
                    events.append(SimulationEvent(
                        event_type="gold_sink_fired", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"mechanism": src_kind},
                    ))
                elif src_kind == "INFORMATION_PURCHASE":
                    events.append(SimulationEvent(
                        event_type="paid_information_transaction", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"source_id": source_id},
                    ))
                    events.append(SimulationEvent(
                        event_type="paid_info_transaction", event_category="economy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"source_id": source_id},
                    ))
                    # paid_info_changed_goal: current_project_id_set is a real, NEW value being
                    # assigned this tick (per the "_set" suffix convention) — comparing it against
                    # prior_state's value derives the same "did the project switch" signal
                    # event_extractor.py gets by comparing post-mutation entity.strategic against
                    # prior_ent.strategic, without needing the materialized post-mutation state.
                    strategic_upd = getattr(e_upd, "strategic", None)
                    new_project_id = getattr(strategic_upd, "current_project_id_set", None)
                    if (prior_ent is not None and strategic_upd is not None
                            and new_project_id is not None
                            and new_project_id != getattr(prior_ent.strategic, "current_project_id", None)):
                        events.append(SimulationEvent(
                            event_type="paid_info_changed_goal", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"source_id": source_id},
                        ))

        return events


class FactionShaper:
    """FACTION domain shaper — diplomatic_transition, alliance_proposed, alliance_accepted,
    territory_ownership_changed, resource_seized, faction_tension_delta, war_declared,
    military_conflict_resolved, faction_trajectory_stagnant.

    Reads `update.faction_updates[]` (typed `FactionUpdate` records) and
    `update.world_events_add[]` (typed `WorldEvent` records) — the same mechanism
    `event_extractor.py` already uses (this domain was already closest to push-shaped).
    `alliance_proposed` additionally reads `prior_state.factions` for the pre-transition
    diplomatic state — available as `apply_generation()`'s own `prior_state` parameter, no new
    plumbing needed.

    Deliberately excluded (see epic investigation.md's event-coverage audit, not silently
    dropped):
    - faction_extinct — a full entity-census scan (iterates ALL of `current_state.entities` AND
      `prior_state.entities` to compute per-faction living-member counts), not a single
      update-record read at all.

    `faction_trajectory_stagnant` (TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY): the first
    cross-tick state this shaper carries — every other event here is derived from a single tick's
    `FactionUpdate` alone. `_last_territory_change_tick`/`_emitted_stagnant` mirror
    `ProgressionShaper`'s own established per-run-state pattern; `reset_run_state()` must be
    wired into `Kernel.__init__` alongside the other stateful shapers.
    """

    _MILITARY_RESOLVED_CATEGORIES = ("TERRITORY_TRANSFERRED", "WAR_ENDED_EXHAUSTION")
    _FACTION_STAGNANT_TICKS = 300

    # Per-run tracking, NOT durable state — cleared via reset_run_state().
    _last_territory_change_tick: dict = {}
    _emitted_stagnant: set = set()

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start (Kernel.__init__) and in test
        teardown."""
        cls._last_territory_change_tick.clear()
        cls._emitted_stagnant.clear()

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to FACTION's events (same confirmation as EconomyShaper).
        # `mode` accepted for EventShaper protocol conformance only.
        events: List[SimulationEvent] = []
        seen_diplo_pairs: set = set()

        faction_upds = getattr(update, "faction_updates", None)
        if not isinstance(faction_upds, (list, tuple)):
            faction_upds = ()

        for upd in faction_upds:
            fid = upd.faction_id

            for other_fid, new_state in (upd.diplomatic_relations_set or {}).items():
                pair = frozenset({fid, other_fid})
                if pair in seen_diplo_pairs:
                    continue
                seen_diplo_pairs.add(pair)
                state_name = getattr(new_state, "name", str(new_state))
                events.append(SimulationEvent(
                    event_type="diplomatic_transition", event_category="faction",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"faction_id": fid, "target_faction_id": other_fid, "new_state": state_name},
                ))

                if state_name == "ALLIED":
                    prior_factions = getattr(prior_state, "factions", None) or {}
                    prior_faction_st = prior_factions.get(fid)
                    prior_diplo = (getattr(prior_faction_st, "diplomatic_relations", None) or {}) if prior_faction_st else {}
                    prior_rel = getattr(prior_diplo.get(other_fid), "name",
                                         str(prior_diplo.get(other_fid, "NEUTRAL")))
                    if prior_rel in ("NEUTRAL", "HOSTILE"):
                        events.append(SimulationEvent(
                            event_type="alliance_proposed", event_category="faction",
                            tick=tick, entity_id=None, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"proposing_faction": fid, "target_faction": other_fid,
                                     "prior_state": prior_rel, "tick": tick},
                        ))
                    events.append(SimulationEvent(
                        event_type="alliance_accepted", event_category="faction",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"faction_id": fid, "partner_id": other_fid},
                    ))

            # faction_territory_pct (TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP): reconstructed
            # from prior_state.factions[fid].territory + this tick's territory_add/territory_remove
            # deltas, over prior_state's own region count (region count itself doesn't change
            # tick-to-tick, so prior_state.regions is an equally valid denominator to current_state's
            # would be) -- same prior-snapshot-plus-delta reconstruction pattern this file already
            # establishes elsewhere (see module docstring / _current_leads()).
            _total_regions = len(getattr(prior_state, "regions", None) or {})
            _prior_faction_st = (getattr(prior_state, "factions", None) or {}).get(fid)
            _prior_territory = set(getattr(_prior_faction_st, "territory", None) or ())
            _curr_territory = (_prior_territory - set(upd.territory_remove or ())) | set(upd.territory_add or ())
            _territory_pct = (len(_curr_territory) / _total_regions) if _total_regions > 0 else 0.0
            for region_id in (upd.territory_add or ()):
                events.append(SimulationEvent(
                    event_type="territory_ownership_changed", event_category="faction",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"faction_id": fid, "region_id": region_id,
                             "faction_territory_pct": _territory_pct},
                ))
                if getattr(upd, "tension_delta", 0.0) > 0:
                    events.append(SimulationEvent(
                        event_type="resource_seized", event_category="faction",
                        tick=tick, entity_id=None, severity="WARNING",
                        source_system="event_shapers", message="",
                        payload={"faction_id": fid, "region_id": region_id, "tick": tick},
                    ))

            if getattr(upd, "tension_delta", 0.0) != 0.0:
                events.append(SimulationEvent(
                    event_type="faction_tension_delta", event_category="faction",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"faction_id": fid, "delta": upd.tension_delta},
                ))

            # faction_trajectory_stagnant (TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY):
            # mirrors WORLD's own trauma_hazard_broken pattern -- a trend flat (territory
            # unchanged) despite an active, ongoing related signal (diplomatic activity for the
            # same faction). Baseline initializes to first-observed tick, not 0, so a faction
            # first seen mid-run isn't immediately misclassified as stagnant.
            _has_territory_change = bool(upd.territory_add) or bool(upd.territory_remove)
            _has_diplo_activity = bool(upd.diplomatic_relations_set)
            if fid not in FactionShaper._last_territory_change_tick:
                FactionShaper._last_territory_change_tick[fid] = tick
            if _has_territory_change:
                FactionShaper._last_territory_change_tick[fid] = tick
            elif _has_diplo_activity and fid not in FactionShaper._emitted_stagnant:
                _since_change = tick - FactionShaper._last_territory_change_tick[fid]
                if _since_change > FactionShaper._FACTION_STAGNANT_TICKS:
                    FactionShaper._emitted_stagnant.add(fid)
                    events.append(SimulationEvent(
                        event_type="faction_trajectory_stagnant", event_category="faction",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"faction_id": fid, "ticks_since_territory_change": _since_change},
                    ))

        world_evts = getattr(update, "world_events_add", None)
        if not isinstance(world_evts, (list, tuple)):
            world_evts = ()

        for we in world_evts:
            cat = getattr(we, "category", None)
            cat_str = getattr(cat, "value", str(cat))
            if cat_str == "FACTION_WAR_DECLARED":
                events.append(SimulationEvent(
                    event_type="war_declared", event_category="faction",
                    tick=tick, entity_id=None, severity="CRITICAL",
                    source_system="event_shapers", message="",
                    payload={"faction_pair": str(getattr(we, "subject", ""))},
                ))
            elif cat_str in self._MILITARY_RESOLVED_CATEGORIES:
                events.append(SimulationEvent(
                    event_type="military_conflict_resolved", event_category="faction",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"subject": str(getattr(we, "subject", "")), "category": cat_str},
                ))

        return events


def _current_leads(prior_ent: Any, strategic_upd: Any) -> dict:
    """Reconstructs an entity's current full `leads` dict from `prior_state`'s full snapshot
    (`prior_ent.strategic.leads`) plus this tick's `StrategicUpdate` delta
    (`leads_add_or_update`/`leads_remove`) -- `AuthoritativeState` is a full snapshot each tick,
    not an incremental structure, so prior-full-state + this-tick-delta == current-full-state for
    any field the delta actually captures. This is what lets `belief_stale` (which needs to
    re-check EVERY current lead, not just ones that changed this tick) stay push-ready without
    reading post-apply `current_state` at all — see StrategyShaper's docstring."""
    leads = dict(getattr(getattr(prior_ent, "strategic", None), "leads", None) or {})
    if strategic_upd is None:
        return leads
    for lead in (getattr(strategic_upd, "leads_add_or_update", None) or []):
        leads[lead.id] = lead
    for lid in (getattr(strategic_upd, "leads_remove", None) or ()):
        leads.pop(lid, None)
    return leads


def _current_projects(prior_ent: Any, strategic_upd: Any) -> dict:
    """Reconstructs an entity's current full `projects` dict from `prior_state`'s full snapshot
    (`prior_ent.strategic.projects`) plus this tick's `StrategicUpdate` delta
    (`projects_add_or_update`/`projects_remove`) -- same reconstruction pattern as
    `_current_leads()`, used by `NarrativeShaper` to detect QuestState status transitions without
    reading post-apply `current_state` (TCK-20260807-QUEST-EVENT-PUSH-MIGRATION)."""
    projects = dict(getattr(getattr(prior_ent, "strategic", None), "projects", None) or {})
    if strategic_upd is None:
        return projects
    for project in (getattr(strategic_upd, "projects_add_or_update", None) or []):
        projects[project.id] = project
    for pid in (getattr(strategic_upd, "projects_remove", None) or ()):
        projects.pop(pid, None)
    return projects


class StrategyShaper:
    """AGENCY/COGNITION/INFORMATION (+ colocated SOCIAL `cooperation_event`) domain shaper —
    route_selected, action_executed, route_family_first_use, defer_with_reason,
    self_model_updated, belief_assimilated, belief_updated, route_new_query, cooperation_event,
    lead_certainty_changed, lead_certainty_updated, belief_stale, decision_diverged_by_belief,
    decision_divergence_detected.

    Two source mechanisms, both confirmed against `event_extractor.py:295-563`'s existing
    behavior (see stored_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY/investigation.md):

    1. `EntityUpdate.property_updates` (a generic per-tick key/value bag) and
       `EntityUpdate.self_model_bundle_set` — read directly for `route_selected`/
       `action_executed`/`route_family_first_use`/`defer_with_reason`/`self_model_updated`/
       `belief_assimilated`/`belief_updated`/`route_new_query`/`cooperation_event`. These were
       already effectively push-shaped in the old extractor (zero prior/current diffing involved
       there either) — just relocated here.
    2. Reconstructed "current view" via `_current_leads()` (leads) and direct
       `StrategicUpdate.current_project_id_set`/`concerns_add_or_update` reads (falling back to
       `prior_ent.strategic` when a field wasn't set this tick — the same fallback pattern
       `CombatShaper` already uses for `alive_set`) — for `lead_certainty_changed`/
       `lead_certainty_updated`/`belief_stale`/`decision_diverged_by_belief`/
       `decision_divergence_detected`, which the old extractor implements by diffing fully
       materialized post-apply state. Confirmed this reconstruction is sufficient (not merely
       approximate) because `dirty_entity_ids` in `event_extractor.py:122` is ALSO
       `update.entity_updates.keys()` under normal operation — the old extractor only visits
       entities with some update this tick too, the same precondition this shaper's own
       `entity_updates.items()` loop already requires. `belief_stale` specifically needs the FULL
       current lead set re-checked every visited tick (a lead can go stale from pure time passing,
       with no lead-specific change that tick) — `_current_leads()` provides that, not just the
       delta list, which is why it's a shared module-level helper rather than inlined.
    """

    # Per-run tracking, NOT durable state — mirrors EventExtractor's identically-named class
    # attributes exactly (same "once per entity per run" / "once per lead per run" semantics for
    # route_family_first_use/belief_stale). Must be cleared at run start via reset_run_state(),
    # same as EventExtractor's own cache — found missing during this ticket's own real-kernel
    # verification (a fresh StrategyShaper cache would otherwise leak across separate runs within
    # the same process, e.g. two consecutive calibration runs in one pytest session).
    _seen_routing_families: dict = {}
    _emitted_stale_leads: set = set()

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start (Kernel.__init__, alongside
        EventExtractor.reset_run_state()) and in test teardown."""
        cls._seen_routing_families.clear()
        cls._emitted_stale_leads.clear()

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to any of this shaper's events (same confirmation as
        # EconomyShaper/FactionShaper — none of these appear in event_extractor.py's 3 mode
        # checks). `mode` accepted for EventShaper protocol conformance only.
        events: List[SimulationEvent] = []
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue

            prop = getattr(e_upd, "property_updates", None) or {}

            # AGENCY: route_selected / action_executed / route_family_first_use
            routing_family = prop.get("last_routing_family")
            if routing_family:
                events.append(SimulationEvent(
                    event_type="route_selected", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"family": routing_family},
                ))
                events.append(SimulationEvent(
                    event_type="action_executed", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"family": routing_family},
                ))
                seen = StrategyShaper._seen_routing_families.setdefault(eid, set())
                if routing_family not in seen:
                    seen.add(routing_family)
                    events.append(SimulationEvent(
                        event_type="route_family_first_use", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"entity_id": eid, "family": routing_family, "tick": tick},
                    ))

            # AGENCY: defer_with_reason
            defer_reason = prop.get("last_defer_reason")
            if defer_reason:
                events.append(SimulationEvent(
                    event_type="defer_with_reason", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"entity_id": eid, "reason": defer_reason, "tick": tick},
                ))

            # COGNITION: self_model_updated
            if getattr(e_upd, "self_model_bundle_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="self_model_updated", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={},
                ))

            # INFORMATION: belief_assimilated + belief_updated
            if prop.get("last_assimilated_tick") == prior_state.tick:
                subject = prop.get("last_assimilated_subject", "unknown")
                events.append(SimulationEvent(
                    event_type="belief_assimilated", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"subject": subject},
                ))
                events.append(SimulationEvent(
                    event_type="belief_updated", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"subject": subject},
                ))

            # INFORMATION: route_new_query
            if prop.get("last_routed_query_tick") == prior_state.tick:
                subject = prop.get("last_routed_query_subject", "unknown")
                events.append(SimulationEvent(
                    event_type="route_new_query", event_category="strategy",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"subject": subject},
                ))

            # SOCIAL: cooperation_event (colocated here, not SocialShaper — same
            # property_updates-reading code region as the events above)
            if prop.get("last_cooperation_decision") is not None:
                events.append(SimulationEvent(
                    event_type="cooperation_event", event_category="social",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"entity_id": eid, "decision": str(prop["last_cooperation_decision"])},
                ))

            # --- Reconstructed-current-view events (leads/projects/concerns) ---
            strategic_upd = getattr(e_upd, "strategic", None)
            if strategic_upd is None:
                continue
            prior_strategic = getattr(prior_ent, "strategic", None)
            if prior_strategic is None:
                continue

            prior_leads = getattr(prior_strategic, "leads", None) or {}
            current_leads = _current_leads(prior_ent, strategic_upd)

            new_project_id = getattr(strategic_upd, "current_project_id_set", None)
            curr_proj_id = new_project_id if new_project_id is not None else getattr(prior_strategic, "current_project_id", None)

            # Cognition: lead_certainty_changed / Information: lead_certainty_updated —
            # only leads genuinely touched this tick (leads_add_or_update), matching the old
            # extractor's own "lead.certainty != prior_lead.certainty" gate exactly.
            for lead in (getattr(strategic_upd, "leads_add_or_update", None) or []):
                prior_lead = prior_leads.get(lead.id)
                if prior_lead is not None and lead.certainty != prior_lead.certainty:
                    events.append(SimulationEvent(
                        event_type="lead_certainty_changed", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={
                            "lead_id": lead.id,
                            "from_certainty": str(prior_lead.certainty),
                            "to_certainty": str(lead.certainty),
                        },
                    ))
                    _prior_cv = _CERTAINTY_FLOAT.get(getattr(prior_lead.certainty, "value", str(prior_lead.certainty)), 0.0)
                    _curr_cv = _CERTAINTY_FLOAT.get(getattr(lead.certainty, "value", str(lead.certainty)), 0.0)
                    events.append(SimulationEvent(
                        event_type="lead_certainty_updated", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={
                            "lead_id": lead.id,
                            "certainty_delta": round(_curr_cv - _prior_cv, 4),
                            "lead_active": curr_proj_id is not None,
                        },
                    ))

            # Information: belief_stale — re-checks EVERY current lead (not just ones touched
            # this tick), matching the old extractor's own full-scan behavior exactly (both are
            # gated on the entity having some update this tick, per the class docstring).
            for lead in current_leads.values():
                cert_str = getattr(lead.certainty, "value", str(lead.certainty))
                age = tick - int(getattr(lead, "discovered_tick", tick))
                stale_key = (eid, lead.id)
                if (stale_key not in StrategyShaper._emitted_stale_leads
                        and cert_str in ("VAGUE", "EXHAUSTED")
                        and age > _BELIEF_STALE_TICKS):
                    StrategyShaper._emitted_stale_leads.add(stale_key)
                    events.append(SimulationEvent(
                        event_type="belief_stale", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"lead_id": lead.id, "certainty": cert_str},
                    ))

            # Information: decision_diverged_by_belief — pursuing a non-information project while
            # holding a VAGUE/EXHAUSTED lead.
            has_vague_lead = any(
                getattr(lead.certainty, "value", str(lead.certainty)) in ("VAGUE", "EXHAUSTED")
                for lead in current_leads.values()
            )
            current_projects = dict(getattr(prior_strategic, "projects", None) or {})
            for proj in (getattr(strategic_upd, "projects_add_or_update", None) or []):
                current_projects[proj.id] = proj
            for pid in (getattr(strategic_upd, "projects_remove", None) or ()):
                current_projects.pop(pid, None)

            if curr_proj_id and has_vague_lead:
                curr_proj = current_projects.get(curr_proj_id)
                proj_kind = getattr(getattr(curr_proj, "kind", None), "value",
                                     str(getattr(curr_proj, "kind", ""))) if curr_proj else ""
                if proj_kind and proj_kind not in ("information", "information_seeking"):
                    events.append(SimulationEvent(
                        event_type="decision_diverged_by_belief", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"project_kind": proj_kind},
                    ))

            # Cognition: decision_divergence_detected — active project kind inconsistent with
            # top-urgency DANGER concern.
            current_concerns = dict(getattr(prior_strategic, "concerns", None) or {})
            for concern in (getattr(strategic_upd, "concerns_add_or_update", None) or []):
                current_concerns[concern.id] = concern
            for cid in (getattr(strategic_upd, "concerns_remove", None) or ()):
                current_concerns.pop(cid, None)

            if curr_proj_id and current_concerns:
                top_concern = max(current_concerns.values(), key=lambda c: getattr(c, "urgency", 0.0), default=None)
                top_urgency = getattr(top_concern, "urgency", 0.0)
                top_kind = getattr(getattr(top_concern, "kind", None), "value",
                                    str(getattr(top_concern, "kind", ""))) if top_concern else ""
                if top_urgency > 0.7 and top_kind == "danger":
                    curr_proj2 = current_projects.get(curr_proj_id)
                    pk2 = getattr(getattr(curr_proj2, "kind", None), "value",
                                  str(getattr(curr_proj2, "kind", ""))) if curr_proj2 else ""
                    if pk2 in _NON_SURVIVAL_PROJECT_KINDS:
                        events.append(SimulationEvent(
                            event_type="decision_divergence_detected", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"project_kind": pk2, "concern_kind": top_kind,
                                     "concern_urgency": round(top_urgency, 4)},
                        ))

        return events


SHAPER_REGISTRY: dict[str, list[EventShaper]] = {
    "combat": [CombatShaper()],
    "economy": [EconomyShaper()],
    "faction": [FactionShaper()],
}

class ProgressionShaper:
    """PROGRESSION domain shaper — xp_granted, level_up, entity_evolved, skill_unlocked,
    trait_expressed, pillar_trait_unlocked, progression_conversion_applied,
    progression_plateau_detected.

    Confirmed against `event_extractor.py:266-282,773-834` and `src/core/updates.py:220-243`
    (`IdentityUpdate`): every event except `progression_plateau_detected` reads an already-typed
    delta field directly — `evolution_points_delta`/`evolution_level_set`/`learned_skills`
    (confirmed a per-tick accumulator, not a full-snapshot replacement, by tracing its
    construction site: `src/engine/evolution.py:122-125`'s
    `learned_skills=list(set(id_upd.learned_skills + skills_to_learn))` unions newly-unlocked
    skill IDs into whatever the update already carries)/`traits_add`/`breakthroughs_add`/
    `unspent_ap_delta`. `progression_plateau_detected` is cross-tick derived (XP unchanged for
    `_XP_PLATEAU_TICKS`, or level>=5 with zero skills) — same shaper-local per-run state pattern
    `StrategyShaper` already established for `belief_stale`/`route_family_first_use`, not new
    instrumentation.
    """

    # Per-run tracking, NOT durable state — mirrors EventExtractor's identically-named class
    # attributes. Must be cleared via reset_run_state(), same as StrategyShaper's own caches.
    _last_xp_tick: dict = {}
    _emitted_plateau: set = set()

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start (Kernel.__init__) and in test
        teardown."""
        cls._last_xp_tick.clear()
        cls._emitted_plateau.clear()

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to any of PROGRESSION's events (none appear in
        # event_extractor.py's 3 mode checks). `mode` accepted for protocol conformance only.
        events: List[SimulationEvent] = []
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue
            prior_id = getattr(prior_ent, "identity", None)
            if prior_id is None:
                continue
            # id_upd may be None — an entity can have SOME update this tick (e.g. a routing
            # change) without an identity-specific one. Only the direct-field events below need a
            # real id_upd to read from; progression_plateau_detected must still run using
            # prior_id alone (matching event_extractor.py's own dirty_entity_ids gate, which is
            # "any update this tick", not "an identity update specifically" — the SAME gap found
            # and fixed for belief_stale in StrategyShaper, confirmed here via a real kernel run
            # showing zero shaper-sourced progression_plateau_detected events despite the old
            # extractor firing 32 times on an identical run).
            id_upd = getattr(e_upd, "identity", None)
            xp_delta = 0
            new_level = None

            if id_upd is not None:
                # xp_granted / level_up
                xp_delta = getattr(id_upd, "evolution_points_delta", 0)
                if xp_delta > 0:
                    events.append(SimulationEvent(
                        event_type="xp_granted", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"amount": xp_delta},
                    ))

                new_level = getattr(id_upd, "evolution_level_set", None)
                if new_level is not None and new_level > getattr(prior_id, "evolution_level", 1):
                    events.append(SimulationEvent(
                        event_type="level_up", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"new_level": new_level},
                    ))

                # skill_unlocked / trait_expressed / pillar_trait_unlocked — each field is a
                # per-tick accumulator of newly-unlocked IDs, not a full snapshot (class docstring).
                for sk in (getattr(id_upd, "learned_skills", None) or []):
                    events.append(SimulationEvent(
                        event_type="skill_unlocked", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"skill_id": sk, "tick": tick},
                    ))
                for tr in (getattr(id_upd, "traits_add", None) or []):
                    events.append(SimulationEvent(
                        event_type="trait_expressed", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"trait_id": tr, "tick": tick},
                    ))
                for bt in (getattr(id_upd, "breakthroughs_add", None) or []):
                    events.append(SimulationEvent(
                        event_type="pillar_trait_unlocked", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"trait_id": bt, "tick": tick},
                    ))

                # progression_conversion_applied — unspent_ap decreased (AP converted to a stat)
                ap_delta = getattr(id_upd, "unspent_ap_delta", 0)
                if ap_delta < 0:
                    events.append(SimulationEvent(
                        event_type="progression_conversion_applied", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"ap_spent": -ap_delta, "tick": tick},
                    ))

            # entity_evolved (TCK-20260906-ENTITY-EVOLVED-EVENT-GAP): species evolution at level
            # thresholds (src/engine/evolution.py's EvolutionSystem). Unlike xp_granted/level_up
            # above, `kind_set` lives directly on EntityUpdate (e_upd), not IdentityUpdate
            # (id_upd) -- EvolutionSystem always writes kind_set (unchanged when not evolved), so
            # this must diff against prior_ent.kind, not just check for a non-None value.
            new_kind = getattr(e_upd, "kind_set", None)
            if new_kind is not None and new_kind != prior_ent.kind:
                events.append(SimulationEvent(
                    event_type="entity_evolved", event_category="lifecycle",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"previous_kind": prior_ent.kind, "new_kind": new_kind},
                ))

            # progression_plateau_detected — cross-tick derived, shaper-local state. Runs for any
            # entity with SOME update this tick (see note above), not just an identity update.
            curr_xp = getattr(prior_id, "evolution_points", 0) + xp_delta
            prior_xp = getattr(prior_id, "evolution_points", 0)
            if curr_xp != prior_xp:
                ProgressionShaper._last_xp_tick[eid] = tick
            elif eid not in ProgressionShaper._emitted_plateau:
                since = tick - ProgressionShaper._last_xp_tick.get(eid, 0)
                curr_level = new_level if new_level is not None else getattr(prior_id, "evolution_level", 1)
                curr_skills = set(getattr(prior_id, "learned_skills", None) or set()) | set(
                    getattr(id_upd, "learned_skills", None) or [])
                if since > _XP_PLATEAU_TICKS:
                    ProgressionShaper._emitted_plateau.add(eid)
                    events.append(SimulationEvent(
                        event_type="progression_plateau_detected", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"type": "xp_rate_zero", "ticks_since_xp": since},
                    ))
                elif curr_level >= 5 and not curr_skills:
                    ProgressionShaper._emitted_plateau.add(eid)
                    events.append(SimulationEvent(
                        event_type="progression_plateau_detected", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"type": "skill_silence", "level": curr_level},
                    ))

        return events


class WorldDynamicsShaper:
    """WORLD dynamics (+ demographic + NARRATIVE co-fire) domain shaper — demographic_birth,
    demographic_mortality, ecology_cycle_completed, spawn_cadence_fired, threat_evolved,
    building_sabotaged, region_ownership_changed, region_transformed, region_trauma_delta,
    calamity_spawned, boss_spawned, raid_party_spawned, narrative_milestone,
    world_emergence_event.

    Confirmed against `event_extractor.py:130-159,889-1030,1108-1186` — every event reads a typed
    `StateUpdate` field directly (`entities_add`/`entities_remove`, `world_updates`,
    `building_updates`, `last_calamity_tick_set`, `world_events_add`), the same
    `world_events_add` record `FactionShaper` already reads for `war_declared`/
    `military_conflict_resolved` — `narrative_milestone`/`world_emergence_event` were left
    "out of migration scope" by Phase 1 (COMBAT/ECONOMY/FACTION only), not because they weren't
    push-ready, just because they weren't that ticket's domain.

    `demographic_mortality` closes a Phase 1 deferral (`INFRA-324`'s original "despawn branch,
    broader than combat" classification) — `StateUpdate.entities_remove` plus the already-shared
    `_real_combat_update` gives the same "despawn without a combat attacker" signal without
    needing full-state absence-checking.

    `building_sabotaged` substitutes `prior_state` for the old extractor's `current_state` in its
    `Kernel.get_building_region()` call — building positions are durable/stable
    (sabotage only changes HP, never position), so a prior-tick lookup is equivalent, confirmed by
    reading `SpatialQueryService.get_building_region()`'s own implementation (reads
    `state.buildings`, not anything sabotage would have changed).
    """

    _MILITARY_RESOLVED = frozenset({
        WorldEventCategory.TERRITORY_TRANSFERRED,
        WorldEventCategory.WAR_ENDED_EXHAUSTION,
    })
    _BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel"))

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to any of this shaper's events. `mode` accepted for
        # protocol conformance only.
        events: List[SimulationEvent] = []

        # demographic_mortality / demographic_birth — StateUpdate.entities_remove/entities_add
        entity_updates = getattr(update, "entity_updates", None) or {}
        for rem_eid in (getattr(update, "entities_remove", None) or []):
            prior_ent = prior_state.entities.get(rem_eid)
            if prior_ent is None:
                continue
            e_upd = entity_updates.get(rem_eid)
            if _real_combat_update(e_upd) is not None:
                continue
            events.append(SimulationEvent(
                event_type="demographic_mortality", event_category="lifecycle",
                tick=tick, entity_id=rem_eid, severity="INFO",
                source_system="event_shapers", message="",
                payload={"kind": getattr(prior_ent, "kind", None)},
            ))
        for new_ent in (getattr(update, "entities_add", None) or []):
            kind = getattr(new_ent, "kind", None)
            new_eid = getattr(new_ent, "id", None)
            events.append(SimulationEvent(
                event_type="demographic_birth", event_category="lifecycle",
                tick=tick, entity_id=new_eid, severity="INFO",
                source_system="event_shapers", message="",
                payload={"kind": kind},
            ))
            if kind in self._BOSS_KINDS:
                events.append(SimulationEvent(
                    event_type="boss_spawned", event_category="lifecycle",
                    tick=tick, entity_id=new_eid, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"kind": kind},
                ))
                events.append(SimulationEvent(
                    event_type="narrative_milestone", event_category="lifecycle",
                    tick=tick, entity_id=new_eid, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"milestone": "first_boss_spawned", "kind": kind},
                ))
            elif kind == "goblin_raider":
                events.append(SimulationEvent(
                    event_type="raid_party_spawned", event_category="lifecycle",
                    tick=tick, entity_id=new_eid, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"kind": kind},
                ))

        # ecology_cycle_completed — tick-modulo sweep, stable region set (no update dependency)
        if tick % 200 == 0:
            for r_id, region in (prior_state.regions or {}).items():
                events.append(SimulationEvent(
                    event_type="ecology_cycle_completed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"region_id": r_id, "cycle_type": getattr(region, "kind", "unknown"),
                             "net_pressure_delta": 0.0},
                ))

        # spawn_cadence_fired — tick-modulo + non-boss entities_add
        if tick % 50 == 0:
            spawned = [e for e in (getattr(update, "entities_add", None) or [])
                       if getattr(e, "kind", None) not in (None, "world_boss", "ancient_sentinel", "goblin_raider")]
            if spawned:
                events.append(SimulationEvent(
                    event_type="spawn_cadence_fired", event_category="lifecycle",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"spawned_count": len(spawned), "tick": tick},
                ))

        # World dynamics events from StateUpdate.world_updates
        for rid, w_upd in (getattr(update, "world_updates", None) or {}).items():
            if getattr(w_upd, "trauma_delta", 0.0) != 0.0:
                events.append(SimulationEvent(
                    event_type="region_trauma_delta", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"region_id": rid, "delta": w_upd.trauma_delta},
                ))

            prior_region = getattr(prior_state, "regions", {}).get(rid) if prior_state else None
            if prior_region is not None:
                try:
                    prior_trauma = float(getattr(prior_region, "trauma_score", 0.0))
                    trauma_delta = float(getattr(w_upd, "trauma_delta", 0.0))
                    new_trauma = prior_trauma + trauma_delta
                    for threshold in (25.0, 50.0, 75.0, 100.0):
                        if prior_trauma < threshold <= new_trauma:
                            events.append(SimulationEvent(
                                event_type="threat_evolved", event_category="region",
                                tick=tick, entity_id=None, severity="WARNING",
                                source_system="event_shapers", message="",
                                payload={"region_id": rid, "threshold": threshold,
                                         "prior_trauma": round(prior_trauma, 2),
                                         "new_trauma": round(new_trauma, 2)},
                            ))
                            break
                except (TypeError, ValueError):
                    pass

            if getattr(w_upd, "owner_faction_id_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_ownership_changed", event_category="region",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"region_id": rid, "new_owner": str(w_upd.owner_faction_id_set)},
                ))
            if getattr(w_upd, "kind_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_transformed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"region_id": rid, "new_kind": w_upd.kind_set},
                ))

        # building_sabotaged — hp_delta < 0 discriminates sabotage from insolvency writes (which
        # only ever set functional_set=False, never hp_delta)
        for b_id, b_upd in (getattr(update, "building_updates", None) or {}).items():
            if getattr(b_upd, "hp_delta", 0.0) is not None and getattr(b_upd, "hp_delta", 0.0) < 0:
                from src.engine.kernel import Kernel
                region = Kernel.get_building_region(prior_state, b_id) if prior_state else None
                events.append(SimulationEvent(
                    event_type="building_sabotaged", event_category="region",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"building_id": b_id, "hp_delta": b_upd.hp_delta,
                             "region_id": region.id if region else None},
                ))

        # calamity_spawned
        if getattr(update, "last_calamity_tick_set", None) == prior_state.tick:
            events.append(SimulationEvent(
                event_type="calamity_spawned", event_category="lifecycle",
                tick=tick, entity_id=None, severity="CRITICAL",
                source_system="event_shapers", message="",
                payload={"tick": tick},
            ))

        # NARRATIVE: world_emergence_event (every WorldEvent) + narrative_milestone (war/sovereignty)
        world_evts = getattr(update, "world_events_add", None)
        if not isinstance(world_evts, (list, tuple)):
            world_evts = ()
        for we in world_evts:
            cat = getattr(we, "category", None)
            events.append(SimulationEvent(
                event_type="world_emergence_event", event_category="lifecycle",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_shapers", message="",
                payload={"category": str(cat) if cat else "",
                         "region_id": str(getattr(we, "region_id", "") or ""),
                         "subject": str(getattr(we, "subject", "") or "")},
            ))
            if cat == WorldEventCategory.FACTION_WAR_DECLARED:
                events.append(SimulationEvent(
                    event_type="narrative_milestone", event_category="lifecycle",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"milestone": "first_war", "subject": str(getattr(we, "subject", "") or "")},
                ))
            elif cat == WorldEventCategory.SOVEREIGNTY_SHIFT:
                events.append(SimulationEvent(
                    event_type="narrative_milestone", event_category="lifecycle",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_shapers", message="",
                    payload={"milestone": "first_sovereignty_transfer",
                             "region_id": str(getattr(we, "region_id", "") or "")},
                ))

        return events


_CONSERVATION_ECONOMY_TYPES = frozenset((
    "resource_harvested", "item_crafted", "shop_transaction",
    "paid_information_transaction", "gold_sink_fired",
))


class DeferredInstrumentationShaper:
    """Closes Phase 1's remaining 3 deferrals — resource_node_depleted/regenerated/
    node_recharged, faction_extinct. (`conservation_law_verified` is a separate, cross-shaper
    aggregation step in `run_shadow_shapers()` itself, not a single shaper's job — see there.)

    **Correction to Phase 1's own audit**: `resource_node_depleted`/`resource_node_regenerated`/
    `node_recharged` were classified "pure `resource_nodes` dict diff, no typed per-node record."
    This was wrong — `StateUpdate.node_updates: Dict[int, ResourceNodeUpdate]` (confirmed
    `src/core/updates.py:701-713`) already exists, with `charges_delta: int` giving exactly the
    signal needed (`new_charges = prior_node.remaining_charges + charges_delta`, same
    reconstruction pattern used throughout this epic). No new instrumentation needed after all —
    found by tracing the real mutation site (`src/engine/apply_plan.py:152-177`), not by trusting
    the earlier audit's classification.

    `faction_extinct` genuinely needs a full-population reconstruction (not a single per-entity
    update read) — same cost profile as the old extractor's own full census scan, just
    reconstructed from `prior_state.entities` + this tick's `entities_add`/`entities_remove`/
    `entity_updates` deltas instead of reading `current_state.entities` directly. **Faithfully
    reproduces a real, pre-existing quirk in the old extractor rather than silently fixing it**:
    `event_extractor.py`'s own HP-alive check reads `getattr(entity, "hp", None)` — but
    `EntityState` has no top-level `hp` attribute (only `entity.combat.hp`), so that check is
    dead code, always `True`, for every entity. In practice this doesn't cause wrong behavior
    (dead entities are removed from `entities`/`entities_remove` entirely, not just HP-zeroed),
    but this shaper reproduces the *actual* behavior (entity presence + faction match only, no HP
    check) rather than the *documented intent* (HP-alive check) — fixing the dead code is out of
    this migration ticket's scope.
    """

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        events: List[SimulationEvent] = []

        # resource_node_depleted / resource_node_regenerated / node_recharged
        prior_nodes = getattr(prior_state, "resource_nodes", None) or {}
        for node_id, n_upd in (getattr(update, "node_updates", None) or {}).items():
            prior_node = prior_nodes.get(node_id)
            if prior_node is None:
                continue
            charges_delta = getattr(n_upd, "charges_delta", 0)
            prior_charges = prior_node.remaining_charges
            new_charges = prior_charges + charges_delta
            if prior_charges > 0 and new_charges == 0:
                events.append(SimulationEvent(
                    event_type="resource_node_depleted", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"node_id": node_id, "charges": 0, "max_charges": prior_node.max_charges},
                ))
            elif prior_charges == 0 and new_charges > 0:
                events.append(SimulationEvent(
                    event_type="resource_node_regenerated", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"node_id": node_id, "charges": new_charges, "max_charges": prior_node.max_charges},
                ))
                events.append(SimulationEvent(
                    event_type="node_recharged", event_category="resource",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_shapers", message="",
                    payload={"node_id": node_id, "charges": new_charges},
                ))

        # faction_extinct — full-population reconstruction, gated the same way the old extractor
        # is (only when faction_updates present this tick).
        faction_upds = getattr(update, "faction_updates", None)
        if isinstance(faction_upds, list) and faction_upds:
            entity_updates = getattr(update, "entity_updates", None) or {}
            removed = set(getattr(update, "entities_remove", None) or [])
            added = getattr(update, "entities_add", None) or []

            def _current_faction(eid: int, prior_ent: Any) -> Any:
                e_upd = entity_updates.get(eid)
                id_upd = getattr(e_upd, "identity", None) if e_upd is not None else None
                new_faction = getattr(id_upd, "faction_set", None) if id_upd is not None else None
                return new_faction if new_faction is not None else getattr(getattr(prior_ent, "identity", None), "faction", None)

            living_faction_ids: set = set()
            for eid, prior_ent in prior_state.entities.items():
                if eid in removed:
                    continue
                fac = _current_faction(eid, prior_ent)
                if fac is not None:
                    living_faction_ids.add(str(fac))
            for new_ent in added:
                fac = getattr(getattr(new_ent, "identity", None), "faction", None)
                if fac is not None:
                    living_faction_ids.add(str(fac))

            prior_living_faction_ids: set = set()
            for prior_ent in prior_state.entities.values():
                fac = getattr(getattr(prior_ent, "identity", None), "faction", None)
                if fac is not None:
                    prior_living_faction_ids.add(str(fac))

            for fid in (getattr(prior_state, "factions", None) or {}).keys():
                if str(fid) in living_faction_ids:
                    continue
                if str(fid) in prior_living_faction_ids:
                    events.append(SimulationEvent(
                        event_type="faction_extinct", event_category="faction",
                        tick=tick, entity_id=None, severity="WARNING",
                        source_system="event_shapers", message="",
                        payload={"faction_id": str(fid)},
                    ))

        return events


class SocialShaper:
    """SOCIAL domain shaper — social_memory_created, reputation_delta, group_joined,
    group_expelled, contract_offer_created, contract_offer_accepted, contract_completed,
    contract_lapsed, contract_expired_offer, contract_milestone_completed.

    Confirmed against `event_extractor.py:565-722` and `src/core/updates.py`:

    - `group_joined`/`group_expelled`: `EntityUpdate.group_id_set: Optional[int]` uses a `-1`
      sentinel for "left the group" (confirmed by tracing `src/engine/patches.py:210-211`'s
      `gid = None if self.group_id_set == -1 else self.group_id_set` — the actual materialization
      logic), distinct from `None` ("not touched this tick"). This was the one genuinely
      unconfirmed field in this epic's original audit — resolved here by reading the real
      mutation/application code, not assumed either way.
    - `reputation_delta`: `SocialUpdate.reputation_set: Optional[float]` — absolute new value
      (`_set` suffix convention, consistent with every other such field this epic has confirmed).
    - `social_memory_created`: `SocialUpdate.trust_delta: Dict[int, float]` — a genuine delta
      (unlike `reputation_set`), reconstructed against `prior_ent.social.trust_history` for both
      the "is new" and "significant change" checks and the absolute score the payload needs.
    - Contract lifecycle events: `StrategicUpdate.contracts_add_or_update: list[ContractState]` —
      each entry's `.status` is the new value (frozen dataclass, same pattern as `LeadState`),
      compared against `prior_ent.strategic.contracts.get(cid)`. The reap-path
      `contract_expired_offer` (contract removed, not status-transitioned) reads
      `contracts_remove` against `prior_ent`'s contracts for an `OFFERED`-status match.
    - `contract_milestone_completed`: same category of gap `belief_stale`/
      `progression_plateau_detected` already found — a purely time-based check
      (`elapsed = tick - created_tick`) that must re-scan ALL of an entity's currently-ACTIVE
      contracts every visited tick, not just ones touched this tick. Solved with the same
      reconstruction technique: merge `prior_ent.strategic.contracts` with this tick's
      `contracts_add_or_update`/`contracts_remove` deltas, then scan the full merged set.
    """

    # Mirrors EventExtractor's identically-valued class attributes (event_extractor.py:81-82).
    _SOCIAL_MEMORY_THRESHOLD = 0.3
    _CONTRACT_MILESTONE_THRESHOLDS = ((0.25, "25%"), (0.50, "50%"), (0.75, "75%"))

    # Per-run tracking, NOT durable state — mirrors EventExtractor's identically-named caches.
    _emitted_social_memory: set = set()
    _emitted_contract_milestones: set = set()

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start (Kernel.__init__) and in test
        teardown."""
        cls._emitted_social_memory.clear()
        cls._emitted_contract_milestones.clear()

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to any of this shaper's events. `mode` accepted for
        # protocol conformance only.
        events: List[SimulationEvent] = []
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue

            # group_joined / group_expelled — group_id_set uses a -1 sentinel for "left"
            group_id_set = getattr(e_upd, "group_id_set", None)
            if group_id_set is not None:
                if group_id_set == -1:
                    prior_group = getattr(prior_ent, "group_id", None)
                    events.append(SimulationEvent(
                        event_type="group_expelled", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"prior_group_id": str(prior_group)},
                    ))
                else:
                    events.append(SimulationEvent(
                        event_type="group_joined", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"group_id": str(group_id_set)},
                    ))

            social_upd = getattr(e_upd, "social", None)
            prior_social = getattr(prior_ent, "social", None)
            if social_upd is not None and prior_social is not None:
                # reputation_delta — reputation_set is an absolute new value
                new_rep = getattr(social_upd, "reputation_set", None)
                if new_rep is not None:
                    prior_rep = getattr(prior_social, "public_reputation", None)
                    if isinstance(new_rep, (int, float)) and isinstance(prior_rep, (int, float)):
                        delta = new_rep - prior_rep
                        if abs(delta) > 0.05:
                            events.append(SimulationEvent(
                                event_type="reputation_delta", event_category="social",
                                tick=tick, entity_id=eid, severity="INFO",
                                source_system="event_shapers", message="",
                                payload={"entity_id": eid, "delta": round(delta, 6)},
                            ))

                # social_memory_created — trust_delta is a genuine per-other-entity delta
                prior_trust = getattr(prior_social, "trust_history", None) or {}
                for other_id, delta_val in (getattr(social_upd, "trust_delta", None) or {}).items():
                    pair = (eid, other_id)
                    if pair in SocialShaper._emitted_social_memory:
                        continue
                    prior_score = prior_trust.get(other_id)
                    is_new = prior_score is None
                    is_significant = (
                        not is_new
                        and isinstance(delta_val, (int, float))
                        and abs(delta_val) >= SocialShaper._SOCIAL_MEMORY_THRESHOLD
                    )
                    if is_new or is_significant:
                        SocialShaper._emitted_social_memory.add(pair)
                        new_score = (prior_score or 0.0) + delta_val
                        events.append(SimulationEvent(
                            event_type="social_memory_created", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"other_entity_id": other_id, "score": round(float(new_score), 6)},
                        ))

            # Contract lifecycle events
            strategic_upd = getattr(e_upd, "strategic", None)
            prior_strategic = getattr(prior_ent, "strategic", None)
            if strategic_upd is None or prior_strategic is None:
                continue
            prior_contracts = getattr(prior_strategic, "contracts", None) or {}
            # Same-tick removals win — a contract can be BOTH status-transitioned to EXPIRED via
            # contracts_add_or_update (ContractLifecycleSystem.check_expirations()) AND reaped via
            # contracts_remove (ContractLifecycleSystem.reap_expired_offers()) in the SAME tick for
            # the same OFFERED-and-expired contract (confirmed by tracing both call sites,
            # src/systems/social_systems/contracts.py:65-76,316-343). The old extractor is immune
            # to this because it reads a single materialized dict (a contract is either present
            # with a new status OR absent, never both); a shaper reading the raw update records
            # separately must reconcile this itself — found as a real ~2x over-fire on
            # contract_expired_offer via a real kernel run, not assumed correct.
            removed_this_tick = set(getattr(strategic_upd, "contracts_remove", None) or ())

            for cs in (getattr(strategic_upd, "contracts_add_or_update", None) or []):
                cid = cs.id
                if cid in removed_this_tick:
                    continue
                prior_cs = prior_contracts.get(cid)
                new_status = getattr(getattr(cs, "status", None), "name", str(getattr(cs, "status", "")))
                if prior_cs is None:
                    if new_status == "OFFERED":
                        events.append(SimulationEvent(
                            event_type="contract_offer_created", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"contract_id": cid},
                        ))
                    continue
                prior_status = getattr(getattr(prior_cs, "status", None), "name", str(getattr(prior_cs, "status", "")))
                if new_status == prior_status:
                    continue
                if prior_status == "OFFERED" and new_status == "ACTIVE":
                    events.append(SimulationEvent(
                        event_type="contract_offer_accepted", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"contract_id": cid},
                    ))
                elif new_status == "FULFILLED":
                    events.append(SimulationEvent(
                        event_type="contract_completed", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"contract_id": cid},
                    ))
                elif new_status == "EXPIRED":
                    if prior_status == "ACTIVE":
                        events.append(SimulationEvent(
                            event_type="contract_lapsed", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"contract_id": cid},
                        ))
                    elif prior_status == "OFFERED":
                        events.append(SimulationEvent(
                            event_type="contract_expired_offer", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"contract_id": cid},
                        ))

            # contract_expired_offer — reap path (contract removed entirely, not transitioned)
            for cid in (getattr(strategic_upd, "contracts_remove", None) or ()):
                prior_cs = prior_contracts.get(cid)
                if prior_cs is None:
                    continue
                prior_status = getattr(getattr(prior_cs, "status", None), "name", str(getattr(prior_cs, "status", "")))
                if prior_status == "OFFERED":
                    events.append(SimulationEvent(
                        event_type="contract_expired_offer", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={"contract_id": cid},
                    ))

            # contract_milestone_completed — purely time-based, must re-scan ALL current ACTIVE
            # contracts every visited tick (same reconstruction pattern as belief_stale)
            current_contracts = dict(prior_contracts)
            for cs in (getattr(strategic_upd, "contracts_add_or_update", None) or []):
                current_contracts[cs.id] = cs
            for cid in (getattr(strategic_upd, "contracts_remove", None) or ()):
                current_contracts.pop(cid, None)

            for cid, cs in current_contracts.items():
                cs_status = getattr(getattr(cs, "status", None), "name", str(getattr(cs, "status", "")))
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
                for threshold, label in SocialShaper._CONTRACT_MILESTONE_THRESHOLDS:
                    gate_key = f"{cid}:{label}"
                    if gate_key in SocialShaper._emitted_contract_milestones:
                        continue
                    if progress >= threshold:
                        SocialShaper._emitted_contract_milestones.add(gate_key)
                        events.append(SimulationEvent(
                            event_type="contract_milestone_completed", event_category="social",
                            tick=tick, entity_id=source_id, severity="INFO",
                            source_system="event_shapers", message="",
                            payload={"contract_id": cid, "milestone": label,
                                     "kind": str(getattr(cs, "kind", ""))},
                        ))

        return events


class NarrativeShaper:
    """NARRATIVE domain shaper — quest_event (TCK-20260807-QUEST-EVENT-PUSH-MIGRATION).

    `event_extractor.py`'s Phase 2 push-migration epic left `quest_event` (entity-project quest
    lifecycle, `SOC-241`, scored by `NarrativeScorer`) unmigrated based on a raw-JSONL inspection
    that concluded it "already come[s] from `quest_system`, a separate live-emission source" —
    that conclusion was wrong (confirmed by reading `event_extractor.py:787-823` directly: it
    constructs `QuestEvent` right there, in the ordinary post-tick diffing loop, gated by neither
    push flag). The mechanism the epic's inspection likely actually saw is
    `QuestOpportunityRewardSystem`'s `WorldEvent(category=QUEST_COMPLETED)`
    (`src/engine/pipeline_phases/quest_opportunity_rewards.py`) -- a genuinely different, already-
    live mechanism for a different registry (`state.quest_registry`'s `QuestOpportunity`
    entries), not the entity-project `QuestState` lifecycle this shaper covers.

    Reconstructs each entity's current `projects` dict via `_current_projects()` (same
    prior-full-state + this-tick-delta pattern as `_current_leads()`) and diffs `QuestState`
    instances' `quest_status` field against the prior snapshot -- byte-identical logic to
    `event_extractor.py`'s own block, just reading `update` instead of post-apply
    `current_state`. No per-run state needed (unlike `StrategyShaper`/`FactionShaper`): this is a
    same-tick prior-vs-current diff with no "once per run" gating semantics.
    """

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to quest_event (same confirmation as EconomyShaper/
        # FactionShaper/StrategyShaper — not one of event_extractor.py's 3 mode-gated types).
        # `mode` accepted for EventShaper protocol conformance only.
        events: List[SimulationEvent] = []
        now = time.time()
        entity_updates = getattr(update, "entity_updates", None) or {}

        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue

            strategic_upd = getattr(e_upd, "strategic", None)
            if strategic_upd is None:
                continue

            prior_projects = getattr(getattr(prior_ent, "strategic", None), "projects", None) or {}
            current_projects = _current_projects(prior_ent, strategic_upd)

            for qid, qstate in current_projects.items():
                if not isinstance(qstate, QuestState):
                    continue
                prior_qstate = prior_projects.get(qid)

                # Same field/payload contract as event_extractor.py's own block
                # (TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG): quest_status (QuestStatus), not the
                # generic ProjectState.status; explicit payload={"status": ...} since QuestEvent
                # .status is a top-level Pydantic field never copied into .payload by
                # ObservabilityEventEnvelope.from_simulation_event().
                if prior_qstate is None or not isinstance(prior_qstate, QuestState):
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status="started",
                        payload={"status": "started"},
                    ))
                elif prior_qstate.quest_status != qstate.quest_status:
                    status_str = qstate.quest_status.name.lower()
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status=status_str,
                        payload={"status": status_str},
                    ))

        return events


QUEST_SHAPER_REGISTRY: dict[str, list[EventShaper]] = {
    "narrative": [NarrativeShaper()],
}


class AgencyShaper:
    """AGENCY domain shaper — commitment_abandoned, rejection_cascade_tick
    (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP,
    TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP).

    Two source mechanisms, both confirmed against `event_extractor.py`'s existing behavior:

    1. `commitment_abandoned` — reconstructs each entity's current `projects` dict via
       `_current_projects()` (same helper `NarrativeShaper` uses) and checks the generic
       `ProjectState.status` (NOT `QuestState.quest_status` — this applies to ANY project kind,
       quest or not) for an ABANDONED transition. `hp`/`max_hp` are reconstructed from
       `prior_ent.combat` + this tick's `CombatUpdate.hp_delta`/`max_hp_delta` (falling back to 0
       when no combat update exists this tick) — the same prior-plus-delta reconstruction
       `CombatShaper` already uses for its own `new_hp` computation, since this event needs the
       POST-mutation hp/max_hp (matching `event_extractor.py`'s own read of `current_state`'s
       `entity.combat.hp`), not the prior tick's value.
    2. `rejection_cascade_tick` — a pure `update`-derived population aggregate (counts rejected
       `intent_results` across all of `update.entity_updates`), no `prior_state` comparison
       needed at all — already the simplest possible shape for this architecture.

    Deliberately NOT colocated with `NarrativeShaper` despite sharing `_current_projects()`:
    `run_shadow_shapers()` gates delivery per-registry, not per-event, and
    `ENABLE_PUSH_EVENT_SHAPERS_QUEST` already defaults `ON` — colocating here would deliver these
    two events live immediately with no independent verification window, so this shaper gets its
    own dedicated `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag/registry instead, mirroring exactly why
    `NarrativeShaper` itself needed its own flag apart from `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`.
    """

    def shape(
        self,
        prior_state: AuthoritativeState,
        update: StateUpdate,
        tick: int,
        mode: ObservabilityMode = ObservabilityMode.LIGHT,
    ) -> List[SimulationEvent]:
        # No volumization rule applies to either event (same confirmation as EconomyShaper/
        # FactionShaper/StrategyShaper/NarrativeShaper — neither is one of event_extractor.py's 3
        # mode-gated types). `mode` accepted for EventShaper protocol conformance only.
        events: List[SimulationEvent] = []
        entity_updates = getattr(update, "entity_updates", None) or {}

        # commitment_abandoned
        for eid, e_upd in entity_updates.items():
            prior_ent = prior_state.entities.get(eid)
            if prior_ent is None:
                continue

            strategic_upd = getattr(e_upd, "strategic", None)
            if strategic_upd is None:
                continue

            prior_projects = getattr(getattr(prior_ent, "strategic", None), "projects", None) or {}
            current_projects = _current_projects(prior_ent, strategic_upd)

            for qid, qstate in current_projects.items():
                prior_qstate = prior_projects.get(qid)
                if prior_qstate is None:
                    continue
                if not (getattr(prior_qstate, "status", None) != ProjectStatus.ABANDONED
                        and getattr(qstate, "status", None) == ProjectStatus.ABANDONED):
                    continue

                combat_upd = getattr(e_upd, "combat", None)
                prior_hp = getattr(getattr(prior_ent, "combat", None), "hp", 100)
                prior_max_hp = getattr(getattr(prior_ent, "combat", None), "max_hp", 100)
                hp = prior_hp + getattr(combat_upd, "hp_delta", 0)
                max_hp = prior_max_hp + getattr(combat_upd, "max_hp_delta", 0)

                classification = AbandonmentEvaluator.evaluate_abandonment(
                    hp, max_hp,
                    is_party_in_combat=False,   # Q1: default; see plan decisions (P1F-ABANDONMENT-TYPE)
                    is_greed_driven=False,       # Q1: default; see plan decisions
                )
                if classification.category != AbandonmentCategory.SURVIVAL:
                    events.append(SimulationEvent(
                        event_type="commitment_abandoned", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_shapers", message="",
                        payload={
                            "entity_id": eid,
                            "project_id": qid,
                            "category": classification.category.value,
                            "penalty": classification.penalty,
                            "tick": tick,
                        },
                    ))

        # rejection_cascade_tick — population aggregate, update-only, no prior_state needed
        total_rejections = 0
        reason_counts: dict[str, int] = {}
        for e_upd in entity_updates.values():
            for ir in (getattr(e_upd, "intent_results", None) or []):
                if not getattr(ir, "accepted", True):
                    total_rejections += 1
                    reason = getattr(ir, "reason", None) or "unknown"
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if total_rejections >= _MAX_CONSECUTIVE_REJECTIONS:
            dominant = max(reason_counts, key=reason_counts.__getitem__) if reason_counts else "unknown"
            events.append(SimulationEvent(
                event_type="rejection_cascade_tick", event_category="strategy",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_shapers", message="",
                payload={
                    "count": total_rejections,
                    "tick": tick,
                    "dominant_failure_reason": dominant,
                },
            ))

        return events


AGENCY_SHAPER_REGISTRY: dict[str, list[EventShaper]] = {
    "agency": [AgencyShaper()],
}


# Phase 2 domains (TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC), gated by their
# own ENABLE_PUSH_EVENT_SHAPERS_PHASE2 flag inside run_shadow_shapers() itself, NOT folded into
# SHAPER_REGISTRY above. Default was "OFF" during Phase 2's build (SHADOW-validated across
# children 2-7); flipped to "ON" by TCK-20260806-PUSH-CUTOVER-PHASE2 — this is now the live
# default path for Phase 2's ~50 events, same exception class as ENABLE_PUSH_EVENT_SHAPERS.
# ENABLE_PUSH_EVENT_SHAPERS already defaults ON (Phase 1's cutover) and kernel.py's own ON/SHADOW
# switch applies uniformly to this whole module's return value — a Phase 2 shaper added directly
# to SHAPER_REGISTRY would have gone live immediately with no SHADOW window during Phase 2's own
# build, since event_extractor.py's branches for these new domains weren't flag-gated at that
# point either. Confirmed as a real bug (self_model_updated/cooperation_event double-firing) via a
# real kernel run before this separate flag/registry split was added — see
# stored_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY/investigation.md.
PHASE2_SHAPER_REGISTRY: dict[str, list[EventShaper]] = {
    "strategy": [StrategyShaper()],
    "progression": [ProgressionShaper()],
    "world_dynamics": [WorldDynamicsShaper()],
    "social": [SocialShaper()],
    "deferred_instrumentation": [DeferredInstrumentationShaper()],
}


def run_shadow_shapers(
    prior_state: AuthoritativeState,
    update: StateUpdate,
    tick: int,
    mode: ObservabilityMode = ObservabilityMode.LIGHT,
) -> List[SimulationEvent]:
    """Run every registered Phase 1 shaper (SHAPER_REGISTRY, live-delivered whenever
    ENABLE_PUSH_EVENT_SHAPERS is not OFF, per Kernel._phase_observability's own switch) plus any
    Phase 2 shaper whose own ENABLE_PUSH_EVENT_SHAPERS_PHASE2 flag is "ON" or "SHADOW".

    Phase 2 shapers are gated INSIDE this function, not by the caller: when
    ENABLE_PUSH_EVENT_SHAPERS_PHASE2="SHADOW", their events are constructed (for real-corpus
    validation) but excluded from the returned list, so Kernel._phase_observability's own
    Phase-1-flag-driven delivery decision never sees them — this is what keeps a Phase 2 shaper
    genuinely undelivered even though the Phase 1 flag it shares this function with already
    defaults ON. Default OFF: Phase 2 shapers are not constructed at all, zero overhead.

    Also computes `conservation_law_verified` (a cross-shaper aggregation, not a single domain's
    job — event_extractor.py's own version checks its own already-constructed `events` list for
    the tick; this function does the equivalent, checking the Phase 1 shapers' combined output
    computed just above) as part of the Phase 2 block, subject to the same ON/SHADOW gating as
    every other Phase 2 event.
    """
    events: List[SimulationEvent] = []
    for domain, shapers in SHAPER_REGISTRY.items():
        for shaper in shapers:
            events.extend(shaper.shape(prior_state, update, tick, mode))

    # Default "ON" (TCK-20260806-PUSH-CUTOVER-PHASE2 — was "OFF" pre-cutover, matching
    # ENABLE_PUSH_EVENT_SHAPERS's own default flip in Phase 1). Must stay in lockstep with
    # event_extractor.py's own `_push_shapers_phase2_active` default read — a mismatch between the
    # two (this defaulting OFF while the extractor's own guard defaults to suppressed) would
    # blackout every Phase 2 event with no explicit override, found and fixed during this ticket's
    # own real-kernel verification.
    phase2_mode = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_PHASE2", "ON")
    if phase2_mode in ("ON", "SHADOW"):
        phase2_events: List[SimulationEvent] = []
        for domain, shapers in PHASE2_SHAPER_REGISTRY.items():
            for shaper in shapers:
                phase2_events.extend(shaper.shape(prior_state, update, tick, mode))

        # conservation_law_verified — throttled (1 per 50 ticks), fires when an economy
        # transaction occurred this tick (checked against `events`, the Phase 1 shapers'
        # combined output computed above, mirroring event_extractor.py's own "check
        # already-constructed events" pattern).
        if tick % 50 == 0 and any(e.event_type in _CONSERVATION_ECONOMY_TYPES for e in events):
            phase2_events.append(SimulationEvent(
                event_type="conservation_law_verified", event_category="economy",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_shapers", message="",
                payload={"tick": tick},
            ))

        if phase2_mode == "ON":
            events.extend(phase2_events)
        else:
            logger.debug(
                "push_event_shapers_phase2 SHADOW: %d events constructed (tick=%d, not delivered)",
                len(phase2_events), tick,
            )

    # Quest domain (TCK-20260807-QUEST-EVENT-PUSH-MIGRATION), gated by its OWN
    # ENABLE_PUSH_EVENT_SHAPERS_QUEST flag -- NOT folded into ENABLE_PUSH_EVENT_SHAPERS_PHASE2,
    # which already defaults "ON": reusing it would deliver this shaper live immediately with no
    # SHADOW window, the exact double-fire-risk mistake TCK-20260806-PUSH-SHAPER-REGISTRY-
    # STRATEGY already found and fixed once for Phase 2 itself (see PHASE2_SHAPER_REGISTRY's own
    # comment above). Default "ON": verified via real-kernel checks (both SHADOW-construct-only
    # and ON-deliver correctness, no double-fire against event_extractor.py's own rollback path)
    # during this same ticket, so an unconfigured run gets the new default behavior directly,
    # matching Phase 1/Phase 2's own "verify then default ON" precedent.
    quest_mode = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_QUEST", "ON")
    if quest_mode in ("ON", "SHADOW"):
        quest_events: List[SimulationEvent] = []
        for domain, shapers in QUEST_SHAPER_REGISTRY.items():
            for shaper in shapers:
                quest_events.extend(shaper.shape(prior_state, update, tick, mode))

        if quest_mode == "ON":
            events.extend(quest_events)
        else:
            logger.debug(
                "push_event_shapers_quest SHADOW: %d events constructed (tick=%d, not delivered)",
                len(quest_events), tick,
            )

    # Agency domain (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP,
    # TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP), gated by its OWN
    # ENABLE_PUSH_EVENT_SHAPERS_AGENCY flag -- same reasoning as the Quest block above: not
    # folded into any already-ON flag, own dedicated SHADOW-validation window. Default "ON":
    # verified via real-kernel checks (both SHADOW-construct-only and ON-deliver correctness, no
    # double-fire against event_extractor.py's own rollback path) during this same ticket.
    agency_mode = (getattr(prior_state, "feature_flags", None) or {}).get(
        "ENABLE_PUSH_EVENT_SHAPERS_AGENCY", "ON")
    if agency_mode in ("ON", "SHADOW"):
        agency_events: List[SimulationEvent] = []
        for domain, shapers in AGENCY_SHAPER_REGISTRY.items():
            for shaper in shapers:
                agency_events.extend(shaper.shape(prior_state, update, tick, mode))

        if agency_mode == "ON":
            events.extend(agency_events)
        else:
            logger.debug(
                "push_event_shapers_agency SHADOW: %d events constructed (tick=%d, not delivered)",
                len(agency_events), tick,
            )

    return events
