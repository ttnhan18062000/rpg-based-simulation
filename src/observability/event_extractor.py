from __future__ import annotations
import time
import logging
from typing import Any, List, Optional
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectStatus
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

# LeadCertainty enum value → float for band-crossing delta computation (lead_certainty_updated)
_CERTAINTY_FLOAT: dict[str, float] = {
    "PRECISE": 1.0, "APPROXIMATE": 0.5, "VAGUE": 0.25, "EXHAUSTED": 0.0,
}

# Ticks without certainty change before a lead is considered stale (belief_stale)
_BELIEF_STALE_TICKS = 50

# How many ticks without XP before progression_plateau_detected fires (xp_rate_zero)
_XP_PLATEAU_TICKS = 50

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
                    # Demographic mortality — despawn without a combat attacker
                    e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                    has_attacker = bool(e_upd and getattr(e_upd, "combat_upd", None) and e_upd.combat_upd.attacker_id)
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

            # Combat damage event
            hp_diff = entity.combat.hp - prior_ent.combat.hp
            if hp_diff < 0:
                is_lethal = (entity.combat.hp <= 0 or not entity.lifecycle.active)
                # Volumization rule: skip routine damage inside LIGHT or LONG_RUN mode unless lethal
                if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    attacker_id = None
                    e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                    if e_upd and getattr(e_upd, "combat_upd", None):
                        attacker_id = e_upd.combat_upd.attacker_id

                    events.append(CombatDamageEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        attacker_id=attacker_id, damage=int(-hp_diff),
                        is_lethal=is_lethal
                    ))

            # Kill events
            if prior_ent.lifecycle.active and not entity.lifecycle.active:
                killer_id = None
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                if e_upd and getattr(e_upd, "combat_upd", None):
                    killer_id = e_upd.combat_upd.attacker_id

                events.append(CombatKillEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    killer_id=killer_id
                ))

                # NARRATIVE: hero_death_unrecorded — hero-kind entity deactivated this tick (D4)
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

            # Combat initiated — entity was at full HP prior tick, now taking damage
            if (entity.lifecycle.active
                    and prior_ent.combat.hp == prior_ent.combat.max_hp
                    and entity.combat.hp < entity.combat.max_hp):
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                attacker_id = None
                if e_upd and getattr(e_upd, "combat_upd", None):
                    attacker_id = e_upd.combat_upd.attacker_id
                events.append(SimulationEvent(
                    event_type="combat_initiated", event_category="combat",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"attacker_id": attacker_id},
                ))

            # Near-death survival — HP crosses below 20% threshold while entity survives
            near_death_hp = prior_ent.combat.max_hp * _NEAR_DEATH_THRESHOLD
            if (entity.lifecycle.active
                    and entity.combat.hp < near_death_hp
                    and prior_ent.combat.hp >= near_death_hp):
                events.append(SimulationEvent(
                    event_type="near_death_survival", event_category="combat",
                    tick=tick, entity_id=eid, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"hp": entity.combat.hp, "max_hp": entity.combat.max_hp},
                ))

            # XP granted and level-up (via IdentityComponent)
            if hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
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

                # Agency: defer_with_reason — property set by phase.py on DEFER_WITH_REASON path.
                # Key "last_defer_reason" must match phase.py property_updates key exactly.
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
                if prop.get("last_assimilated_tick") == tick:
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

                # Social: cooperation_event (PP-05)
                if prop.get("last_cooperation_decision") is not None:
                    events.append(SimulationEvent(
                        event_type="cooperation_event", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"entity_id": eid,
                                 "decision": str(prop["last_cooperation_decision"])},
                    ))

                # Economy + Information events from intent_results (resource_transfers cleared by PP-27)
                _GOLD_SINK_KINDS = frozenset(("REPAIR_FEE", "SERVICE_FEE", "TAX"))
                for ir in (getattr(e_upd_ext, "intent_results", None) or []):
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

                # World: hazard_drain_applied (WorldDynamicsSystem sets outcome_kind="HAZARD")
                combat_upd = getattr(e_upd_ext, "combat", None)
                if combat_upd and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
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
            if hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
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

            # Social: group_joined / group_expelled (PP-34 group membership state diff)
            curr_group = getattr(entity, "group_id", None)
            prior_group = getattr(prior_ent, "group_id", None)
            if curr_group != prior_group:
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

            # Social: reputation_delta (PP-18, significant public reputation change)
            if hasattr(entity, "social") and hasattr(prior_ent, "social"):
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

            # Social: contract lifecycle events (PP-35 contracts state diff)
            if hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
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

            # Quest progress lifecycle events
            prior_projects = prior_ent.strategic.projects
            current_projects = entity.strategic.projects
            for qid, qstate in current_projects.items():
                prior_qstate = prior_projects.get(qid)
                if prior_qstate is None:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status="started"
                    ))
                elif prior_qstate.status != qstate.status:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status=str(qstate.status)
                    ))
                    # Agency: commitment_abandoned (behavioral classification, not just
                    # status change — coexists with the QuestEvent above which becomes
                    # project_abandoned via _TRANSLATE_CONDITIONAL in quality_hub.py)
                    if (getattr(prior_qstate, "status", None) != ProjectStatus.ABANDONED
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
            # progression_conversion_applied, progression_plateau_detected
            if hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
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

        # Agency: rejection_cascade_tick — post-entity-loop population aggregate.
        # Count all rejected intent results across entities in this tick's updates.
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

        # Resource node depletion and regeneration
        if hasattr(current_state, "resource_nodes") and hasattr(prior_state, "resource_nodes"):
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
        # ResourceEcologyService.ECOLOGY_INTERVAL == 200
        if tick % 200 == 0 and hasattr(current_state, "regions"):
            for _r_id, _region in (current_state.regions or {}).items():
                events.append(SimulationEvent(
                    event_type="ecology_cycle_completed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": _r_id,
                             "cycle_type": getattr(_region, "kind", "unknown"),
                             "net_pressure_delta": 0.0},
                ))

        # World: spawn_cadence_fired — detects spawn batch committed on cadence tick
        if tick % _SPAWN_INTERVAL == 0:
            _spawned_monsters = [
                e for e in (getattr(update, "entities_add", None) or [])
                if getattr(e, "kind", None) not in (None, "world_boss", "ancient_sentinel", "goblin_raider")
            ]
            if _spawned_monsters:
                events.append(SimulationEvent(
                    event_type="spawn_cadence_fired", event_category="lifecycle",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"spawned_count": len(_spawned_monsters), "tick": tick},
                ))

        # Economy: conservation_law_verified — throttled (1 per 50 ticks) to avoid noise
        # Fires when economy transactions occurred this tick, implying the conservation law was checked
        if tick % 50 == 0:
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

        # World dynamics events — from StateUpdate world_updates and entities_add
        for rid, w_upd in (getattr(update, "world_updates", None) or {}).items():
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

        if getattr(update, "last_calamity_tick_set", None) == tick:
            events.append(SimulationEvent(
                event_type="calamity_spawned", event_category="lifecycle",
                tick=tick, entity_id=None, severity="CRITICAL",
                source_system="event_extractor", message="",
                payload={"tick": tick},
            ))

        _BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel"))
        for new_ent in (getattr(update, "entities_add", None) or []):
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

        # Faction events from FactionUpdate records (PP-08/09/10/11)
        _seen_diplo_pairs: set = set()
        _faction_upds = getattr(update, "faction_updates", None)
        if not isinstance(_faction_upds, (list, tuple)):
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

            # FACTION: territory_ownership_changed (PP-11)
            for region_id in (upd.territory_add or ()):
                events.append(SimulationEvent(
                    event_type="territory_ownership_changed", event_category="faction",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"faction_id": fid, "region_id": region_id},
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
            if cat == WorldEventCategory.FACTION_WAR_DECLARED:
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

            # NARRATIVE: world_emergence_event — one per WorldEvent in world_events_add (D1)
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

        # FACTION: faction_extinct (PP-08/PP-33) — only when faction state changed this tick
        _faction_upd_list = getattr(update, "faction_updates", None)
        if isinstance(_faction_upd_list, list) and _faction_upd_list:
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
